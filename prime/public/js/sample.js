function sc_fix_primary_btn_color(frm) {
	setTimeout(function() {
		var btn = frm.page.btn_primary[0];
		if (btn) btn.style.setProperty('color', '#ffffff', 'important');
	}, 500);
}

frappe.ui.form.on('Sample Collection', {
	refresh(frm) {
		frm.page.wrapper.addClass('si-modern');
		sc_fix_primary_btn_color(frm);

		frm.remove_custom_button('View Lab Tests');
		frm.add_custom_button(__('Call'), function() {
			frm.set_value('que_steps', 'Called');
			frm.save();
		});
	},
});
