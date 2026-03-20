import frappe


@frappe.whitelist(allow_guest=False)
def get_live_queue():
    """Return today's open queue grouped by practitioner for the TV display."""
    today = frappe.utils.today()
    ques = frappe.get_all(
        "Que",
        filters={"date": today, "status": "Open"},
        fields=[
            "name", "token_no", "patient_name",
            "practitioner", "practitioner_name", "department",
            "que_steps", "que_type", "time"
        ],
        order_by="token_no asc",
    )

    by_practitioner = {}
    for q in ques:
        key = q.practitioner
        if key not in by_practitioner:
            by_practitioner[key] = {
                "practitioner": key,
                "practitioner_name": q.practitioner_name or key,
                "department": q.department or "",
                "current_token": None,
                "current_patient": None,
                "next_token": None,
                "waiting_count": 0,
                "_waiting": [],
            }
        entry = by_practitioner[key]
        if q.que_steps == "Called" and entry["current_token"] is None:
            entry["current_token"] = q.token_no
            entry["current_patient"] = q.patient_name
        elif q.que_steps == "Waiting":
            entry["_waiting"].append(q)

    result = []
    for entry in by_practitioner.values():
        waiting = entry.pop("_waiting")
        entry["waiting_count"] = len(waiting)
        if waiting:
            entry["next_token"] = waiting[0].token_no
        result.append(entry)

    result.sort(key=lambda x: x["practitioner_name"])
    return result


@frappe.whitelist(allow_guest=False)
def call_next_token(practitioner):
    """Cashier calls next waiting patient for a given practitioner."""
    if not practitioner:
        frappe.throw("practitioner is required")

    today = frappe.utils.today()

    # Mark any currently Called token as still Open/Waiting (revert if not closed yet)
    currently_called = frappe.get_all(
        "Que",
        filters={
            "practitioner": practitioner,
            "date": today,
            "status": "Open",
            "que_steps": "Called",
        },
        fields=["name"],
        limit=1,
    )
    if currently_called:
        frappe.db.set_value("Que", currently_called[0].name, "que_steps", "Waiting")

    # Get next waiting token
    next_que = frappe.get_all(
        "Que",
        filters={
            "practitioner": practitioner,
            "date": today,
            "status": "Open",
            "que_steps": "Waiting",
        },
        fields=["name", "token_no", "patient_name"],
        order_by="token_no asc",
        limit=1,
    )

    if not next_que:
        return {"called": False, "message": "No patients waiting"}

    q = next_que[0]
    frappe.db.set_value("Que", q.name, "que_steps", "Called")
    frappe.publish_realtime("que_update")

    return {
        "called": True,
        "que": q.name,
        "token_no": q.token_no,
        "patient_name": q.patient_name,
    }


@frappe.whitelist(allow_guest=False)
def checkin_by_qr(reference_id):
    """Look up a Que by its MOBILE:reference_id (pre-arrival QR pass check-in)."""
    if not reference_id:
        frappe.throw("reference_id is required")

    ref_tag = f"MOBILE:{reference_id}"
    row = frappe.db.get_value(
        "Que",
        {"reference": ref_tag},
        ["name", "token_no", "patient_name", "practitioner", "practitioner_name",
         "department", "status", "que_steps", "date"],
        as_dict=True,
    )
    if not row:
        return {"found": False}

    waiting_ahead = frappe.db.count(
        "Que",
        {
            "practitioner": row.practitioner,
            "date": row.date,
            "status": "Open",
            "que_steps": "Waiting",
            "token_no": ["<", row.token_no],
        },
    )

    return {
        "found": True,
        "que": row.name,
        "token_no": row.token_no,
        "patient_name": row.patient_name,
        "practitioner_name": row.practitioner_name,
        "department": row.department,
        "status": row.status,
        "que_steps": row.que_steps,
        "patients_ahead": waiting_ahead,
    }
