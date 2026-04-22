# 03 — Backend API Deep Dive

**File:** `prime/api/ai.py`

## Module Structure

```python
TOOLS = [...]              # Tool definitions (JSON schemas for Claude)
_build_system_prompt()     # Builds the context-aware system prompt
_execute_tool()            # Dispatches tool calls to Frappe ORM
chat()                     # Main @frappe.whitelist() entry point
```

## TOOLS — The Tool Definitions

Tools are JSON Schema objects that tell Claude what functions it can call and what parameters they accept. Claude reads these schemas and decides which tool to use based on the user's message and the tool's `description` field.

```python
TOOLS = [
    {
        "name": "query_data",
        "description": "...",
        "input_schema": { ... }
    },
    ...
]
```

The `description` is the most important part — it is what Claude reads to decide when to use each tool. It must be precise and use natural language that matches how users phrase requests.

**Why 5 tools and not 1?**

Each tool has a distinct purpose:
- `query_data` — returns a list of records (multiple rows)
- `aggregate_data` — returns a single number (count/sum/avg)
- `get_record` — returns full details of one record
- `create_record` — creates a new document
- `update_record` — modifies an existing document

Having separate tools makes Claude's decisions more accurate. If there was only one tool, Claude would need to figure out what kind of operation to perform inside a generic function. Separate tools with clear descriptions make the AI's job easier and errors rarer.

## _build_system_prompt() — The Context Layer

```python
def _build_system_prompt():
    today = frappe.utils.today()
    ...
    return "You are an intelligent AI assistant..."
```

This function is called on every request and dynamically injects:

### Today's Date and Date Ranges
```python
today = frappe.utils.today()                          # "2026-04-22"
first_of_month = today[:8] + "01"                     # "2026-04-01"
last_month_end = frappe.utils.get_last_day(...)       # "2026-03-31"
```

These are injected into the prompt as:
```
- today = 2026-04-22
- this month: 2026-04-01 to 2026-04-22
- last month: 2026-03-01 to 2026-03-31
```

Without this, when a user asks "how many patients this month?", Claude would not know what "this month" means. By injecting the current date server-side, Claude can construct the correct filters.

### Doctype Map
The prompt lists every key doctype with its field names:
```
- Patient: name, patient_name, dob, sex, mobile, blood_group, status
- Que: name, patient, patient_name, status (Open/Closed/Called), token_number, ...
```

This is critical because Claude does not know that your queue system uses a doctype called `Que` (not `Queue`), or that patient name is stored in `patient_name` not `name`. The system prompt teaches Claude your system's vocabulary.

### Business Rules
```
- 'Unpaid invoices' = docstatus=1 AND outstanding_amount > 0
- Queue doctype is called 'Que' (not 'Queue')
```

These are facts about your data that Claude cannot derive from general knowledge. Every time a user says "unpaid invoices", Claude knows to filter `outstanding_amount > 0 AND docstatus=1`.

### Behavioral Instructions
```
- For write actions: summarize what you will do and ask for confirmation before calling the tool
- Lead with the answer
- Never make up data — only use results from the tools
```

These instructions shape how Claude responds — making it concise, safe, and professional.

## _execute_tool() — The Action Layer

```python
def _execute_tool(tool_name, tool_input):
    if tool_name == "query_data":
        return frappe.get_list(...)
    if tool_name == "aggregate_data":
        ...
    if tool_name == "get_record":
        ...
    if tool_name == "create_record":
        ...
    if tool_name == "update_record":
        ...
```

This function is the bridge between Claude's decisions and Frappe's database.

### query_data
```python
return frappe.get_list(
    tool_input["doctype"],
    filters=tool_input.get("filters", {}),
    fields=tool_input["fields"],
    limit=tool_input.get("limit", 20),
    order_by=tool_input.get("order_by", "creation desc"),
    ignore_permissions=False   # ← IMPORTANT: always False
)
```

