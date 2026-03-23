frappe.pages['pharmacy-dispense'].on_page_load = function (wrapper) {
    frappe.ui.make_app_page({ parent: wrapper, title: 'Pharmacy Dispense', single_column: true });

    $(frappe.render_template('pharmacy_dispense', {})).appendTo($(wrapper).find('.page-content'));
    new PharmacyDispense(wrapper);
};

var PharmacyDispense = function(wrapper) {
    this.wrapper = wrapper;
    this.bindEvents();
    setTimeout(function() { $('#phd-input').focus(); }, 300);
};

PharmacyDispense.prototype.bindEvents = function() {
    var self = this;
    $('#phd-lookup-btn').on('click', function() { self.lookup(); });
    $('#phd-input').on('keydown', function(e) {
        if (e.key === 'Enter') self.lookup();
    });
};

PharmacyDispense.prototype.lookup = function() {
    var raw = ($('#phd-input').val() || '').trim();
    if (!raw) {
        frappe.show_alert({ message: 'Please enter or scan an invoice ID', indicator: 'orange' });
        return;
    }

    var invoice = raw;
    try {
        var url = new URL(raw);
        invoice = url.searchParams.get('invoice') || url.searchParams.get('ref') || raw;
    } catch(e) { /* not a URL */ }

    var self = this;
    frappe.call({
        method: 'prime.api.queue_display_api.get_invoice_for_dispensing',
        args: { invoice_name: invoice },
        freeze: true,
        freeze_message: 'Looking up invoice...',
        callback: function(r) {
            if (!r.message) return;
            var data = r.message;
            if (!data.found) {
                self.showError(data.error || ('Invoice not found: ' + invoice));
            } else if (!data.paid) {
                self.showUnpaid(data);
            } else {
                self.showInvoice(data);
            }
        }
    });
};

PharmacyDispense.prototype.showError = function(msg) {
    var html = '<div class="phd-result-title">Invoice Not Found</div>'
        + '<p style="color:#555">' + frappe.utils.escape_html(msg) + '</p>';
    $('#phd-result').removeClass('success warning').addClass('error').html(html).show();
};

PharmacyDispense.prototype.showUnpaid = function(data) {
    var html = '<div class="phd-result-title">Invoice Not Paid</div>'
        + '<div class="phd-patient">Patient: ' + frappe.utils.escape_html(data.patient) + '</div>'
        + '<p style="color:#555">This invoice has not been paid yet. Medicines cannot be dispensed.</p>';
    $('#phd-result').removeClass('success error').addClass('warning').html(html).show();
};

PharmacyDispense.prototype.showInvoice = function(data) {
    var rows = '';
    for (var i = 0; i < (data.items || []).length; i++) {
        var item = data.items[i];
        rows += '<tr>'
            + '<td>' + frappe.utils.escape_html(item.item_name || item.item_code) + '<\/td>'
            + '<td>' + frappe.utils.escape_html(String(item.qty)) + '<\/td>'
            + '<td>' + frappe.utils.escape_html(item.description || '') + '<\/td>'
            + '<\/tr>';
    }

    var dispensedBadge = data.already_dispensed
        ? '<div class="phd-dispensed-badge">Already Dispensed</div>' : '';

    var dispenseBtn = !data.already_dispensed
        ? '<button class="btn btn-success phd-dispense-btn" id="phd-dispense-btn">Dispense Medicines<\/button>' : '';

    var html = '<div class="phd-result-title">Invoice: ' + frappe.utils.escape_html(data.invoice) + '<\/div>'
        + '<div class="phd-patient">Patient: ' + frappe.utils.escape_html(data.patient) + '<\/div>'
        + dispensedBadge
        + '<table class="phd-items-table">'
        + '<thead><tr><th>Medicine<\/th><th>Qty<\/th><th>Notes<\/th><\/tr><\/thead>'
        + '<tbody>' + rows + '<\/tbody>'
        + '<\/table>'
        + '<div class="phd-action-row">' + dispenseBtn + '<\/div>';

    $('#phd-result').removeClass('warning error').addClass('success').html(html).show();

    if (!data.already_dispensed) {
        var invoice = data.invoice;
        var self = this;
        $('#phd-dispense-btn').on('click', function() {
            self.dispense(invoice);
        });
    }
};

PharmacyDispense.prototype.dispense = function(invoice) {
    frappe.call({
        method: 'prime.api.queue_display_api.mark_invoice_dispensed',
        args: { invoice_name: invoice },
        freeze: true,
        freeze_message: 'Marking as dispensed...',
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({ message: 'Medicines dispensed successfully', indicator: 'green' });
                $('#phd-dispense-btn').prop('disabled', true).text('Dispensed');
                $('#phd-result').prepend('<div class="phd-dispensed-badge">Dispensed<\/div>');
            }
        }
    });
};
