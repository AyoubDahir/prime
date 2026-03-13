# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	
	return get_columns(), get_data(filters)

def get_data(filters):
	
	_from ,to  = filters.get('from_date'), filters.get('to') 
	
	data = frappe.db.sql(f"""
	select 
	posting_date,
	name, 
	customer_name ,
	net_total,
	paid_amount,
	discount_amount,
	outstanding_amount,
	
	owner  

from `tabSales Invoice`
where posting_date between "{_from}" and "{to}"  and docstatus = 1
 ;""")
	return data
def get_columns():
	return [

		"Date: Date:120",
		"Reciept No:Link/Sales Invoice:220",
		"Customer Name:Link/Customer:200", 
		"Amount:Currency:110",
		
		"Piad:Currency:110",
		"Discount:Currency:110",
		"Unpaid:Currency:110",
		"User:Link/User:220",

	
		
	]

