from . import __version__ as app_version
import prime.monkey_patches.workflow

app_name = "prime"
app_title = "Prime"
app_publisher = "Prime"
app_description = "Prime"
app_email = "prime"
app_license = "MIT"
required_apps = ["erpnext","healthcare"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = ["/assets/prime/css/prime.css"]
app_include_js = ["/assets/prime/js/prime.js"]


# include js, css files in header of web template
# web_include_css = "/assets/prime/css/prime.css"
# web_include_js = "/assets/prime/js/prime.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "prime/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Invoice" : "public/js/sales_invoice.js" , 
    "Patient" : "public/js/patient.js" ,  
    "Patient Appointment" : "public/js/patient_encounter.js" , 
    "Patient Encounter" : "public/js/encounter_steps.js",
    "Sample Collection": "public/js/sample.js",
    "Inpatient Record": "public/js/inpatient_record.js"


    
    
    }
doctype_list_js = {
    "Sales Order" : "public/js/opd_order_list.js", 
    "Inpatient Record": "public/js/inpatient_record_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#   "Role": "home_page"
# }

website_route_rules = [
    {"from_route": "/screen/screen/<roomname>", "to_route": "screen/screen"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#   "methods": "prime.utils.jinja_methods",
#   "filters": "prime.utils.jinja_filters"
# }

# Installation
# ------------


# before_install = "prime.install.before_install"
after_install = "prime.setup.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "prime.uninstall.before_uninstall"
# after_uninstall = "prime.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "prime.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#   "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#   "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    # "Item": "prime.api.retail_setup.CustomItem",
    "Clinical Procedure": "prime.api.clinical_procedure.CustomClinicalProcedure",
     "Sales Order": "prime.override.sales_order.CustomSalesOrder",
      "Sales Invoice": "prime.override.sales_invoice.CustomSalesInvoice"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Patient Encounter": {
        "before_validate": "prime.api.patient_encounter.set_so_values_from_db",
        "on_update": "prime.api.patient_encounter.enqueue_sales_orders",
        "on_update_after_submit": "prime.api.patient_encounter.enqueue_sales_orders",
        "after_insert" : "prime.api.patient_encounter.close_que_after_save_pe",
    },
    #     "Doctor Plan": {
    #     "before_validate": "prime.api.doctor_plan.set_so_values_from_db",
    #     "on_update": "prime.api.doctor_plan.enqueue_sales_orders",
    #     "on_update_after_submit": "prime.api.doctor_plan.enqueue_sales_orders",
    # },
    #     "Inpatient Order": {
    #     "before_validate": "prime.api.inpatient_order.set_so_values_from_db",
    #     "on_update": "prime.api.inpatient_order.enqueue_sales_orders",
    #     "on_update_after_submit": "prime.api.inpatient_order.enqueue_sales_orders",
    # },
    "Stock Entry": {
        "on_submit": "prime.api.pharmacy_audit.log_stock_entry"
    },
    "Item Price": {
        "on_update": "prime.api.pharmacy_audit.log_item_price_change"
    },
    # "Emergency": {
    #     "before_validate": "prime.api.emergency.set_so_values_from_db",
    #     "on_update": "prime.api.emergency.enqueue_sales_orders",
    #     "on_update_after_submit": "prime.api.emergency.enqueue_sales_orders",
    # },
    # "Que": {
    #     "before_save": 
    #     ["prime.api.Que_to_make_sales_invove.make_invoice",
    #     "prime.api.Que_to_fee_validity.make_fee_validity",
    #     "prime.api.que_token_number.token_numebr"]
        
        
    # },
        "Sample Collection": {
        "before_insert": ["prime.api.make_sample_collection.token_number"],
        "on_submit": ["prime.api.create_lab_test.create_lab_tests"]
      
        
    },
    "Patient": {
            "before_save": ["prime.api.make_uppercase.make_uppercase", "prime.api.patient.age_todate"]
            
    },
      "Inpatient Record": {
            "before_save": "prime.api.admit.invoice_addition_beds",
            
    },
    "Journal Entry" : {
      "before_cancel" : "prime.api.journal_entry.cancell_sales_invoice"
    },
    "Sales Order": {
        "on_submit": [
            "prime.api.make_sample_collection.make_sample_collection_from_order",
                # "prime.api.radiology.create_radiolgy_from_order",
                ],
    },
    "Clinical Procedure":{
        "on_submit": "prime.api.clinical_procedure.make_anethesia",
    },
    "Sales Invoice": {
            "on_submit": [

                "prime.api.journal_entry.insurance",
                "prime.api.journal_entry.employee_due",
                "prime.api.journal_entry.free_que_expense",
                "prime.api.make_sample_collection.make_sample_collection",
                "prime.api.sales_invoice.real",
                
                "prime.api.clinical_procedure.clinical_pro_comm",
                
                "prime.api.radiology.create_radiolgy",
                "prime.api.radiology.make_cytology",
                # "prime.api.ot_prepation.make_ot_prepararion",
                "prime.api.egd.make_egd",
                "prime.api.clinical_procedure.make_procedures"
                
                ],
                "before_cancel" : "prime.api.journal_entry.cancell_journal"
            
    },
    "Stock Reconciliation" : {
        # "on_submit" : "prime.api.retail_setup.stock_reconciliation_retail",
    },
    "Purchase Invoice" : {
        # "on_submit" : "prime.api.retail_setup.purchase_invoice_retail",
    },
    # "Patient Encounter" : {
    #   "before_save" : "prime.api.patient_encounter.close_que_after_save_pe",
    # }
    
#"Patient": {"after_insert": "prime.api.patient.invoice_registration"}
    
#   "*": {
#       "on_update": "method",
#       "on_cancel": "method",
#       "on_trash": "method"
#   }
}

# Scheduled Tasks
# ---------------
scheduler_events = {
       "cron": {
	"* 16 * * *": [
		 "prime.api.send_sms_follow_up.sendsms",
       
        

		
	],
	   }
}

# scheduler_events = {
#   "all": [
#       "prime.tasks.all"
#   ],
#   "daily": [
#       "prime.tasks.daily"
#   ],
#   "hourly": [
#       "prime.tasks.hourly"
#   ],
#   "weekly": [
#       "prime.tasks.weekly"
#   ],
#   "monthly": [
#       "prime.tasks.monthly"
#   ],
# }

# Testing
# -------

# before_tests = "prime.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "healthcare.healthcare.doctype.lab_test.lab_test.create_multiple": "prime.override.lab_test.create_multiple"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#   "Task": "prime.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
#   {
#       "doctype": "{doctype_1}",
#       "filter_by": "{filter_by}",
#       "redact_fields": ["{field_1}", "{field_2}"],
#       "partial": 1,
#   },
#   {
#       "doctype": "{doctype_2}",
#       "filter_by": "{filter_by}",
#       "partial": 1,
#   },
#   {
#       "doctype": "{doctype_3}",
#       "strict": False,
#   },
#   {
#       "doctype": "{doctype_4}"
#   }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#   "prime.auth.validate"
# ]
