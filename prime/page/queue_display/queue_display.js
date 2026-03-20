frappe.pages["queue-display"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: "Queue Display",
		single_column: true,
	});

	$(wrapper).find(".page-head").hide();
	$("body").css("background", "#0a0a0a");

	var $body = $(wrapper).find(".page-content, .layout-main-section, .page-body").first();
	if (!$body.length) $body = $(wrapper);

	var $container = $('<div id="qd-root" style="padding:20px;color:#fff;font-family:sans-serif;"></div>');
	$body.append($container);

	function render(data) {
		if (!data || !data.length) {
			$container.html('<div style="text-align:center;margin-top:80px;font-size:2rem;color:#666;">No active queue today</div>');
			return;
		}
		var html = '<div style="display:flex;flex-wrap:wrap;gap:20px;">';
		data.forEach(function (doc) {
			var cur = doc.current_token != null ? doc.current_token : "—";
			var nxt = doc.next_token != null ? doc.next_token : "—";
			html += '<div style="flex:1;min-width:280px;background:#1a1a2e;border-radius:12px;padding:24px;border:1px solid #2a2a4a;">';
			html += '<div style="font-size:1rem;color:#a0a0c0;margin-bottom:2px;">' + frappe.utils.escape_html(doc.department || "") + '</div>';
			html += '<div style="font-size:1.4rem;font-weight:700;color:#e0e0ff;margin-bottom:18px;">' + frappe.utils.escape_html(doc.practitioner_name) + '</div>';
			html += '<div style="margin-bottom:14px;"><div style="font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:1px;">Now Serving</div>';
			html += '<div style="font-size:4rem;font-weight:900;color:#00d4ff;line-height:1;">' + frappe.utils.escape_html(String(cur)) + '</div></div>';
			html += '<div style="display:flex;gap:20px;">';
			html += '<div><div style="font-size:0.75rem;color:#888;">Next</div><div style="font-size:1.8rem;font-weight:700;color:#ffd700;">' + frappe.utils.escape_html(String(nxt)) + '</div></div>';
			html += '<div><div style="font-size:0.75rem;color:#888;">Waiting</div><div style="font-size:1.8rem;font-weight:700;color:#ff6b6b;">' + frappe.utils.escape_html(String(doc.waiting_count)) + '</div></div>';
			html += '</div></div>';
		});
		html += '</div>';
		$container.html(html);
	}

	function load() {
		frappe.call({
			method: "prime.api.queue_display_api.get_live_queue",
			callback: function (r) {
				if (r.message !== undefined) render(r.message);
			},
		});
	}

	load();
	frappe.realtime.on("que_update", load);
	var interval = setInterval(load, 30000);

	$(wrapper).on("remove", function () {
		clearInterval(interval);
		frappe.realtime.off("que_update");
		$("body").css("background", "");
	});
};
