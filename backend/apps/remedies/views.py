from datetime import date

from django.shortcuts import get_object_or_404
from django.utils import timezone as dj_tz
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services import is_pro, require_pro
from apps.daily.context import request_lang, resolve_profile
from apps.vedic.content import goals as gc
from apps.vedic.content.common import GLYPH, short
from apps.vedic.content.remedies import KINDS

from . import services
from .models import UserRemedy

PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]


def local_today(request) -> date:
    """The user's local date: client sends ?today=YYYY-MM-DD; fall back to the current place's tz."""
    raw = request.query_params.get("today") or (request.data.get("today") if isinstance(request.data, dict) else None)
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    place = request.user.current_place
    if place:
        from zoneinfo import ZoneInfo
        return dj_tz.now().astimezone(ZoneInfo(place.timezone)).date()
    return dj_tz.now().date()


def list_payload(request) -> dict:
    lang = request_lang(request)
    today = local_today(request)
    user = request.user
    profile = resolve_profile(request, required=False)
    services.seed_for(user, profile)
    services.sync_chart(user, profile)
    remedies = services.active(user).prefetch_related("logs")
    focus = services.focus_planets(profile) if profile else []
    return {
        "locked": not is_pro(user),
        "focus": [{"code": p, "glyph": GLYPH[p], "name": short(p, lang)} for p in focus],
        "goals": [gc.goal(g, lang) for g in user.goals if g in gc.GOAL_KEYS],
        "streak": services.streak(user, today),
        "remedies": [services.serialize(r, today, lang) for r in remedies],
    }


class FieldsSerializer(serializers.Serializer):
    """The parts of a remedy the user can write."""
    title = serializers.CharField(max_length=120, required=False, allow_blank=True)
    text = serializers.CharField(max_length=300, required=False, allow_blank=True)
    how = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    cadence = serializers.CharField(max_length=80, required=False, allow_blank=True)
    target = serializers.IntegerField(min_value=1, max_value=100000, required=False, allow_null=True)
    weekdays = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=6), min_length=1,
                                     max_length=7, required=False, allow_null=True, help_text="Sunday = 0")
    reminder = serializers.BooleanField(required=False)


class RemedyListView(APIView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT}, summary="My remedies, goals, streak and focus graha")
    def get(self, request):
        return Response(list_payload(request))

    class AddSerializer(FieldsSerializer):
        planet = serializers.ChoiceField(choices=PLANETS, required=False)
        kinds = serializers.ListField(child=serializers.ChoiceField(choices=KINDS), required=False)

        def validate(self, attrs):
            if not attrs.get("planet") and not (attrs.get("title") or "").strip():
                raise serializers.ValidationError({"title": "Give your remedy a name."})
            return attrs

    @extend_schema(request=AddSerializer, responses={201: OpenApiTypes.OBJECT},
                   summary="Add catalogue remedies for a graha ({planet, kinds}) or a custom remedy ({title, ...}) (Pro)")
    def post(self, request):
        require_pro(request.user)
        ser = self.AddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        if d.get("planet"):
            added = services.add_for_planet(request.user, d["planet"], d.get("kinds") or ["mantra", "charity"])
        else:
            fields = {f: d[f] for f in UserRemedy.OVERRIDES if d.get(f) not in (None, "")}
            added = [UserRemedy.objects.create(user=request.user, kind=UserRemedy.Kind.CUSTOM, user_added=True,
                                               reminder=d.get("reminder", True), **fields)]
        today = local_today(request)
        lang = request_lang(request)
        return Response({"remedies": [services.serialize(r, today, lang) for r in added]}, status=status.HTTP_201_CREATED)


