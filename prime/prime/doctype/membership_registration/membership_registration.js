// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Membership Registration', {
    onload: function(frm) {
        // Store initial value on load
        frm._last_status = frm.doc.status;
    },

    after_save: function(frm) {
        if (!frm._last_status || frm._last_status === frm.doc.status) return;

        if (frm.doc.status === "Active") {
            frappe.show_alert({
                message: "Membership reactivated. Benefits restored.",
                indicator: "green"
            });
        } else if (frm.doc.status === "Inactive") {
            frappe.show_alert({
                message: "Membership deactivated. Members reset.",
                indicator: "orange"
            });
        }

        // Update the stored value
        frm._last_status = frm.doc.status;
    },
    register_all: function(frm) {
        frappe.confirm("Register all unvisited family members?", () => {
            frappe.call({
                method: "prime.prime.doctype.membership_registration.membership_registration.register_family_members",
                args: { docname: frm.doc.name },
                freeze: true,
                freeze_message: "Registering all members...",
                callback: function(r) {
                    if (r.message.length) {
                        frappe.msgprint(__('Registered: ') + r.message.join(", "));
                        frm.reload_doc();
                    } else {
                        frappe.show_alert("All members already registered!", 5);
                    }
                }
            });
        });
    }
});


frappe.ui.form.on('Family Members', {
	create_patient: function(frm, cdt, cdn) {
	    const row = locals[cdt][cdn];
	    frappe.confirm(`Register ${row.full_name} as Patient?`, () => {
	        frappe.call({
	            method: "prime.prime.doctype.membership_registration.membership_registration.register_single_member",
	            args: {
	                docname: frm.doc.name,
	                membername: row.name
	            },
	            freeze: true,
	            freeze_message: "Registering member...",
	            callback: function(r) {
	                if (r.message.status === "ok") {
	                    frappe.msgprint(__('Patient created for ') + r.message.name);
	                    frm.reload_doc();
	                } else {
	                    frappe.show_alert(r.message.name + " is already registered!", 5);
	                }
	            }
	        });
	    });
	}
});

