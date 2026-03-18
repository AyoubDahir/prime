import frappe


def execute():
    # Legacy typo in Que DocField: patient.companys (invalid field on Patient).
    # This breaks queue insert during link fetch validation.
    targets = [
        ("DocField", {"parent": "Que", "fieldname": "company"}),
        ("Custom Field", {"dt": "Que", "fieldname": "company"}),
    ]

    for doctype, filters in targets:
        rows = frappe.get_all(doctype, filters=filters, fields=["name", "fetch_from"])
        for row in rows:
            if (row.fetch_from or "").strip().lower() == "patient.companys":
                frappe.db.set_value(
                    doctype,
                    row.name,
                    "fetch_from",
                    "patient.customer",
                    update_modified=False,
                )

    frappe.clear_cache(doctype="Que")
    frappe.db.commit()
