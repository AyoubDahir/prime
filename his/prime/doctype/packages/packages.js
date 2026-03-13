// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Packages', {
	refresh : function(frm){
		if (!frm.is_new()){
		frm.add_custom_button(__('Cash Sales'), function() {
		frappe.db.get_doc("Packages" , frm.doc.name).then(r => {
          frappe.model.open_mapped_doc({
			method: "prime.api.make_invoice.make_sales_invoice",
			source_name: `${r.services_so}`   // <-- key fix
		})
		 });
       });

	   frm.add_custom_button(__('Credit Sales'), function() {
		frappe.db.get_doc("Packages" , frm.doc.name).then(r => {
           frappe.model.open_mapped_doc({
			method: "prime.api.make_invoice.make_credit_invoice",
			source_name: `${r.services_so}`   // <-- key fix
		})
       });
	   })
	     frm.add_custom_button(__('Create Que'), function() {
		 frappe.new_doc("Que", { "patient": frm.doc.patient, "practitioner": frm.doc.practitioner, "is_free": true, "reference": "This is a Package", "paid_amount": 0})
	   })
		}
	},
	package: function(frm){
		if (frm.doc.package){
		  frappe.call({
			method: 'prime.prime.doctype.packages.packages.fetch_package_prescriptions',
			args: {
			parent_name: frm.doc.package 

			},
			callback: function(r) {
				console.log(r)
				frm.clear_table('package_prescription');
				frm.set_value('package_prescription',r.message);

			
			},
		  })
		setTimeout(function(){
			if(frm.doc.package_amount && frm.doc.doctor_number){
			frm.set_value("total", frm.doc.package_amount+frm.doc.doctor_number)
		}
		
		
		}, 100);
	}
	},
	after_save: function(frm){
		frm.set_df_property('patient',  'read_only',   1);
		frm.set_df_property('practitioner',  'read_only',   1);
		frm.set_df_property('package',  'read_only',   1);
		frm.set_df_property('date',  'read_only',   1);
		frm.set_df_property('paid_amount',  'read_only',   1);
	},

});

