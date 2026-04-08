import frappe
from frappe.utils import today, get_first_day, flt


@frappe.whitelist()
def get_stats():
    td = today()
    first_day = str(get_first_day(td))

    def q(sql, *args):
        return frappe.db.sql(sql, args or None, as_dict=True)

    def scalar(sql, *args):
        r = frappe.db.sql(sql, args or None)
        return flt(r[0][0]) if r else 0

    # ── KPIs ──────────────────────────────────────────────────────────────────
    patients_today = scalar(
        "SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date=%s AND status!='Cancelled'", td)
    patients_month = scalar(
        "SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date>=%s AND status!='Cancelled'", first_day)
    revenue_today = scalar(
        "SELECT COALESCE(SUM(grand_total),0) FROM `tabSales Invoice` WHERE DATE(posting_date)=%s AND docstatus=1", td)
    revenue_month = scalar(
        "SELECT COALESCE(SUM(grand_total),0) FROM `tabSales Invoice` WHERE posting_date>=%s AND docstatus=1", first_day)
    pending_invoices = scalar(
        "SELECT COUNT(*) FROM `tabSales Invoice` WHERE outstanding_amount>0 AND docstatus=1")
    outstanding_amount = scalar(
        "SELECT COALESCE(SUM(outstanding_amount),0) FROM `tabSales Invoice` WHERE outstanding_amount>0 AND docstatus=1")
    queue_active = scalar(
        "SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND status NOT IN ('Completed','Cancelled')", td)
    new_patients = scalar(
        "SELECT COUNT(*) FROM `tabPatient` WHERE DATE(creation)=%s", td)

    # ── Monthly revenue (last 6 months) ──────────────────────────────────────
    monthly_raw = frappe.db.sql("""
        SELECT YEAR(posting_date) AS yr, MONTH(posting_date) AS mo,
               COALESCE(SUM(grand_total),0) AS value
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY YEAR(posting_date), MONTH(posting_date)
        ORDER BY YEAR(posting_date), MONTH(posting_date)
    """, as_dict=True)
    import calendar
    monthly = [{"label": calendar.month_abbr[int(r.mo)] + " " + str(r.yr), "value": r.value} for r in monthly_raw]

    # ── Appointments by department today ─────────────────────────────────────
    by_dept = q("""
        SELECT COALESCE(department,'General') AS label, COUNT(*) AS value
        FROM `tabPatient Appointment`
        WHERE appointment_date=%s AND status!='Cancelled'
        GROUP BY department
        ORDER BY value DESC LIMIT 8
    """, td)

    # ── Top doctors this month ────────────────────────────────────────────────
    top_doctors = q("""
        SELECT practitioner_name AS doctor, COUNT(*) AS patients,
               SUM(CASE WHEN status='Closed' THEN 1 ELSE 0 END) AS seen
        FROM `tabPatient Appointment`
        WHERE appointment_date>=%s AND status!='Cancelled'
        GROUP BY practitioner
        ORDER BY patients DESC LIMIT 6
    """, first_day)

    # ── Queue by status today ─────────────────────────────────────────────────
    queue_status = q("""
        SELECT COALESCE(status,'Unknown') AS label, COUNT(*) AS value
        FROM `tabQue` WHERE date=%s
        GROUP BY status
    """, td)

    return {
        "kpis": {
            "patients_today": int(patients_today),
            "patients_month": int(patients_month),
            "revenue_today": revenue_today,
            "revenue_month": revenue_month,
            "pending_invoices": int(pending_invoices),
            "outstanding_amount": outstanding_amount,
            "queue_active": int(queue_active),
            "new_patients": int(new_patients),
        },
        "monthly_revenue": monthly,
        "by_department": by_dept,
        "top_doctors": top_doctors,
        "queue_status": queue_status,
    }
