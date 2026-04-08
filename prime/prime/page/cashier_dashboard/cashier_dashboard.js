frappe.pages["cashier-dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Cashier Dashboard",
		single_column: true,
	});

	page.add_action_icon("refresh", function () { load(); });

	page.body.html(`
		<div class="dash-page">
			<div class="dash-header">
				<div>
					<div class="dash-title">Cashier Dashboard</div>
					<div class="dash-subtitle">Today's billing and collection overview</div>
				</div>
				<div class="dash-refresh-info" id="cd-last-refresh"></div>
			</div>
			<div id="cd-kpis" class="dash-kpi-grid">
				<div class="dash-loading">Loading...</div>
			</div>
			<div class="dash-chart-row two-col">
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">Revenue by Hour</div>
					<div class="dash-chart-wrap" id="cd-chart-hourly"></div>
				</div>
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">Payment Mode Split</div>
					<div class="dash-chart-wrap" id="cd-chart-mode"></div>
				</div>
			</div>
			<div class="dash-chart-row full">
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">Recent Invoices</div>
					<table class="dash-table" id="cd-invoices">
						<thead><tr><th>Invoice</th><th>Patient</th><th>Amount</th><th>Status</th><th>Time</th></tr></thead>
						<tbody></tbody>
					</table>
				</div>
			</div>
		</div>
	`);

	function fmt(v) {
		return "SOS " + parseFloat(v || 0).toLocaleString("en-US", { minimumFractionDigits: 0 });
	}

	function load() {
		frappe.call({
			method: "prime.prime.page.cashier_dashboard.cashier_dashboard_api.get_stats",
			callback: function (r) {
				if (!r.message) return;
				var d = r.message;
				render_kpis(d.kpis);
				render_bar("cd-chart-hourly", d.hourly, ["#2563eb"]);
				render_pie("cd-chart-mode", d.mode_split, ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6"]);
				render_invoices(d.recent);
				document.getElementById("cd-last-refresh").textContent = "Updated " + frappe.datetime.now_time();
			}
		});
	}

	function render_kpis(k) {
		var cards = [
			{ icon: "🧾", color: "blue",   value: k.invoices_today,  label: "Invoices Today" },
			{ icon: "💰", color: "green",  value: fmt(k.revenue_today), label: "Total Billed Today" },
			{ icon: "✅", color: "teal",   value: fmt(k.collected_today), label: "Collected Today" },
			{ icon: "⏳", color: "amber",  value: k.pending_count,   label: "Pending Invoices" },
			{ icon: "💳", color: "red",    value: fmt(k.pending_amount), label: "Outstanding Amount" },
			{ icon: "📱", color: "purple", value: k.waafi_today,     label: "Waafi Payments" },
			{ icon: "💵", color: "indigo", value: k.cash_today,      label: "Cash Payments" },
			{ icon: "🎁", color: "pink",   value: k.free_today,      label: "Free / Exempted" },
		];
		document.getElementById("cd-kpis").innerHTML = cards.map(function (c) {
			return '<div class="dash-kpi-card">' +
				'<div class="dash-kpi-icon ' + c.color + '">' + c.icon + '</div>' +
				'<div><div class="dash-kpi-value">' + c.value + '</div><div class="dash-kpi-label">' + c.label + '</div></div>' +
				'</div>';
		}).join("");
	}

	function render_bar(id, data, colors) {
		var el = document.getElementById(id);
		if (!el || !data || !data.length) { el && (el.innerHTML = '<div class="dash-loading">No data yet</div>'); return; }
		el.innerHTML = "";
		new frappe.Chart(el, { type: "bar", data: { labels: data.map(function (r) { return r.label; }), datasets: [{ values: data.map(function (r) { return r.value || 0; }) }] }, height: 220, colors: colors });
	}

	function render_pie(id, data, colors) {
		var el = document.getElementById(id);
		if (!el || !data || !data.length) { el && (el.innerHTML = '<div class="dash-loading">No data yet</div>'); return; }
		el.innerHTML = "";
		new frappe.Chart(el, { type: "donut", data: { labels: data.map(function (r) { return r.label || "Unknown"; }), datasets: [{ values: data.map(function (r) { return r.value || 0; }) }] }, height: 220, colors: colors });
	}

	function render_invoices(rows) {
		var tbody = document.querySelector("#cd-invoices tbody");
		if (!tbody) return;
		tbody.innerHTML = (rows || []).map(function (r) {
			var badge = r.pay_status === "Paid"
				? '<span class="dash-badge green">Paid</span>'
				: '<span class="dash-badge amber">Unpaid</span>';
			return "<tr><td><a href='/app/sales-invoice/" + r.name + "' target='_blank'>" + r.name + "</a></td><td>" +
				(r.patient_name || "-") + "</td><td>" + fmt(r.grand_total) + "</td><td>" + badge + "</td><td>" + (r.time || "-") + "</td></tr>";
		}).join("") || '<tr><td colspan="5" style="text-align:center;color:#bbb">No invoices today</td></tr>';
	}

	load();
	setInterval(load, 30000);
};
