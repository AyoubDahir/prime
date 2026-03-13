import frappe
from frappe.model.document import Document
from frappe.utils import today, get_first_day

class PatientInvoices(Document):
	pass

@frappe.whitelist()
def get_invoices_data(company, customer, from_date=None, to_date=None, ref_practitioner=None):
	"""Returns data for the Item-wise Sales Register report."""

	# Default date range if not provided
	if not from_date:
		from_date = get_first_day(today()).strftime("%Y-%m-%d")
	if not to_date:
		to_date = today()

	# Fetch the Item-wise Sales Register report
	report = frappe.get_doc("Report", "Item-wise Sales Register")
   
	# Define report filters
	report_filters = {
		"company": company,
		"customer": customer,
		"from_date": from_date,
		"to_date": to_date
	}

	# Fetch data from the report using get_data() method
	columns, data = report.get_data(
		limit=500, user="Administrator", filters=report_filters, as_dict=True
	)

	# Filter unpaid invoices
	total_amount=0
	unpaid_invoices = []
	for invoice in data:
		sales_invoice_name = invoice.get("invoice")  # Assuming the invoice name is in 'invoice' field
		if sales_invoice_name:
			sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
			if sales_invoice and sales_invoice.status != "Paid":
				if not ref_practitioner or sales_invoice.ref_practitioner == ref_practitioner:
					unpaid_invoices.append(invoice)
					total_amount += invoice.amount
				# Fetch the 'ref_practitioner' field from the Sales Invoice document
				invoice['ref_practitioner'] = sales_invoice.ref_practitioner
	# Add serial numbers (optional)
	columns.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
	for i in range(len(unpaid_invoices)):
		unpaid_invoices[i]["idx"] = i + 1
	unpaid_invoices.append({
		"item_code": "Total",
		"amount": total_amount,  # Assuming 'grand_total' is the correct field name
		# "idx": len(unpaid_invoices) + 1  # Serial number for the total row
	})

	# frappe.errprint(unpaid_invoices)
	discount = frappe.db.sql(f'''
	select sum(discount_amount) as discount from `tabSales Invoice` where customer = "{customer}" and posting_date between "{from_date}"  and "{to_date}" and docstatus= 1 
	''', as_dict=1)[0]["discount"]

	return unpaid_invoices, discount

	



@frappe.whitelist()
def get_total_discount(patient):
    # Get all Sales Invoices for the given patient
    invoices = frappe.get_all('Sales Invoice', 
                              filters={'patient': patient, 'docstatus': 1}, 
                              fields=['name', 'discount_amount'])

    # Sum the discount amounts
    total_discount = sum([inv.discount_amount or 0 for inv in invoices])

    return total_discount

# Call this function in your custom method that generates the context for the print format
@frappe.whitelist()
def before_print_format(doc):
    # Get total discount and attach it to the document
    total_discount = get_total_discount(doc.patient)
    doc.total_discount = total_discount


