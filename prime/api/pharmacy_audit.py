
import frappe
from frappe import _

def log_stock_entry(doc, method):
    """
    Log Stock Reconciliations and Stock Entries where stock is being adjusted.
    """
    try:
        # Only log Stock Reconciliation or Stock Entry (Material Receipt/Issue)
        if doc.doctype == "Stock Reconciliation" or (doc.doctype == "Stock Entry" and doc.purpose in ["Material Receipt", "Material Issue"]):
            
            # Simple check: logs any submitted stock entry of these types
            audit_log = frappe.new_doc("Financial Audit Log")
            audit_log.event_type = "Stock Adjustment"
            audit_log.amount_involved = doc.total_amount if hasattr(doc, 'total_amount') else 0
            audit_log.reason = f"Stock Adjustment via {doc.doctype}: {doc.purpose if hasattr(doc, 'purpose') else 'Reconciliation'}"
            
            details = {
                "user": frappe.session.user,
                "entry_id": doc.name,
                "purpose": doc.purpose if hasattr(doc, 'purpose') else "Reconciliation",
                "items": []
            }

            for item in doc.items:
                details["items"].append({
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "valuation_rate": item.valuation_rate,
                    "amount": item.amount
                })
            
            audit_log.details = frappe.as_json(details)
            audit_log.insert(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(f"Failed to log Stock Audit: {str(e)}", "Pharmacy Audit Error")

def log_item_price_change(doc, method):
    """
    Log changes to Item Price.
    """
    try:
        # Check if price has changed (using get_doc_before_save usually, but hooks pass 'method' not context)
        # For 'on_update', doc is the current state. We can compare with DB.
        
        # NOTE: db_value might be None if it's a new record
        old_price_list_rate = frappe.db.get_value("Item Price", doc.name, "price_list_rate")
        
        if old_price_list_rate is not None and float(old_price_list_rate) != float(doc.price_list_rate):
             audit_log = frappe.new_doc("Financial Audit Log")
             audit_log.event_type = "Price Change"
             audit_log.amount_involved = 0 
             audit_log.reason = f"Item Price changed for {doc.item_code} in {doc.price_list}"
             
             audit_log.details = frappe.as_json({
                 "user": frappe.session.user,
                 "item_code": doc.item_code,
                 "price_list": doc.price_list,
                 "old_price": old_price_list_rate,
                 "new_price": doc.price_list_rate
             })
             audit_log.insert(ignore_permissions=True)
             
    except Exception as e:
         frappe.log_error(f"Failed to log Price Audit: {str(e)}", "Pharmacy Audit Error")