`ignore_permissions=False` means Frappe's role-based access control is active. If the logged-in user does not have read permission on a doctype, this call raises a `PermissionError`.

### aggregate_data
```python
if agg == "count":
    return {"count": frappe.db.count(doctype, filters)}

# For sum/avg: build raw SQL
conditions, values = frappe.db.build_conditions(filters)
sql = "SELECT SUM(`field`) FROM `tabDocType` WHERE ..."
result = frappe.db.sql(sql, values)
```

The count path uses `frappe.db.count()` which is safe and ORM-based. For sum/avg, raw SQL is needed because `frappe.get_list()` doesn't support aggregation functions.

`frappe.db.build_conditions()` is used to convert the filter dict to safe parameterized SQL — this prevents SQL injection by separating conditions from values.

### create_record
```python
doc = frappe.new_doc(tool_input["doctype"])
doc.update(tool_input["data"])
doc.insert()
frappe.db.commit()
return {"success": True, "created": doc.name, "doctype": ...}
```

`frappe.new_doc()` creates a new document object in memory with all defaults applied. `.update()` sets field values. `.insert()` runs Frappe's full lifecycle: `validate()`, `before_insert()`, `after_insert()`, all doctype hooks. `frappe.db.commit()` persists the transaction.

### update_record
```python
doc = frappe.get_doc(tool_input["doctype"], tool_input["name"])
doc.update(tool_input["data"])
doc.save()
frappe.db.commit()
```

`frappe.get_doc()` fetches the existing document (with permission check). `.save()` runs Frappe's full update lifecycle including any `on_update` hooks defined in `hooks.py`.

## chat() — The Entry Point

```python
@frappe.whitelist()
def chat(message, history=None):
```

`@frappe.whitelist()` does three things:
1. Makes the function callable via HTTP POST at `/api/method/prime.api.ai.chat`
2. Requires the user to be authenticated (valid session cookie)
3. Handles CSRF token validation

### API Key Loading
```python
api_key = frappe.conf.get("anthropic_api_key")
if not api_key:
    frappe.throw(_("anthropic_api_key is not set in site_config.json"))
```

`frappe.conf` reads from `sites/alihsans.com/site_config.json`. The key is never in source code.

### History Parsing
```python
if history:
    try:
        parsed = json.loads(history) if isinstance(history, str) else history
        for m in parsed:
            if isinstance(m.get("content"), str):  # only text messages
                messages.append(m)
    except Exception:
        messages = []
```

The history is filtered to only include text-based messages (not tool_use or tool_result blocks). This is because tool_use blocks contain Anthropic-internal IDs that become stale across sessions, and sending them back in history causes API errors.

### The Tool Use Loop
```python
while iteration < max_iterations:
    response = client.messages.create(...)

    if response.stop_reason == "end_turn":
        # Claude finished — extract text and return
        break

    if response.stop_reason == "tool_use":
        # Execute tools, feed results back, loop again
        ...
```

The loop continues until:
- `stop_reason == "end_turn"` — Claude has finished and written a response
- `max_iterations` (10) is reached — safety limit to prevent infinite loops

A single user message can trigger multiple tool calls. For example: "Compare this month's revenue to last month" would trigger two `aggregate_data` calls (one per month), then Claude writes the comparison.

### Building the Assistant Message for History

When Claude uses a tool, the response content is a list of blocks — some text, some tool_use. The full block structure must be preserved when adding to messages:

```python
assistant_content = []
for block in response.content:
    if block.type == "text":
        assistant_content.append({"type": "text", "text": block.text})
    elif block.type == "tool_use":
        assistant_content.append({
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input
        })
messages.append({"role": "assistant", "content": assistant_content})
```

The tool results are then added as a `user` message:
```python
messages.append({"role": "user", "content": tool_results})
```

This alternating `assistant` → `user` pattern is required by the Anthropic API for multi-turn tool use conversations.
