# Copyright (c) 2024, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on 
from prime.api.create_p_e import payment_re
from prime.api.create_p_e import payment_re_by_debtor

class Receipt(Document):
	def on_submit(self):
		cost_center= self.cost_center
		# def payment_re(party ,paid_amount, posting_date, company,mode_of_payment = None, discount = None ):
		if self.customer:
			party = self.customer
			paid_amount = self.paid_amount
			posting_date = self.posting_date
			discount = self.discount
			mode_of_payment = self.mode_of_payment
			cost_center= self.cost_center
			company = frappe.defaults.get_user_default("company")
			patient = self.patient.split(',')[0].strip()
			
			invoices = get_patient(party , self.from_date , self.to_date ,patient)[1]
			for i in invoices:
				i['reference_doctype']  = 'Sales Invoice'
				i['allocated_amount'] = i.outstanding_amount
			# frappe.errprint(invoices)
			payment_re(party ,paid_amount, posting_date, mode_of_payment, company , discount , invoices, cost_center )
		else:
			for ref in self.reference:
				party = ref.patient
				paid_amount = ref.balance
				posting_date = self.posting_date
				discount = ref.discount
				mode_of_payment = self.mode_of_payment
				company = frappe.defaults.get_user_default("company")
				patient = self.patient.split(',')[0].strip()
				
				invoices = get_invoices(party , self.from_date , self.to_date ,cost_center)
				for i in invoices:
					i['reference_doctype']  = 'Sales Invoice'
					i['allocated_amount'] = i.outstanding_amount
				# frappe.errprint(invoices)
				# frappe.errprint(party)
				# frappe.errprint(paid_amount)
				# frappe.errprint(company)
				# frappe.errprint(discount)
				# frappe.errprint(cost_center)
				# frappe.errprint(mode_of_payment)
				if paid_amount>0:
					payment_re_by_debtor(party ,paid_amount, posting_date, mode_of_payment, company , discount , invoices, cost_center  )




# @frappe.whitelist()
# def get_customer_balance(customer , from_date , to_date):
# 	company = frappe.defaults.get_user_default("Company"),
# 	party_type =  "Customer",
# 	party = frm.doc.customer,
# 	date = frappe.datetime.get_today()
# 	balance = get_balance_on(company , party_type , party , date)



@frappe.whitelist()
def get_patient(customer , from_date , to_date , patient = 'All'):
	so_type= ""
	v = frappe.db.get_value("User Permission",{"user": frappe.session.user, "allow": "Sales Type"},"for_value")
	if v=="Cashiers":
		so_type= "and so_type='Cashiers'"
	elif v=="Pharmacy":
		so_type= "and so_type ='Pharmacy'"
	patient_cond =  f"and patient IS NOT NULL  "
	if patient != "All":
		patient_cond = f"and patient = '{patient}' "

	all_patient = frappe.db.sql(f""" 
	
		 select patient ,patient_name, sum(outstanding_amount) as balance from `tabSales Invoice`  where customer = '{customer}' {patient_cond} {so_type} and posting_date between '{from_date}' and '{to_date}'  and docstatus =1 group by patient;
		""", as_dict =1)
	all_invoices = frappe.db.sql(f""" 
	
		 select name  as reference_name,grand_total as total_amount, outstanding_amount  from `tabSales Invoice`  where customer = '{customer}' {patient_cond} {so_type}  and posting_date between '{from_date}' and '{to_date}'  and docstatus =1;
		""", as_dict =1)
	return [all_patient , all_invoices]



@frappe.whitelist()
def get_customers(customer_group , from_date , to_date , cost_center, patient = 'All'):
	all_cs = frappe.db.get_list('Customer',filters = {'customer_group' : customer_group} , pluck='name')
	all_cs = tuple(all_cs)
	patient_cond =  f"and patient IS NOT NULL"
	if patient != "All":
		patient_cond = f"and customer = '{patient}'"

	all_patient = frappe.db.sql(f""" 
	
		 select customer as patient ,patient_name, sum(outstanding_amount) as balance,  sum(outstanding_amount) as balances from `tabSales Invoice`  where customer in {all_cs} {patient_cond} and posting_date between '{from_date}' and '{to_date}' and cost_center= '{cost_center}' and docstatus =1 group by patient;
		""", as_dict =1)
	all_invoices = frappe.db.sql(f""" 
	
		 select name  as reference_name,grand_total as total_amount, outstanding_amount  from `tabSales Invoice`  where customer in {all_cs} {patient_cond} and posting_date between '{from_date}' and '{to_date}' and cost_center= '{cost_center}' and docstatus =1;
		""", as_dict =1)
	return [all_patient , all_invoices]


@frappe.whitelist()
def get_invoices(party , from_date , to_date , cost_center):


	all_invoices = frappe.db.sql(f""" 
	
		 select name  as reference_name,grand_total as total_amount, outstanding_amount  from `tabSales Invoice`  where customer = '{party}'  and posting_date between '{from_date}' and '{to_date}' and cost_center= '{cost_center}' and docstatus =1;
		""", as_dict =1)
	return all_invoices