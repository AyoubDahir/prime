# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils import add_to_date
from prime.api.get_mode_of_payments import  mode_of_payments
def execute(filters=None):
	
	return get_columns(), get_data(filters)

def get_data(filters):
	account = mode_of_payments()[0]
	abbr = frappe.db.get_value("Company", frappe.defaults.get_user_default("company"), "abbr")
	company = frappe.defaults.get_global_default("company")
	_from ,to = filters.get('from_date'), filters.get('to')  
	report_gl = frappe.get_doc("Report", "General Ledger")
   

	report_gl_filters = {
		
		"company": company,
		

		"from_date": _from,
		"to_date": to,
		"group_by": "Group by Voucher (Consolidated)",
		"account" : ['1100 - Cash In Hand - RH', '112 - Cash in Bank - RH'],
		"cost_center" : [filters.cost_center]
	}
	if filters.account :
		report_gl_filters["account"] = [filters.account]
	# else:
	# 	report_gl_filters["account"] = [account]

		
	columns_gl, data_gl = report_gl.get_data(
		limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
	)
	# frappe.errprint(data_gl)
	sales_data = []
	recips = []
	payments= []
	purchase = []
	others = []
	incash = []
	totals = []
	totals_ = [{"customer_name" :  "<b>Summery</b>" } ,{"customer_name" :  "Total Sales"  , "debit" : 0}   , {"customer_name" :  "Total Refund"  , "debit" : 0}  , {"customer_name" :  "Total Debt Recieved"  , "debit" : 0}]
	for data in data_gl:
		if data.posting_date and data.voucher_type == "Sales Invoice":
			sales_type = "Sales"
			if frappe.db.get_value("Sales Invoice" , data.voucher_no , "is_return"):
				sales_type = "Refund"
				totals_[2]['debit'] = totals_[2]['debit'] + data.credit
			else:
				totals_[1]['debit'] = totals_[1]['debit'] + data.debit
			sales_data.append(
					{
						"type" : sales_type,
						"voucher_type": data.voucher_type,
						"date" : data.posting_date,
						"time" : frappe.db.get_value("Sales Invoice" , data.voucher_no, "posting_time"),
						"user": frappe.db.get_value("User", frappe.db.get_value("Sales Invoice", data.voucher_no,"owner"), "full_name"),
						"voucher_no" : data.voucher_no,
						"customer" :   frappe.db.get_value("Patient", {"customer":data.against},"name") or data.against,
						"customer_name" :  frappe.db.get_value("Customer" ,data.against, "customer_name"),
						"mobile":  frappe.db.get_value("Sales Invoice" , data.voucher_no, "contact_mobile"),
						"account" : data.account,
						"debit" : data.debit or '',
						"credit" : data.credit or '',
						"balance" : data.balance or '',
						
					}

			)
		if data.posting_date and data.voucher_type == "Purchase Invoice":
			# if data.account.replace("'","") != 'Total':
			purchase.append({
							"voucher_type" : data.voucher_type,
							"type": "Purchase",
							"date" : data.posting_date,
							"user": frappe.db.get_value("User", frappe.db.get_value("Sales Invoice", data.voucher_no,"owner"), "full_name"),
							"customer" :   frappe.db.get_value("Patient", {"customer":data.against},"name") or data.against,
							"voucher_no" : data.voucher_no,
							"debit" : data.debit or '',
							"credit" : data.credit or '',
							"balance" : data.balance or '',
						}
				
			)
		elif data.posting_date and data.voucher_type == "Payment Entry" and frappe.db.get_value("Payment Entry", data.voucher_no, "payment_type") == "Receive":
			# if data.account.replace("'","") != 'Total':
			totals_[3]['debit'] = totals_[3]['debit'] + data.debit
			recips.append({
							"type" : "Receive",
							"date" : data.posting_date,
							"user": frappe.db.get_value("User", frappe.db.get_value("Sales Invoice", data.voucher_no,"owner"), "full_name"),
							"voucher_type": data.voucher_type,
							"customer_name" : frappe.db.get_value("Customer" ,data.against, "customer_name"),
							"customer" :  frappe.db.get_value("Patient", {"customer":data.against},"name") or data.against, 
							"voucher_no" : data.voucher_no,
							"account" : data.account,
							"debit" : data.debit or '',
							"credit" : data.credit or '',
							"balance" : data.balance or '',
							# "user": "Mohamed Aweis",
						}
				
			)
		elif data.posting_date and data.voucher_type == "Payment Entry" and frappe.db.get_value("Payment Entry", data.voucher_no, "payment_type") == "Pay":
			# if data.account.replace("'","") != 'Total':
			payments.append({
							"type" : "Payment",
							"voucher_type": data.voucher_type,
							"date" : data.posting_date,
							"user": frappe.db.get_value("User", frappe.db.get_value("Sales Invoice", data.voucher_no,"owner"), "full_name"),
							"customer" :  frappe.db.get_value("Patient", {"customer":data.against},"name") or data.against,
							"voucher_no" : data.voucher_no,
							"debit" : data.debit or '',
							"credit" : data.credit or '',
							"balance" : data.balance or '',
						}
				
			)
		elif data.posting_date and data.voucher_type == "Journal Entry":
			# if data.account.replace("'","") != 'Total':
			# totals_[4]['debit'] = totals_[4]['debit'] + data.debit
			others.append({
							"type" : data.voucher_type,
							"voucher_type": data.voucher_type,
							"date" : data.posting_date,
							"user": frappe.db.get_value("User", frappe.db.get_value("Sales Invoice", data.voucher_no,"owner"), "full_name"),
							"customer" :  frappe.db.get_value("Patient", {"customer":data.against},"name") or data.against,
							"voucher_no" : data.voucher_no,
							"debit" : data.debit or '',
							"credit" : data.credit or '',
							"balance" : data.balance or '',
						}
				
			)
		else:
			if data.account.replace("'","") == 'Opening' :
			
				incash.append({
							"type" : data.account.replace("'",""),
							"date" : data.posting_date,
							
							"voucher_no" : data.voucher_no,
							"debit" : data.debit ,
							"credit" : data.credit ,
							"balance" : data.balance ,
							
						}
				
			)
			if data.account.replace("'","") == 'Total' or data.account.replace("'","") == 'Closing (Opening + Total)' :
			
				totals.append({
							"type" : data.account.replace("'",""),
							"date" : data.posting_date,
							
							"voucher_no" : data.voucher_no,
							"debit" : data.debit ,
							"credit" : data.credit ,
							"balance" : data.balance ,
							
						}
				
			)
				if data.account.replace("'","") == 'Total': 
					totals.append({
								"type" : "Balance",
								"date" : data.posting_date,
								
								"voucher_no" : data.voucher_no,
								"credit" : "" ,
								"debit" : "" ,
								"balance" : data.balance ,
								
								
							}
					
				)

	for data_list in (sales_data , recips , purchase , payments , others , totals , totals_) :
		for data in data_list:
			incash.append(data)
	# if not filters.account:
	# 	return []
	return incash



