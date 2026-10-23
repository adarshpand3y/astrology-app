from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.services import subscription_for


class Command(BaseCommand):
    help = "Grant Pro to a user (until store billing is integrated)."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("--days", type=int, default=0, help="0 = no end date")
        parser.add_argument("--revoke", action="store_true")

    def handle(self, *args, email, days, revoke, **opts):
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise CommandError(f"No user {email}")
        sub = subscription_for(user)
        if revoke:
            sub.plan, sub.pro_until, sub.trial_ends_at = "free", None, None
        else:
            sub.plan = "pro"
            sub.pro_until = timezone.now() + timedelta(days=days) if days else None
        sub.source = "admin"
        sub.save()
        self.stdout.write(self.style.SUCCESS(f"{email}: plan={sub.plan} is_pro={sub.is_pro}"))
