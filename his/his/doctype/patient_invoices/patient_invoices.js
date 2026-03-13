frappe.ui.form.on('Patient Invoices', {
    print: function (frm) {
        if (frm.doc.docstatus != 1) {


            // Ensure the required fields are filled before fetching data
            if (!frm.doc.customer || !frm.doc.from_date || !frm.doc.to_date) {
                frappe.msgprint(__('Please enter Customer, From Date, and To Date.'));
                return;
            }

            // Convert the dates to ISO format to avoid any date format issues
            let from_date = moment(frm.doc.from_date).format('YYYY-MM-DD');
            let to_date = moment(frm.doc.to_date).format('YYYY-MM-DD');

            // Call the custom Python method to fetch invoices data
            frappe.call({
                method: 'prime.prime.doctype.patient_invoices.patient_invoices.get_invoices_data',  // Update to the correct app path
                args: {
                    company: 'Royal Hospital',  // Hardcode the company name
                    customer: frm.doc.customer,
                    from_date: from_date,
                    to_date: to_date,
                    ref_practitioner: frm.doc.ref_practitioner,
                },
                callback: function (response) {
                    console.log("Data from backend: ", response.message[1]);
                    frm.set_value("total_discount", response.message[1])

                    if (response.message && response.message[0].length > 0) {
                        let invoices = response.message[0];

                        // Clear the existing child table rows
                        frm.clear_table('pich');

                        // Loop through each invoice and add it to the child table
                        invoices.forEach(function (invoice) {
                            let child = frm.add_child('pich');
                            child.customer_name = invoice.customer_name;
                            child.item_code = invoice.item_code;
                            child.item_group = invoice.item_group;
                            child.invoice = invoice.invoice;
                            child.posting_date = invoice.posting_date;
                            child.stock_qty = invoice.stock_qty;
                            // child.discount = frappe.db.get_value("Sales Invoice",invoice.invoice, "discount_amount" )
                            child.rate = invoice.rate;
                            child.amount = invoice.amount;
                            child.ref_practitioner = invoice.ref_practitioner;
                        });

                        // Refresh the child table after adding new rows
                        frm.refresh_field('pich');
                    } else {
                        frappe.msgprint(__('No data found for the selected filters.'));
                    }
                }
            });
        }
    }
});
