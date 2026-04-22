# 04 — Tools Reference

Tools are the bridge between Claude's language understanding and your Frappe database. Claude reads the tool definitions (name, description, input schema) and decides which tool to call based on the user's message.

---

## Tool 1: query_data

**Purpose:** Fetch a list of records from any Frappe doctype.

**When Claude uses it:** Questions like "show me", "list", "find", "what are", "give me all"

**Input Schema:**
```json
{
  "doctype":  "string — e.g. Patient, Sales Invoice, Patient Appointment",
  "filters":  "object — e.g. {\"status\": \"Open\"} or {\"posting_date\": [\"between\", [\"2026-04-01\", \"2026-04-22\"]]}",
  "fields":   "array — e.g. [\"name\", \"patient_name\", \"grand_total\"]",
  "limit":    "integer — default 20",
  "order_by": "string — e.g. \"creation desc\""
}
```

**Frappe call:**
```python
frappe.get_list(doctype, filters, fields, limit, order_by, ignore_permissions=False)
```

**Example interaction:**
```
User: Show me today's open appointments
Claude calls: query_data({
  "doctype": "Patient Appointment",
  "filters": {"appointment_date": "2026-04-22", "status": "Open"},
  "fields": ["name", "patient_name", "practitioner", "appointment_time"],
  "limit": 20,
  "order_by": "appointment_time asc"
})
Result: [{...}, {...}, ...]
Claude replies: "There are 8 open appointments today: ..."
```

**Frappe filter syntax Claude uses:**
```python
# Equality
{"status": "Open"}

# Range (between)
{"posting_date": ["between", ["2026-04-01", "2026-04-30"]]}

# Greater than
{"outstanding_amount": [">", 0]}

# Like (search)
{"patient_name": ["like", "%Ayoub%"]}

# Multiple conditions (AND)
{"status": "Open", "department": "OPD"}
```

---

## Tool 2: aggregate_data

**Purpose:** Get a single numeric result — count, sum, or average.

**When Claude uses it:** Questions like "how many", "total", "sum of", "average", "count"

**Input Schema:**
```json
{
  "doctype":   "string",
  "aggregate": "count | sum | avg",
  "field":     "string — required for sum/avg, the field to aggregate",
  "filters":   "object — filter conditions"
}
```

**Frappe calls:**
```python
# count
frappe.db.count(doctype, filters)

# sum / avg — uses raw parameterized SQL
frappe.db.build_conditions(filters)   # → conditions string + values list
frappe.db.sql("SELECT SUM(`field`) FROM `tabDoctype` WHERE ...", values)
```

**Why raw SQL for sum/avg?**
`frappe.get_list()` does not support SQL aggregate functions. Raw SQL is the only way to compute Sums and Averages. The SQL is safe because:
1. The doctype and field names come from Claude (not raw user input) and are embedded in the query string
2. The filter values are passed as parameterized SQL using `frappe.db.build_conditions()` which prevents SQL injection

**Example interaction:**
```
User: What is the total unpaid amount across all submitted invoices?
Claude calls: aggregate_data({
  "doctype": "Sales Invoice",
  "aggregate": "sum",
  "field": "outstanding_amount",
  "filters": {"docstatus": 1, "outstanding_amount": [">", 0]}
})
Result: {"sum": 45230.50}
Claude replies: "The total outstanding amount on unpaid submitted invoices is $45,230.50."
```

---

## Tool 3: get_record

**Purpose:** Fetch the complete details of a single document by its ID.

**When Claude uses it:** When a user references a specific record ID, or after `query_data` returns a list and the user asks for more detail on one item.

**Input Schema:**
```json
{
  "doctype": "string",
  "name":    "string — the record ID e.g. PAT-00123, ACC-PAY-2026-00001"
}
```

**Frappe call:**
```python
doc = frappe.get_doc(doctype, name)
return doc.as_dict()
```

`frappe.get_doc()` raises `frappe.PermissionError` if the current user cannot read this record. `.as_dict()` converts the document object to a Python dict, including all fields and child tables.

