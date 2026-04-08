import frappe
from frappe.utils import today, get_first_day, flt
import calendar


@frappe.whitelist()
def get_stats():
    td = today()
    first_day = str(get_first_day(td))
    user = frappe.session.user

    # user_id is the correct field name in tabHealthcare Practitioner
    practitioner = frappe.db.get_value(
        "Healthcare Practitioner", {"user_id": user}, "name"
    )

    def scalar(sql, values=None):
        r = frappe.db.sql(sql, values) if values else frappe.db.sql(sql)
        return flt(r[0][0]) if r else 0

    def q(sql, values=None):
        return frappe.db.sql(sql, values, as_dict=True) if values else frappe.db.sql(sql, as_dict=True)

    if practitioner:
        appt_today       = scalar("SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date=%s AND practitioner=%s AND status!='Cancelled'", (td, practitioner))
        seen_today       = scalar("SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date=%s AND practitioner=%s AND status='Closed'", (td, practitioner))
        pending_today    = scalar("SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND practitioner=%s AND status NOT IN ('Completed','Cancelled')", (td, practitioner))
        encounters_today = scalar("SELECT COUNT(*) FROM `tabPatient Encounter` WHERE DATE(creation)=%s AND practitioner=%s", (td, practitioner))
        lab_pending      = scalar("SELECT COUNT(*) FROM `tabLab Test` WHERE DATE(creation)=%s AND practitioner=%s AND status NOT IN ('Completed','Approved')", (td, practitioner))
        month_patients   = scalar("SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date>=%s AND practitioner=%s AND status!='Cancelled'", (first_day, practitioner))

        weekly_raw = frappe.db.sql(
            "SELECT appointment_date AS day_date, COUNT(*) AS value"
            " FROM `tabPatient Appointment`"
            " WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
            " AND practitioner=%s AND status!='Cancelled'"
            " GROUP BY appointment_date ORDER BY appointment_date",
            (practitioner,), as_dict=True
        )
        weekly = [{"label": calendar.day_abbr[r.day_date.weekday()] + " " + str(r.day_date.day), "value": r.value} for r in weekly_raw]

        gender_split = q(
            "SELECT p.sex AS label, COUNT(*) AS value"
            " FROM `tabPatient Appointment` a JOIN `tabPatient` p ON p.name=a.patient"
            " WHERE a.appointment_date>=%s AND a.practitioner=%s AND a.status!='Cancelled'"
            " GROUP BY p.sex",
            (first_day, practitioner)
        )
        recent = q(
            "SELECT patient_name, appointment_date, appointment_time, COALESCE(status,'Open') AS status"
            " FROM `tabPatient Appointment`"
            " WHERE appointment_date=%s AND practitioner=%s AND status!='Cancelled'"
            " ORDER BY appointment_time LIMIT 10",
            (td, practitioner)
        )
    else:
        appt_today = seen_today = pending_today = encounters_today = lab_pending = month_patients = 0
        weekly = gender_split = recent = []

    return {
        "practitioner": practitioner,
        "kpis": {
            "appt_today":       int(appt_today),
            "seen_today":       int(seen_today),
            "pending_today":    int(pending_today),
            "encounters_today": int(encounters_today),
            "lab_pending":      int(lab_pending),
            "month_patients":   int(month_patients),
        },
        "weekly":       weekly,
        "gender_split": gender_split,
        "recent":       recent,
    }
