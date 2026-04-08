import frappe
from frappe import _


@frappe.whitelist()
def run_cleanup(group):
    if "System Manager" not in frappe.get_roles():
        frappe.throw(_("Only System Manager can run data cleanup."))

    log = []
    db = frappe.db

    def safe_delete(table, where=None):
        try:
            sql = "DELETE FROM `{}`".format(table)
            if where:
                sql += " WHERE " + where
            db.sql(sql)
            log.append("Deleted: {}".format(table))
        except Exception as e:
            log.append("Skipped {}: {}".format(table, str(e)))

    if group in ("transactions", "all"):
        safe_delete("tabPayment Entry Reference")
        safe_delete("tabPayment Entry Deduction")
        safe_delete("tabGL Entry", "voucher_type='Payment Entry'")
        safe_delete("tabPayment Entry")
        safe_delete("tabSales Invoice Item")
        safe_delete("tabSales Invoice Payment")
        safe_delete("tabSales Taxes and Charges", "parenttype='Sales Invoice'")
        safe_delete("tabGL Entry", "voucher_type='Sales Invoice'")
        safe_delete("tabStock Ledger Entry", "voucher_type='Sales Invoice'")
        safe_delete("tabPayment Ledger Entry", "voucher_type='Sales Invoice'")
        safe_delete("tabSales Invoice")
        safe_delete("tabSales Order Item")
        safe_delete("tabSales Taxes and Charges", "parenttype='Sales Order'")
        safe_delete("tabSales Order")
        safe_delete("tabGL Entry")
        safe_delete("tabPayment Ledger Entry")
        safe_delete("tabStock Ledger Entry")

    if group in ("clinical", "all"):
        safe_delete("tabPatient Encounter Symptom")
        safe_delete("tabPatient Encounter Diagnosis")
        safe_delete("tabDrug Prescription")
        safe_delete("tabLab Prescription")
        safe_delete("tabRadiology Prescription")
        safe_delete("tabProcedure Prescription")
        safe_delete("tabPatient Encounter")
        safe_delete("tabPatient Appointment")
        safe_delete("tabVital Signs")
        safe_delete("tabLab Commission")
        safe_delete("tabLab Test Expenses")
        safe_delete("tabLab Test Sample")
        safe_delete("tabLab Sample")
        safe_delete("tabLab Result")
        safe_delete("tabLab Test")
        safe_delete("tabSample")
        safe_delete("tabSample Collection")
        safe_delete("tabQue")

    if group in ("patients", "all"):
        safe_delete("tabPatient Medical Record")
        safe_delete("tabPatient")

    if group in ("logs", "all"):
        safe_delete("tabError Log")
        safe_delete("tabScheduled Job Log")
        safe_delete("tabNotification Log")
        safe_delete("tabSMS Log")
        safe_delete("tabEmail Queue Recipient")
        safe_delete("tabEmail Queue")
        safe_delete("tabActivity Log")
        safe_delete("tabAccess Log")

    if group == "all":
        try:
            db.sql("UPDATE `tabSeries` SET current = 0")
            log.append("Reset all naming series to 0")
        except Exception as e:
            log.append("Series reset skipped: " + str(e))

    frappe.db.commit()
    return {"success": True, "log": log}
