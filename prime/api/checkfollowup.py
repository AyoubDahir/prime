import  frappe

@frappe.whitelist()
def Check_follow_up(**args):
	patient=args.get("patient")
	#doc=args.get("doctor_name")
	sql=frappe.db.sql(f""" select * from `tabFee Validity` where patient='{patient}'  """ ,  as_dict=True)
	return sql