**Example interaction:**
```
User: Give me full details of invoice SINV-00089
Claude calls: get_record({"doctype": "Sales Invoice", "name": "SINV-00089"})
Result: {"name": "SINV-00089", "patient": "PAT-00012", "patient_name": "Ahmed Ali",
         "grand_total": 350.0, "outstanding_amount": 350.0, "posting_date": "2026-04-20",
         "items": [...], ...}
Claude replies: "Invoice SINV-00089 for patient Ahmed Ali: Total $350.00, unpaid, dated April 20..."
```

---

## Tool 4: create_record

**Purpose:** Create a new Frappe document.

**When Claude uses it:** Instructions like "register", "create", "add", "book", "open"

**Input Schema:**
```json
{
  "doctype": "string",
  "data":    "object — field values for the new record"
}
```

**Frappe call:**
```python
doc = frappe.new_doc(doctype)
doc.update(data)
doc.insert()
frappe.db.commit()
```

`frappe.new_doc()` creates a document object with all Frappe defaults applied (naming series, default values). `doc.insert()` runs the full Frappe document lifecycle: `validate()`, `before_insert()`, `after_insert()`, and all hooks defined in `hooks.py`.

**Safety behavior:**
The system prompt instructs Claude to always confirm with the user before calling this tool:
```
System prompt: "For write actions: summarize what you will do and ask the user to confirm"
```

So the conversation looks like:
```
User: Register a patient, name Ayoub, male, age 25
Claude: I'll create a Patient record with:
  - Name: Ayoub
  - Sex: Male
  - Date of Birth: 2001-04-22 (estimated from age 25)
  Shall I proceed?
User: Yes
Claude calls: create_record({"doctype": "Patient", "data": {"patient_name": "Ayoub", "sex": "Male", "dob": "2001-04-22"}})
Result: {"success": true, "created": "PAT-00234", "doctype": "Patient"}
Claude replies: "Patient registered successfully. ID: PAT-00234"
```

**Minimum required fields for Patient:**
- `patient_name` — full name
- `sex` — Male / Female
- `dob` — date of birth (YYYY-MM-DD)

---

## Tool 5: update_record

**Purpose:** Modify fields on an existing Frappe document.

**When Claude uses it:** Instructions like "update", "change", "set", "mark", "cancel"

**Input Schema:**
```json
{
  "doctype": "string",
  "name":    "string — record ID",
  "data":    "object — only the fields to change"
}
```

**Frappe call:**
```python
doc = frappe.get_doc(doctype, name)
doc.update(data)
doc.save()
frappe.db.commit()
```

`doc.save()` runs the full Frappe update lifecycle including `on_update` hooks.

**Example interaction:**
```
User: Update appointment APP-00045 to Scheduled
Claude: I'll update appointment APP-00045 status to "Scheduled". Shall I proceed?
User: Yes
Claude calls: update_record({
  "doctype": "Patient Appointment",
  "name": "APP-00045",
  "data": {"status": "Scheduled"}
})
Result: {"success": true, "updated": "APP-00045"}
Claude replies: "Appointment APP-00045 has been updated to Scheduled."
```

---

## Tool Selection Logic (How Claude Decides)

Claude reads the tool descriptions and selects the most appropriate tool. Here is how it reasons:

| User says | Claude picks | Why |
|-----------|-------------|-----|
| "How many patients this week?" | `aggregate_data` (count) | "how many" = count |
| "Total revenue last month" | `aggregate_data` (sum) | "total" = sum |
| "Show me today's appointments" | `query_data` | "show me" = list |
| "Details of invoice SINV-001" | `get_record` | specific ID + "details" = single record |
| "Register a patient" | `create_record` | "register" = create |
| "Update appointment status" | `update_record` | "update" = modify |
| "Which department had most patients?" | `aggregate_data` → `query_data` | may chain tools |

Claude can chain tools — first count by department, then look up details — without any programming from the developer.
