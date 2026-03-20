frappe.pages["qr-checkin"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: "QR Check-in",
		single_column: true,
	});

	var $body = $(wrapper).find(".page-content, .layout-main-section, .page-body").first();
	if (!$body.length) $body = $(wrapper);

	$body.css({ "max-width": "600px", margin: "30px auto", padding: "0 20px" });

	$body.append(`
		<p style="color:#888;margin-bottom:20px;">Scan patient mobile QR or enter reference ID manually.</p>
		<div style="display:flex;gap:10px;margin-bottom:24px;">
			<input id="qci-input" type="text" class="form-control"
				placeholder="Scan QR or type reference ID…"
				style="flex:1;font-size:1.1rem;padding:10px 14px;">
			<button id="qci-btn" class="btn btn-primary" style="padding:10px 20px;">Check In</button>
		</div>
		<div id="qci-result"></div>
	`);

	var $input = $body.find("#qci-input");
	var $btn = $body.find("#qci-btn");
	var $result = $body.find("#qci-result");

	$input.focus();

	function showResult(data) {
		if (!data.found) {
			$result.html(`
				<div class="alert alert-warning" style="border-radius:10px;padding:20px;">
					<strong>Not Found</strong> — No queue entry found for this reference.<br><br>
					<a href="/app/que/new-que" class="btn btn-sm btn-default">Create New Queue Manually</a>
				</div>
			`);
			return;
		}
		var color = data.que_steps === "Called" ? "#28a745" : "#ffc107";
		$result.html(`
			<div style="background:#f8f9fa;border-radius:12px;padding:24px;border:1px solid #dee2e6;">
				<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
					<div>
						<div style="font-size:0.8rem;color:#888;text-transform:uppercase;">Token</div>
						<div style="font-size:3.5rem;font-weight:900;color:#0066cc;line-height:1;">${frappe.utils.escape_html(String(data.token_no))}</div>
					</div>
					<span style="background:${color};color:#fff;padding:4px 12px;border-radius:20px;font-size:0.85rem;">${frappe.utils.escape_html(data.que_steps || data.status)}</span>
				</div>
				<div style="margin-bottom:4px;font-weight:600;">${frappe.utils.escape_html(data.patient_name)}</div>
				<div style="color:#666;font-size:0.9rem;">Dr. ${frappe.utils.escape_html(data.practitioner_name)}</div>
				<div style="color:#666;font-size:0.9rem;margin-bottom:16px;">${frappe.utils.escape_html(data.department || "")}</div>
				<div style="background:#fff3cd;border-radius:8px;padding:12px;text-align:center;font-size:1.1rem;color:#856404;">
					<strong>${frappe.utils.escape_html(String(data.patients_ahead))}</strong> patient(s) ahead
				</div>
				<div style="margin-top:16px;text-align:center;">
					<a href="/app/que/${frappe.utils.escape_html(data.que)}" class="btn btn-sm btn-default" target="_blank">Open Queue Record</a>
				</div>
			</div>
		`);
	}

	function doLookup() {
		var ref = $input.val().trim();
		if (!ref) return;
		$result.html('<div style="text-align:center;padding:20px;color:#666;">Looking up…</div>');
		frappe.call({
			method: "prime.api.queue_display_api.checkin_by_qr",
			args: { reference_id: ref },
			callback: function (r) {
				if (r.message !== undefined) showResult(r.message);
			},
			error: function () {
				$result.html('<div class="alert alert-danger">Error looking up reference. Please try again.</div>');
			},
		});
	}

	$btn.on("click", doLookup);
	$input.on("keydown", function (e) { if (e.key === "Enter") doLookup(); });
};
