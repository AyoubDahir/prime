import frappe
from erpnext.stock.get_item_details import get_pos_profile


def _normalize_mobile(mobile):
    return (mobile or "").strip()


def _get_default_company():
    return (
        frappe.defaults.get_user_default("company")
        or frappe.defaults.get_global_default("company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )


def _get_default_mode_of_payment(company):
    if not company:
        return None
    try:
        pos_profile = get_pos_profile(company)
        if not pos_profile:
            return None
        return frappe.db.get_value(
            "POS Payment Method",
            {"parent": pos_profile.name},
            "mode_of_payment",
        )
    except Exception:
        return None


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

    patient_name = (full_name or "").strip()
    if not patient_name:
        patient_name = " ".join(
            [p for p in [(first_name or "").strip(), (last_name or "").strip()] if p]
        ).strip()
    if not patient_name:
        frappe.throw("first_name or full_name is required for patient self-registration")
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

    existing_patient = frappe.db.get_value("Patient", {"mobile": mobile}, "name")
    if existing_patient:
        return {"created": False, "patient": existing_patient}

    patient = frappe.get_doc(
        {
            "doctype": "Patient",
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
        return {
            "created": False,
            "que": existing.name,
            "invoice": existing.sales_invoice,
            "reference_id": reference_id,
        }

    practitioner_doc = frappe.get_doc("Healthcare Practitioner", practitioner)
    patient_doc = frappe.get_doc("Patient", patient)
    customer = frappe.db.get_value("Patient", patient, "customer")
    doctor_amount = practitioner_doc.op_consulting_charge or 0

    paid_amount = frappe.utils.flt(paid_amount or 0)
    if paid_amount > 0 and not mode_of_payment:
        mode_of_payment = _get_default_mode_of_payment(_get_default_company())

    que = frappe.get_doc(
        {
            "doctype": "Que",
            "patient": patient,
            "patient_name": patient_doc.patient_name,
            "mobile": patient_doc.mobile,
            "gender": patient_doc.sex,
            "age": patient_doc.p_age or patient_doc.age,
            "customer": customer,
            "practitioner": practitioner,
            "practitioner_name": practitioner_doc.practitioner_name,
            "department": department or practitioner_doc.department,
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

    que.insert(ignore_permissions=True)

    return {
        "created": True,
        "que": que.name,
        "invoice": que.sales_invoice,
        "reference_id": reference_id,
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
