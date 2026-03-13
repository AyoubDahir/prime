# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt
from erpnext.stock.get_item_details import get_pos_profile
import frappe
from frappe.model.document import Document
from prime.api.package import set_so_values_from_db
from prime.api.package import enqueue_sales_orders

class Packages(Document):
	def after_insert(self):
		# frappe.msgprint("ll")
		enqueue_sales_orders(self)

@frappe.whitelist()
def fetch_package_prescriptions(parent_name):
	return frappe.get_all(
		"Package prescription",
		filters={"parent": parent_name},
		fields=["*"],
		order_by="idx asc"
	)