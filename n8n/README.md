# n8n Integration for BADGR Harness

## Prerequisites

1. BADGR Harness API running: `uvicorn api:app --host 0.0.0.0 --port 8765`
2. n8n running (self-hosted or cloud)
3. Ollama running on localhost:11434

---

## Start the API server

```bash
cd /home/t0n34781/projects/badgr_harness
uvicorn api:app --host 0.0.0.0 --port 8765
```

Verify: `curl http://localhost:8765/health`

---

## Import Workflows

In n8n: **Settings → Import from File** → select any JSON from `n8n/workflows/`.

| Workflow file | What it does |
|---|---|
| `badgr_task_runner.json` | Webhook endpoint — POST any goal, returns structured result |
| `badgr_scheduled_intel.json` | Weekday 8AM market intel extraction → Telegram |
| `badgr_email_draft.json` | Webhook → BADGR drafts email → optionally sends via Gmail |
| `badgr_social_post.json` | 10AM/3PM LinkedIn post generator with confidence gate |

---

## n8n Variables to configure

Set these under **Settings → Variables** in n8n before activating workflows:

| Variable | Description |
|---|---|
| `BADGR_TELEGRAM_CHAT_ID` | Your Telegram chat or group ID |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn OAuth access token |
| `LINKEDIN_PERSON_ID` | Your LinkedIn person URN (without `urn:li:person:`) |

---

## Credentials to configure

| Credential name | Type | Required by |
|---|---|---|
| `BADGR Telegram Bot` | Telegram Bot API | Scheduled Intel, Social Post |
| `BADGR Gmail` | Gmail OAuth2 | Email Draft |

---

## Quick test

With the API server running:

```bash
# Submit a task
curl -X POST http://localhost:8765/task \
  -H "Content-Type: application/json" \
  -d '{"goal": "What web services does BADGR LLC offer?", "source": "manual_test"}'

# Check health
curl http://localhost:8765/health

# Today's log summary
curl http://localhost:8765/logs
```

---

## Running as a background service (systemd)

```ini
# /etc/systemd/system/badgr-api.service
[Unit]
Description=BADGR Harness API
After=network.target

[Service]
User=t0n34781
WorkingDirectory=/home/t0n34781/projects/badgr_harness
ExecStart=/home/t0n34781/projects/badgr_harness/.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8765
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable badgr-api
sudo systemctl start badgr-api
```
