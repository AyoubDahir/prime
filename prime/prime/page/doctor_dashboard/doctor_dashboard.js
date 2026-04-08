frappe.pages["doctor-dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Doctor Dashboard",
		single_column: true,
	});

	page.add_action_icon("refresh", function () { load(); });

	page.body.html(`
		<div class="dash-page">
			<div class="dash-header">
				<div>
					<div class="dash-title">Doctor Dashboard</div>
					<div class="dash-subtitle" id="dd-doctor-name">Loading...</div>
				</div>
				<div class="dash-refresh-info" id="dd-last-refresh"></div>
			</div>
			<div id="dd-kpis" class="dash-kpi-grid">
				<div class="dash-loading">Loading...</div>
			</div>
			<div class="dash-chart-row two-col">
				<div class="dash-chart-card">
					<div class="dash-chart-title">Last 7 Days</div>
					<div class="dash-chart-heading">My Appointments</div>
					<div class="dash-chart-wrap" id="dd-chart-weekly"></div>
				</div>
				<div class="dash-chart-card">
					<div class="dash-chart-title">This Month</div>
					<div class="dash-chart-heading">Patient Gender Split</div>
					<div class="dash-chart-wrap" id="dd-chart-gender"></div>
				</div>
			</div>
			<div class="dash-chart-row full">
				<div class="dash-chart-card">
					<div class="dash-chart-title">Today</div>
					<div class="dash-chart-heading">My Patients</div>
					<table class="dash-table" id="dd-patients">
						<thead><tr><th>Patient</th><th>Time</th><th>Status</th></tr></thead>
						<tbody></tbody>
					</table>
				</div>
			</div>
		</div>
	`);

	function status_badge(s) {
		var cls = { "Closed": "green", "Open": "blue", "Checked In": "amber", "Cancelled": "red" }[s] || "gray";
		return '<span class="dash-badge ' + cls + '">' + (s || "Open") + "</span>";
	}

	function load() {
		frappe.call({
			method: "prime.prime.page.doctor_dashboard.doctor_dashboard_api_v2.get_stats",
			callback: function (r) {
				if (!r.message) return;
				var d = r.message;
				var name_el = document.getElementById("dd-doctor-name");
				if (name_el) name_el.textContent = d.practitioner ? "Dr. " + d.practitioner : "No practitioner linked to your account";
				render_kpis(d.kpis);
				render_chart("dd-chart-weekly", d.weekly, ["#2563eb"]);
				render_chart_pie("dd-chart-gender", d.gender_split, ["#2563eb", "#f9a8d4", "#a78bfa"]);
				render_patients(d.recent);
				document.getElementById("dd-last-refresh").textContent = "Updated " + frappe.datetime.now_time();
			}
		});
	}

	function render_kpis(k) {
		var cards = [
			{ icon: "📋", color: "blue",   value: k.appt_today,    label: "Appointments Today" },
			{ icon: "✅", color: "green",  value: k.seen_today,    label: "Patients Seen" },
			{ icon: "⏳", color: "amber",  value: k.pending_today, label: "Waiting in Queue" },
			{ icon: "🩺", color: "teal",   value: k.encounters_today, label: "Encounters Created" },
			{ icon: "🧪", color: "red",    value: k.lab_pending,   label: "Lab Results Pending" },
			{ icon: "📅", color: "purple", value: k.month_patients, label: "Patients This Month" },
		];
		document.getElementById("dd-kpis").innerHTML = cards.map(function (c) {
			return '<div class="dash-kpi-card">' +
				'<div class="dash-kpi-icon ' + c.color + '">' + c.icon + '</div>' +
				'<div><div class="dash-kpi-value">' + c.value + '</div><div class="dash-kpi-label">' + c.label + '</div></div>' +
				'</div>';
		}).join("");
	}

	function render_chart(id, data, colors) {
		var el = document.getElementById(id);
		if (!el || !data || !data.length) { el && (el.innerHTML = '<div class="dash-loading">No data</div>'); return; }
		el.innerHTML = "";
		new frappe.Chart(el, {
			type: "bar",
			data: { labels: data.map(function (r) { return r.label; }), datasets: [{ values: data.map(function (r) { return r.value || 0; }) }] },
			height: 220, colors: colors
		});
	}

	function render_chart_pie(id, data, colors) {
		var el = document.getElementById(id);
		if (!el || !data || !data.length) { el && (el.innerHTML = '<div class="dash-loading">No data</div>'); return; }
		el.innerHTML = "";
		new frappe.Chart(el, {
			type: "pie",
			data: { labels: data.map(function (r) { return r.label || "Unknown"; }), datasets: [{ values: data.map(function (r) { return r.value || 0; }) }] },
			height: 220, colors: colors
		});
	}

	function render_patients(rows) {
		var tbody = document.querySelector("#dd-patients tbody");
		if (!tbody) return;
		tbody.innerHTML = (rows || []).map(function (r) {
			return "<tr><td>" + (r.patient_name || "-") + "</td><td>" + (r.appointment_time || "-") + "</td><td>" + status_badge(r.status) + "</td></tr>";
		}).join("") || '<tr><td colspan="3" style="text-align:center;color:#bbb">No appointments today</td></tr>';
	}

	load();
	setInterval(load, 60000);
};
