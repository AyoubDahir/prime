import frappe
from frappe.utils import today, get_first_day, get_last_day, add_months, flt
import calendar


@frappe.whitelist()
def get_stats():
    td = today()
    first_this = str(get_first_day(td))
    first_last = str(get_first_day(add_months(td, -1)))
    last_last   = str(get_last_day(add_months(td, -1)))

    def scalar(sql, values=None):
        r = frappe.db.sql(sql, values) if values else frappe.db.sql(sql)
        return flt(r[0][0]) if r else 0

    def q(sql, values=None):
        return frappe.db.sql(sql, values, as_dict=True) if values else frappe.db.sql(sql, as_dict=True)

    revenue_this_month   = scalar("SELECT COALESCE(SUM(grand_total),0) FROM `tabSales Invoice` WHERE posting_date>=%s AND docstatus=1", (first_this,))
    collected_this_month = scalar("SELECT COALESCE(SUM(grand_total-outstanding_amount),0) FROM `tabSales Invoice` WHERE posting_date>=%s AND docstatus=1", (first_this,))
    revenue_last_month   = scalar("SELECT COALESCE(SUM(grand_total),0) FROM `tabSales Invoice` WHERE posting_date BETWEEN %s AND %s AND docstatus=1", (first_last, last_last))
    total_outstanding    = scalar("SELECT COALESCE(SUM(outstanding_amount),0) FROM `tabSales Invoice` WHERE outstanding_amount>0 AND docstatus=1")
    total_invoices       = scalar("SELECT COUNT(*) FROM `tabSales Invoice` WHERE posting_date>=%s AND docstatus=1", (first_this,))
    paid_invoices        = scalar("SELECT COUNT(*) FROM `tabSales Invoice` WHERE posting_date>=%s AND docstatus=1 AND outstanding_amount=0", (first_this,))

    collection_rate = flt((collected_this_month / revenue_this_month * 100) if revenue_this_month else 0, 1)
    growth          = flt(((revenue_this_month - revenue_last_month) / revenue_last_month * 100) if revenue_last_month else 0, 1)

    # 6-month trend — no % chars
    monthly_raw = frappe.db.sql(
        "SELECT YEAR(posting_date) AS yr, MONTH(posting_date) AS mo,"
        " COALESCE(SUM(grand_total),0) AS value,"
        " COALESCE(SUM(grand_total-outstanding_amount),0) AS collected"
        " FROM `tabSales Invoice`"
        " WHERE docstatus=1 AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)"
        " GROUP BY YEAR(posting_date), MONTH(posting_date)"
        " ORDER BY YEAR(posting_date), MONTH(posting_date)",
        as_dict=True
    )
    monthly = [{"label": calendar.month_abbr[int(r.mo)] + " " + str(r.yr), "value": r.value, "collected": r.collected} for r in monthly_raw]

    insurance_split = q(
        "SELECT CASE WHEN is_insurance=1 THEN 'Insurance' ELSE 'Direct Pay' END AS label,"
        " COALESCE(SUM(grand_total),0) AS value"
        " FROM `tabSales Invoice` WHERE posting_date>=%s AND docstatus=1 GROUP BY is_insurance",
        (first_this,)
    )

    mode_split = q(
        "SELECT COALESCE(mode_of_payment,'Unknown') AS label, COUNT(*) AS value"
        " FROM `tabQue`"
        " WHERE date>=%s AND mode_of_payment IS NOT NULL AND mode_of_payment!=''"
        " GROUP BY mode_of_payment ORDER BY value DESC",
        (first_this,)
    )

    top_services = q(
        "SELECT item_name AS service, COALESCE(SUM(amount),0) AS revenue, COUNT(*) AS qty"
        " FROM `tabSales Invoice Item`"
        " WHERE parent IN (SELECT name FROM `tabSales Invoice` WHERE posting_date>=%s AND docstatus=1)"
        " GROUP BY item_name ORDER BY revenue DESC LIMIT 8",
        (first_this,)
    )

    return {
        "kpis": {
            "revenue_this_month":   revenue_this_month,
            "collected_this_month": collected_this_month,
            "revenue_last_month":   revenue_last_month,
            "total_outstanding":    total_outstanding,
            "collection_rate":      collection_rate,
            "growth":               growth,
            "total_invoices":       int(total_invoices),
            "paid_invoices":        int(paid_invoices),
        },
        "monthly":          monthly,
        "insurance_split":  insurance_split,
        "mode_split":       mode_split,
        "top_services":     top_services,
    }
