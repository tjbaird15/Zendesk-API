from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import httpx

from app.models import ChatMessage
from app.models import ChatTranscript
from app.services.settings import Settings


class ZendeskClient:
    """Zendesk Chat (Team plan) API client for recent chats + transcripts."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = f"https://{settings.zendesk_subdomain}"
        self._auth = (
            f"{settings.zendesk_email}/token",
            settings.zendesk_api_token.get_secret_value(),
        )

    async def get_last_week_transcripts(self) -> list[ChatTranscript]:
        """Return transcripts created in the trailing 7-day window.

        Zendesk Chat API on Team plans expects Unix timestamps for `start_time`.
        """

        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        start_time = int(week_ago.timestamp())

        chats = await self._fetch_chat_summaries(start_time=start_time)
        async with httpx.AsyncClient(timeout=30) as client:
            transcripts: list[ChatTranscript] = []
            for chat in chats:
                chat = await self._hydrate_chat_if_needed(client, chat)
                transcripts.append(self._normalize_chat(chat))
            return transcripts

    async def _fetch_chat_summaries(self, start_time: int) -> list[dict[str, Any]]:
        params = {"start_time": start_time, "page[size]": 200}
        url: str | None = f"{self._base_url}{self._settings.zendesk_chat_list_path}"
        output: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30) as client:
            while url:
                response = await client.get(url, params=params if "?" not in url else None, auth=self._auth)
                response.raise_for_status()
                payload = response.json()

                output.extend(payload.get("chats", payload.get("data", [])))
                url = payload.get("next_url") or payload.get("next_page")
                params = None

        return output

    async def _hydrate_chat_if_needed(
        self,
        client: httpx.AsyncClient,
        raw_chat: dict[str, Any],
    ) -> dict[str, Any]:
        """Fetch full transcript only when summary payload has no messages."""

        messages = raw_chat.get("messages") or raw_chat.get("transcript")
        if messages:
            return raw_chat

        chat_id = raw_chat.get("id") or raw_chat.get("chat_id")
        if not chat_id:
            return raw_chat

        detail_url = f"{self._base_url}/api/v2/chats/{chat_id}"
        response = await client.get(detail_url, auth=self._auth)
        if response.status_code >= 400:
            return raw_chat

        detail = response.json()
        return detail.get("chat", detail.get("data", raw_chat))

    def _normalize_chat(self, raw_chat: dict[str, Any]) -> ChatTranscript:
        """Normalize variant Zendesk payload shapes into ChatTranscript."""

        chat_id = str(raw_chat.get("id") or raw_chat.get("chat_id") or "unknown")
        created = raw_chat.get("created_at") or raw_chat.get("timestamp")
        created_at = _parse_dt(created)

        raw_messages = raw_chat.get("messages") or raw_chat.get("transcript") or []
        messages: list[ChatMessage] = []
        for row in raw_messages:
            text = row.get("message") or row.get("text") or ""
            if not text.strip():
                continue
            messages.append(
                ChatMessage(
                    sender=row.get("sender_name")
                    or row.get("author")
                    or row.get("role")
                    or row.get("nick")
                    or "unknown",
                    timestamp=_parse_dt(row.get("timestamp") or row.get("created_at")),
                    text=text.strip(),
                )
            )

        return ChatTranscript(
            chat_id=chat_id,
            created_at=created_at,
            customer_id=str(raw_chat.get("visitor_id") or raw_chat.get("customer_id") or "")
            or None,
            messages=messages,
        )


def _parse_dt(value: str | int | None) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, int):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
