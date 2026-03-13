import frappe
from frappe import _
from frappe.utils import getdate
from frappe.model.mapper import map_doc

def set_so_values_from_db(doc, method=None):
    so_type = "services_so"  # single value, not an iterable of chars
    if not doc.get(so_type):
        doc.set(so_type, doc.db_get(so_type))

def enqueue_sales_orders(doc, method=None):
    create_sales_orders(doc=doc)
    frappe.publish_realtime("new_msg")

def create_sales_orders(doc):
    so_type = "services_so"  # single value
    sales_order = None

    so_name = doc.get(so_type)
    if so_name:
        sales_order = frappe.get_doc("Sales Order", so_name)
    else:
        sales_order = frappe.new_doc("Sales Order")
        sales_order.source_order = "Package"
        # sales_order.ref_practitioner = doc.practitioner

    map_doc(
        doc,
        sales_order,
        {
            "Packages": {
                "doctype": "Sales Order",
                "field_no_map": ["source", "docstatus"],
            },
        },
    )

    sales_order.__updated_items = []
    sales_order.delivery_date = getdate()
    sales_order.customer = frappe.db.get_value("Patient", doc.patient, "customer")
    if not sales_order.customer:
        frappe.throw("Please set a Customer linked to the Patient")

    add_package_items(sales_order, doc)  # only once
    sales_order.so_type = "Cashiers"
    sales_order.user = frappe.session.user
    sales_order.full_name = frappe.db.get_value("User", frappe.session.user, "full_name")

    # Keep only items we just touched
    sales_order.items = [
        row for row in sales_order.get("items", default=[])
        if row.reference_dn in sales_order.__updated_items
    ]

    # If there are no items and it's a new doc, do nothing
    if not sales_order.items and not sales_order.name:
        return

    sales_order.flags.ignore_links = 1
    sales_order.flags.ignore_validate_update_after_submit = 1
    sales_order.flags.ignore_permissions = 1

    if sales_order.name:
        if not sales_order.items:
            sales_order.reload()
            sales_order.cancel()
            doc.db_set(so_type, "", update_modified=False, notify=True)
            return
        sales_order.db_set("docstatus", 0, update_modified=False)

    sales_order.save()
    sales_order.submit()
    frappe.db.set_value('Packages', doc.name, 'services_so', sales_order.name)
    # doc.services_so = sales_order.name

def add_package_items(so, doc):
    # remove the bogus outer loop; just iterate the child table once
    for row in doc.get("package_prescription", []):
        so_item = find_or_create_item(row, so, doc)
        so_item.item_code = row.item
        so_item.item_name = row.item
        so_item.qty = 1
        so_item.rate = row.rate
        so_item.description = row.description

def find_or_create_item(row, so, doc, from_templae=False):
    for item in so.get("items", []):
        if item.reference_dn == row.name:
            break
    else:
        item = so.append("items")
        item.reference_dt = row.doctype
        item.reference_dn = row.name

    if from_templae:
        item.reference_dt = ""
        item.reference_dn = ""

    if doc.get("branch"):
        item.branch = doc.branch

    so.__updated_items.append(item.reference_dn)
    return item
