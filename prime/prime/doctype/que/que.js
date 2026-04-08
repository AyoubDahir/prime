// Copyright (c) 2023, Rasiin Tech and contributors
frappe.provide('erpnext.queries');

// ── Modern CSS ─────────────────────────────────────────────────────────────────
function inject_que_styles() {
    if (document.getElementById('que-modern-css')) return;
    const style = document.createElement('style');
    style.id = 'que-modern-css';
    style.textContent = `
/* ── Que Modern Form ─────────────────────────────────────────────────── */

/* Wrapper background */
.que-modern .layout-main-section-wrapper {
    background: transparent;
}
.que-modern .layout-main-section {
    background: #f0f4f8;
    border-radius: 16px;
    padding: 20px;
    border: none;
    box-shadow: 0 2px 20px rgba(0,0,0,0.07);
}

/* ── Patient Banner ──────────────────────────────────────────────────── */
.que-patient-banner {
    background: linear-gradient(135deg, #0f2044 0%, #1d4ed8 100%);
    border-radius: 12px;
    padding: 20px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(29,78,216,0.30);
}
.que-patient-banner.empty-state {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.que-patient-banner .qb-left { flex: 1; min-width: 0; }
.que-patient-banner .qb-name {
    font-size: 22px;
    font-weight: 800;
    color: white;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.que-patient-banner .qb-name.placeholder {
    font-size: 16px;
    font-weight: 500;
    opacity: 0.5;
}
.que-patient-banner .qb-meta {
    font-size: 12px;
    color: rgba(255,255,255,0.65);
    margin-top: 5px;
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
}
.que-patient-banner .qb-meta span {
    display: flex;
    align-items: center;
    gap: 4px;
}
.que-patient-banner .qb-status-badge {
    display: inline-block;
    margin-top: 8px;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    background: rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.9);
}
.que-patient-banner .qb-status-badge.Open   { background: rgba(251,191,36,0.25); color: #fcd34d; }
.que-patient-banner .qb-status-badge.Closed { background: rgba(52,211,153,0.25); color: #6ee7b7; }
.que-patient-banner .qb-status-badge.Canceled { background: rgba(248,113,113,0.25); color: #fca5a5; }
.que-patient-banner .qb-right {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    margin-left: 20px;
}
.que-patient-banner .qb-token-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: rgba(255,255,255,0.55);
}
.que-patient-banner .qb-token {
    background: white;
    color: #0f2044;
    border-radius: 14px;
    padding: 10px 24px;
    font-size: 34px;
    font-weight: 900;
    min-width: 90px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    line-height: 1;
    letter-spacing: 2px;
}
.que-patient-banner .qb-token.empty {
    font-size: 18px;
    color: #94a3b8;
    font-weight: 500;
    letter-spacing: 0;
}

/* ── Sections ────────────────────────────────────────────────────────── */
.que-modern .form-section.card-section {
    background: white !important;
    border-radius: 12px !important;
    border: 1.5px solid #e2e8f0 !important;
    margin: 0 0 14px 0 !important;
    overflow: hidden;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04) !important;
}
.que-modern .form-section.card-section > .section-head {
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    padding: 10px 18px !important;
}
.que-modern .form-section.card-section > .section-head .label {
    font-size: 10px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: #2563eb !important;
    margin: 0 !important;
}
.que-modern .section-body {
    padding: 16px 18px !important;
}

/* ── Field labels ─────────────────────────────────────────────────────── */
.que-modern .frappe-control .control-label {
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    color: #94a3b8 !important;
    margin-bottom: 5px !important;
}
.que-modern .frappe-control .reqd-star { color: #ef4444 !important; }

/* ── All inputs ───────────────────────────────────────────────────────── */
.que-modern .frappe-control input.input-with-feedback,
.que-modern .frappe-control select.input-with-feedback,
.que-modern .frappe-control textarea.input-with-feedback {
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 9px 12px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #1e293b !important;
    background: #fafbfc !important;
    height: auto !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
    box-shadow: none !important;
}
.que-modern .frappe-control input.input-with-feedback:focus,
.que-modern .frappe-control select.input-with-feedback:focus,
.que-modern .frappe-control textarea.input-with-feedback:focus {
    border-color: #2563eb !important;
    background: white !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.10) !important;
    outline: none !important;
}
/* read-only */
.que-modern .frappe-control[data-fieldname="patient_name"] input,
.que-modern .frappe-control[data-fieldname="gender"] input,
.que-modern .frappe-control[data-fieldname="age"] input,
.que-modern .frappe-control[data-fieldname="department"] .input-with-feedback,
.que-modern .frappe-control[data-fieldname="referring_practitioner"] input,
.que-modern .frappe-control[data-fieldname="date"] input,
.que-modern .frappe-control[data-fieldname="doctor_amount"] .input-with-feedback {
    background: #f1f5f9 !important;
    color: #64748b !important;
    border-color: #e2e8f0 !important;
    cursor: not-allowed;
}

/* Patient field — prominent */
.que-modern .frappe-control[data-fieldname="patient"] input,
.que-modern .frappe-control[data-fieldname="practitioner"] input {
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    background: white !important;
    border-color: #cbd5e1 !important;
}
.que-modern .frappe-control[data-fieldname="patient"] input:focus,
.que-modern .frappe-control[data-fieldname="practitioner"] input:focus {
    border-color: #2563eb !important;
}

/* Token No — hero display */
.que-modern .frappe-control[data-fieldname="token_no"] input {
    font-size: 40px !important;
    font-weight: 900 !important;
    text-align: center !important;
    color: #1e3a8a !important;
    border: 2.5px solid #3b82f6 !important;
    border-radius: 14px !important;
    background: linear-gradient(135deg, #eff6ff, #dbeafe) !important;
    padding: 18px 12px !important;
    letter-spacing: 4px;
    height: auto !important;
}

/* Paid amount — success green */
.que-modern .frappe-control[data-fieldname="paid_amount"] input {
    border-color: #10b981 !important;
    background: #f0fdf4 !important;
    color: #065f46 !important;
    font-weight: 700 !important;
    font-size: 16px !important;
}

/* Discount — amber */
.que-modern .frappe-control[data-fieldname="discount"] input {
    border-color: #f59e0b !important;
    background: #fffbeb !important;
    color: #92400e !important;
    font-weight: 600 !important;
}

/* Mode of payment — violet */
.que-modern .frappe-control[data-fieldname="mode_of_payment"] input {
    border-color: #8b5cf6 !important;
    background: #faf5ff !important;
}

/* Reference / Remark */
.que-modern .frappe-control[data-fieldname="reference"] input {
    border-color: #94a3b8 !important;
}

/* ── Checkboxes ───────────────────────────────────────────────────────── */
.que-modern .frappe-control[data-fieldtype="Check"] {
    background: #f8fafc;
    border: 1.5px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px !important;
    margin-bottom: 8px !important;
    transition: border-color 0.15s;
}
.que-modern .frappe-control[data-fieldtype="Check"]:hover {
    border-color: #93c5fd;
    background: #eff6ff;
}
.que-modern .frappe-control[data-fieldtype="Check"] .label-area {
    font-size: 13px !important;
    font-weight: 600;
    color: #374151 !important;
}
.que-modern .frappe-control[data-fieldname="is_free"] { border-color: #6ee7b7 !important; }
.que-modern .frappe-control[data-fieldname="is_free"]:hover { background: #f0fdf4 !important; }
.que-modern .frappe-control[data-fieldname="bill_to_other_customer"] { border-color: #c4b5fd !important; }
.que-modern .frappe-control[data-fieldname="bill_to_other_customer"]:hover { background: #faf5ff !important; }

/* ── Custom buttons ───────────────────────────────────────────────────── */
.que-modern .page-actions .btn-primary {
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 8px 20px !important;
    font-size: 13px !important;
    letter-spacing: 0.3px;
}
.que-modern .custom-btn-group .btn {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 7px 16px !important;
    border: 1.5px solid #e2e8f0 !important;
    transition: all 0.2s ease;
}
.que-modern .custom-btn-group .btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.12) !important;
}
.que-modern .custom-btn-group .btn[data-label="Cancel"],
.que-modern .custom-btn-group .btn[data-label="Cancel Que"] {
    border-color: #fca5a5 !important;
    color: #dc2626 !important;
    background: #fff5f5 !important;
}
.que-modern .custom-btn-group .btn[data-label="Cancel"]:hover,
.que-modern .custom-btn-group .btn[data-label="Cancel Que"]:hover {
    background: #fee2e2 !important;
}

/* Scan button */
.que-modern .custom-btn-group .btn[data-label*="Scan"] {
    border-color: #93c5fd !important;
    color: #1d4ed8 !important;
    background: #eff6ff !important;
}

/* ── Status indicator dot ─────────────────────────────────────────────── */
.que-modern .indicator-pill {
    border-radius: 20px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    padding: 3px 10px !important;
}

/* ── Scrollbar ────────────────────────────────────────────────────────── */
.que-modern ::-webkit-scrollbar { width: 5px; height: 5px; }
.que-modern ::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 3px; }
.que-modern ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
.que-modern ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    `;
    document.head.appendChild(style);
}

