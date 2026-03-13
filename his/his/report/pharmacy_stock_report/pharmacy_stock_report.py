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
			"label": _("Description"),
			"fieldname": "description",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 120
		},
		{
			"label": _("Qty"),
			"fieldname": "actual_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 100
		},
		{
			"label": _("Valuation Rate"),
			"fieldname": "valuation_rate",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Stock Value"),
			"fieldname": "stock_value",
			"fieldtype": "Currency",
			"width": 120
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	sql_query = f"""
		SELECT
			item.item_code,
			item.item_name,
			item.description,
			bin.warehouse,
			bin.actual_qty,
			item.stock_uom,
			bin.valuation_rate,
			(bin.actual_qty * bin.valuation_rate) as stock_value
		FROM
			`tabBin` bin
			INNER JOIN `tabItem` item ON bin.item_code = item.item_code
			INNER JOIN `tabWarehouse` wh ON bin.warehouse = wh.name
		WHERE
			bin.actual_qty != 0
			AND item.disabled = 0
			{conditions}
		ORDER BY
			item.item_code ASC
	"""
	
	data = frappe.db.sql(sql_query, filters, as_dict=True)
	return data

def get_conditions(filters):
	conditions = []
	
	if filters.get("company"):
		conditions.append("wh.company = %(company)s")
		
	if filters.get("warehouse"):
		conditions.append("bin.warehouse = %(warehouse)s")
		
	if filters.get("item_group"):
		conditions.append("item.item_group = %(item_group)s")

	if filters.get("item_code"):
		conditions.append("item.item_code = %(item_code)s")
		
	return "AND " + " AND ".join(conditions) if conditions else ""
