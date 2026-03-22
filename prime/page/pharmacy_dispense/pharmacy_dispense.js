frappe.pages["pharmacy-dispense"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Pharmacy Dispense",
		single_column: true,
	});

	$(page.body).css({ "max-width": "640px", margin: "30px auto", padding: "0 20px" });

	var html =
		'<p style="color:#888;margin-bottom:20px;">Scan patient payment QR code or enter invoice ID manually.</p>'
		+ '<div style="display:flex;gap:10px;margin-bottom:24px;">'
		+ '<input id="pd-input" type="text" class="form-control" placeholder="Scan QR or type invoice ID\u2026" style="flex:1;font-size:1.1rem;padding:10px 14px;" autocomplete="off">'
		+ '<button id="pd-btn" class="btn btn-primary" style="padding:10px 20px;">Look Up</button>'
		+ '</div>'
		+ '<div id="pd-result"></div>';

	$(page.body).append(html);

	var $input  = $(page.body).find("#pd-input");
	var $btn    = $(page.body).find("#pd-btn");
	var $result = $(page.body).find("#pd-result");

	$input.focus();

	function showResult(data) {
		var e = frappe.utils.escape_html;

		if (!data.found) {
			$result.html(
				'<div class="alert alert-warning" style="border-radius:10px;padding:20px;">'
				+ '<strong>Not Found</strong> &mdash; '
				+ (data.error ? e(data.error) : 'No invoice found for this reference.')
				+ '</div>'
			);
			return;
		}

		if (!data.paid) {
			$result.html(
				'<div class="alert alert-danger" style="border-radius:10px;padding:20px;">'
				+ '<strong>Payment Pending</strong> &mdash; This invoice has not been paid yet.<br>'
				+ '<small>Patient: ' + e(data.patient) + ' &nbsp;|&nbsp; Invoice: ' + e(data.invoice) + '</small>'
				+ '</div>'
			);
			return;
		}

		var itemRows = (data.items || []).map(function (item) {
			return '<tr>'
				+ '<td style="padding:8px 12px;">' + e(item.item_code) + '</td>'
				+ '<td style="padding:8px 12px;">' + e(item.item_name || item.description || "") + '</td>'
				+ '<td style="padding:8px 12px;text-align:center;">' + e(String(item.qty)) + '</td>'
				+ '</tr>';
		}).join("");

		var dispenseBtn = data.already_dispensed
			? '<div class="alert alert-success" style="margin-top:16px;border-radius:8px;">Already dispensed.</div>'
			: '<button id="pd-dispense-btn" class="btn btn-success btn-lg" style="width:100%;margin-top:20px;padding:14px;">Dispense Medicines</button>';

		$result.html(
			'<div style="background:#f8f9fa;border-radius:12px;padding:24px;border:1px solid #dee2e6;">'
			+ '<div style="margin-bottom:16px;">'
			+ '<div style="font-size:0.8rem;color:#888;text-transform:uppercase;margin-bottom:4px;">Patient</div>'
			+ '<div style="font-size:1.4rem;font-weight:700;color:#212529;">' + e(data.patient) + '</div>'
			+ '<div style="font-size:0.85rem;color:#666;">Invoice: ' + e(data.invoice) + '</div>'
			+ '</div>'
			+ '<table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #dee2e6;">'
			+ '<thead><tr style="background:#0066cc;color:#fff;">'
			+ '<th style="padding:8px 12px;text-align:left;">Item Code</th>'
			+ '<th style="padding:8px 12px;text-align:left;">Name</th>'
			+ '<th style="padding:8px 12px;text-align:center;">Qty</th>'
			+ '</tr></thead>'
			+ '<tbody>' + itemRows + '</tbody>'
			+ '</table>'
			+ dispenseBtn
			+ '</div>'
		);

		if (!data.already_dispensed) {
			$(page.body).find("#pd-dispense-btn").on("click", function () {
				var $dispBtn = $(this);
				$dispBtn.prop("disabled", true).text("Dispensing\u2026");
				frappe.call({
					method: "prime.api.queue_display_api.mark_invoice_dispensed",
					args: { invoice_name: data.invoice },
					callback: function (r) {
						if (r.message && r.message.success) {
							$dispBtn.replaceWith('<div class="alert alert-success" style="margin-top:16px;border-radius:8px;font-size:1.1rem;text-align:center;">Medicines dispensed successfully.</div>');
							$input.val("");
							setTimeout(function () { $input.focus(); }, 300);
						}
					},
					error: function () {
						$dispBtn.prop("disabled", false).text("Dispense Medicines");
						frappe.msgprint("Failed to mark as dispensed. Please try again.");
					},
				});
			});
		}
	}

	function doLookup() {
		var ref = $input.val().trim();
		if (!ref) return;
		$result.html('<div style="text-align:center;padding:20px;color:#666;">Looking up\u2026</div>');
		frappe.call({
			method: "prime.api.queue_display_api.get_invoice_for_dispensing",
			args: { invoice_name: ref },
			callback: function (r) {
				if (r.message !== undefined) showResult(r.message);
			},
			error: function () {
				$result.html('<div class="alert alert-danger">Error looking up invoice. Please try again.</div>');
			},
		});
	}

	$btn.on("click", doLookup);
	$input.on("keydown", function (e) { if (e.key === "Enter") doLookup(); });
};
