# 02 — Architecture

## Component Map

```
┌─────────────────────────────────────────────────────────┐
│                  FRAPPE DESK (Browser)                  │
│                                                         │
│   /app/ai-assistant                                     │
│   ┌─────────────────────────────────────────────────┐   │
│   │  Chat UI (ai_assistant.js)                      │   │
│   │  - Message history (JS array)                   │   │
│   │  - User input field + Send button               │   │
│   │  - frappe.call() to backend                     │   │
│   └────────────────────┬────────────────────────────┘   │
└────────────────────────┼────────────────────────────────┘
                         │  HTTP POST
                         │  prime.api.ai.chat
                         │  { message, history }
                         ▼
┌─────────────────────────────────────────────────────────┐
│               FRAPPE PYTHON BACKEND                     │
│                                                         │
│   prime/api/ai.py                                       │
│   ┌─────────────────────────────────────────────────┐   │
│   │  @frappe.whitelist()                            │   │
│   │  def chat(message, history):                    │   │
│   │    1. Build system prompt (with today's date,   │   │
│   │       doctype map, business rules)              │   │
│   │    2. Call Claude API with messages + tools     │   │
│   │    3. Loop: if Claude calls a tool → execute    │   │
│   │       it against Frappe → feed result back      │   │
│   │    4. Return final text reply + updated history │   │
│   └──────────────┬──────────────────────────────────┘   │
└──────────────────┼──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────┐    ┌─────────────────────────┐
│  ANTHROPIC    │    │  FRAPPE ORM / DATABASE  │
│  CLAUDE API   │    │                         │
│               │    │  frappe.get_list()      │
│  claude-opus  │    │  frappe.get_doc()       │
│  -4-7         │    │  frappe.db.count()      │
│               │    │  frappe.db.sql()        │
│  Tool Use     │    │  frappe.new_doc()       │
│  Protocol     │    │  doc.insert()           │
│               │    │  doc.save()             │
└───────────────┘    │                         │
                     │  (runs as session user  │
                     │  → Frappe enforces      │
                     │  role permissions)      │
                     └─────────────────────────┘
```

## Request Lifecycle (Step by Step)

### Step 1 — User Sends a Message

The user types "How many patients registered this month?" and clicks Send.

The JS page calls:
```javascript
frappe.call({
    method: "prime.api.ai.chat",
    args: { message: "How many patients registered this month?", history: "[]" }
})
```

### Step 2 — Python Receives the Request

`prime.api.ai.chat` is a `@frappe.whitelist()` function. Frappe automatically:
- Validates the user is logged in
- Deserializes the request
- Enforces CSRF protection

The function reads the Anthropic API key from `site_config.json`, builds the system prompt, and prepares the message array.

### Step 3 — First Claude API Call

The backend calls the Claude API with:
- `system`: The hospital system prompt (doctype map, business rules, today's date)
- `messages`: `[{ "role": "user", "content": "How many patients registered this month?" }]`
- `tools`: The 5 tool definitions (JSON schemas)
- `model`: `claude-opus-4-7`

### Step 4 — Claude Decides to Use a Tool

Claude reads the question and the tool definitions. It responds with `stop_reason: "tool_use"` and a tool call:

```json
{
  "type": "tool_use",
  "name": "aggregate_data",
  "input": {
    "doctype": "Patient",
    "aggregate": "count",
    "filters": {
      "creation": ["between", ["2026-04-01", "2026-04-22"]]
    }
  }
}
```

Claude did not guess the date range — it computed it from the current date that was injected into the system prompt.

### Step 5 — Python Executes the Tool

The `_execute_tool()` function receives the tool name and input, and runs:
```python
frappe.db.count("Patient", {"creation": ["between", ["2026-04-01", "2026-04-22"]]})
```

This query runs as `frappe.session.user` — the logged-in hospital staff member. If they don't have read permission on Patient, this fails with a Frappe permission error, which gets returned to Claude as an error result.

Result: `{"count": 47}`

### Step 6 — Tool Result Fed Back to Claude

The Python code appends the assistant message (containing the tool_use block) and a new user message (containing the tool result) to the messages array, then calls the Claude API again.

Claude now sees the result and generates a final text response:
```
47 patients were registered this month.
```

### Step 7 — Response Returned to Browser

The Python function returns:
```json
{
  "reply": "47 patients were registered this month.",
  "history": [
    { "role": "user", "content": "How many patients registered this month?" },
    { "role": "assistant", "content": "47 patients were registered this month." }
  ]
}
```

The JS page appends the reply to the chat and stores the updated history for the next turn.

### Step 8 — Next Message Uses History

When the user sends the next message, the full conversation history is sent back. Claude has context of the entire conversation, enabling follow-up questions like "Which department had the most?" without repeating context.

## Tool Use Loop

Claude can call multiple tools in sequence or make a chain of decisions. The Python backend loops until `stop_reason == "end_turn"`:

```
Claude call → tool_use → execute → feed result → Claude call → tool_use → execute → ... → end_turn
```

Maximum 10 iterations (safety limit in the code).

## Multi-Turn Conversation

The conversation history is maintained in the browser (JavaScript array). On each message, the full history is serialized to JSON and sent to the server. The server does not store conversation state — it is stateless.

This means:
- Each request is independent from the server's perspective
- The browser holds the memory of the conversation
- If the user refreshes the page, history is lost (by design — this is a session-level chat)
- The history is trimmed to the last 20 messages (10 exchanges) to avoid token limits

## Permissions Model

```
User logs in to Frappe desk
         ↓
User opens /app/ai-assistant
         ↓
Frappe checks page roles (ai_assistant.json)
→ if user's role is not in the list → 403 access denied
         ↓
User sends a chat message
         ↓
@frappe.whitelist() validates session
         ↓
Tool executes as frappe.session.user
         ↓
frappe.get_list / frappe.get_doc enforce DocType permissions
→ user cannot see/edit what their role doesn't allow
```

Roles with page access (defined in `ai_assistant.json`):
- System Manager
- Physician
- Nurse
- Receptionist
- Main Cashier
- Lab Technician
- Pharmacy
