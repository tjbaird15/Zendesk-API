# Zendesk Quality Audit API

This project provides a FastAPI service that:

1. Pulls Zendesk Chat transcripts from the last 7 days (Team plan, standard REST API).
2. Sends each transcript to OpenAI for QA scoring.
3. Flags chats where the customer appears dissatisfied and/or support quality appears poor.

## API Endpoints

- `GET /health` — health check.
- `POST /audit/last-week` — run an on-demand quality audit over chats in the trailing week.

> This implementation returns real-time results only and does **not** store audit history.

## Environment Variables

Create a `.env` file:

```bash
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=agent@company.com
ZENDESK_API_TOKEN=your_zendesk_api_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
# Optional override if needed, defaults to /api/v2/chats
# ZENDESK_CHAT_LIST_PATH=/api/v2/chats
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

## Zendesk Chat Team plan behavior

- The client uses the standard Zendesk Chat endpoint path (default: `/api/v2/chats`).
- The list API call uses a Unix `start_time` for the trailing 7-day window.
- If a list row does not include transcript messages, the client attempts to hydrate details via `/api/v2/chats/{chat_id}`.
- Pagination is followed when `next_url` or `next_page` is present.

## Suggested next enhancements

- Add score breakdown dimensions (empathy, resolution quality, policy compliance, tone).
- Add automatic daily run + notification workflow.
- Add optional persistence once you decide to track trends over time.
