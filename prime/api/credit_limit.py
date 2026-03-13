import frappe
@frappe.whitelist()
def credit_limit(doc , method =None):
    doc.append("credit_limits" , {
        "company" : frappe.defaults.get_user_default("company"),
        "credit_limit" : 0.01
    })