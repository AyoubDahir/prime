frappe.pages['queue-display'].on_page_load = function (wrapper) {
    frappe.ui.make_app_page({ parent: wrapper, title: 'Queue Display', single_column: true });
    // Hide Frappe chrome for full-screen TV mode
    $('.page-head').hide();
    new QueueDisplay(wrapper);
};

class QueueDisplay {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.prevTokens = {};   // track previous tokens to animate changes

        frappe.require(['/assets/prime/css/queue_display.css'], () => {
            $(frappe.render_template('queue_display', {})).appendTo($(wrapper).find('.page-content'));
            this.startClock();
            this.refresh();
            this.subscribeRealtime();
            // Full refresh every 30 seconds as safety net
            setInterval(() => this.refresh(), 30000);
        });
    }

    startClock() {
        const tick = () => {
            const now = new Date();
            $('#qd-time').text(now.toLocaleTimeString('en-GB'));
            $('#qd-date').text(now.toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }));
        };
        tick();
        setInterval(tick, 1000);
    }

    subscribeRealtime() {
        frappe.realtime.on('que_update', () => this.refresh());
    }

    refresh() {
        frappe.call({
            method: 'prime.api.queue_display_api.get_live_queue',
            callback: (r) => {
                if (r.message !== undefined) {
                    this.render(r.message);
                }
            }
        });
    }

    render(doctors) {
        const body = $('#qd-body');
        if (!doctors || doctors.length === 0) {
            body.html('<div class="qd-loading">No open queue today</div>');
            return;
        }

        let html = '';
        doctors.forEach(doc => {
            const currentToken = doc.current_token;
            const nextToken = doc.next_token;
            const prev = this.prevTokens[doc.practitioner];
            const changed = prev !== undefined && prev !== currentToken;

            const nowHtml = currentToken
                ? `<div class="qd-now-token${changed ? ' pulse' : ''}" id="tok-${doc.practitioner.replace(/\W/g,'_')}">${currentToken}</div>`
                : `<div class="qd-now-empty">—</div>`;

            html += `
            <div class="qd-card">
              <div class="qd-card-header">
                <div class="qd-card-dept">${frappe.utils.escape_html(doc.department || 'OPD')}</div>
                <div class="qd-card-doctor">${frappe.utils.escape_html(doc.practitioner_name)}</div>
              </div>
              <div class="qd-card-body">
                <div class="qd-now-label">Now Serving</div>
                ${nowHtml}
                <hr class="qd-divider">
                <div class="qd-meta-row">
                  <div class="qd-meta-item">
                    <span class="qd-meta-label">Next</span>
                    <span class="qd-meta-value">${nextToken || '—'}</span>
                  </div>
                  <div class="qd-meta-item" style="text-align:right">
                    <span class="qd-meta-label">Waiting</span>
                    <span class="qd-meta-value waiting-count">${doc.waiting_count}</span>
                  </div>
                </div>
              </div>
            </div>`;

            this.prevTokens[doc.practitioner] = currentToken;
        });

        body.html(html);
    }
}
