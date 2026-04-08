frappe.pages["nurse-dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Nurse Dashboard",
		single_column: true,
	});

	page.add_action_icon("refresh", function () { load(); });

	page.body.html(`
		<div class="dash-page">
			<div class="dash-header">
				<div>
					<div class="dash-title">Nurse Dashboard</div>
					<div class="dash-subtitle">Live patient queue and clinical activity</div>
				</div>
				<div class="dash-refresh-info" id="nd-last-refresh"></div>
			</div>
			<div id="nd-kpis" class="dash-kpi-grid">
				<div class="dash-loading">Loading...</div>
			</div>
			<div class="dash-chart-row two-col">
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today — Live</div>
					<div class="dash-chart-heading">Patient Queue</div>
					<table class="dash-table" id="nd-queue">
						<thead><tr><th>#</th><th>Patient</th><th>Doctor</th><th>Dept</th><th>Status</th><th>Time</th></tr></thead>
						<tbody></tbody>
					</table>
				</div>
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">Queue by Status</div>
					<div class="dash-chart-wrap" id="nd-chart-queue"></div>
				</div>
			</div>
			<div class="dash-chart-row two-col">
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">Vitals Recorded by Hour</div>
					<div class="dash-chart-wrap" id="nd-chart-vitals"></div>
				</div>
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">Patients Awaiting Vitals</div>
					<table class="dash-table" id="nd-no-vitals">
						<thead><tr><th>Patient</th><th>Doctor</th><th>Time</th></tr></thead>
						<tbody></tbody>
					</table>
				</div>
			</div>
		</div>
	`);

	function status_badge(s) {
		var map = { "Waiting": "amber", "Called": "blue", "Completed": "green", "Cancelled": "red", "In Progress": "teal" };
		return '<span class="dash-badge ' + (map[s] || "gray") + '">' + (s || "Waiting") + "</span>";
	}

	function load() {
		frappe.call({
			method: "prime.prime.page.nurse_dashboard.nurse_dashboard_api.get_stats",
			callback: function (r) {
				if (!r.message) return;
				var d = r.message;
				render_kpis(d.kpis);
				render_queue(d.live_queue);
				render_pie("nd-chart-queue", d.queue_breakdown, ["#f59e0b", "#2563eb", "#10b981", "#ef4444", "#6b7280"]);
				render_bar("nd-chart-vitals", d.vitals_hourly, ["#10b981"]);
				render_no_vitals(d.no_vitals);
				document.getElementById("nd-last-refresh").textContent = "Updated " + frappe.datetime.now_time();
			}
		});
	}

	function render_kpis(k) {
		var cards = [
			{ icon: "⏳", color: "amber",  value: k.queue_waiting,       label: "Waiting" },
			{ icon: "📢", color: "blue",   value: k.queue_called,        label: "Called" },
			{ icon: "✅", color: "green",  value: k.queue_completed,     label: "Completed Today" },
			{ icon: "👥", color: "purple", value: k.queue_total,         label: "Total Queue Today" },
			{ icon: "❤️", color: "red",    value: k.vitals_today,        label: "Vitals Recorded" },
			{ icon: "🧪", color: "teal",   value: k.lab_samples_today,   label: "Lab Samples Collected" },
			{ icon: "📅", color: "indigo", value: k.appointments_today,  label: "Appointments Today" },
			{ icon: "🏁", color: "pink",   value: k.appointments_seen,   label: "Appointments Seen" },
		];
		document.getElementById("nd-kpis").innerHTML = cards.map(function (c) {
			return '<div class="dash-kpi-card">' +
				'<div class="dash-kpi-icon ' + c.color + '">' + c.icon + '</div>' +
				'<div><div class="dash-kpi-value">' + c.value + '</div><div class="dash-kpi-label">' + c.label + '</div></div>' +
				'</div>';
		}).join("");
	}

	function render_queue(rows) {
		var tbody = document.querySelector("#nd-queue tbody");
		if (!tbody) return;
		tbody.innerHTML = (rows || []).map(function (r) {
			return "<tr><td><strong>" + (r.token_no || "-") + "</strong></td><td>" + (r.patient_name || "-") +
				"</td><td>" + (r.practitioner_name || "-") + "</td><td>" + (r.department || "-") +
				"</td><td>" + status_badge(r.status) + "</td><td>" + (r.time ? r.time.substring(0, 5) : "-") + "</td></tr>";
		}).join("") || '<tr><td colspan="6" style="text-align:center;color:#bbb">No active queue</td></tr>';
	}

	function render_no_vitals(rows) {
		var tbody = document.querySelector("#nd-no-vitals tbody");
		if (!tbody) return;
		tbody.innerHTML = (rows || []).map(function (r) {
			return "<tr><td>" + (r.patient_name || "-") + "</td><td>" + (r.practitioner_name || "-") + "</td><td>" + (r.appointment_time || "-") + "</td></tr>";
		}).join("") || '<tr><td colspan="3" style="text-align:center;color:#bbb">All patients have vitals</td></tr>';
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

	load();
	setInterval(load, 30000);
};
