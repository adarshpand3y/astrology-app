"""Email backend that sends through the Nitrosend REST API (no SMTP, no extra dependency).

Configure via MAILERS (see settings.build_mailers):

    "BACKEND": "apps.core.mail.NitrosendBackend",
    "OPTIONS": {"api_key": "...", "base_url": "https://api.nitrosend.com/v1/my"}

API: POST {base_url}/messages with a Bearer key and a JSON body
{channel: "email", to, subject, body | html, from, reply_to, headers}. Every send needs an
Idempotency-Key. `to` takes a single address, so each recipient is sent as its own message.
The sender must be a verified sender identity in Nitrosend (DEFAULT_FROM_EMAIL).
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.mail import InvalidMailer
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

API_URL = "https://api.nitrosend.com/v1/my"
RETRY_STATUSES = {429, 500, 502, 503, 504}  # plus timeouts and connection errors


class NitrosendError(Exception):
    """Nitrosend rejected the message or could not be reached."""


class NitrosendBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, *, api_key: str = "", base_url: str = API_URL, timeout: float = 20,
                 retries: int = 1, backoff: float = 1, **kwargs):
        super().__init__(**kwargs)
        self.fail_silently = fail_silently  # handled here, like Django's SMTP backend
        if not api_key:
            raise InvalidMailer("Nitrosend needs an API key (NITROSEND_API_KEY).", alias=self.alias)
        self.api_key = api_key
        self.url = f"{base_url.rstrip('/')}/messages"
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def send_messages(self, email_messages) -> int:
        sent = 0
        for message in email_messages:
            if not message.recipients():
                continue
            try:
                for recipient in message.to:
                    self._post(self.payload(message, recipient))
                sent += 1
            except NitrosendError:
                if not self.fail_silently:
                    raise
                logger.exception("Nitrosend send failed (fail_silently)")
        return sent

    def payload(self, message, recipient: str) -> dict:
        """JSON body for one recipient of `message`."""
        if message.cc or message.bcc:
            raise NitrosendError("cc/bcc are not supported by the Nitrosend API; send separate messages.")
        if message.attachments:
            raise NitrosendError("Attachments are not supported by NitrosendBackend.")
        body = {"channel": "email", "to": recipient, "subject": message.subject, "from": message.from_email}
        if message.body:
            body["html" if message.content_subtype == "html" else "body"] = message.body
        for alt in getattr(message, "alternatives", []) or []:
            if alt[1] == "text/html":
                body["html"] = alt[0]
        if message.reply_to:
            body["reply_to"] = message.reply_to[0]
        if message.extra_headers:
            body["headers"] = {k: str(v) for k, v in message.extra_headers.items()}
        return body

    def _post(self, body: dict) -> None:
        request = Request(self.url, data=json.dumps(body).encode(), method="POST", headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Required by Nitrosend. One key per message, reused on retries: if a timed-out attempt
            # was accepted after all, Nitrosend returns that message instead of sending it twice.
            "Idempotency-Key": str(uuid.uuid4()),
        })
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:  # noqa: S310 (fixed https URL)
                    result = json.loads(response.read() or b"{}")
                break
            except HTTPError as exc:
                detail = exc.read().decode(errors="replace")[:300]
                error = NitrosendError(f"Nitrosend rejected the message ({exc.code}): {detail}")
                if exc.code not in RETRY_STATUSES or attempt == self.retries:
                    raise error from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt == self.retries:
                    raise NitrosendError(f"Could not reach Nitrosend: {exc}") from exc
            logger.warning("Nitrosend send to %s failed (attempt %d), retrying", body["to"], attempt + 1)
            time.sleep(self.backoff * (attempt + 1))
        logger.info("Nitrosend accepted message %s to %s", result.get("id"), body["to"])
