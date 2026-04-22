# 08 — Extending the AI Assistant

## Adding a New Doctype to the System Prompt

This is the most common extension. When a user asks about a doctype Claude doesn't know, it will either guess wrong field names or say it doesn't know.

**Edit `_build_system_prompt()` in `prime/api/ai.py`:**

```python
"- **Pharmacy Order**: name, patient, patient_name, status, order_date, items (child table)\n"
```

Include:
- The exact doctype name (case-sensitive, spaces must match Frappe's naming)
- The key fields the user is likely to ask about
- Status values if it has a status field
- Which field to use for date filters

Changes take effect immediately on the next request — no migration needed.

---

## Adding a New Tool

When you need capability that doesn't fit the existing 5 tools, add a new one.

**Example: Submit a document**

**Step 1 — Add the tool definition to `TOOLS` list:**

```python
{
    "name": "submit_document",
    "description": (
        "Submit (finalize) a Frappe document. Use for 'submit invoice', "
        "'submit this order', 'finalize lab test'. "
        "Always confirm with the user before calling."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "doctype": {"type": "string"},
            "name":    {"type": "string", "description": "Record ID to submit"}
        },
        "required": ["doctype", "name"]
    }
}
```

**Step 2 — Add execution logic to `_execute_tool()`:**

```python
if tool_name == "submit_document":
    doc = frappe.get_doc(tool_input["doctype"], tool_input["name"])
    doc.submit()
    frappe.db.commit()
    return {"success": True, "submitted": doc.name}
```

**Step 3 — (Optional) Update the system prompt** to tell Claude when to use it:

```python
"- To submit a document, use submit_document tool\n"
"- Only submitted invoices (docstatus=1) can be paid\n"
```

---

## Adding Business Rules

Any fact about your data that Claude cannot derive from general knowledge should be in the system prompt.

**Examples of rules to add:**

```python
# In _build_system_prompt():

"- Insurance patients have 'insurance_company' field set on Patient\n"
"- 'Active inpatients' = Inpatient Record with status='Admitted'\n"
"- Dental appointments are in department='Dental'\n"
"- Pharmacy Sales Orders have sales_type='Pharmacy'\n"
"- A Que is 'waiting' when status='Open' and hasn't been called yet\n"
```

---

## Adding Date Shortcuts

If users frequently ask about specific date ranges:

```python
# In _build_system_prompt():
week_start = frappe.utils.get_first_day_of_week(today)
week_end = frappe.utils.get_last_day_of_week(today)

return (
    ...
    "- This week: {week_start} to {week_end}\n"
    ...
).format(
    ...
    week_start=str(week_start),
    week_end=str(week_end)
)
```

---

## Adding Role-Based Context

Different roles need different information. You can inject the current user's role into the system prompt:

```python
def _build_system_prompt():
    user = frappe.session.user
    roles = frappe.get_roles(user)

    role_context = ""
    if "Physician" in roles:
        role_context = "The current user is a Physician. Focus on clinical data."
    elif "Main Cashier" in roles:
        role_context = "The current user is a Cashier. Focus on billing and payments."
    elif "Receptionist" in roles:
        role_context = "The current user is a Receptionist. Focus on appointments and patient registration."

    return (
        ...
        "## Current User\n"
        + role_context + "\n\n"
        ...
    )
```

---

## Adding Conversation Persistence (Database Storage)

Currently, conversation history is stored in the browser and lost on page refresh. To persist conversations to a database:

**Step 1 — Create a DocType `AI Chat Session`:**
```
Fields:
  - user (Link → User)
  - session_id (Data)
  - history (Long Text — stores JSON)
  - created_at (Datetime)
```

**Step 2 — Update `chat()` to save/load history:**

```python
@frappe.whitelist()
def chat(message, session_id=None, history=None):
    # Load history from DB if session_id provided
    if session_id:
        session = frappe.db.get_value(
            "AI Chat Session",
            {"session_id": session_id, "user": frappe.session.user},
            ["history"],
            as_dict=True
        )
        if session:
            history = session.history

    # ... run chat logic ...

    # Save history back to DB
    if session_id:
        frappe.db.set_value("AI Chat Session", session_id, "history", json.dumps(messages))
        frappe.db.commit()

    return {"reply": reply, "history": messages, "session_id": session_id}
```

---

## Adding a Floating Chat Button (All Pages)

To add the AI assistant as a floating button on every Frappe desk page (not just `/app/ai-assistant`), add to `public/js/his.js`:

```javascript
// Floating AI chat button on all pages
frappe.after_ajax(function() {
    if ($('#ai-float-btn').length) return;  // already added

    $('body').append(
        '<button id="ai-float-btn" style="position:fixed;bottom:24px;right:24px;z-index:9999;'
        + 'width:56px;height:56px;border-radius:50%;background:#0066cc;color:#fff;'
        + 'border:none;font-size:1.5rem;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);">AI</button>'
    );

    $('#ai-float-btn').on('click', function() {
        frappe.set_route('ai-assistant');
    });
});
```

---

## Changing the AI Model

The model is set in `chat()` in `prime/api/ai.py`:

```python
response = client.messages.create(
    model="claude-opus-4-7",   ← change this
    ...
)
```

Available models (as of April 2026):
- `claude-opus-4-7` — most capable, slowest, most expensive (current)
- `claude-sonnet-4-6` — balanced (fast, cheaper, slightly less accurate for complex queries)
- `claude-haiku-4-5-20251001` — fastest, cheapest (good for simple lookups)

For a hospital system where accuracy matters, `claude-opus-4-7` is recommended.

---

## Restricting Certain Actions by Role

To prevent certain roles from performing write actions:

```python
def _execute_tool(tool_name, tool_input):
    if tool_name in ("create_record", "update_record"):
        allowed_roles = ["System Manager", "Receptionist", "Physician"]
        user_roles = frappe.get_roles(frappe.session.user)
        if not any(r in user_roles for r in allowed_roles):
            return {"error": "Your role does not have permission to perform this action."}
    ...
```
