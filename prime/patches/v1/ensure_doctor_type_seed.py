import frappe


def _ensure_doctor_type(name: str) -> None:
    if frappe.db.exists("Doctor Type", name):
        return

    doc = frappe.get_doc(
        {
            "doctype": "Doctor Type",
            "do_type": name,
        }
    )
    doc.insert(ignore_permissions=True)


def execute():
    # Seed Doctor Type masters used by Healthcare Practitioner.doc_type link field.
    for doctor_type in ("Doctor", "GP", "Specialist"):
        _ensure_doctor_type(doctor_type)

    # Normalize existing practitioners that had invalid/empty doc_type values.
    practitioners = frappe.get_all(
        "Healthcare Practitioner",
        filters={"doc_type": ("in", ["", None])},
        fields=["name"],
    )
    for row in practitioners:
        frappe.db.set_value(
            "Healthcare Practitioner",
            row.name,
            "doc_type",
            "Doctor",
            update_modified=False,
        )

    # Ensure broken legacy values are corrected as well.
    invalid = frappe.db.sql(
        """
        SELECT hp.name
        FROM `tabHealthcare Practitioner` hp
        LEFT JOIN `tabDoctor Type` dt ON dt.name = hp.doc_type
        WHERE IFNULL(hp.doc_type, '') != '' AND dt.name IS NULL
        """,
        as_dict=True,
    )
    for row in invalid:
        frappe.db.set_value(
            "Healthcare Practitioner",
            row.name,
            "doc_type",
            "Doctor",
            update_modified=False,
        )

    frappe.db.commit()
