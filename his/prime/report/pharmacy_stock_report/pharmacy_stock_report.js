// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Pharmacy Stock Report"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "get_query": function () {
                var company = frappe.query_report.get_filter_value("company");
                return {
                    filters: {
                        "company": company
                    }
                };
            }
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname": "item_code",
            "label": __("Item"),
            "fieldtype": "Link",
            "options": "Item"
        }
    ]
};
