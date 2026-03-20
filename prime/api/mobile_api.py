import frappe
from erpnext.stock.get_item_details import get_pos_profile
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from frappe.utils import flt


def _normalize_mobile(mobile):
    raw = (mobile or "").strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("252"):
        return digits
    if digits.startswith("0"):
        return "252" + digits[1:]
    return digits


def _mobile_candidates(mobile):
    normalized = _normalize_mobile(mobile)
    if not normalized:
        return []
    candidates = {normalized}
    if normalized.startswith("252") and len(normalized) > 3:
        candidates.add("0" + normalized[3:])
    candidates.add("+" + normalized)
    return list(candidates)


def _get_default_company():
    return (
        frappe.defaults.get_user_default("company")
        or frappe.defaults.get_global_default("company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )


def _get_default_mode_of_payment(company):
    if company:
        try:
            pos_profile = get_pos_profile(company)
            if pos_profile:
                mop = frappe.db.get_value(
                    "POS Payment Method",
                    {"parent": pos_profile.name},
                    "mode_of_payment",
                )
                if mop:
                    return mop
        except Exception:
            pass
    # Fallback when POS Profile is not configured.
    return frappe.db.get_value("Mode of Payment", {}, "name")


def _ensure_doctor_type_exists(doc_type_name):
    value = (doc_type_name or "").strip()
    if not value:
        return
    if frappe.db.exists("Doctor Type", value):
        return
    doc = frappe.get_doc({"doctype": "Doctor Type", "do_type": value})
    doc.insert(ignore_permissions=True)


def _register_patient_from_mobile(
    first_name=None,
    last_name=None,
    full_name=None,
    mobile=None,
    sex=None,
    p_age=None,
    age_type=None,
):
    mobile = _normalize_mobile(mobile)
    if not mobile:
        frappe.throw("mobile is required for patient self-registration")

    normalized_first_name = (first_name or "").strip()
    normalized_last_name = (last_name or "").strip()

    patient_name = (full_name or "").strip()
    if not patient_name:
        patient_name = " ".join([p for p in [normalized_first_name, normalized_last_name] if p]).strip()
    if not patient_name:
        frappe.throw("first_name or full_name is required for patient self-registration")
    if not normalized_first_name:
        name_parts = patient_name.split(" ", 1)
        normalized_first_name = name_parts[0].strip()
        if not normalized_last_name and len(name_parts) > 1:
            normalized_last_name = name_parts[1].strip()
    if not normalized_last_name:
        normalized_last_name = "Unknown"
    if p_age in (None, ""):
        frappe.throw("p_age is required for patient self-registration")
    try:
        p_age = int(p_age)
    except Exception:
        frappe.throw("p_age must be a valid number")
    if p_age < 0:
        frappe.throw("p_age cannot be negative")

    age_type = (age_type or "").strip().title()
    if age_type not in ("Year", "Month", "Day"):
        frappe.throw("age_type must be one of: Year, Month, Day")

    existing_patient = None
    candidates = _mobile_candidates(mobile)
    if candidates:
        existing = frappe.get_all(
            "Patient",
            filters={"mobile": ["in", candidates]},
            fields=["name"],
            limit_page_length=1,
        )
        if existing:
            existing_patient = existing[0].name
    if existing_patient:
        return {"created": False, "patient": existing_patient}

    patient = frappe.get_doc(
        {
            "doctype": "Patient",
            "first_name": normalized_first_name,
            "last_name": normalized_last_name,
            "patient_name": patient_name,
            "mobile": mobile,
            "sex": sex or "Male",
            "p_age": p_age,
            "age_type": age_type,
        }
    )
    patient.insert(ignore_permissions=True)
    return {"created": True, "patient": patient.name}


@frappe.whitelist()
def register_patient_from_mobile(
    first_name=None,
    last_name=None,
    full_name=None,
    mobile=None,
    sex=None,
    p_age=None,
    age_type=None,
):
    return _register_patient_from_mobile(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        mobile=mobile,
        sex=sex,
        p_age=p_age,
        age_type=age_type,
    )


@frappe.whitelist()
def create_que_from_mobile(
    practitioner,
    patient=None,
    appointment_date=None,
    appointment_time=None,
    department=None,
    reference_id=None,
    paid_amount=0,
    mode_of_payment=None,
    first_name=None,
    last_name=None,
    full_name=None,
    mobile=None,
    sex=None,
    p_age=None,
    age_type=None,
):
    if not practitioner:
        frappe.throw("practitioner is required")
    if not reference_id:
        frappe.throw("reference_id is required")

    if not patient:
        registered = _register_patient_from_mobile(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            mobile=mobile,
            sex=sex,
            p_age=p_age,
            age_type=age_type,
        )
        patient = registered["patient"]
    elif not frappe.db.exists("Patient", patient):
        # If caller sends non-existing patient id but includes registration payload,
        # auto-register and continue queue flow.
        if mobile or first_name or full_name:
            registered = _register_patient_from_mobile(
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                mobile=mobile or patient,
                sex=sex,
                p_age=p_age,
                age_type=age_type,
            )
            patient = registered["patient"]
        else:
            frappe.throw(f"Patient not found: {patient}")

    if not frappe.db.exists("Healthcare Practitioner", practitioner):
        frappe.throw(f"Practitioner not found: {practitioner}")

    queue_date = appointment_date or frappe.utils.getdate()
    queue_time = appointment_time or frappe.utils.nowtime()
    ref_tag = f"MOBILE:{reference_id}"

    # Idempotency: same mobile reference should return existing queue.
    existing = frappe.db.get_value(
        "Que",
        {"reference": ref_tag},
        ["name", "sales_invoice"],
        as_dict=True,
    )
    if existing:
        # Also ensure the invoice is paid — the first webhook may have created the
        # Que but failed to create the Payment Entry. Retry it here so a second
        # webhook call (or reconciliation poll) completes the financial posting.
        payment_entry = None
        if existing.sales_invoice:
            try:
                pay_result = mark_sales_invoice_paid_from_mobile(
                    invoice=existing.sales_invoice,
                    mode_of_payment="Waafi",
                    reference_id=reference_id,
                )
                payment_entry = pay_result.get("payment_entry")
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    "create_que_from_mobile: idempotency payment_entry retry failed",
                )
        existing_patient = frappe.db.get_value("Que", existing.name, "patient")
        existing_practitioner = frappe.db.get_value("Que", existing.name, "practitioner")
        return {
            "created": False,
            "que": existing.name,
            "invoice": existing.sales_invoice,
            "reference_id": reference_id,
            "patient": existing_patient,
            "patient_name": frappe.db.get_value("Patient", existing_patient, "patient_name") if existing_patient else None,
            "practitioner": existing_practitioner,
            "practitioner_name": frappe.db.get_value("Healthcare Practitioner", existing_practitioner, "practitioner_name") if existing_practitioner else None,
            "payment_entry": payment_entry,
        }

    practitioner_doc = frappe.get_doc("Healthcare Practitioner", practitioner)
    _ensure_doctor_type_exists(practitioner_doc.get("doc_type") or "Doctor")
    patient_doc = frappe.get_doc("Patient", patient)
    customer = frappe.db.get_value("Patient", patient, "customer") or patient_doc.get("customer")
    doctor_amount = flt(practitioner_doc.get("op_consulting_charge") or 0)

    paid_amount = frappe.utils.flt(paid_amount or 0)
    if paid_amount > 0 and not mode_of_payment:
        mode_of_payment = _get_default_mode_of_payment(_get_default_company())

    patient_name = patient_doc.get("patient_name") or patient_doc.get("first_name") or patient
    patient_mobile = _normalize_mobile(patient_doc.get("mobile") or patient_doc.get("phone") or "")
    patient_gender = patient_doc.get("sex") or patient_doc.get("gender") or "Male"
    patient_age = patient_doc.get("p_age") or patient_doc.get("age") or 0
    practitioner_name = practitioner_doc.get("practitioner_name") or practitioner
    practitioner_department = department or practitioner_doc.get("department")

    que = frappe.get_doc(
        {
            "doctype": "Que",
            "patient": patient,
            "patient_name": patient_name,
            "mobile": patient_mobile,
            "gender": patient_gender,
            "age": patient_age,
            "customer": customer,
            "bill_to": customer,
            "practitioner": practitioner,
            "practitioner_name": practitioner_name,
            "department": practitioner_department,
            "doctor_amount": doctor_amount,
            "date": queue_date,
            "time": queue_time,
            "que_type": "New Patient",
            "status": "Open",
            "is_free": 0,
            "follow_up": 0,
            "is_package": 0,
            "is_insurance": 0,
            "paid_amount": paid_amount,
            "mode_of_payment": mode_of_payment,
            "reference": ref_tag,
        }
    )

    try:
        que.insert(ignore_permissions=True)
        # Reload to avoid TimestampMismatchError if hooks modified the document
        que.reload()
        que.submit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "create_que_from_mobile failed")
        frappe.throw(
            "Unable to create queue from mobile. Check patient/practitioner data and required Que fields."
        )

    # Auto-pay the invoice since Waafi payment is already confirmed
    payment_entry = None
    if que.sales_invoice:
        try:
            pay_result = mark_sales_invoice_paid_from_mobile(
                invoice=que.sales_invoice,
                mode_of_payment="Waafi",
                reference_id=reference_id,
            )
            payment_entry = pay_result.get("payment_entry")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "create_que_from_mobile: payment_entry failed")

    return {
        "created": True,
        "que": que.name,
        "invoice": que.sales_invoice,
        "reference_id": reference_id,
        "patient": patient,
        "patient_name": patient_name,
        "practitioner": practitioner,
        "practitioner_name": practitioner_name,
        "payment_entry": payment_entry,
    }


