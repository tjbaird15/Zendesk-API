
from app.services.zendesk_client import _build_base_url
from app.services.zendesk_client import _normalize_path
 main
from app.services.zendesk_client import _parse_dt
from app.services.zendesk_client import ZendeskClient
from app.services.settings import Settings


def _settings() -> Settings:
    return Settings(
        zendesk_subdomain="example",
        zendesk_email="qa@example.com",
        zendesk_api_token="token",
        openai_api_key="sk-test",
    )



def test_build_base_url_from_subdomain() -> None:
    assert _build_base_url("acme") == "https://acme.zendesk.com"


def test_build_base_url_from_host() -> None:
    assert _build_base_url("www.zopim.com") == "https://www.zopim.com"


 main
def test_parse_dt_invalid_returns_none() -> None:
    assert _parse_dt("not-a-date") is None


def test_parse_dt_unix_timestamp() -> None:
    parsed = _parse_dt(1_700_000_000)
    assert parsed is not None
    assert parsed.tzinfo is not None



def test_normalize_path_strips_spaces() -> None:
    assert _normalize_path("  /api/v2/chats.json  ") == "/api/v2/chats.json"


main
def test_normalize_chat_ignores_blank_messages() -> None:
    client = ZendeskClient(_settings())
    normalized = client._normalize_chat(
        {
            "id": "abc-123",
            "messages": [
                {"author": "agent", "text": "  "},
                {"author": "customer", "text": "Need help with return label"},
            ],
        }
    )

    assert normalized.chat_id == "abc-123"
    assert len(normalized.messages) == 1
    assert normalized.messages[0].sender == "customer"
