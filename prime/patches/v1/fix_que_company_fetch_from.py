import frappe


def execute():
    # Legacy typo in Que DocField: patient.companys (invalid field on Patient).
    # This breaks queue insert during link fetch validation.
    # Also sanitize any Que fetch_from that points to missing Patient fields.
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

    patient_fields = {
        row.fieldname
        for row in frappe.get_all("DocField", filters={"parent": "Patient"}, fields=["fieldname"])
    }
    patient_fields.update(
        row.fieldname
        for row in frappe.get_all("Custom Field", filters={"dt": "Patient"}, fields=["fieldname"])
    )

    for doctype, filters in [("DocField", {"parent": "Que"}), ("Custom Field", {"dt": "Que"})]:
        rows = frappe.get_all(doctype, filters=filters, fields=["name", "fetch_from"])
        for row in rows:
            fetch_from = (row.fetch_from or "").strip()
            if not fetch_from.lower().startswith("patient."):
                continue
            patient_field = fetch_from.split(".", 1)[1].strip()
            if patient_field and patient_field not in patient_fields:
                frappe.db.set_value(
                    doctype,
                    row.name,
                    "fetch_from",
                    "",
                    update_modified=False,
                )

    frappe.clear_cache(doctype="Que")
    frappe.db.commit()