@frappe.whitelist()
def get_unpaid_sales_invoices_for_mobile(patient, limit=100):
    if not patient:
        frappe.throw("patient is required")

    try:
        limit = int(limit)
    except Exception:
        limit = 100
    if limit <= 0:
        limit = 100

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "patient": patient,
            "docstatus": 1,
            "outstanding_amount": [">", 0],
        },
        fields=[
            "name",
            "posting_date",
            "due_date",
            "status",
            "currency",
            "grand_total",
            "outstanding_amount",
        ],
        order_by="posting_date desc",
        limit_page_length=limit,
    )
    return invoices


@frappe.whitelist()
def mark_sales_invoice_paid_from_mobile(
    invoice,
    amount=None,
    mode_of_payment=None,
    reference_id=None,
    provider_txn_id=None,
):
    if not invoice:
        frappe.throw("invoice is required")
    if not frappe.db.exists("Sales Invoice", invoice):
        frappe.throw(f"Sales Invoice not found: {invoice}")

    inv = frappe.get_doc("Sales Invoice", invoice)
    if inv.docstatus != 1:
        frappe.throw("Only submitted sales invoices can be paid from mobile")

    outstanding = flt(inv.outstanding_amount or 0)
    if outstanding <= 0:
        # Invoice already paid (e.g. via POS inline payment in Que.after_insert).
        # Look up an existing Payment Entry that references this invoice.
        existing_pe = frappe.db.get_value(
            "Payment Entry Reference",
            {"reference_doctype": "Sales Invoice", "reference_name": inv.name},
            "parent",
        )
        if not existing_pe:
            # POS invoice — no separate Payment Entry exists yet. Create one now
            # so it appears in the accounting Payment Entry list.
            try:
                pe = get_payment_entry("Sales Invoice", inv.name, party_amount=flt(inv.grand_total))
                pe.mode_of_payment = mode_of_payment or "Waafi"
                pe.reference_no = provider_txn_id or reference_id or inv.name
                pe.reference_date = frappe.utils.nowdate()
                pe.remarks = f"Mobile payment for {inv.name} (ref: {reference_id or ''})".strip()
                pe.paid_amount = flt(inv.grand_total)
                pe.received_amount = flt(inv.grand_total)
                pe.insert(ignore_permissions=True)
                pe.submit()
                existing_pe = pe.name
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Mobile Payment Entry creation failed")
        return {
            "paid": True,
            "invoice": inv.name,
            "outstanding_amount": 0,
            "status": inv.status,
            "payment_entry": existing_pe,
        }

    paid_amount = flt(amount) if amount is not None else outstanding
    if paid_amount <= 0:
        frappe.throw("amount must be greater than zero")
    if paid_amount > outstanding:
        paid_amount = outstanding

    pe = get_payment_entry("Sales Invoice", inv.name, party_amount=paid_amount)
    if mode_of_payment:
        pe.mode_of_payment = mode_of_payment
    elif not pe.mode_of_payment:
        pe.mode_of_payment = _get_default_mode_of_payment(inv.company or _get_default_company())

    if reference_id or provider_txn_id:
        pe.reference_no = provider_txn_id or reference_id
        pe.reference_date = frappe.utils.nowdate()
    pe.remarks = f"Mobile payment for {inv.name} (ref: {reference_id or ''})".strip()
    pe.paid_amount = paid_amount
    pe.received_amount = paid_amount
    pe.insert(ignore_permissions=True)
    pe.submit()

    inv.reload()
    return {
        "paid": flt(inv.outstanding_amount or 0) <= 0,
        "invoice": inv.name,
        "outstanding_amount": inv.outstanding_amount,
        "status": inv.status,
        "payment_entry": pe.name,
    }


