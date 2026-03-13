
import frappe
from frappe.model import workflow
import sys

print("Original get_workflow_safe_globals:", workflow.get_workflow_safe_globals)

try:
    import prime.monkey_patches.workflow
    print("Imported prime.monkey_patches.workflow")
except Exception as e:
    print(f"Error importing monkey patch: {e}")

print("Current get_workflow_safe_globals:", workflow.get_workflow_safe_globals)

safe_globals = workflow.get_workflow_safe_globals()
if "get_allowed_discount" in safe_globals:
    print("SUCCESS: get_allowed_discount is in globals.")
else:
    print("FAILURE: get_allowed_discount is NOT in globals.")
