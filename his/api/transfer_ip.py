import frappe

@frappe.whitelist()
def transfer_ip(self, service_unit, check_in, leave_from):
    self = frappe.get_doc("Inpatient Record" , self)
    if leave_from:
        patient_leave_service_unit(self, check_in, leave_from)
    if service_unit:
        transfer_patient(self, service_unit, check_in)


def transfer_patient(inpatient_record, service_unit, check_in):
	item_line = inpatient_record.append("inpatient_occupancies", {})
	item_line.service_unit = service_unit
	item_line.check_in = check_in

	inpatient_record.save(ignore_permissions=True)

	frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Occupied")


def patient_leave_service_unit(inpatient_record, check_out, leave_from):
	if inpatient_record.inpatient_occupancies:
		for inpatient_occupancy in inpatient_record.inpatient_occupancies:
			if inpatient_occupancy.left != 1 and inpatient_occupancy.service_unit == leave_from:
				inpatient_occupancy.left = True
				inpatient_occupancy.check_out = check_out
				frappe.db.set_value(
					"Healthcare Service Unit", inpatient_occupancy.service_unit, "occupancy_status", "Vacant"
				)
	inpatient_record.save(ignore_permissions=True)