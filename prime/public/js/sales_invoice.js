function fix_primary_btn_color(frm) {
	// Frappe desk CSS has color:#000 !important on btn-primary.
	// Only inline style with !important can override it.
	setTimeout(function() {
		var btn = frm.page.btn_primary[0];
		if (btn) btn.style.setProperty('color', '#ffffff', 'important');
	}, 500);
}

function reorder_si_fields(frm) {
	var fd = frm.fields_dict;
	var $posting_time = fd.posting_time    && fd.posting_time.$wrapper;
	var $employee     = fd.employee        && fd.employee.$wrapper;
	var $debtor       = fd.debtor          && fd.debtor.$wrapper;
	var $service_unit = fd.service_unit    && fd.service_unit.$wrapper;
	if (!$posting_time || !$posting_time.length) return;
	if ($employee && $employee.length) $posting_time.after($employee);
	if ($debtor && $debtor.length) {
		var $anchor = ($employee && $employee.length) ? $employee : $posting_time;
		$anchor.after($debtor);
	}
	if ($service_unit && $service_unit.length && $debtor && $debtor.length) {
		$debtor.after($service_unit);
	}
}

function setup_inline_payments(frm) {
	var payments_field = frm.fields_dict.payments;
	var is_pos_field = frm.fields_dict.is_pos;
	if (!payments_field || !is_pos_field) return;

	var $payments = payments_field.$wrapper;
	var $is_pos = is_pos_field.$wrapper;

	// Move payments DOM element right after is_pos if not already there
	if (!$is_pos.next().is($payments)) {
		$is_pos.after($payments);
	}

	// Always show the payments table regardless of is_pos
	$payments.show();
	payments_field.grid.refresh();
}

frappe.ui.form.on('Sales Invoice', {
  refresh(frm) {
		frm.page.wrapper.addClass('si-modern');
		reorder_si_fields(frm);
		setup_inline_payments(frm);
		fix_primary_btn_color(frm);

		if (frm.doc.docstatus !== 0 || frm.doc.workflow_state != "Approved") return;

		const editable_fields = ['is_pos', 'payments'];
		frm.fields
			.forEach(field => {
				if (editable_fields.includes(field.df.fieldname)) return;
				frm.set_df_property(field.df.fieldname, "read_only", 1);
			});
	},
  is_pos(frm) {
		setup_inline_payments(frm);
	},
    on_submit: function(frm) {
       
           //  let url= `${frappe.urllib.get_base_url()}/printview?doctype=Sales Invoice&name=${frm.doc.name}&trigger_print=1&settings=%7B%7D&_lang=en`;
             let url= `${frappe.urllib.get_base_url()}/printview?doctype=Sales Invoice&name=${frm.doc.name}&trigger_print=1&settings=%7B%7D&_lang=en`;
             window.open(url, '_blank');
        },
        onload(frm) {
          if (frm.is_new() && frm.doc.patient) {
      // 			frm.trigger('toggle_payment_fields');
            frappe.call({
              method: 'frappe.client.get',
              args: {
                doctype: 'Patient',
                name: frm.doc.patient
              },
              callback: function(data) {
                  
                
                      //   alert(data.message.is_insurance)
                          if (data.message.is_insurance){

                                            let d = new frappe.ui.Dialog({

                              title: `This patient in insurance <strong>${frm.doc.patient}</strong> is in insurance <strong>${data.message.ref_insturance} </strong> do you want to Charge Patient or insurance

                                <br>

                              `,
                              fields: [
                              {
                               label: 'Insurance',
                               fieldname: 'btn',
                               fieldtype: 'HTML',
                               options: `<button type="button" class="btn btn-success" style="background-color:green" onclick='$(".modal-dialog").hide()'>Patient</button>
                                        <button type="button" class="btn btn-danger" onclick='frappe.model.set_value("${frm.doctype}", "${frm.docname}", "is_insurance", 1); $(".modal-dialog").hide()'>insurance</button>`,
                               
                               }]

                                
                                
                          });

                          d.show();
                              // frappe.warn('This patient in insurance ',
                              //         '<strong>'+frm.doc.patient+ '</strong>'+ ' is in insurance <strong>'+ data.message.ref_insturance+ '</strong>'+ ' do you want to Charge Patient or insurance',
                              //         () => {
                              //             frappe.model.set_value(frm.doctype, frm.docname, 'is_insurance', 1);
                              //             frappe.model.set_value(frm.doctype, frm.docname, 'insurance', data.message.ref_insturance);
                              //             frappe.model.set_value(frm.doctype, frm.docname, 'insurance_id', data.message.insurance_number);

                              //             // action to perform if Continue is selected
                              //         },
                              //         'insurance',
                              //         true // Sets dialog as minimizable
                              //     )
                              
                          }
              }
            });
          }
        },
        discount_amount:function(frm){
          setTimeout(() => {
            // alert(percentage(frm.doc.discount_amount , frm.doc.base_total))
            // if(!additional_discount_percentage){
              frm.set_value("percentage" , percentage(frm.doc.discount_amount , frm.doc.base_total))

            // }
           

            
          }, 100);
       
        },
        additional_discount_percentage:function(frm){
          frm.set_value("percentage" , frm.doc.additional_discount_percentage)


        }
        
         
        
    })


frappe.ui.form.on('Sales Invoice Item', {
      refresh(frm) {
        // your code here
      },
      
      //     item_code: function(frm ,  cdt , cdn){
      //     let row = locals[cdt][cdn]
      //    // console.log(row)
      //    frappe.db.get_value("Retail Setup" , "Retail Setup" , "allow_retail").then( r =>{
      //        if (r.message.allow_retail) {
      //         frappe.db.get_value("Item" , row.item_code , "strep").then( item_st =>{
      //         console.log(r)
      //         if (frappe.user_roles.includes('Tafaariiq') && item_st.message.strep) {
      //             setTimeout(() => {
      //                 frappe.model.set_value(cdt, cdn, "uom", "Strep");
      //                 console.log("Delayed for 1 second.");
      //               }, 1000);
      //        //alert("we need this")
             
      //        //row.uom = "Strep";
      //        //frm.refresh_field("items")
             
      //    }
      //     })
      //        }
      //    })
         
      // }
      
    })

    function percentage(partialValue, totalValue) {
      // alert( (100 * partialValue) / totalValue)
      return (100 * partialValue) / totalValue;
   } 