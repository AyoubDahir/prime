from erpnext.stock.get_item_details import get_pos_profile
import  frappe

@frappe.whitelist()
def token_numebr(doc, method=None):
	if not frappe.db.get_value('Que', doc.name, "name"):
		# if not frappe.get_doc("Patient Appointment", doc.name):
		prac = doc.practitioner
		# prac ="HLC-PRAC-2021-00002"
		appoinda = doc.date
		b = frappe.db.sql(f""" select Max(token_no) as max from `tabQue` where date = '{appoinda}' and practitioner = '{prac}'  ; """ , as_dict = True)
		num = b[0]['max'] 
		
		if num == None:
			num = 0
		
		doc.token_no = int(num) + 1
	
		# doc.appointment_time = ""
	