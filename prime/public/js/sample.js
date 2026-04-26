function sc_fix_primary_btn_color(frm) {
	setTimeout(function() {
		var btn = frm.page.btn_primary[0];
		if (btn) btn.style.setProperty('color', '#ffffff', 'important');
	}, 500);
}

function sc_layout_ref_fields(frm) {
	setTimeout(function() {
		var fd = frm.fields_dict;
		var ref_fields = ['reff_invoice', 'source_order', 'custom_reff_order', 'custom_reff_ipdorder', 'custom_patient_encounter'];

		if (!fd.reff_invoice || !fd.reff_invoice.$wrapper.length) return;
		if (fd.reff_invoice.$wrapper.closest('.sc-ref-grid').length) return;

		var missing = ref_fields.filter(function(f) {
			return !fd[f] || !fd[f].$wrapper || !fd[f].$wrapper.length;
		});
		if (missing.length) return;

		var $grid = $('<div class="sc-ref-grid"></div>');
		fd.reff_invoice.$wrapper.before($grid);
		ref_fields.forEach(function(f) { $grid.append(fd[f].$wrapper); });

		$grid.closest('.form-column').addClass('sc-full-col');
	}, 350);
}

frappe.ui.form.on('Sample Collection', {
	refresh(frm) {
		frm.page.wrapper.addClass('si-modern');
		sc_layout_ref_fields(frm);
		sc_fix_primary_btn_color(frm);

		frm.remove_custom_button('View Lab Tests');
		frm.add_custom_button(__('Call'), function() {
			frm.set_value('que_steps', 'Called');
			frm.save();
		});
	},
});
