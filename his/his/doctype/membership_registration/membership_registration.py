# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MembershipRegistration(Document):
    def validate(self):
        self.total = len(self.family_members)
        self.flags._previous_status = frappe.db.get_value(self.doctype, self.name, "status")

    def before_insert(self):
        # Get last card number from settings
        last_card = frappe.db.get_single_value("Prime Settings", "last_card_number") or 0
        new_card = int(last_card) + 1

        # Assign new card number
        self.card_number = new_card

        # Save new last card number
        frappe.db.set_value("Prime Settings", "Prime Settings", "last_card_number", new_card)

    def on_update(self):
        # frappe.errprint(self)
        # Store initial status on load
        if self.discount_level and self.status == "Active":
            # frappe.errprint(f"Inactive IF {previous_status}")
            for member in self.family_members:
                if member.patient:
                    frappe.db.set_value("Patient", member.patient, {
                        "percentage": self.discount_level,
                        
                    })


        previous_status = getattr(self.flags, "_previous_status", None)
            
        if self.status == "Inactive" and previous_status != "Inactive":
            # frappe.errprint(f"Inactive IF {previous_status}")
            for member in self.family_members:
                if member.patient:
                    try:
                        frappe.db.set_value("Patient", member.patient, {
                            "percentage": 0,
                            # "customer_group": "All Customer Groups",
                            "is_membership": "",
                            "member_card_status": "Inactive"
                        })
                    except Exception as e:
                        frappe.log_error(f"Failed to deactivate patient {member.patient}: {str(e)}", "Membership Deactivation")

        elif self.status == "Active" and previous_status == "Inactive":
            # frappe.errprint(f"Active ELIF {previous_status}")
            # customer_group = frappe.db.get_single_value("Prime Settings", "default_customer_group") or "Membership"
            for member in self.family_members:
                if member.patient:
                    try:
                        frappe.db.set_value("Patient", member.patient, {
                            "percentage": self.discount_level,
                            # "customer_group": customer_group,
                            "is_membership": "Membership",
                            "member_card_status": "Active"
                        })
                    except Exception as e:
                        frappe.log_error(f"Failed to reactivate patient {member.patient}: {str(e)}", "Membership Reactivation")




@frappe.whitelist()
def register_family_members(docname):
    doc = frappe.get_doc("Membership Registration", docname)
    registered = []
    skipped = []

    for member in doc.family_members:
        if member.visited:
            continue

        # Validate required fields
        if not member.full_name or not member.mobile or not member.age:
            frappe.log_error(f"Incomplete info for member: {member.name}", "Registration Skipped")
            skipped.append({"name": member.name, "reason": "Incomplete information"})
            continue

        try:
            if member.patient:
                updating_patient = frappe.get_doc("Patient", member.patient)
                updating_patient.first_name = member.full_name
                updating_patient.mobile_no = member.mobile
                updating_patient.sex = member.sex
                updating_patient.p_age = member.age
                updating_patient.age_type = member.age_type
                updating_patient.percentage = doc.discount_level
                updating_patient.is_membership = "Membership"
                # updating_patient.customer_group = customer_group
                updating_patient.membership = doc.name
                updating_patient.member_card = doc.card_number
                updating_patient.member_company = doc.company
                updating_patient.member_contact = doc.contact_number
                updating_patient.member_head = doc.family_head_person
                updating_patient.save()
                member.visited = 1
            else:
                patient = frappe.get_doc({
                    "doctype": "Patient",
                    "first_name": member.full_name,
                    "mobile_no": member.mobile,
                    "sex": member.sex,
                    "p_age": member.age,
                    "age_type": member.age_type,
                    "percentage": doc.discount_level,
                    "is_membership": "Membership",
                    # "customer_group": customer_group,
                    "membership": doc.name,
                    "member_card": doc.card_number,
                    "member_company": doc.company,
                    "member_contact": doc.contact_number,
                    "member_head": doc.family_head_person
                })
                patient.insert(ignore_permissions=True)
                member.visited = 1
                member.patient = patient.name
            registered.append(member.full_name)
        except Exception as e:
            frappe.log_error(f"Error inserting patient for {member.full_name}: {str(e)}", "Membership Error")
            skipped.append({"name": member.full_name, "reason": str(e)})

    doc.save()

    return {
        "registered": registered,
        "skipped": skipped,
        "total_registered": len(registered),
        "total_skipped": len(skipped)
    }

@frappe.whitelist()
def register_single_member(docname, membername):
    doc = frappe.get_doc("Membership Registration", docname)
    member = next((m for m in doc.family_members if m.name == membername), None)

    if not member:
        frappe.throw("Member not found")

    if member.visited:
        return {"status": "already_registered", "name": member.full_name}

    # Validate required fields
    if not member.full_name or not member.mobile or not member.age:
        frappe.throw(f"Incomplete information for {member.full_name}")

    try:
        if member.patient:
            updating_patient = frappe.get_doc("Patient", member.patient)
            updating_patient.first_name = member.full_name
            updating_patient.mobile_no = member.mobile
            updating_patient.sex = member.sex
            updating_patient.p_age = member.age
            updating_patient.age_type = member.age_type
            updating_patient.percentage = doc.discount_level
            updating_patient.is_membership = "Membership"
            # updating_patient.customer_group = customer_group
            updating_patient.membership = doc.name
            updating_patient.member_card = doc.card_number
            updating_patient.member_company = doc.company
            updating_patient.member_contact = doc.contact_number
            updating_patient.member_head = doc.family_head_person
            updating_patient.save()
            member.visited = 1
            doc.save()
            return {"status": "ok", "name": member.full_name}

        else:
            patient = frappe.get_doc({
                "doctype": "Patient",
                "first_name": member.full_name,
                "mobile_no": member.mobile,
                "sex": member.sex,
                "p_age": member.age,
                "age_type": member.age_type,
                "percentage": doc.discount_level,
                "is_membership": "Membership",
                # "customer_group": customer_group,
                "membership": doc.name,
                "member_card": doc.card_number,
                "member_company": doc.company,
                "member_contact": doc.contact_number,
                "member_head": doc.family_head_person
            })
            patient.insert(ignore_permissions=True)
            member.visited = 1
            member.patient = patient.name
            doc.save()
            return {"status": "ok", "name": member.full_name}

    except Exception as e:
        frappe.log_error(f"Patient creation failed: {str(e)}", "Register Single")
        frappe.throw("Something went wrong while registering patient")

