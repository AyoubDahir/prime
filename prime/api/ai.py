import json
import frappe
from frappe import _

TOOLS = [
    {
        "name": "query_data",
        "description": (
            "Fetch a list of records from the system. Use for questions like "
            "'show me today appointments', 'list unpaid invoices', 'find patient by name'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doctype": {
                    "type": "string",
                    "description": "Frappe doctype name e.g. Patient, Sales Invoice, Patient Appointment, Que, Lab Test"
                },
                "filters": {
                    "type": "object",
                    "description": "Field-value filters e.g. {\"status\": \"Open\"} or {\"posting_date\": [\"between\", [\"2026-04-01\", \"2026-04-30\"]]}"
                },
                "fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fields to return e.g. [\"name\", \"patient_name\", \"grand_total\"]"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max records to return, default 20",
                    "default": 20
                },
                "order_by": {
                    "type": "string",
                    "description": "e.g. 'creation desc'"
                }
            },
            "required": ["doctype", "fields"]
        }
    },
    {
        "name": "aggregate_data",
        "description": (
            "Get totals, counts, or averages. Use for questions like "
            "'how many patients this week', 'total revenue last month', 'average invoice amount'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doctype": {"type": "string"},
                "aggregate": {
                    "type": "string",
                    "enum": ["count", "sum", "avg"],
                    "description": "Type of aggregation"
                },
                "field": {
                    "type": "string",
                    "description": "Field to sum or average (not needed for count)"
                },
                "filters": {
                    "type": "object",
                    "description": "Filter conditions"
                }
            },
            "required": ["doctype", "aggregate"]
        }
    },
    {
        "name": "get_record",
        "description": "Get full details of a single record by its ID/name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doctype": {"type": "string"},
                "name": {"type": "string", "description": "Record ID e.g. PAT-00123 or ACC-PAY-2026-00001"}
            },
            "required": ["doctype", "name"]
        }
    },
    {
        "name": "create_record",
        "description": (
            "Create a new record in the system. Use for 'register patient', 'create appointment', etc. "
            "Always confirm with the user before calling this tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doctype": {"type": "string"},
                "data": {
                    "type": "object",
                    "description": "Field values for the new record"
                }
            },
            "required": ["doctype", "data"]
        }
    },
    {
        "name": "update_record",
        "description": (
            "Update fields on an existing record. "
            "Always confirm with the user before calling this tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "doctype": {"type": "string"},
                "name": {"type": "string"},
                "data": {"type": "object", "description": "Fields to update"}
            },
            "required": ["doctype", "name", "data"]
        }
    }
]


def _build_system_prompt():
    today = frappe.utils.today()
    now = frappe.utils.now()

    first_of_month = today[:8] + "01"
    last_month_end = frappe.utils.get_last_day(frappe.utils.add_months(today, -1))
    last_month_start = str(last_month_end)[:8] + "01"

    return (
        "You are an intelligent AI assistant embedded inside Alihsan Hospital Management System "
        "(built on Frappe/ERPNext). You help staff query live hospital data and perform actions.\n\n"

        "## Today\n"
        "- Date: {today}\n"
        "- This month: {first_of_month} to {today}\n"
        "- Last month: {last_month_start} to {last_month_end}\n\n"

        "## Key Doctypes & Fields\n"
        "- **Patient**: name, patient_name, dob, sex, mobile, blood_group, status\n"
        "- **Patient Appointment**: name, patient, patient_name, practitioner, appointment_date, appointment_time, status (Open/Scheduled/Cancelled/Closed), department\n"
        "- **Patient Encounter**: name, patient, patient_name, practitioner, encounter_date, docstatus\n"
        "- **Que**: name, patient, patient_name, status (Open/Closed/Called), token_number, practitioner, department, creation\n"
        "- **Sales Invoice**: name, patient, patient_name, grand_total, outstanding_amount, posting_date, status, docstatus (0=Draft 1=Submitted 2=Cancelled)\n"
        "- **Sales Order**: name, patient, patient_name, grand_total, transaction_date, docstatus, per_billed, delivery_status\n"
        "- **Lab Test**: name, patient, patient_name, result_date, status, docstatus\n"
        "- **Sample Collection**: name, patient, patient_name, docstatus, creation\n"
        "- **Inpatient Record**: name, patient, patient_name, status, admitted_datetime, discharge_datetime\n"
        "- **Healthcare Practitioner**: name, practitioner_name, department\n\n"

        "## Business Rules\n"
        "- 'Unpaid invoices' = docstatus=1 AND outstanding_amount > 0\n"
        "- 'Submitted' documents = docstatus=1\n"
        "- Queue doctype is called 'Que' (not 'Queue')\n"
        "- Patient registration minimum fields: patient_name, dob, sex\n"
        "- Use posting_date for Sales Invoice date filters\n"
        "- Use transaction_date for Sales Order date filters\n"
        "- Use appointment_date for Patient Appointment date filters\n"
        "- Use creation for Que date filters\n\n"

        "## Instructions\n"
        "- For read questions: query the data and give a direct, clear answer\n"
        "- For write actions (create/update): summarize exactly what you will do and ask the user to confirm before calling the tool\n"
        "- Lead with the answer (e.g. '47 patients were registered this month')\n"
        "- For lists of records: show a clean summary, not raw JSON\n"
        "- If a query returns no results, say so clearly\n"
        "- If you get a permission error, tell the user their role does not allow that action\n"
        "- Never make up data — only use results from the tools\n"
        "- Keep responses concise and professional\n"
    ).format(
        today=today,
        first_of_month=first_of_month,
        last_month_start=last_month_start,
        last_month_end=str(last_month_end)
    )


