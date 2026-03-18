import frappe


def execute():
    # The custom field stores values like "Doctor"; these are DocType names.
    # Keep link validation aligned with existing records.
    if frappe.db.exists("Custom Field", "Healthcare Practitioner-doc_type"):
        frappe.db.set_value(
            "Custom Field",
            "Healthcare Practitioner-doc_type",
            "options",
            "DocType",
            update_modified=False,
        )

    # Ensure value is set for legacy rows where it may be empty.
    for row in frappe.get_all(
        "Healthcare Practitioner",
        filters={"doc_type": ("in", ["", None])},
        fields=["name"],
    ):
        frappe.db.set_value(
            "Healthcare Practitioner",
            row.name,
            "doc_type",
            "Doctor",
            update_modified=False,
        )

    frappe.clear_cache(doctype="Healthcare Practitioner")
    frappe.db.commit()
