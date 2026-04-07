from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.models import AuditResult
from app.models import ChatTranscript
from app.services.settings import Settings


class TranscriptAuditor:
    """Runs quality checks over chat transcripts using OpenAI."""

    def __init__(self, settings: Settings) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
        self._model = settings.openai_model

    async def audit(self, transcript: ChatTranscript) -> AuditResult:
        """Evaluate one transcript and return a structured quality assessment."""

        transcript_text = "\n".join(
            f"[{m.sender}] {m.text}" for m in transcript.messages
        )
        if not transcript_text.strip():
            return AuditResult(
                chat_id=transcript.chat_id,
                flag=False,
                issue_type="none",
                severity=1,
                reason="No transcript messages available for analysis.",
                coaching_tip="Ensure transcript ingestion captures message text.",
            )

        prompt = (
            "You are a strict eCommerce support QA reviewer. "
            "Evaluate whether this transcript suggests customer dissatisfaction, poor support quality, both, or neither. "
            "Return ONLY valid JSON with keys: flag (bool), issue_type (dissatisfied_customer|poor_service|both|none), "
            "severity (1-5), reason (string), coaching_tip (string).\n\n"
            f"Transcript ID: {transcript.chat_id}\n"
            f"Transcript:\n{transcript_text}"
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a strict eCommerce support QA reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={ "type": "json_object" }
        )

        text = response.choices[0].message.content.strip()
        data = json.loads(text)
        return AuditResult(chat_id=transcript.chat_id, **data)
