# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Posting Time"),
			"fieldname": "posting_time",
			"fieldtype": "Time",
			"width": 100
		},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 120
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 140
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 160
		},
		{
			"label": _("Qty"),
			"fieldname": "actual_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Batch No"),
			"fieldname": "batch_no",
			"fieldtype": "Link",
			"options": "Batch",
			"width": 120
		},
		{
			"label": _("Serial No"),
			"fieldname": "serial_no",
			"fieldtype": "Data",
			"width": 120
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	sql_query = f"""
		SELECT
			sle.posting_date,
			sle.posting_time,
			sle.item_code,
			item.item_name,
			sle.warehouse,
			sle.voucher_type,
			sle.voucher_no,
			sle.actual_qty,
			sle.batch_no,
			sle.serial_no
		FROM
			`tabStock Ledger Entry` sle
			LEFT JOIN `tabItem` item ON sle.item_code = item.item_code
		WHERE
			sle.docstatus = 1
			{conditions}
		ORDER BY
			sle.posting_date DESC, sle.posting_time DESC
	"""
	
	data = frappe.db.sql(sql_query, filters, as_dict=True)
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("company"):
		conditions.append("sle.company = %(company)s")
		
	if filters.get("warehouse"):
		conditions.append("sle.warehouse = %(warehouse)s")
		
	if filters.get("from_date"):
		conditions.append("sle.posting_date >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("sle.posting_date <= %(to_date)s")

	if filters.get("item_code"):
		conditions.append("sle.item_code = %(item_code)s")
		
	return "AND " + " AND ".join(conditions) if conditions else ""
