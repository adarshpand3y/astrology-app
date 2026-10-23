"""Seed a ready-to-use demo account with ~1.5 months of remedy and journal activity (see USAGE)."""
import random
from argparse import RawDescriptionHelpFormatter
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError, DjangoHelpFormatter
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.services import subscription_for
from apps.journal.models import JournalEntry
from apps.journal.services import DEFAULT_TAGS
from apps.places.models import Place
from apps.profiles.serializers import BirthProfileSerializer
from apps.remedies import services
from apps.remedies.models import RemedyLog, UserRemedy
from apps.vedic.content import goals as gc

# Used only when the places table is empty (load_places not run).
FALLBACK_PLACES = {
    "Bengaluru": dict(geonames_id=1277333, name="Bengaluru", ascii_name="Bengaluru", admin1="Karnataka",
                      country_code="IN", country="India", latitude=12.97194, longitude=77.59369,
                      timezone="Asia/Kolkata", population=8443675),
    "Pune": dict(geonames_id=1259229, name="Pune", ascii_name="Pune", admin1="Maharashtra",
                 country_code="IN", country="India", latitude=18.51957, longitude=73.85535,
                 timezone="Asia/Kolkata", population=2935744),
}


def place(name: str) -> Place:
    found = Place.objects.filter(name=name).order_by("-population").first()
    if found:
        return found
    obj, _ = Place.objects.get_or_create(geonames_id=FALLBACK_PLACES[name]["geonames_id"], defaults=FALLBACK_PLACES[name])
    return obj


USAGE = """\
The user is verified and onboarded (birth chart, goals, suggested remedies), with
remedy completions (including some missed days) and journal check-ins up to today,
so the streak, heatmap and trends screens have data. Sign in to the app with the
--email and --password values.

examples:
  python manage.py seed_demo
      demo@example.com / Demo-pass-123, free plan, goal: marriage, last 45 days
  python manage.py seed_demo --pro --goals marriage,career --days 60
      Pro user with two goals (more than one goal needs --pro) and 60 days of history
  python manage.py seed_demo --reset
      delete the existing demo account and seed it again
  python manage.py seed_demo --email riya@example.com --password Riya-pass-123 --seed 3
      a second account with a different (but repeatable) activity pattern
  python manage.py seed_demo --clear
      delete ALL users and their data (asks to confirm; only when DEBUG=True)
  python manage.py seed_demo --clear --noinput && python manage.py seed_demo
      start from an empty database with just the demo account
"""


class HelpFormatter(DjangoHelpFormatter, RawDescriptionHelpFormatter):
    """Django's option ordering, but keep the line breaks in the usage examples."""


