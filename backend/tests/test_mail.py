"""Nitrosend email backend: request shape, errors and wiring through Django's MAILERS."""
import io
import json
from unittest import mock
from urllib.error import HTTPError, URLError

import pytest
from django.core import mail
from django.core.mail import EmailMultiAlternatives, InvalidMailer
from django.test import override_settings

from apps.core.mail import NitrosendBackend, NitrosendError

OPTIONS = {"api_key": "ns-key-123"}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def ok(*_args, **_kwargs):
    return FakeResponse(json.dumps({"id": 987, "status": "queued"}).encode())


def requests_sent(urlopen):
    return [(c.args[0], json.loads(c.args[0].data)) for c in urlopen.call_args_list]


def test_posts_one_message_per_recipient():
    backend = NitrosendBackend(**OPTIONS, alias="default")
    msg = EmailMultiAlternatives("Verify your email", "Your code is 123456.", "Astrology <no-reply@example.com>",
                                 ["a@example.com", "b@example.com"], reply_to=["help@example.com"],
                                 headers={"X-Tag": "otp"})
    msg.attach_alternative("<p>Your code is <b>123456</b>.</p>", "text/html")
    with mock.patch("apps.core.mail.urlopen", side_effect=ok) as urlopen:
        assert backend.send_messages([msg]) == 1
    sent = requests_sent(urlopen)
    assert [body["to"] for _, body in sent] == ["a@example.com", "b@example.com"]
    request, body = sent[0]
    assert request.full_url == "https://api.nitrosend.com/v1/my/messages" and request.get_method() == "POST"
    assert request.headers["Authorization"] == "Bearer ns-key-123"
    assert request.headers["Content-type"] == "application/json"
    keys = {r.headers["Idempotency-key"] for r, _ in sent}
    assert len(keys) == 2 and all(keys)  # required by Nitrosend, unique per send
    assert body == {
        "channel": "email", "to": "a@example.com", "subject": "Verify your email",
        "from": "Astrology <no-reply@example.com>", "body": "Your code is 123456.",
        "html": "<p>Your code is <b>123456</b>.</p>", "reply_to": "help@example.com", "headers": {"X-Tag": "otp"},
    }


def test_missing_key_is_rejected():
    with pytest.raises(InvalidMailer):
        NitrosendBackend(api_key="", alias="default")


def test_cc_bcc_unsupported():
    msg = EmailMultiAlternatives("s", "b", "f@example.com", ["a@example.com"], cc=["c@example.com"])
    with mock.patch("apps.core.mail.urlopen", side_effect=ok) as urlopen:
        with pytest.raises(NitrosendError, match="cc/bcc"):
            NitrosendBackend(**OPTIONS, alias="default").send_messages([msg])
    urlopen.assert_not_called()


def test_api_errors_raise_unless_fail_silently():
    msg = EmailMultiAlternatives("s", "b", "f@example.com", ["a@example.com"])
    rejected = HTTPError("u", 422, "Unprocessable", {}, io.BytesIO(b'{"error":true,"code":"validation_error"}'))
    with mock.patch("apps.core.mail.urlopen", side_effect=rejected) as urlopen:
        with pytest.raises(NitrosendError, match="422.*validation_error"):
            NitrosendBackend(**OPTIONS, backoff=0, alias="default").send_messages([msg])
    assert urlopen.call_count == 1  # a rejection is final, no retry
    with mock.patch("apps.core.mail.urlopen", side_effect=URLError("no route")) as urlopen:
        with pytest.raises(NitrosendError, match="reach"):
            NitrosendBackend(**OPTIONS, backoff=0, alias="default").send_messages([msg])
        assert urlopen.call_count == 2  # one retry
        assert NitrosendBackend(**OPTIONS, backoff=0, fail_silently=True, alias="default").send_messages([msg]) == 0


def test_timeout_is_retried_with_the_same_idempotency_key():
    msg = EmailMultiAlternatives("s", "b", "f@example.com", ["a@example.com"])
    with mock.patch("apps.core.mail.urlopen", side_effect=[TimeoutError("read timed out"), ok()]) as urlopen:
        assert NitrosendBackend(**OPTIONS, backoff=0, alias="default").send_messages([msg]) == 1
    keys = [r.headers["Idempotency-key"] for r, _ in requests_sent(urlopen)]
    assert len(keys) == 2 and keys[0] == keys[1]  # Nitrosend dedupes if the first attempt went through


def test_skips_messages_without_recipients():
    with mock.patch("apps.core.mail.urlopen", side_effect=ok) as urlopen:
        assert NitrosendBackend(**OPTIONS, alias="default").send_messages([EmailMultiAlternatives("s", "b", "f@x.com", [])]) == 0
    urlopen.assert_not_called()


@override_settings(MAILERS={"default": {"BACKEND": "apps.core.mail.NitrosendBackend", "OPTIONS": OPTIONS}})
def test_send_mail_goes_through_nitrosend():
    with mock.patch("apps.core.mail.urlopen", side_effect=ok) as urlopen:
        assert mail.send_mail("Hi", "Body", "no-reply@example.com", ["a@example.com"]) == 1
    (_, body), = requests_sent(urlopen)
    assert body["to"] == "a@example.com" and body["body"] == "Body" and body["channel"] == "email"


def test_settings_alias(monkeypatch):
    from astrology.settings.base import NITROSEND_BACKEND, build_mailers

    monkeypatch.setenv("EMAIL_BACKEND", "nitrosend")
    monkeypatch.setenv("NITROSEND_API_KEY", "ns-key-123")
    mailer = build_mailers("django.core.mail.backends.console.EmailBackend")["default"]
    assert mailer["BACKEND"] == NITROSEND_BACKEND
    assert mailer["OPTIONS"] == {"api_key": "ns-key-123", "base_url": "https://api.nitrosend.com/v1/my", "timeout": 20}
