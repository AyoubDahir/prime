$(document).on('page-change', function () {
	if (!frappe.user_roles || !frappe.boot) return;

	// System Manager and Administrator always have full access
	if (
		frappe.user_roles.includes('System Manager') ||
		frappe.user_roles.includes('Administrator')
	) return;

	var route = frappe.get_route();
	if (!route || route.length < 2) return;

	var view = route[0];
	var doctype = route[1];

	// Only guard standard doctype views
	if (!['List', 'Form', 'Report', 'Tree', 'Dashboard'].includes(view)) return;
	if (!doctype) return;

	if (!frappe.model.can_read(doctype)) {
		frappe.set_route('');
		frappe.msgprint({
			title: __('Access Denied'),
			message: __('You do not have permission to access <b>{0}</b>.', [__(doctype)]),
			indicator: 'red'
		});
	}
});
