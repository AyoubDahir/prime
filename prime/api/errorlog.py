import frappe
def create_error_log(doct , docn ,method, err):
    err_do = frappe.get_doc({
        "doctype" : "Error Log",
        # "reference_doctype" : doct,
        "reference_name" : docn,
        # "custom_ref_doc" : docn,
        "method" : method,
        "error" : err
    }).insert(ignore_permissions = 1)