@frappe.whitelist()
def get_lab_reports_for_mobile(patient, limit=50):
    if not patient:
        frappe.throw("patient is required")

    try:
        limit = int(limit)
    except Exception:
        limit = 50
    if limit <= 0:
        limit = 50

    reports = frappe.get_all(
        "Lab Result",
        filters={"patient": patient},
        fields=["name", "lab_test_name", "date", "status", "docstatus", "creation"],
        order_by="creation desc",
        limit_page_length=limit,
    )

    if not reports:
        return []

    names = [r["name"] for r in reports]
    files = frappe.get_all(
        "File",
        filters={"attached_to_doctype": "Lab Result", "attached_to_name": ["in", names]},
        fields=["attached_to_name", "file_name", "file_url", "is_private"],
        order_by="creation desc",
    )

    files_by_report = {}
    for f in files:
        files_by_report.setdefault(f["attached_to_name"], []).append(
            {
                "file_name": f.get("file_name"),
                "file_url": f.get("file_url"),
                "is_private": f.get("is_private"),
            }
        )

    response = []
    for r in reports:
        attachments = files_by_report.get(r["name"], [])
        response.append(
            {
                "name": r.get("name"),
                "lab_test_name": r.get("lab_test_name"),
                "date": r.get("date"),
                "status": r.get("status"),
                "docstatus": r.get("docstatus"),
                "download_url": attachments[0]["file_url"] if attachments else None,
                "attachments": attachments,
            }
        )

    return response
