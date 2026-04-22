# AI Assistant — Documentation Index

This directory contains full technical documentation for the AI Assistant built into the Alihsan Hospital Management System (Frappe/ERPNext `prime` app).

## Documents

| File | What it covers |
|------|---------------|
| [README.md](README.md) | This index |
| [01-overview.md](01-overview.md) | What was built, why, and how it works at a high level |
| [02-architecture.md](02-architecture.md) | Full system architecture, data flow, and component diagram |
| [03-backend-api.md](03-backend-api.md) | Deep dive into `prime/api/ai.py` — every function explained |
| [04-tools-reference.md](04-tools-reference.md) | All 5 tools: purpose, input schema, how they execute |
| [05-system-prompt.md](05-system-prompt.md) | The system prompt explained — why each section exists |
| [06-frontend-page.md](06-frontend-page.md) | Deep dive into the Frappe desk chat page (JS) |
| [07-deployment.md](07-deployment.md) | GitOps deployment flow — how code gets to the server |
| [08-extending.md](08-extending.md) | How to add new tools, doctypes, and capabilities |
| [09-troubleshooting.md](09-troubleshooting.md) | Common errors and how to fix them |

## Quick Reference

**Files created:**
```
prime/
  api/
    ai.py                          ← Python backend (chat endpoint + tools)
  page/
    ai_assistant/
      ai_assistant.json            ← Frappe page manifest (roles, metadata)
      ai_assistant.py              ← Empty controller (required by Frappe)
      ai_assistant.js              ← Chat UI (JavaScript)
requirements.txt                   ← Added: anthropic>=0.40.0
```

**Access the assistant:**
```
https://alihsans.com/app/ai-assistant
```

**API endpoint:**
```
POST /api/method/prime.api.ai.chat
{ "message": "...", "history": "[...]" }
```

**Required server config:**
```bash
bench --site alihsans.com set-config anthropic_api_key "sk-ant-..."
```
