import frappe
from prime.api.errorlog import create_error_log
from erpnext.stock.get_item_details import get_pos_profile
from datetime import datetime

def make_sample_collection(doc, method=None , items = None):
    pos_profile = get_pos_profile(doc.company)
    if not pos_profile:
        # No POS Profile configured, skip sample collection for non-POS invoices
        return
    mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
    default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
    # for i in  doc.payments:
    #     if i.mode_of_payment != mode_of_payment:
    #         frappe.throw(f"Please Change Mode of Payment {i.mode_of_payment}")
    itms= []
    if items:
        itms = items
    else:
        if not doc.is_return:
            count=0
            last_id = None
            for i in doc.items:
                # frappe.msgprint(str(last_id))
              count=count+1
              if frappe.db.exists("Lab Test Template", i.item_code, cache=True) and doc.source_order != "IPD":
                    if frappe.db.get_value("Lab Test Template", i.item_code, "custom_is_profile"):
                        pro_doc = frappe.get_doc("Lab Test Template" ,i.item_code )
                        for test in pro_doc.lab_test_groups:
                            itms.append(
                                {
                                    "lab_test": test.lab_test_template, 
                                    "custom_urgent" :0,
                                }
                            )
                    else:
                        itms.append(
                                    {
                                    "lab_test": i.item_code, 
                                    "custom_urgent" : i.custom_urgent, 
                                    # "test_id" : get_test_id(last_id)         
                        }
                        )
                    # last_id = get_test_id()

    if itms:
        sm_doc = frappe.get_doc({
            'doctype': 'Sample Collection',
            'sample_qty': 1,
            'practitioner':doc.ref_practitioner,
            'patient': doc.patient,
            'lab_test': itms,
            'reff_invoice' : doc.name,
            'source_order' : doc.source_order,
            'doner' : doc.doner,
            "for_patient" : doc.ref_patient,
            "invoiced" : 1,
            "reff_inovoice" : doc.name,
            "custom_urgent" : doc.custom_urgent
           
            # "blood_donar" : 1
        })
        sm_doc.insert(ignore_permissions = True)
        event = "lab_test_update"
    # msg = {"content" : "This updated Encounter"}
        frappe.publish_realtime(event)
        # if doc.ref_patient:
        #     blood_strore = 



def make_sample_collection_from_order(doc, method=None , items = None):
    try:
        his_settings = frappe.get_doc("Prime Settings", "Prime Settings")
        if his_settings.bill_services_after_complication:
                    
            if doc.source_order =="IPD" and doc.so_type=="Cashiers":
                itms= []
                if items:
                    itms = items
                else:
                    count=0
                    for i in doc.items:
                        if frappe.db.exists("Lab Test Template", i.item_code, cache=True):
                            if frappe.db.get_value("Lab Test Template", i.item_code, "custom_is_profile"):
                                pro_doc = frappe.get_doc("Lab Test Template" ,i.item_code )
                                for test in pro_doc.lab_test_groups:
                                    itms.append(
                                        {
                                            "lab_test": test.lab_test_template,
                                            "custom_urgent" :0,
                                            })
                            else:
                                itms.append(
                                    {
                                        "lab_test": i.item_code,
                                        "custom_urgent" : i.custom_urgent,
                                        # "test_id" : get_test_id(last_id)
                                        })
                            # last_id = get_test_id()

                if itms:
                    sm_doc = frappe.get_doc({
                        'doctype': 'Sample Collection',
                        'sample_qty': 1,
                        'practitioner':doc.ref_practitioner,
                        'patient': doc.patient,
                        'lab_test': itms,
                        "custom_urgent" : doc.custom_urgent,
                        'custom_reff_order' : doc.name,
                        'custom_reff_ipdorder' : doc.custom_reff_ipdorder,
                        'source_order' : doc.source_order,
                        # 'doner' : doc.doner,
                        "for_patient" : doc.patient,
                        # "blood_donar" : 1
                    })
                    sm_doc.insert(ignore_permissions = True)
                    event = "lab_test_update"
                    # msg = {"content" : "This updated Encounter"}
                    frappe.publish_realtime(event)
                        # if doc.ref_patient:
                        #     blood_strore = 
    except Exception as e:
        # pass
        create_error_log("Sample Collection" , doc.name , "Creting Collection From Order" , str(e))


def get_test_id(last_id = None):
    if not last_id:
        lab_doc = frappe.get_last_doc("Lab Sample")
        last_lab_id = lab_doc.test_id
    else:
        last_lab_id = last_id
    if last_lab_id:
        # frappe.msgprint(str(last_lab_id))
        test_id = int(last_lab_id) + 1
    else:
        test_id =  1
    
    return  test_id



@frappe.whitelist()
def token_number(doc, method=None):
    # Only assign token_no if this is a new Sample Collection (not yet saved)
    if not frappe.db.exists('Sample Collection', doc.name):

        # Ensure date is in datetime.date format
        if isinstance(doc.date, str):
            doc_date = datetime.strptime(doc.date, "%Y-%m-%d").date()
        else:
            doc_date = doc.date

        # Fetch max token_no for that specific date
        result = frappe.db.sql("""
            SELECT MAX(token_no) AS max_token
            FROM `tabSample Collection`
            WHERE date = %s
        """, (doc_date,), as_dict=True)

        max_token = result[0].get("max_token") if result else 0
        next_token = (max_token or 0) + 1

        # Assign to the document
        doc.token_no = next_token
        doc.token_no_display = f"{next_token:03}"  # e.g., "001", "002", ...

        # Optional: Set lab_ref from the last sample collection (if needed)
        last_doc = frappe.get_last_doc("Sample Collection")
        if last_doc and last_doc.lab_ref:
            try:
                doc.lab_ref = int(last_doc.lab_ref) + 1
            except (ValueError, TypeError):
                doc.lab_ref = 1


# # midkan by number kaliya waaye sida 1,2,3
# @frappe.whitelist()
# def token_number(doc, method=None):
#     if not frappe.db.get_value('Sample Collection', doc.name, "name"):
#         # if not frappe.get_doc("Patient Appointment", doc.name):
#         # prac = doc.doctor
#         # prac ="HLC-PRAC-2021-00002"
#         date = doc.date
#         b = frappe.db.sql(f""" select Max(token_no) as max from `tabSample Collection` where date = '{date}'  ; """ , as_dict = True)
#         num = b[0]['max'] 
#         # frappe.msgprint(num)
#         if num == None:
#             num = 0
        
#         doc.token_no = int(num) + 1
#         # doc.appointment_time = ""
#         col = frappe.get_last_doc("Sample Collection")
        
#         if col:
#             if col.lab_ref:
#                 doc.lab_ref = int(col.lab_ref) + 1