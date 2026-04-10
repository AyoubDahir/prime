frappe.listview_settings['Sales Order'] = {
    
    
          button: {
        show: function(doc) {
            return true;
        },
        get_label: function() {
            return __('CASH');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.customer])
        },
        action: function(doc) {
            frappe.confirm(
                __('Create a draft Sales Invoice for {0}?', [doc.customer_name || doc.name]),
                function() {
                    frappe.call({
                        method: "prime.api.make_invoice.make_draft_invoice",
                        args: { so_name: doc.name },
                        freeze: true,
                        freeze_message: __('Creating invoice...'),
                        callback: function(r) {
                            if (r.message) {
                                frappe.set_route("Form", "Sales Invoice", r.message);
                            }
                        }
                    });
                }
            );
        },
        
    },
}
     
     
    
    
    