def _execute_tool(tool_name, tool_input):
    if tool_name == "query_data":
        return frappe.get_list(
            tool_input["doctype"],
            filters=tool_input.get("filters", {}),
            fields=tool_input["fields"],
            limit=tool_input.get("limit", 20),
            order_by=tool_input.get("order_by", "creation desc"),
            ignore_permissions=False
        )

    if tool_name == "aggregate_data":
        doctype = tool_input["doctype"]
        agg = tool_input["aggregate"]
        filters = tool_input.get("filters", {})

        if agg == "count":
            return {"count": frappe.db.count(doctype, filters)}

        field = tool_input.get("field")
        if not field:
            frappe.throw(_("Field is required for sum/avg aggregation"))

        fn_map = {"sum": "SUM", "avg": "AVG"}
        conditions, values = frappe.db.build_conditions(filters)
        where_clause = "WHERE " + conditions if conditions else ""
        sql = "SELECT {fn}(`{field}`) FROM `tab{dt}` {where}".format(
            fn=fn_map[agg],
            field=field,
            dt=doctype,
            where=where_clause
        )
        result = frappe.db.sql(sql, values)
        value = result[0][0] if result and result[0][0] is not None else 0
        return {agg: float(value)}

    if tool_name == "get_record":
        doc = frappe.get_doc(tool_input["doctype"], tool_input["name"])
        return doc.as_dict()

    if tool_name == "create_record":
        doc = frappe.new_doc(tool_input["doctype"])
        doc.update(tool_input["data"])
        doc.insert()
        frappe.db.commit()
        return {"success": True, "created": doc.name, "doctype": tool_input["doctype"]}

    if tool_name == "update_record":
        doc = frappe.get_doc(tool_input["doctype"], tool_input["name"])
        doc.update(tool_input["data"])
        doc.save()
        frappe.db.commit()
        return {"success": True, "updated": doc.name}

    return {"error": "Unknown tool: " + tool_name}


@frappe.whitelist()
def chat(message, history=None):
    try:
        import anthropic
    except ImportError:
        frappe.throw(_("anthropic package is not installed. Run: bench pip install anthropic"))

    api_key = frappe.conf.get("anthropic_api_key")
    if not api_key:
        frappe.throw(_("anthropic_api_key is not set in site_config.json"))

    client = anthropic.Anthropic(api_key=api_key)

    messages = []
    if history:
        try:
            parsed = json.loads(history) if isinstance(history, str) else history
            # only keep text-based messages for multi-turn (strip tool_use blocks)
            for m in parsed:
                if isinstance(m.get("content"), str):
                    messages.append(m)
        except Exception:
            messages = []

    messages.append({"role": "user", "content": message})

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=_build_system_prompt(),
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            reply = ""
            for block in response.content:
                if hasattr(block, "text"):
                    reply = block.text
                    break
            messages.append({"role": "assistant", "content": reply})
            return {"reply": reply, "history": messages}

        if response.stop_reason == "tool_use":
            tool_results = []
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
                    try:
                        result = _execute_tool(block.name, block.input)
                        content = json.dumps(result, default=str)
                    except Exception as e:
                        content = json.dumps({"error": str(e)})

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content
                    })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    return {"reply": "I was unable to complete the request. Please try again.", "history": messages}
