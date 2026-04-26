function lt_fix_primary_btn_color(frm) {
	setTimeout(function() {
		var btn = frm.page.btn_primary[0];
		if (btn) btn.style.setProperty('color', '#ffffff', 'important');
	}, 500);
}

function lt_merge_sections(frm) {
	setTimeout(function() {
		var $sections = $(frm.wrapper).find('.form-section');
		var totals_idx = -1;
		$sections.each(function(i) {
			var t = $(this).find('.section-head').first().text().trim().toUpperCase();
			if (t.indexOf('TOTAL') !== -1) { totals_idx = i; }
		});
		if (totals_idx >= 0 && totals_idx + 1 < $sections.length) {
			$sections.eq(totals_idx).addClass('si-merge-top');
			$sections.eq(totals_idx + 1).addClass('si-merge-bottom');
		}
	}, 700);
}

frappe.ui.form.on('Lab Test', {
	refresh(frm) {
		frm.page.wrapper.addClass('si-modern');
		lt_merge_sections(frm);
		lt_fix_primary_btn_color(frm);
	}
});
