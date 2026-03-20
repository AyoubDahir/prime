frappe.pages['qr-checkin'].on_page_load = function (wrapper) {
    frappe.ui.make_app_page({ parent: wrapper, title: 'QR Check-in', single_column: true });

    frappe.require(['/assets/prime/css/qr_checkin.css'], () => {
        $(frappe.render_template('qr_checkin', {})).appendTo($(wrapper).find('.page-content'));
        new QrCheckin(wrapper);
    });
};

class QrCheckin {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.bindEvents();
        // Auto-focus scan input so USB scanner works immediately
        setTimeout(() => $('#qrc-input').focus(), 300);
    }

    bindEvents() {
        // Lookup on button click
        $('#qrc-scan-btn').on('click', () => this.lookup());

        // Lookup on Enter key (USB scanners send Enter after barcode)
        $('#qrc-input').on('keydown', (e) => {
            if (e.key === 'Enter') this.lookup();
        });

        // Manual Que creation — opens existing New Que form
        $('#qrc-manual-btn').on('click', () => frappe.new_doc('Que'));
    }

    lookup() {
        const raw = ($('#qrc-input').val() || '').trim();
        if (!raw) {
            frappe.show_alert({ message: 'Please enter or scan a reference', indicator: 'orange' });
            return;
        }

        // Strip any URL prefix — support scanning a full URL or bare reference
        // e.g. https://alihsans.com/...?ref=APPT-xxx  or  just  APPT-xxx
        let ref = raw;
        try {
            const url = new URL(raw);
            ref = url.searchParams.get('ref') || url.searchParams.get('reference_id') || raw;
        } catch (_) { /* not a URL, use as-is */ }

        frappe.call({
            method: 'prime.api.queue_display_api.checkin_by_qr',
            args: { reference_id: ref },
            freeze: true,
            freeze_message: 'Looking up...',
            callback: (r) => {
                if (!r.message) return;
                const data = r.message;
                if (data.found) {
                    this.showFound(data);
                } else {
                    this.showNotFound(ref);
                }
                $('#qrc-input').val('').focus();
            }
        });
    }

    showFound(data) {
        const aheadText = data.patients_ahead === 0
            ? '<span style="color:#2e7d32;font-weight:700">Next in line!</span>'
            : `${data.patients_ahead} patient(s) ahead`;

        const statusBadge = data.que_steps === 'Called'
            ? '<span style="color:#1565c0;font-weight:700">🔔 Being Called Now</span>'
            : data.que_steps === 'Waiting'
            ? '<span style="color:#555">Waiting</span>'
            : `<span>${frappe.utils.escape_html(data.que_steps)}</span>`;

        const html = `
        <div class="qrc-result-title">✅ Pre-booked Patient Found</div>
        <div class="qrc-info-grid">
          <div class="qrc-info-item">
            <span class="qrc-info-label">Token Number</span>
            <span class="qrc-token-big">#${data.token_no}</span>
          </div>
          <div class="qrc-info-item">
            <span class="qrc-info-label">Status</span>
            <span class="qrc-info-value">${statusBadge}</span>
          </div>
          <div class="qrc-info-item">
            <span class="qrc-info-label">Patient</span>
            <span class="qrc-info-value">${frappe.utils.escape_html(data.patient_name)}</span>
          </div>
          <div class="qrc-info-item">
            <span class="qrc-info-label">Doctor</span>
            <span class="qrc-info-value">${frappe.utils.escape_html(data.practitioner_name)}</span>
          </div>
          <div class="qrc-info-item">
            <span class="qrc-info-label">Department</span>
            <span class="qrc-info-value">${frappe.utils.escape_html(data.department || '—')}</span>
          </div>
          <div class="qrc-info-item">
            <span class="qrc-info-label">Patients Ahead</span>
            <span class="qrc-info-value">${aheadText}</span>
          </div>
        </div>
        <div class="qrc-action-row">
          <button class="btn btn-default btn-sm" onclick="frappe.set_route('Form','Que','${frappe.utils.escape_html(data.que)}')">
            Open Queue Record
          </button>
          <button class="btn btn-default btn-sm" onclick="window.print()">
            🖨 Print Token
          </button>
        </div>`;

        $('#qrc-result').removeClass('not-found').addClass('found').html(html).show();
        frappe.utils.play_sound('submit');
    }

    showNotFound(ref) {
        const html = `
        <div class="qrc-result-title">⚠️ No pre-booked queue found for: <code>${frappe.utils.escape_html(ref)}</code></div>
        <p style="color:#555;margin-bottom:14px">
          The patient may not have pre-booked via the mobile app, or the reference has already been used.
          Please create a queue manually below.
        </p>
        <button class="btn btn-primary btn-sm" onclick="frappe.new_doc('Que')">
          ➕ Create New Queue Manually
        </button>`;

        $('#qrc-result').removeClass('found').addClass('not-found').html(html).show();
    }
}
