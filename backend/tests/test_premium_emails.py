import re
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing import emails
from apps.billing.models import PremiumEmailState
from apps.billing.services import extend_pro

pytestmark = pytest.mark.django_db

CHECKOUT = "https://pages.razorpay.com/pro?email={email}"


@pytest.fixture(autouse=True)
def premium_settings(settings):
    settings.PREMIUM_CHECKOUT_URL = CHECKOUT
    settings.PREMIUM_EMAIL_DAYS = [0, 3, 7]
    settings.PUBLIC_BASE_URL = "https://api.example.com"


def make_user(email="asha@example.com", days_ago=0, verified=True):
    return User.objects.create_user(email, "Str0ng-pass-123", is_email_verified=verified,
                                    date_joined=timezone.now() - timedelta(days=days_ago))


def _premium_mail():
    return [m for m in mail.outbox if "Unsubscribe:" in m.body]


def test_first_email_sent_on_verification_with_the_configured_link():
    c = APIClient()
    c.post("/api/v1/auth/register/", {"email": "new@example.com", "password": "Str0ng-pass-123", "full_name": "N"},
           format="json")
    code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
    assert not _premium_mail()  # nothing before the email is verified
    assert c.post("/api/v1/auth/verify-email/", {"email": "new@example.com", "code": code}, format="json").status_code == 200
    [m] = _premium_mail()
    assert "https://pages.razorpay.com/pro?email=new%40example.com" in m.body
    assert "https://pages.razorpay.com/pro?email=new%40example.com" in m.alternatives[0][0]
    assert "/email/unsubscribe/" in m.body
    assert not {"List-Unsubscribe", "List-Unsubscribe-Post"} & set(m.extra_headers)  # reserved by Nitrosend


def test_off_without_a_checkout_link(settings):
    settings.PREMIUM_CHECKOUT_URL = ""
    assert not emails.send_due(make_user())
    assert not mail.outbox


def test_reminders_follow_the_schedule_once_each():
    u = make_user()
    assert emails.send_due(u)
    assert not emails.send_due(u)  # day 0 done, day 3 not due
    later = timezone.now() + timedelta(days=3, hours=1)
    assert emails.send_due(u, now=later)
    assert not emails.send_due(u, now=later)
    assert len(_premium_mail()) == 2
    assert PremiumEmailState.objects.get(user=u).steps_sent == [0, 3]


def test_overdue_steps_send_only_the_latest():
    u = make_user(days_ago=30)
    assert emails.send_all_due() == 1
    assert len(_premium_mail()) == 1
    assert PremiumEmailState.objects.get(user=u).steps_sent == [0, 3, 7]
    assert emails.send_all_due() == 0


def test_skips_pro_unverified_and_unsubscribed():
    pro = make_user("pro@example.com")
    extend_pro(pro, 30, "test")
    make_user("unverified@example.com", verified=False)
    gone = make_user("gone@example.com")
    emails.unsubscribe(gone)
    assert emails.send_all_due() == 0
    assert not _premium_mail()


def test_unsubscribe_link_needs_post():
    u = make_user()
    path = emails.unsubscribe_url(u).removeprefix("https://api.example.com")
    c = APIClient()
    assert c.get(path).status_code == 200  # confirm page only: link scanners can't unsubscribe
    assert not PremiumEmailState.objects.filter(user=u, unsubscribed_at__isnull=False).exists()
    assert c.post(path).status_code == 200
    assert PremiumEmailState.objects.get(user=u).unsubscribed_at
    assert not emails.send_due(u)
    assert c.post("/email/unsubscribe/forged-token/").status_code == 200
    assert "not valid" in c.get("/email/unsubscribe/forged-token/").content.decode()


def test_failed_send_is_retried(monkeypatch):
    u = make_user()
    monkeypatch.setattr("django.core.mail.EmailMultiAlternatives.send", lambda self: (_ for _ in ()).throw(OSError()))
    assert not emails.send_due(u)
    monkeypatch.undo()
    assert emails.send_due(u)
