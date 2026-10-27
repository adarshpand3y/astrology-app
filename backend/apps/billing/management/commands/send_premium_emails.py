from django.core.management.base import BaseCommand

from apps.billing import emails


class Command(BaseCommand):
    help = 'Send the due "unlock Pro on the website" emails (run hourly, e.g. from cron).'

    def handle(self, *args, **opts):
        if not emails.enabled():
            self.stdout.write("PREMIUM_CHECKOUT_URL is not set; nothing sent.")
            return
        self.stdout.write(self.style.SUCCESS(f"Sent {emails.send_all_due()} email(s)."))