class RemedyDetailView(APIView):
    class UpdateSerializer(FieldsSerializer):
        reset = serializers.BooleanField(required=False, help_text="Clear all edits (back to the suggested remedy).")

    def get_object(self, request, pk):
        return get_object_or_404(services.active(request.user).prefetch_related("logs"), pk=pk)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request, pk):
        return Response(services.serialize(self.get_object(request, pk), local_today(request), request_lang(request)))

    @extend_schema(request=UpdateSerializer, responses={200: OpenApiTypes.OBJECT},
                   summary="Edit a remedy: text, count, days, reminder or reset (Pro)")
    def patch(self, request, pk):
        require_pro(request.user)
        remedy = self.get_object(request, pk)
        ser = self.UpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        if "reminder" in d:
            remedy.reminder = d["reminder"]
        custom = remedy.kind == UserRemedy.Kind.CUSTOM
        if d.get("reset") and not custom:
            for f in UserRemedy.OVERRIDES:
                setattr(remedy, f, None if f in ("target", "weekdays") else "")
        for f in UserRemedy.OVERRIDES:
            if f in d:
                setattr(remedy, f, d[f] if d[f] is not None or f in ("target", "weekdays") else "")
        if custom and not remedy.title.strip():
            raise serializers.ValidationError({"title": ["Give your remedy a name."]})
        remedy.save()
        return Response(services.serialize(remedy, local_today(request), request_lang(request)))

    @extend_schema(responses={204: None}, summary="Remove a remedy (its history stays on the heatmap)")
    def delete(self, request, pk):
        remedy = self.get_object(request, pk)
        remedy.archived_at = dj_tz.now()
        remedy.save(update_fields=["archived_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RemedyProgressView(APIView):
    class ProgressSerializer(serializers.Serializer):
        count = serializers.IntegerField(min_value=0, max_value=100000, required=False)
        increment = serializers.IntegerField(min_value=1, max_value=1000, required=False)
        completed = serializers.BooleanField(required=False)
        today = serializers.DateField(required=False)

    @extend_schema(request=ProgressSerializer, responses={200: OpenApiTypes.OBJECT},
                   summary="Update today's count or mark today complete")
    def post(self, request, pk):
        remedy = get_object_or_404(services.active(request.user), pk=pk)
        ser = self.ProgressSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        today = d.get("today") or local_today(request)
        log = services.log_for(remedy, today)
        target = services.effective(remedy, "en")["target"]
        if "count" in d:
            log.count = d["count"]
        if "increment" in d:
            log.count += d["increment"]
        if log.count >= target:
            log.completed = True
        if "completed" in d:
            log.completed = d["completed"]
            if log.completed and log.count < target:
                log.count = target
        log.save()
        remedy = get_object_or_404(UserRemedy.objects.prefetch_related("logs"), pk=pk)
        lang = request_lang(request)
        return Response({"remedy": services.serialize(remedy, today, lang),
                         "streak": services.streak(request.user, today)})


class GoalsView(APIView):
    class GoalsSerializer(serializers.Serializer):
        goals = serializers.ListField(child=serializers.ChoiceField(choices=gc.GOAL_KEYS),
                                      min_length=1, max_length=gc.MAX_GOALS)

    @extend_schema(responses={200: OpenApiTypes.OBJECT},
                   summary="Goal catalogue and my goals (`max` is 1 on the free plan, 3 with Pro)")
    def get(self, request):
        lang = request_lang(request)
        pro = is_pro(request.user)
        return Response({"max": gc.MAX_GOALS if pro else gc.FREE_GOALS, "pro_max": gc.MAX_GOALS, "is_pro": pro,
                         "goals": request.user.goals, "catalogue": gc.catalogue(lang)})

    @extend_schema(request=GoalsSerializer, responses={200: OpenApiTypes.OBJECT},
                   summary="Set my goals (1 free, up to 3 with Pro) and get remedies suggested for them")
    def put(self, request):
        ser = self.GoalsSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        goals = list(dict.fromkeys(ser.validated_data["goals"]))
        if len(goals) > gc.FREE_GOALS:
            require_pro(request.user)
        services.set_goals(request.user, resolve_profile(request, required=False), goals)
        return Response(list_payload(request))


class RemedyHistoryView(APIView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT},
                   summary="Remedies done vs due per day (?days=365, max 400) for the heatmap")
    def get(self, request):
        try:
            days = min(400, max(7, int(request.query_params.get("days", 365))))
        except ValueError:
            days = 365
        return Response(services.history(request.user, local_today(request), days))
