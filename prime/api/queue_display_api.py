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
def get_queue_status(que_name):
    """Return queue position for a specific Que — used by mobile app after booking."""
    if not que_name:
        frappe.throw("que_name is required")

    row = frappe.db.get_value(
        "Que",
        que_name,
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


@frappe.whitelist(allow_guest=False)
def get_invoice_for_dispensing(invoice_name):
    """Return invoice + medicine items for pharmacist QR scan dispensing."""
    si = frappe.db.get_value(
        "Sales Invoice",
        invoice_name,
        ["name", "patient", "customer", "outstanding_amount", "docstatus", "is_dispensed"],
        as_dict=True,
    )
    if not si:
        return {"found": False}

    if si.docstatus != 1:
        return {"found": False, "error": "Invoice is not submitted"}

    if si.outstanding_amount > 0:
        return {"found": True, "paid": False, "invoice": si.name, "patient": si.customer}

    patient_name = frappe.db.get_value("Patient", si.patient, "patient_name") if si.patient else si.customer

    items = frappe.db.get_all(
        "Sales Invoice Item",
        filters={"parent": invoice_name},
        fields=["item_code", "item_name", "qty", "description"],
    )

    return {
        "found": True,
        "paid": True,
        "already_dispensed": bool(si.is_dispensed),
        "invoice": si.name,
        "patient": patient_name,
        "items": items,
    }


@frappe.whitelist(allow_guest=False)
def mark_invoice_dispensed(invoice_name):
    """Mark a Sales Invoice as dispensed and deduct stock from pharmacy warehouse."""
    si = frappe.get_doc("Sales Invoice", invoice_name)
    if si.docstatus != 1:
        frappe.throw("Invoice must be submitted before dispensing")
    if si.outstanding_amount > 0:
        frappe.throw("Invoice has not been paid yet")

    # Deduct stock: create a Material Issue Stock Entry for each stock item
    stock_items = []
    for item in si.items:
        if not frappe.db.get_value("Item", item.item_code, "is_stock_item"):
            continue
        # Determine warehouse: use item's default warehouse for this company
        warehouse = frappe.db.get_value(
            "Item Default",
            {"parent": item.item_code, "company": si.company},
            "default_warehouse",
        ) or item.warehouse
        if not warehouse:
            frappe.throw(
                "No warehouse found for item {0}. Please set a default warehouse on the item.".format(item.item_code)
            )
        stock_items.append({"item_code": item.item_code, "qty": item.qty, "warehouse": warehouse})

    if stock_items:
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Issue"
        se.purpose = "Material Issue"
        se.company = si.company
        se.remarks = "Pharmacy dispense for Invoice {0}".format(invoice_name)
        for row in stock_items:
            se.append("items", {
                "item_code": row["item_code"],
                "qty": row["qty"],
                "s_warehouse": row["warehouse"],
            })
        se.flags.ignore_permissions = True
        se.save()
        se.submit()

    frappe.db.set_value("Sales Invoice", invoice_name, "is_dispensed", 1)
    return {"success": True}


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


def send_called_sms(doc, method=None):
    """Send Somali SMS to patient the moment Que status changes to Called."""
    if doc.status != "Called":
        return

    # Only fire when status just changed to Called (not on every save)
    before = doc.get_doc_before_save()
    if before and before.status == "Called":
        return

    if not doc.patient:
        return

    mobile = frappe.db.get_value("Patient", doc.patient, "mobile")
    if not mobile:
        return

    patient_name = doc.patient_name or ""
    message = (
        f"Salam {patient_name},\n\n"
        "Waqtigii ballantaadu waa la gaadhay. Fadlan si degdeg ah ugu gudub dhakhtarka.\n\n"
        "Fadlan ogow: haddii aadan waqtigan ku iman, waxaa la siin doonaa fursadda bukaanka kugu xiga.\n\n"
        "Mahadsanid,\nAl-Ihsan Hospital"
    )

    try:
        frappe.call(
            "frappe.core.doctype.sms_settings.sms_settings.send_sms",
            receiver_list=[mobile],
            msg=message
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Queue Called SMS Failed")
