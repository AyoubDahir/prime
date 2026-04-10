import frappe
from erpnext.stock.get_item_details import get_pos_profile
from prime.api.get_mode_of_payments import mode_of_payments


def _sanitize_sales_invoice_defaults():
	"""Clear invalid eval defaults that break Sales Invoice creation."""
	frappe.db.sql(
		"""
		UPDATE `tabDocField`
		SET `default` = ''
		WHERE parent IN ('Sales Invoice', 'Sales Invoice Item')
		  AND LOWER(IFNULL(`default`, '')) LIKE '%return%'
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabCustom Field`
		SET `default` = ''
		WHERE dt IN ('Sales Invoice', 'Sales Invoice Item')
		  AND LOWER(IFNULL(`default`, '')) LIKE '%return%'
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabProperty Setter`
		SET value = ''
		WHERE doc_type IN ('Sales Invoice', 'Sales Invoice Item')
		  AND LOWER(IFNULL(value, '')) LIKE '%return%'
		"""
	)


@frappe.whitelist()
def make_invoice(doc, method=None):
	try:
		_make_invoice(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Que make_invoice failed for " + str(doc.name))
		frappe.msgprint(
			f"⚠️ Sales Invoice could not be created automatically. Please check the Error Log for details.",
			indicator="orange",
			alert=True,
		)


def _make_invoice(doc):
	# Guard: skip if invoice already created
	current_si = frappe.db.get_value("Que", doc.name, "sales_invoice") if doc.name else None
	if current_si:
		return

	# Skip for free, follow-up, renew, revisit, refer queues
	if doc.que_type in ("Refer", "Renew", "Revisit") or doc.follow_up:
		return

	d = frappe.get_doc("Healthcare Practitioner", doc.practitioner)
	consulting_item = d.op_consulting_charge_item
	consulting_rate = d.op_consulting_charge or 0

	if not consulting_item:
		frappe.log_error(
			f"No op_consulting_charge_item on practitioner {doc.practitioner}",
			"Que make_invoice"
		)
		return

	customer = doc.bill_to or frappe.db.get_value("Patient", doc.patient, "customer")
	if not customer:
		frappe.log_error(f"No customer linked to patient {doc.patient}", "Que make_invoice")
		return

	pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
	pos_profile_name = pos_profile.name if pos_profile else None
	cost_center = frappe.db.get_value("POS Profile", pos_profile_name, "write_off_cost_center") if pos_profile_name else None

	is_insurance = doc.is_insurance
	paid_amount = 0 if is_insurance else (doc.paid_amount or 0)
	mode_of_payment = (
		doc.mode_of_payment
		or (frappe.db.get_value("POS Payment Method", {"parent": pos_profile_name}, "mode_of_payment") if pos_profile_name else None)
		or "Cashiers"  # fallback so SI submission never fails due to missing payment row
	)

	# ── 1. Sales Order (consultation fee) ─────────────────────────────────
	so = frappe.new_doc("Sales Order")
	so.source_order = "OPD"
	so.ref_practitioner = doc.practitioner
	so.so_type = "Cashiers"
	so.customer = customer
	so.delivery_date = frappe.utils.getdate()
	so.sales_team = []
	so.flags.ignore_links = 1
	so.flags.ignore_permissions = 1
	so.flags.ignore_mandatory = 1
	so.append("items", {
		"item_code": consulting_item,
		"item_name": consulting_item,
		"qty": 1,
		"rate": consulting_rate,
		"delivery_date": frappe.utils.getdate(),
	})
	so.save()
	so.submit()

	# Mark as "To Bill" — consultation is a service, no delivery note needed
	frappe.db.sql(
		"UPDATE `tabSales Order Item` SET delivered_qty = qty WHERE parent = %s",
		so.name
	)
	frappe.db.set_value("Sales Order", so.name, {"status": "To Bill", "per_delivered": 100})

	# ── 2. Sales Invoice from SO ───────────────────────────────────────────
	_sanitize_sales_invoice_defaults()

	from prime.api.make_invoice import make_sales_invoice as _map_si
	si = _map_si(so.name)

	si.patient = doc.patient
	si.patient_name = doc.patient_name
	si.ref_practitioner = doc.practitioner
	si.is_pos = 1
	si.pos_profile = pos_profile_name
	si.cost_center = cost_center
	si.bill_to_employee = doc.is_employee
	si.employee = doc.employee
	si.is_insurance = is_insurance
	si.is_free = doc.is_free
	si.source_order = "OPD"
	si.posting_date = frappe.utils.getdate()
	si.bill_to_other_customer = doc.bill_to_other_customer
	si.other_customer = doc.other_customer
	si.discount_amount = doc.discount or 0
	si.sales_team = []
	si.flags.ignore_permissions = True
	si.flags.ignore_mandatory = True

	# Payment table — cashier has already collected payment when saving the Que
	si.payments = []
	if mode_of_payment:
		si.append("payments", {
			"mode_of_payment": mode_of_payment,
			"amount": paid_amount,
		})

	si.save()
	si.submit()
	# After SI submit, SO per_billed becomes 100 → status = "Completed" automatically

	frappe.db.set_value("Que", doc.name, "sales_invoice", si.name)
	if frappe.db.has_column("Que", "sales_order"):
		frappe.db.set_value("Que", doc.name, "sales_order", so.name)
	
		
		# frappe.msgprint('Sales Invoice Created successfully')
		
		# if doc.is_free == 1 and doc.follow_up == 0 and  doc.is_insurance==0 and  doc.is_package==0:
		# 		sales_doc = frappe.get_doc({
		# 			"doctype" : "Sales Invoice",
		# 			"patient" : doc.patient,
		# 			"patient_name" : doc.patient_name,
		# 			"customer" : frappe.db.get_value("Patient" , doc.patient, "customer"),
		# 			"practitioner" : doc.practitioner,
		# 			"source_order": "PACKAGE",
		# 			"bill_to_employee" : is_employee,
		# 			"employee" : employee,
		# 			"is_pos" : 1,
		# 			"cost_center": mode_cost[1],
		# 			"pos_profile" : pos_profile.name,
		# 			"posting_date" : frappe.utils.getdate(),
		# 			"items": [{
		# 						"item_code": d.op_consulting_charge_item,
		# 						"item_name": d.op_consulting_charge_item,
								
		# 						"qty": 1,
		# 						"rate": d.op_consulting_charge,
		# 						"amount": 1*d.op_consulting_charge,
					
		# 						"doctype": "Sales Invoice Item"
		# 			}],
		# 			"payments" : [{
		# 				"mode_of_payment" : "Free",
		# 				"amount" : doc.paid_amount
		# 			}]
				
		# 		})
		# 		sales_doc.insert()
		# 		sales_doc.status= "Unpaid"
		# 		sales_doc.save()
		# 		sales_doc.submit()
		# 		doc.sales_invoice=sales_doc.name
		# 		frappe.msgprint('Sales Invoice Created successfully')
			
		# if doc.is_free==0 and doc.follow_up == 0 and  doc.is_insurance==1 and  doc.is_package==0:
		# 	sales_doc = frappe.get_doc({
		# 		"doctype" : "Sales Invoice",
		# 		"patient" : doc.patient,
		# 		"patient_name" : doc.patient_name,
		# 		"customer" : frappe.db.get_value("Patient" , doc.patient, "customer"),
		# 		"practitioner" : doc.practitioner,
		# 		"is_insurance" : 1,
		# 		"source_order": "PACKAGE",
		# 		"bill_to_employee" : is_employee,
		# 		"employee" : employee,
		# 		"is_pos" : 1,
		# 		"cost_center": mode_cost[1],
		# 		"pos_profile" : pos_profile.name,
		# 		"posting_date" : frappe.utils.getdate(),
		# 		"items": [{
		# 					"item_code": d.op_consulting_charge_item,
		# 					"item_name": d.op_consulting_charge_item,
							
		# 					"qty": 1,
		# 					"rate": d.op_consulting_charge,
		# 					"amount": 1*d.op_consulting_charge,
				
		# 					"doctype": "Sales Invoice Item"
		# 		}],
		# 		"payments" : [{
		# 			"mode_of_payment" : mode_cost,
		# 			"amount" : 0
		# 		}]
			
		# 	})
		# 	sales_doc.insert()
		# 	sales_doc.submit()
		# 	doc.sales_invoice=sales_doc.name
		# 	frappe.msgprint('Sales Invoice Created successfully')
		

# @frappe.whitelist()
# def make_invoice_patient_fee(doc, method=None):
# 	pos_profile = get_pos_profile(doc.company)
# 	patient_fee=frappe.db.get_single_value('Healthcare Settings', 'patient_ragistration_fee')
# 	currency=frappe.db.get_single_value('Healthcare Settings', 'currency')

	
# 	if patient_fee:
# 		invoice = frappe.get_doc({
# 			"doctype" : "Sales Invoice",
# 			"patient" : doc.first_name,
# 			"patient_name" : doc.first_name,
# 			"customer" : doc.first_name,
			
# 			"is_pos" : 1,
# 			"pos_profile" : pos_profile.name,
# 			"posting_date" : frappe.utils.getdate(),
# 			"items": [{
# 						"item_code": "Ragistration",
# 						"item_name": "Ragistration",
						
# 						"qty": 1,
# 						"rate": currency,
# 						"amount": 1*currency,
			
# 						"doctype": "Sales Invoice Item"
# 			}],
# 			"payments" : [{
# 				"mode_of_payment" : "Isfree",
# 				"amount" : currency
# 			}]
		   
# 		})
# 		invoice.insert()
# 		invoice.submit()
		
# 		frappe.msgprint('Sales Invoice Created successfully')


@frappe.whitelist()
def renew(name):
	old_que = frappe.get_doc("Que" , name)
	old_que.status = "Renewed"
	old_que.save()
	que = frappe.get_doc({
				"doctype" : "Que",
				"patient": old_que.patient,
				"patient_name" : old_que.patient_name,
				"gender" : old_que.gender,
				"age": old_que.age,
				"practitioner": old_que.practitioner,
				"practitioner_name": old_que.practitioner_name,
				"department" : old_que.department,
				
				"follow_up": 0,
				"is_free" : 0,
				"is_package" : 0,
				"date" : frappe.utils.getdate(),
				"que_type" : "Renew"			
				})
					            
	que.insert(ignore_permissions=1) 
	que.submit()