class Command(BaseCommand):
    help = ("Create a demo user (profile, goals, remedies) with remedy and journal activity for the last N days, "
            "or with --clear wipe all user data (DEBUG only).")

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, formatter_class=HelpFormatter, **kwargs)
        parser.epilog = USAGE
        return parser

    def add_arguments(self, parser):
        parser.add_argument("--email", default="demo@example.com", help="login email (default demo@example.com)")
        parser.add_argument("--password", default="Demo-pass-123", help="login password (default Demo-pass-123)")
        parser.add_argument("--name", default="Ananya Rao", help="name on the account and birth chart")
        parser.add_argument("--days", type=int, default=45, help="days of history, ending today (default 45)")
        parser.add_argument("--goals", default="", help=f"comma-separated, from: {', '.join(gc.GOAL_KEYS)} "
                                 "(default: marriage; marriage,career with --pro)")
        parser.add_argument("--pro", action="store_true", help="put the user on Pro (allows up to 3 goals)")
        parser.add_argument("--reset", action="store_true", help="delete an existing user with this email first")
        parser.add_argument("--seed", type=int, default=7, help="random seed, for repeatable activity")
        parser.add_argument("--clear", action="store_true",
                            help="instead of seeding, delete ALL users and everything they own (charts, remedies, "
                                 "logs, journal, subscriptions, tokens) plus sessions; places are kept. "
                                 "Only allowed when DEBUG=True")
        parser.add_argument("--noinput", "--no-input", action="store_false", dest="interactive",
                            help="with --clear: don't ask for confirmation")

    def handle(self, *args, email, password, name, days, goals, pro, reset, seed, clear, interactive, **opts):
        if clear:
            return self.clear(interactive)
        email = email.lower().strip()
        goals = [g.strip() for g in goals.split(",") if g.strip()] or (["marriage", "career"] if pro else ["marriage"])
        unknown = [g for g in goals if g not in gc.GOAL_KEYS]
        if unknown:
            raise CommandError(f"Unknown goal(s): {', '.join(unknown)}. Choose from: {', '.join(gc.GOAL_KEYS)}")
        limit = gc.MAX_GOALS if pro else gc.FREE_GOALS
        if len(goals) > limit:
            raise CommandError(f"Pro users can have at most {limit} goals." if pro
                               else "Free users can have only 1 goal; add --pro for up to 3.")
        if not 1 <= days <= 400:
            raise CommandError("--days must be between 1 and 400.")

        existing = User.objects.filter(email__iexact=email).first()
        if existing and not reset:
            raise CommandError(f"{email} already exists. Re-run with --reset to replace it.")

        rng = random.Random(seed)
        with transaction.atomic():
            if existing:
                existing.delete()
            user, profile, today = self.create_account(email, password, name, pro)
            start = today - timedelta(days=days - 1)
            services.set_goals(user, profile, goals)
            remedies = list(services.active(user))
            # Backdate the remedies so the heatmap counts them as due from the first day.
            UserRemedy.objects.filter(user=user).update(
                created_at=timezone.now() - timedelta(days=days))
            self.personalise(remedies)
            logs = self.remedy_activity(remedies, start, today, rng)
            entries = self.journal_activity(user, start, today, rng)

        streak = services.streak(user, today)
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {email} / {password} ({'Pro' if pro else 'free'})\n"
            f"  goals: {', '.join(goals)}, {len(remedies)} remedies\n"
            f"  {start} to {today}: {logs} remedies done, {entries} journal entries, "
            f"current streak {streak['current']}, best {streak['best']}"))

    def clear(self, interactive):
        """Wipe all user data. Everything user-owned cascades from User; reference data (places) stays."""
        if not settings.DEBUG:
            raise CommandError("--clear only runs with DEBUG=True. Refusing to delete data.")
        users = User.objects.count()
        if not users and not Session.objects.exists():
            self.stdout.write("Nothing to clear: there are no users.")
            return
        if interactive:
            db = connection.settings_dict["NAME"]
            answer = input(f"This deletes ALL {users} user(s) and all their data from {db}.\n"
                           "Type 'yes' to continue: ")
            if answer.strip().lower() != "yes":
                raise CommandError("Cancelled; nothing was deleted.")
        with transaction.atomic():
            total, per_model = User.objects.all().delete()
            sessions, _ = Session.objects.all().delete()
        counts = ", ".join(f"{n} {label.split('.')[-1]}" for label, n in sorted(per_model.items()) if n)
        self.stdout.write(self.style.SUCCESS(f"Cleared {total + sessions} rows: {counts}"
                                             + (f", {sessions} Session" if sessions else "")))

    def create_account(self, email, password, name, pro):
        birth, home = place("Bengaluru"), place("Pune")
        user = User.objects.create_user(email=email, password=password, full_name=name,
                                        is_email_verified=True, current_place=home)
        ps = BirthProfileSerializer(data={"name": name, "relation": "self", "birth_date": "1994-08-14",
                                          "birth_time": "03:42", "place_id": birth.id})
        ps.is_valid(raise_exception=True)
        profile = ps.save(owner=user)
        user.active_profile = profile
        user.save(update_fields=["active_profile"])
        if pro:
            sub = subscription_for(user)
            sub.plan, sub.pro_until, sub.source = "pro", None, "admin"
            sub.save()
        today = timezone.now().astimezone(ZoneInfo(home.timezone)).date()
        return user, profile, today

    def personalise(self, remedies):
        """One edited remedy, so the demo shows the 'edited' state: a shorter daily japa."""
        mantra = next((r for r in remedies if r.kind == "mantra"), None)
        if mantra:
            mantra.target, mantra.how = 54, "Half a mala before work, facing east. I'll go back to 108 on weekends."
            mantra.save(update_fields=["target", "how"])

    def remedy_activity(self, remedies, start, today, rng) -> int:
        """A believable practice: strong start, a dip mid-way, a clean streak over the last week."""
        logs, done = [], 0
        total = (today - start).days + 1
        for i in range(total):
            day = start + timedelta(days=i)
            phase = i / max(total - 1, 1)
            recent = (today - day).days < 7
            if not recent and rng.random() < (0.28 if 0.4 < phase < 0.6 else 0.1):
                continue  # a missed day
            for r in remedies:
                info = services.effective(r, "en")
                if not services.is_due(r, day, info):
                    continue
                chance = 0.97 if recent else (0.85 if r.kind == "mantra" else 0.65)
                target = info["target"]
                if rng.random() < chance:
                    logs.append(RemedyLog(remedy=r, date=day, count=target, completed=True))
                    done += 1
                elif target > 1 and rng.random() < 0.5:
                    logs.append(RemedyLog(remedy=r, date=day, count=rng.randint(1, target - 1), completed=False))
        RemedyLog.objects.bulk_create(logs)
        return done

    def journal_activity(self, user, start, today, rng) -> int:
        tags = DEFAULT_TAGS["en"]
        notes = ["", "", "", "Slept well.", "Long day at work.", "Calm evening with family.", "Felt scattered."]
        entries = []
        for i in range((today - start).days + 1):
            day = start + timedelta(days=i)
            if rng.random() < 0.7:
                entries.append(JournalEntry(user=user, date=day, rating=rng.choices([2, 3, 4, 5], [1, 3, 4, 2])[0],
                                            tags=rng.sample(tags, rng.randint(0, 2)), note=rng.choice(notes)))
        JournalEntry.objects.bulk_create(entries)
        return len(entries)