def get_columns():
	columns = [

{
			"label": _("Date"),
			"fieldtype": "Date",
			"fieldname": "date",
			
			"width": 80,
		},
		{
			"label": _("Time"),
			"fieldtype": "Time",
			"fieldname": "time",
			
			"width": 80,
		},
		{
			"label": _("User"),
			"fieldtype": "Data",
			"fieldname": "user",
			
			"width": 130,
		},

		{
			"label": _("Type"),
			"fieldtype": "Data",
			"fieldname": "type",
			
			"width": 80,
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type", 
			"width": 100,
			"hidden": 1,
			
		},


		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 150,
		},
	
		
		
		# 	{
		# 	"label": _("Account"),
		# 	"fieldtype": "Data",
		# 	"fieldname": "account",
			
		# 	"width": 200,
		# },

		{
			"label": _("PID"),
			"fieldtype": "Data",
			"fieldname": "customer",
			
			"width": 100,
		},
		
			{
			"label": _("against"),
			"fieldtype": "Data",
			"fieldname": "customer_name",
			
			"width": 300,
		},
		
		{
			"label": _("Mobile"),
			"fieldtype": "Data",
			"fieldname": "mobile",
			
			"width": 200,
		},


			{
			"label": _("Account"),
			"fieldtype": "Link",
			"fieldname": "account",
			"options" : "Account" ,
			
			"width": 200,
		},
			
			
		
		
			{
			"label": _("Debit"),
			"fieldtype": "Currency",
			"fieldname": "debit",
			
			"width": 100,
		},

		{
			"label": _("Credit"),
			"fieldtype": "Currency",
			"fieldname": "credit",
			
			"width": 100,
		},
		{
			"label": _("Balance"),
			"fieldtype": "Currency",
			"fieldname": "balance",
			
			"width": 150,
		},
			
	]

	return columns



