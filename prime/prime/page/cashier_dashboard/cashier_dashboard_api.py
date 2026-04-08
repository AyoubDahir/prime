import frappe
from frappe.utils import today, flt


@frappe.whitelist()
def get_stats():
    td = today()

    def scalar(sql, values=None):
        r = frappe.db.sql(sql, values) if values else frappe.db.sql(sql)
        return flt(r[0][0]) if r else 0

    def q(sql, values=None):
        return frappe.db.sql(sql, values, as_dict=True) if values else frappe.db.sql(sql, as_dict=True)

    invoices_today  = scalar("SELECT COUNT(*) FROM `tabSales Invoice` WHERE DATE(posting_date)=%s AND docstatus=1", (td,))
    revenue_today   = scalar("SELECT COALESCE(SUM(grand_total),0) FROM `tabSales Invoice` WHERE DATE(posting_date)=%s AND docstatus=1", (td,))
    collected_today = scalar("SELECT COALESCE(SUM(paid_amount),0) FROM `tabSales Invoice` WHERE DATE(posting_date)=%s AND docstatus=1", (td,))
    pending_count   = scalar("SELECT COUNT(*) FROM `tabSales Invoice` WHERE outstanding_amount>0 AND docstatus=1")
    pending_amount  = scalar("SELECT COALESCE(SUM(outstanding_amount),0) FROM `tabSales Invoice` WHERE outstanding_amount>0 AND docstatus=1")
    waafi_today     = scalar("SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND mode_of_payment LIKE 'Waafi%'", (td,))
    cash_today      = scalar("SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND mode_of_payment LIKE 'Cash%'", (td,))
    free_today      = scalar("SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND is_free=1", (td,))

    hourly = q(
        "SELECT CONCAT(LPAD(HOUR(posting_time),2,'0'),':00') AS label,"
        " COALESCE(SUM(grand_total),0) AS value"
        " FROM `tabSales Invoice`"
        " WHERE DATE(posting_date)=%s AND docstatus=1"
        " GROUP BY HOUR(posting_time) ORDER BY HOUR(posting_time)",
        (td,)
    )

    mode_split = q(
        "SELECT COALESCE(mode_of_payment,'Unknown') AS label, COUNT(*) AS value"
        " FROM `tabQue`"
        " WHERE date=%s AND mode_of_payment IS NOT NULL AND mode_of_payment!=''"
        " GROUP BY mode_of_payment ORDER BY value DESC",
        (td,)
    )

    recent = q(
        "SELECT name, patient_name, grand_total, outstanding_amount,"
        " CASE WHEN outstanding_amount=0 THEN 'Paid' ELSE 'Unpaid' END AS pay_status,"
        " DATE_FORMAT(posting_time,'%%H:%%i') AS time"
        " FROM `tabSales Invoice`"
        " WHERE DATE(posting_date)=%s AND docstatus=1"
        " ORDER BY posting_time DESC LIMIT 12",
        (td,)
    )

    return {
        "kpis": {
            "invoices_today":  int(invoices_today),
            "revenue_today":   revenue_today,
            "collected_today": collected_today,
            "pending_count":   int(pending_count),
            "pending_amount":  pending_amount,
            "waafi_today":     int(waafi_today),
            "cash_today":      int(cash_today),
            "free_today":      int(free_today),
        },
        "hourly":     hourly,
        "mode_split": mode_split,
        "recent":     recent,
    }
