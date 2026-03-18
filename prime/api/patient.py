import frappe
from datetime import datetime # from python std library
from frappe.utils import add_to_date


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


def enforce_unique_mobile(doc, method=None):
    normalized = _normalize_mobile(doc.get("mobile"))
    if not normalized:
        return

    doc.mobile = normalized
    if "mobile_no" in doc.meta.get_valid_columns():
        doc.mobile_no = normalized

    duplicate = frappe.db.get_value(
        "Patient",
        {"mobile": normalized, "name": ["!=", doc.name or ""]},
        "name",
    )
    if duplicate:
        frappe.throw(f"Patient with mobile {normalized} already exists: {duplicate}")


def age_todate(doc, method=None):
    if doc.p_age is None:
        frappe.throw("Age is mandatory")
    if not doc.age_type:
        frappe.throw("Age type is mandatory")
    if doc.p_age < 0 :
        frappe.throw("Age Can not be Negative ")
    if doc.age_type=="Year":

        # frappe.msgprint(str(doc.p_age)+ " "+ str(doc.age_type))
        add_year = add_to_date(datetime.now(), years=-doc.p_age, as_string=True)
        doc.dob=add_year
        # frappe.msgprint(add_year)
    elif doc.age_type=="Month":
        add_month = add_to_date(datetime.now(), months=-doc.p_age, as_string=True)
        doc.dob=add_month
        # frappe.msgprint(add_month)
    elif doc.age_type=="Day":
        add_day = add_to_date(datetime.now(), days=-doc.p_age, as_string=True)
        doc.dob=add_day
        # frappe.msgprint(add_day)


# def invoice_registration(doc, method=None):
#     invoice_info = doc.invoice_patient_registration()
#     invoice = frappe.get_doc("Sales Invoice", invoice_info["invoice"])
#     invoice.patient = doc.name

#     fee_item = invoice.items[0]
#     fee_item.item_name = fee_item.description = "Registration Fee"

#     if doc.collect_registration_fee:
#         invoice.is_pos = True
#         invoice.append(
#             "payments",
#             {"mode_of_payment": doc.mode_of_payment, "amount": invoice.grand_total},
#         )
#         invoice.set_missing_values()
#         invoice.update_stock = 0
#         set_account_for_mode_of_payment(invoice)

#     invoice.flags.ignore_permissions = True
#     invoice.submit()


# @frappe.whitelist()
# def get_mode_of_payment():
#     company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value(
#         "Global Defaults", "default_company"
#     )

#     if not company:
#         return

#     pos_profile = get_pos_profile(company)
#     if not pos_profile:
#         return

#     pos_profile = frappe.get_doc("POS Profile", pos_profile.get("name"))
#     if not pos_profile.payments:
#         return

#     for payment in pos_profile.payments:
#         if payment.default:
#             return payment.mode_of_payment
#     else:
#         return pos_profile.payments[0].mode_of_payment