// ── Patient Banner ─────────────────────────────────────────────────────────────
function render_patient_banner(frm) {
    let $wrapper = $(frm.wrapper);
    let $mainSection = $wrapper.find('.layout-main-section');
    if (!$mainSection.length) return;

    let $banner = $mainSection.find('.que-patient-banner');
    if (!$banner.length) {
        $banner = $('<div class="que-patient-banner"></div>');
        $mainSection.prepend($banner);
    }

    let name = frm.doc.patient_name || frm.doc.patient || '';
    let token = frm.doc.token_no || '';
    let status = frm.doc.status || 'Open';
    let mobile = frm.doc.mobile || '';
    let gender = frm.doc.gender || '';
    let age = frm.doc.age || '';
    let dept = frm.doc.department || '';

    if (!name) {
        $banner.addClass('empty-state').html(`
            <div class="qb-left">
                <div class="qb-name placeholder">Select a patient to begin registration</div>
                <div class="qb-meta"><span>🏥 New Queue Entry</span></div>
            </div>
            <div class="qb-right">
                <div class="qb-token-label">Token</div>
                <div class="qb-token empty">—</div>
            </div>
        `);
    } else {
        $banner.removeClass('empty-state');
        let metaParts = [];
        if (mobile) metaParts.push(`<span>📱 ${mobile}</span>`);
        if (gender) metaParts.push(`<span>⚧ ${gender}</span>`);
        if (age)    metaParts.push(`<span>🎂 ${age}</span>`);
        if (dept)   metaParts.push(`<span>🏥 ${dept}</span>`);

        $banner.html(`
            <div class="qb-left">
                <div class="qb-name">${frappe.utils.escape_html(name)}</div>
                <div class="qb-meta">${metaParts.join('') || '<span>Patient loaded</span>'}</div>
                <span class="qb-status-badge ${status}">${status}</span>
            </div>
            <div class="qb-right">
                <div class="qb-token-label">Token No.</div>
                <div class="qb-token ${token ? '' : 'empty'}">${token || '—'}</div>
            </div>
        `);
    }
}

