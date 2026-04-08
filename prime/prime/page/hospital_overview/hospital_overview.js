frappe.pages["hospital-overview"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Hospital Overview",
		single_column: true,
	});

	page.add_action_icon("refresh", function () { load(); });

	page.body.html(`
		<div class="dash-page">
			<div class="dash-header">
				<div>
					<div class="dash-title">Hospital Overview</div>
					<div class="dash-subtitle">Real-time overview of hospital operations</div>
				</div>
				<div class="dash-refresh-info" id="ho-last-refresh"></div>
			</div>
			<div id="ho-kpis" class="dash-kpi-grid">
				<div class="dash-loading">Loading...</div>
			</div>
			<div class="dash-chart-row two-col">
				<div class="dash-chart-card">
					<div class="dash-chart-title">Revenue Overview</div>
					<div class="dash-chart-heading">Monthly Revenue (6 months)</div>
					<div class="dash-chart-wrap" id="ho-chart-revenue"></div>
				</div>
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">Appointments by Department</div>
					<div class="dash-chart-wrap" id="ho-chart-dept"></div>
				</div>
			</div>
			<div class="dash-chart-row two-col">
				<div class="dash-chart-card">
					<div class="dash-chart-title">This Month</div>
					<div class="dash-chart-heading">Top Doctors by Appointments</div>
					<table class="dash-table" id="ho-top-doctors">
						<thead><tr><th>Doctor</th><th>Appointments</th><th>Seen</th></tr></thead>
						<tbody></tbody>
					</table>
				</div>
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">Queue Status</div>
					<div class="dash-chart-wrap" id="ho-chart-queue"></div>
				</div>
			</div>
		</div>
	`);

	function fmt_currency(v) {
		return "SOS " + parseFloat(v || 0).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
	}

	function load() {
		frappe.call({
			method: "prime.prime.page.hospital_overview.hospital_overview_api.get_stats",
			callback: function (r) {
				if (!r.message) return;
				var d = r.message;
				render_kpis(d.kpis);
				render_chart("ho-chart-revenue", "bar", d.monthly_revenue, ["#2563eb"], false);
				render_chart("ho-chart-dept", "pie", d.by_department, ["#2563eb","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316","#84cc16"], true);
				render_chart("ho-chart-queue", "pie", d.queue_status, ["#f59e0b","#2563eb","#10b981","#ef4444","#6b7280"], true);
				render_top_doctors(d.top_doctors);
				document.getElementById("ho-last-refresh").textContent = "Updated " + frappe.datetime.now_time();
			}
		});
	}

	function render_kpis(k) {
		var cards = [
			{ icon: "🏥", color: "blue",   value: k.patients_today,    label: "Appointments Today" },
			{ icon: "📅", color: "purple", value: k.patients_month,    label: "Appointments This Month" },
			{ icon: "💰", color: "green",  value: fmt_currency(k.revenue_today),  label: "Revenue Today" },
			{ icon: "📊", color: "teal",   value: fmt_currency(k.revenue_month),  label: "Revenue This Month" },
			{ icon: "⏳", color: "amber",  value: k.queue_active,      label: "Active Queue" },
			{ icon: "👤", color: "indigo", value: k.new_patients,      label: "New Patients Today" },
			{ icon: "🧾", color: "red",    value: k.pending_invoices,  label: "Pending Invoices" },
			{ icon: "💳", color: "pink",   value: fmt_currency(k.outstanding_amount), label: "Outstanding Amount" },
		];
		document.getElementById("ho-kpis").innerHTML = cards.map(function (c) {
			return '<div class="dash-kpi-card">' +
				'<div class="dash-kpi-icon ' + c.color + '">' + c.icon + '</div>' +
				'<div><div class="dash-kpi-value">' + c.value + '</div><div class="dash-kpi-label">' + c.label + '</div></div>' +
				'</div>';
		}).join("");
	}

	function render_chart(id, type, data, colors, is_pie) {
		var el = document.getElementById(id);
		if (!el || !data || !data.length) { el && (el.innerHTML = '<div class="dash-loading">No data</div>'); return; }
		el.innerHTML = "";
		new frappe.Chart(el, {
			type: type,
			data: {
				labels: data.map(function (r) { return r.label; }),
				datasets: [{ values: data.map(function (r) { return r.value || 0; }) }]
			},
			height: 220,
			colors: colors,
			truncateLegends: true,
			tooltipOptions: { formatTooltipY: function (v) { return v; } }
		});
	}

	function render_top_doctors(rows) {
		var tbody = document.querySelector("#ho-top-doctors tbody");
		if (!tbody) return;
		tbody.innerHTML = (rows || []).map(function (r) {
			return "<tr><td>" + (r.doctor || "-") + "</td><td>" + r.patients + "</td><td>" + r.seen + "</td></tr>";
		}).join("") || '<tr><td colspan="3" style="text-align:center;color:#bbb">No data</td></tr>';
	}

	load();
	setInterval(load, 60000);
};
