frappe.pages["data-cleanup"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Data Cleanup",
		single_column: true,
	});

	page.body.html(`
		<div class="cleanup-page">
			<div class="cleanup-warning">
				<span class="cleanup-warning-icon">&#9888;</span>
				<strong>Warning:</strong> These actions permanently delete data and cannot be undone.
				Only use this before going live or to reset a test environment.
				A database backup is strongly recommended first.
			</div>

			<div class="cleanup-grid">

				<div class="cleanup-card" id="card-transactions">
					<div class="cleanup-card-header">
						<span class="cleanup-card-icon">&#128196;</span>
						<div>
							<div class="cleanup-card-title">Transactions</div>
							<div class="cleanup-card-subtitle">Sales Invoice, Sales Order, Payment Entry</div>
						</div>
					</div>
					<ul class="cleanup-list">
						<li>Sales Invoice &amp; line items</li>
						<li>Sales Order &amp; line items</li>
						<li>Payment Entry &amp; references</li>
						<li>GL Entry (all)</li>
						<li>Payment Ledger Entry</li>
						<li>Stock Ledger Entry</li>
					</ul>
					<button class="btn btn-danger cleanup-btn" data-group="transactions">
						Delete Transactions
					</button>
				</div>

				<div class="cleanup-card" id="card-clinical">
					<div class="cleanup-card-header">
						<span class="cleanup-card-icon">&#129657;</span>
						<div>
							<div class="cleanup-card-title">Clinical Records</div>
							<div class="cleanup-card-subtitle">Encounters, Lab, Appointments</div>
						</div>
					</div>
					<ul class="cleanup-list">
						<li>Patient Encounter &amp; prescriptions</li>
						<li>Patient Appointment</li>
						<li>Vital Signs</li>
						<li>Lab Test &amp; results</li>
						<li>Sample Collection</li>
						<li>Que (queue tokens)</li>
					</ul>
					<button class="btn btn-danger cleanup-btn" data-group="clinical">
						Delete Clinical Records
					</button>
				</div>

				<div class="cleanup-card" id="card-patients">
					<div class="cleanup-card-header">
						<span class="cleanup-card-icon">&#128100;</span>
						<div>
							<div class="cleanup-card-title">Patients</div>
							<div class="cleanup-card-subtitle">All patient master records</div>
						</div>
					</div>
					<ul class="cleanup-list">
						<li>All Patient records</li>
						<li>Patient Medical Records</li>
					</ul>
					<button class="btn btn-danger cleanup-btn" data-group="patients">
						Delete Patients
					</button>
				</div>

				<div class="cleanup-card" id="card-logs">
					<div class="cleanup-card-header">
						<span class="cleanup-card-icon">&#128203;</span>
						<div>
							<div class="cleanup-card-title">Logs &amp; Notifications</div>
							<div class="cleanup-card-subtitle">System logs, SMS, notifications</div>
						</div>
					</div>
					<ul class="cleanup-list">
						<li>Error Log</li>
						<li>Scheduled Job Log</li>
						<li>Notification Log</li>
						<li>SMS Log</li>
						<li>Email Queue</li>
						<li>Activity Log</li>
					</ul>
					<button class="btn btn-warning cleanup-btn" data-group="logs">
						Clear Logs
					</button>
				</div>

				<div class="cleanup-card cleanup-card-full" id="card-all">
					<div class="cleanup-card-header">
						<span class="cleanup-card-icon">&#128465;</span>
						<div>
							<div class="cleanup-card-title">Full Reset</div>
							<div class="cleanup-card-subtitle">Delete everything above and reset all naming series to 0</div>
						</div>
					</div>
					<button class="btn btn-danger cleanup-btn" id="btn-full-reset">
						Full Reset — Delete All UAT Data
					</button>
				</div>

			</div>
		</div>
	`);

	// Individual group buttons
	page.body.find(".cleanup-btn[data-group]").on("click", function () {
		var group = $(this).data("group");
		var labels = {
			transactions: "all transaction data (Sales Invoice, Sales Order, Payment Entry, GL entries)",
			clinical: "all clinical records (Encounters, Lab Tests, Appointments, Que)",
			patients: "ALL patient records",
			logs: "all system logs and notifications",
		};
		frappe.confirm(
			"Are you sure you want to permanently delete " + labels[group] + "? This cannot be undone.",
			function () {
				run_cleanup(group);
			}
		);
	});

	// Full reset button
	page.body.find("#btn-full-reset").on("click", function () {
		frappe.confirm(
			"<strong>FULL RESET</strong>: This will delete ALL UAT data and reset all naming series to zero.<br><br>Are you absolutely sure?",
			function () {
				frappe.confirm(
					"Last chance — confirm you have a database backup and want to proceed.",
					function () {
						run_cleanup("all");
					}
				);
			}
		);
	});

	function run_cleanup(group) {
		frappe.show_progress("Deleting data...", 0, 100, "Please wait");
		frappe.call({
			method: "prime.prime.page.data_cleanup.data_cleanup.run_cleanup",
			args: { group: group },
			callback: function (r) {
				frappe.hide_progress();
				if (r.message && r.message.success) {
					frappe.msgprint({
						title: "Done",
						message: r.message.log.join("<br>"),
						indicator: "green",
					});
				} else {
					frappe.msgprint({
						title: "Error",
						message: (r.message && r.message.error) || "Unknown error",
						indicator: "red",
					});
				}
			},
			error: function () {
				frappe.hide_progress();
				frappe.msgprint({ title: "Error", message: "Request failed.", indicator: "red" });
			},
		});
	}
};