// ── Main Form Events ──────────────────────────────────────────────────────────
frappe.ui.form.on('Que', {

    is_free: function(frm) {
        frm.set_value("paid_amount", 0);
    },

    discount: function(frm) {
        frm.set_value("paid_amount", (frm.doc.doctor_amount - frm.doc.discount));
    },

    refresh: function(frm) {
        // ── Modern styling ──────────────────────────────────────────────────
        inject_que_styles();
        $(frm.wrapper).addClass('que-modern');
        render_patient_banner(frm);

        // ── QR Patient Card Scan ────────────────────────────────────────────
        if (frm.is_new() && (
            frappe.user_roles.includes('Cashier') ||
            frappe.user_roles.includes('Main Cashier') ||
            frappe.user_roles.includes('System Manager')
        )) {
            frm.add_custom_button(__('📷 Scan Patient Card'), function () {
                let d = new frappe.ui.Dialog({
                    title: 'Scan Patient QR Card',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            options: `<p style="color:#555;margin-bottom:8px">
                                Place cursor in the box below and scan the patient's QR card with a scanner,
                                or type the Patient ID manually.
                            </p>`
                        },
                        {
                            label: 'Patient ID / QR Code',
                            fieldname: 'scanned_patient',
                            fieldtype: 'Data',
                            reqd: 1,
                            description: 'USB scanner will auto-submit after reading'
                        }
                    ],
                    primary_action_label: 'Load Patient',
                    primary_action(values) {
                        const pid = (values.scanned_patient || '').trim();
                        if (!pid) return;
                        frappe.db.exists('Patient', pid).then(exists => {
                            if (exists) {
                                frm.set_value('patient', pid);
                                d.hide();
                                frappe.show_alert({ message: `Patient ${pid} loaded`, indicator: 'green' });
                            } else {
                                frappe.show_alert({ message: `Patient "${pid}" not found`, indicator: 'red' });
                            }
                        });
                    }
                });
                d.show();
                setTimeout(() => {
                    d.fields_dict.scanned_patient.$input.on('keydown', function(e) {
                        if (e.key === 'Enter') { d.get_primary_btn().trigger('click'); }
                    }).focus();
                }, 200);
            });
        }

        // ── Practitioner query ──────────────────────────────────────────────
        frm.set_query('practitioner', function() {
            return { query: "prime.api.dp_drug_pr_link_query.my_custom_query" };
        });

        if (frm.is_new()) {
            frm.set_value("status", "Open");
        }

        if (frappe.user_roles.includes('Doctor') && !frappe.user_roles.includes('Cashier')) {
            frm.set_df_property('paid_amount', 'hidden', 1);
            frm.set_df_property('doctor_amount', 'hidden', 1);
            frm.set_df_property('mode_of_payment', 'hidden', 1);
            frm.set_df_property('reference', 'hidden', 1);
            frm.set_df_property('debtor', 'hidden', 1);
            frm.set_df_property('bill_to', 'hidden', 1);
            if (frm.doc.status === "Open" || frm.doc.status === "Closed") {
                frm.add_custom_button(__("Open Encounter"), function() {
                    frappe.new_doc("Patient Encounter", {
                        "que": frm.doc.name,
                        "patient": frm.doc.patient,
                        "practitioner": frm.doc.practitioner
                    });
                });
            }
        }

        if (!frm.is_new()) {
            if (frm.doc.status === "Open") {
                if (frappe.user_roles.includes('Main Cashier') || frappe.user_roles.includes('Cashier')) {
                    frm.add_custom_button(__("Cancel"), function() {
                        frappe.confirm('Are you sure you want to Cancel?', () => {
                            frappe.call({
                                method: "prime.api.make_cancel_ques.make_cancel",
                                args: {
                                    "que": frm.doc.name,
                                    "sales_invoice": frm.doc.sales_invoice,
                                    "sakes_order": frm.doc.sales_order,
                                    "fee": frm.doc.fee_validity,
                                },
                                callback: function(r) {
                                    console.log(r);
                                    frappe.utils.play_sound("submit");
                                    frappe.show_alert({
                                        message: __('Patient Que Canceled Successfully'),
                                        indicator: 'red',
                                    }, 5);
                                    frm.reload_doc();
                                }
                            });
                        }, () => {});
                    });
                }
            }
        }
    },

    practitioner: function(frm) {
        setTimeout(() => {
            if (!frm.doc.is_insurance && !frm.doc.is_free) {
                frm.set_value("paid_amount", frm.doc.doctor_amount);
            }
            render_patient_banner(frm);
        }, 100);
    },

    patient: function(frm) {
        if (frm.doc.patient) {
            frm.trigger('toggle_payment_fields');
            frappe.call({
                method: 'frappe.client.get',
                args: { doctype: 'Patient', name: frm.doc.patient },
                callback: function(data) {
                    let age = null;
                    if (data.message.dob) {
                        age = calculate_age(data.message.dob);
                    }
                    frappe.model.set_value(frm.doctype, frm.docname, 'age', age);

                    if (data.message.is_insurance) {
                        let d = new frappe.ui.Dialog({
                            title: `Insurance Patient: ${frm.doc.patient}`,
                            fields: [{
                                label: 'Insurance',
                                fieldname: 'btn',
                                fieldtype: 'HTML',
                                options: `
                                    <p style="margin-bottom:14px;color:#374151;">
                                        This patient is covered by <strong>${data.message.ref_insturance}</strong>.
                                        How should this visit be billed?
                                    </p>
                                    <div style="display:flex;gap:10px;">
                                        <button type="button" class="btn btn-success" style="flex:1;border-radius:8px;font-weight:600"
                                            onclick='$(".modal-dialog").hide()'>
                                            👤 Charge Patient
                                        </button>
                                        <button type="button" class="btn btn-primary" style="flex:1;border-radius:8px;font-weight:600"
                                            onclick='frappe.model.set_value("${frm.doctype}", "${frm.docname}", "is_insurance", 1); $(".modal-dialog").hide()'>
                                            🏥 Charge Insurance
                                        </button>
                                    </div>`
                            }]
                        });
                        d.show();
                    }

                    if (data.message.is_employee) {
                        frm.set_value("is_employee", 1);
                        frm.set_value("employee", data.message.linked_employee);
                    }

                    // Update banner after patient data loads
                    setTimeout(() => render_patient_banner(frm), 150);
                }
            });
        }
    },

    after_save: function(frm) {
        render_patient_banner(frm);
    }
});

let calculate_age = function(birth) {
    let ageMS = Date.parse(Date()) - Date.parse(birth);
    let age = new Date();
    age.setTime(ageMS);
    let years = age.getFullYear() - 1970;
    return `${years} ${__('Years(s)')} ${age.getMonth()} ${__('Month(s)')} ${age.getDate()} ${__('Day(s)')}`;
};
