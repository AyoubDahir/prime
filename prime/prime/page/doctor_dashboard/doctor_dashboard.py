import frappe
from frappe.utils import today, get_first_day, flt, add_days


@frappe.whitelist()
def get_stats():
    td = today()
    first_day = str(get_first_day(td))
    user = frappe.session.user

    # Find practitioner for current user
    practitioner = frappe.db.get_value("Healthcare Practitioner", {"user": user}, "name")

    def scalar(sql, *args):
        r = frappe.db.sql(sql, args or None)
        return flt(r[0][0]) if r else 0

    def q(sql, *args):
        return frappe.db.sql(sql, args or None, as_dict=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    if practitioner:
        appt_today = scalar(
            "SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date=%s AND practitioner=%s AND status!='Cancelled'",
            td, practitioner)
        seen_today = scalar(
            "SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date=%s AND practitioner=%s AND status='Closed'",
            td, practitioner)
        pending_today = scalar(
            "SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND practitioner=%s AND status NOT IN ('Completed','Cancelled')",
            td, practitioner)
        encounters_today = scalar(
            "SELECT COUNT(*) FROM `tabPatient Encounter` WHERE DATE(creation)=%s AND practitioner=%s",
            td, practitioner)
        lab_pending = scalar(
            "SELECT COUNT(*) FROM `tabLab Test` WHERE DATE(creation)=%s AND practitioner=%s AND status NOT IN ('Completed','Approved')",
            td, practitioner)
        month_patients = scalar(
            "SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date>=%s AND practitioner=%s AND status!='Cancelled'",
            first_day, practitioner)
    else:
        appt_today = seen_today = pending_today = encounters_today = lab_pending = month_patients = 0

    # ── Weekly appointments (last 7 days) ─────────────────────────────────────
    if practitioner:
        weekly_raw = frappe.db.sql("""
            SELECT appointment_date AS day_date, COUNT(*) AS value
            FROM `tabPatient Appointment`
            WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
              AND practitioner=%s AND status!='Cancelled'
            GROUP BY appointment_date ORDER BY appointment_date
        """, (practitioner,), as_dict=True)
        import calendar
        weekly = [{"label": calendar.day_abbr[r.day_date.weekday()] + " " + str(r.day_date.day), "value": r.value} for r in weekly_raw]

        # Patient gender breakdown
        gender_split = q("""
            SELECT p.sex AS label, COUNT(*) AS value
            FROM `tabPatient Appointment` a
            JOIN `tabPatient` p ON p.name=a.patient
            WHERE a.appointment_date>=%s AND a.practitioner=%s AND a.status!='Cancelled'
            GROUP BY p.sex
        """, first_day, practitioner)

        # Recent patients
        recent = q("""
            SELECT patient_name, appointment_date, appointment_time,
                   COALESCE(status,'Open') AS status
            FROM `tabPatient Appointment`
            WHERE appointment_date=%s AND practitioner=%s AND status!='Cancelled'
            ORDER BY appointment_time LIMIT 10
        """, td, practitioner)
    else:
        weekly = []
        gender_split = []
        recent = []

    return {
        "practitioner": practitioner,
        "kpis": {
            "appt_today": int(appt_today),
            "seen_today": int(seen_today),
            "pending_today": int(pending_today),
            "encounters_today": int(encounters_today),
            "lab_pending": int(lab_pending),
            "month_patients": int(month_patients),
        },
        "weekly": weekly,
        "gender_split": gender_split,
        "recent": recent,
    }
