function so_fix_primary_btn_color(frm) {
	setTimeout(function() {
		var btn = frm.page.btn_primary[0];
		if (btn) btn.style.setProperty('color', '#ffffff', 'important');
	}, 500);
}

function so_merge_sections(frm) {
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

function so_hide_buttons(frm) {
	setTimeout(function() {
		frm.page.inner_toolbar.find('button').filter(function() {
			return $(this).text().trim() === 'Fetch Timesheet';
		}).hide();
		frm.page.inner_toolbar.find('.btn-group, .custom-btn-group').filter(function() {
			return $(this).text().indexOf('Get Items From') !== -1;
		}).hide();
	}, 400);
}

function so_reorder_fields(frm) {
	var fd = frm.fields_dict;

	// Middle column anchor: so_type (Sales Order Type)
	var $so_type  = fd.so_type          && fd.so_type.$wrapper;
	// Left column — to move out
	var $ref_prac = fd.ref_practitioner && fd.ref_practitioner.$wrapper;

	// Right column anchor: po_no (Customer's Purchase Order)
	var $po_no = fd.po_no && fd.po_no.$wrapper;
	// Left column — to move out
	var $room  = fd.room  && fd.room.$wrapper;
	var $bed   = fd.bed   && fd.bed.$wrapper;

	// Move Referring Practitioner → middle column, after Sales Order Type
	if ($so_type && $so_type.length && $ref_prac && $ref_prac.length) {
		$so_type.after($ref_prac);
	}

	// Move Room and Bed → right column, after Customer's Purchase Order
	if ($po_no && $po_no.length) {
		if ($room && $room.length)                          $po_no.after($room);
		if ($room && $room.length && $bed && $bed.length)   $room.after($bed);
	}
}

frappe.ui.form.on('Sales Order', {
	refresh(frm) {
		frm.page.wrapper.addClass('si-modern');
		so_reorder_fields(frm);
		so_merge_sections(frm);
		so_hide_buttons(frm);
		so_fix_primary_btn_color(frm);
	}
});
