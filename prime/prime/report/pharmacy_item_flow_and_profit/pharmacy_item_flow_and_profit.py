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
			"label": _("Incoming Qty"),
			"fieldname": "incoming_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Outgoing Qty"),
			"fieldname": "outgoing_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Balance Qty"),
			"fieldname": "balance_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Sales Revenue"),
			"fieldname": "sales_revenue",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Cost of Sales"),
			"fieldname": "cost_of_sales",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Profit"),
			"fieldname": "profit",
			"fieldtype": "Currency",
			"width": 120
		}
	]

def get_data(filters):
	stock_data = get_stock_data(filters)
	sales_data = get_sales_data(filters)
	
	# Merge data
	data_map = {}
	
	for row in stock_data:
		item_code = row.item_code
		if item_code not in data_map:
			data_map[item_code] = {
				"item_code": item_code,
				"item_name": row.item_name,
				"incoming_qty": 0.0,
				"outgoing_qty": 0.0,
				"balance_qty": 0.0,
				"sales_revenue": 0.0,
				"cost_of_sales": 0.0,
				"profit": 0.0
			}
		data_map[item_code]["incoming_qty"] = row.incoming_qty
		data_map[item_code]["outgoing_qty"] = row.outgoing_qty
		data_map[item_code]["balance_qty"] = row.balance_qty

	for row in sales_data:
		item_code = row.item_code
		if item_code not in data_map:
			data_map[item_code] = {
				"item_code": item_code,
				"item_name": row.item_name,
				"incoming_qty": 0.0,
				"outgoing_qty": 0.0,
				"balance_qty": 0.0,
				"sales_revenue": 0.0,
				"cost_of_sales": 0.0,
				"profit": 0.0
			}
		data_map[item_code]["sales_revenue"] = row.sales_revenue
		data_map[item_code]["cost_of_sales"] = row.cost_of_sales
		data_map[item_code]["profit"] = row.profit

	return list(data_map.values())

def get_stock_data(filters):
	conditions = get_conditions(filters, "sle")
	
	sql_query = f"""
		SELECT
			sle.item_code,
			item.item_name,
			SUM(CASE WHEN sle.actual_qty > 0 THEN sle.actual_qty ELSE 0 END) as incoming_qty,
			SUM(CASE WHEN sle.actual_qty < 0 THEN ABS(sle.actual_qty) ELSE 0 END) as outgoing_qty,
			SUM(sle.actual_qty) as balance_qty
		FROM
			`tabStock Ledger Entry` sle
			LEFT JOIN `tabItem` item ON sle.item_code = item.item_code
		WHERE
			sle.docstatus = 1
			AND sle.is_cancelled = 0
			{conditions}
		GROUP BY
			sle.item_code
	"""
	return frappe.db.sql(sql_query, filters, as_dict=True)

def get_sales_data(filters):
	conditions = get_conditions(filters, "si")
	
	# Mapping SI fields to Filters
	# Note: Date filters need to apply to SII via Parent (Sales Invoice)
	# Conditions generator needs to be aware of the alias or we manually build here.
	
	# Custom conditions for Sales Invoice
	si_conditions = []
	if filters.get("company"):
		si_conditions.append("si.company = %(company)s")
	if filters.get("from_date"):
		si_conditions.append("si.posting_date >= %(from_date)s")
	if filters.get("to_date"):
		si_conditions.append("si.posting_date <= %(to_date)s")
	if filters.get("warehouse"):
		# Warehouse is on Item level usually
		si_conditions.append("sii.warehouse = %(warehouse)s")
	
	where_clause = "AND " + " AND ".join(si_conditions) if si_conditions else ""

	sql_query = f"""
		SELECT
			sii.item_code,
			sii.item_name,
			SUM(sii.base_net_amount) as sales_revenue,
			SUM(sii.stock_qty * sii.incoming_rate) as cost_of_sales,
			SUM(sii.base_net_amount - (sii.stock_qty * sii.incoming_rate)) as profit
		FROM
			`tabSales Invoice` si
			INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
		WHERE
			si.docstatus = 1
			{where_clause}
		GROUP BY
			sii.item_code
	"""
	return frappe.db.sql(sql_query, filters, as_dict=True)

def get_conditions(filters, table_alias):
	conditions = []
	
	if filters.get("company"):
		conditions.append(f"{table_alias}.company = %(company)s")
		
	if filters.get("warehouse") and table_alias == "sle":
		conditions.append(f"{table_alias}.warehouse = %(warehouse)s")
		
	if filters.get("from_date") and table_alias == "sle":
		conditions.append(f"{table_alias}.posting_date >= %(from_date)s")

	if filters.get("to_date") and table_alias == "sle":
		conditions.append(f"{table_alias}.posting_date <= %(to_date)s")

	if filters.get("item_code"):
		# Item Code is common
		col = "item_code" if table_alias else "item_code" 
		conditions.append(f"{table_alias}.{col} = %(item_code)s")
		
	return "AND " + " AND ".join(conditions) if conditions else ""
