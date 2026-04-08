frappe.pages["accounting-dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Accounting Dashboard",
		single_column: true,
	});

	page.add_action_icon("refresh", function () { load(); });

	page.body.html(`
		<div class="dash-page">
			<div class="dash-header">
				<div>
					<div class="dash-title">Accounting Dashboard</div>
					<div class="dash-subtitle">Financial performance overview</div>
				</div>
				<div class="dash-refresh-info" id="ad-last-refresh"></div>
			</div>
			<div id="ad-kpis" class="dash-kpi-grid">
				<div class="dash-loading">Loading...</div>
			</div>
			<div class="dash-chart-row two-col">
				<div class="dash-chart-card">
					<div class="dash-chart-title">Last 6 Months</div>
					<div class="dash-chart-heading">Revenue vs Collected</div>
					<div class="dash-chart-wrap" id="ad-chart-monthly"></div>
				</div>
				<div class="dash-chart-card">
					<div class="dash-chart-title">This Month</div>
					<div class="dash-chart-heading">Insurance vs Direct Pay</div>
					<div class="dash-chart-wrap" id="ad-chart-insurance"></div>
				</div>
			</div>
			<div class="dash-chart-row two-col">
				<div class="dash-chart-card">
					<div class="dash-chart-title">This Month</div>
					<div class="dash-chart-heading">Payment Mode Distribution</div>
					<div class="dash-chart-wrap" id="ad-chart-mode"></div>
				</div>
				<div class="dash-chart-card">
					<div class="dash-chart-title">This Month</div>
					<div class="dash-chart-heading">Top Services by Revenue</div>
					<table class="dash-table" id="ad-services">
						<thead><tr><th>Service</th><th>Revenue</th><th>Qty</th></tr></thead>
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
			method: "prime.prime.page.accounting_dashboard.accounting_dashboard_api.get_stats",
			callback: function (r) {
				if (!r.message) return;
				var d = r.message;
				render_kpis(d.kpis);
				render_dual_bar("ad-chart-monthly", d.monthly);
				render_pie("ad-chart-insurance", d.insurance_split, ["#2563eb", "#10b981"]);
				render_pie("ad-chart-mode", d.mode_split, ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"]);
				render_services(d.top_services);
				document.getElementById("ad-last-refresh").textContent = "Updated " + frappe.datetime.now_time();
			}
		});
	}

	function render_kpis(k) {
		var growth_color = k.growth >= 0 ? "#10b981" : "#ef4444";
		var growth_arrow = k.growth >= 0 ? "▲" : "▼";
		var cards = [
			{ icon: "📈", color: "blue",   value: fmt(k.revenue_this_month),   label: "Revenue This Month" },
			{ icon: "✅", color: "green",  value: fmt(k.collected_this_month), label: "Collected This Month" },
			{ icon: "📉", color: "purple", value: fmt(k.revenue_last_month),   label: "Last Month Revenue" },
			{ icon: "💳", color: "red",    value: fmt(k.total_outstanding),    label: "Total Outstanding" },
			{ icon: "🎯", color: "teal",   value: k.collection_rate + "%",     label: "Collection Rate" },
			{ icon: "📊", color: "amber",  value: (k.growth >= 0 ? "+" : "") + k.growth + "%", label: "Growth vs Last Month" },
			{ icon: "🧾", color: "indigo", value: k.total_invoices,            label: "Invoices This Month" },
			{ icon: "☑️", color: "pink",   value: k.paid_invoices,             label: "Fully Paid Invoices" },
		];
		document.getElementById("ad-kpis").innerHTML = cards.map(function (c) {
			return '<div class="dash-kpi-card">' +
				'<div class="dash-kpi-icon ' + c.color + '">' + c.icon + '</div>' +
				'<div><div class="dash-kpi-value">' + c.value + '</div><div class="dash-kpi-label">' + c.label + '</div></div>' +
				'</div>';
		}).join("");
	}

	function render_dual_bar(id, data) {
		var el = document.getElementById(id);
		if (!el || !data || !data.length) { el && (el.innerHTML = '<div class="dash-loading">No data</div>'); return; }
		el.innerHTML = "";
		new frappe.Chart(el, {
			type: "bar",
			data: {
				labels: data.map(function (r) { return r.label; }),
				datasets: [
					{ name: "Billed",    values: data.map(function (r) { return r.value || 0; }) },
					{ name: "Collected", values: data.map(function (r) { return r.collected || 0; }) }
				]
			},
			height: 220,
			colors: ["#2563eb", "#10b981"]
		});
	}

	function render_pie(id, data, colors) {
		var el = document.getElementById(id);
		if (!el || !data || !data.length) { el && (el.innerHTML = '<div class="dash-loading">No data</div>'); return; }
		el.innerHTML = "";
		new frappe.Chart(el, { type: "donut", data: { labels: data.map(function (r) { return r.label || "Unknown"; }), datasets: [{ values: data.map(function (r) { return r.value || 0; }) }] }, height: 220, colors: colors });
	}

	function render_services(rows) {
		var tbody = document.querySelector("#ad-services tbody");
		if (!tbody) return;
		tbody.innerHTML = (rows || []).map(function (r) {
			return "<tr><td>" + (r.service || "-") + "</td><td>SOS " + parseFloat(r.revenue || 0).toLocaleString() + "</td><td>" + r.qty + "</td></tr>";
		}).join("") || '<tr><td colspan="3" style="text-align:center;color:#bbb">No data</td></tr>';
	}

	load();
	setInterval(load, 120000);
};
