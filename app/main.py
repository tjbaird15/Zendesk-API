from fastapi import Depends
from fastapi import FastAPI

from app.models import AuditResponse
from app.services.auditor import TranscriptAuditor
from app.services.settings import HealthInfo
from app.services.settings import Settings
from app.services.settings import get_settings
from app.services.zendesk_client import ZendeskClient

app = FastAPI(title="Zendesk Quality Audit API", version="0.1.0")


@app.get("/health", response_model=HealthInfo)
async def health() -> HealthInfo:
    """Basic health endpoint."""

    return HealthInfo(status="ok")


@app.post("/audit/last-week", response_model=AuditResponse)
async def audit_last_week(
    settings: Settings = Depends(get_settings),
) -> AuditResponse:
    """Fetch the last 7 days of chats from Zendesk and audit them with OpenAI."""

    zendesk = ZendeskClient(settings)
    auditor = TranscriptAuditor(settings)

    transcripts = await zendesk.get_last_week_transcripts()
    results = [await auditor.audit(t) for t in transcripts]
    flagged = [row for row in results if row.flag]

    return AuditResponse(
        audited_count=len(results),
        flagged_count=len(flagged),
        flagged_items=flagged,
    )
