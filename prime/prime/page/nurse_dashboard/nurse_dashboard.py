import frappe
from frappe.utils import today, flt


@frappe.whitelist()
def get_stats():
    td = today()

    def scalar(sql, *args):
        r = frappe.db.sql(sql, args or None)
        return flt(r[0][0]) if r else 0

    def q(sql, *args):
        return frappe.db.sql(sql, args or None, as_dict=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    queue_waiting = scalar(
        "SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND status='Waiting'", td)
    queue_called = scalar(
        "SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND status='Called'", td)
    queue_completed = scalar(
        "SELECT COUNT(*) FROM `tabQue` WHERE date=%s AND status='Completed'", td)
    queue_total = scalar(
        "SELECT COUNT(*) FROM `tabQue` WHERE date=%s", td)

    vitals_today = scalar(
        "SELECT COUNT(*) FROM `tabVital Signs` WHERE DATE(creation)=%s AND docstatus!=2", td)
    lab_samples_today = scalar(
        "SELECT COUNT(*) FROM `tabSample Collection` WHERE DATE(creation)=%s", td)
    appointments_today = scalar(
        "SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date=%s AND status!='Cancelled'", td)
    appointments_seen = scalar(
        "SELECT COUNT(*) FROM `tabPatient Appointment` WHERE appointment_date=%s AND status='Closed'", td)

    # ── Live queue list ────────────────────────────────────────────────────────
    live_queue = q("""
        SELECT token_no, patient_name, practitioner_name, department,
               COALESCE(status,'Waiting') AS status, time
        FROM `tabQue`
        WHERE date=%s AND status NOT IN ('Completed','Cancelled')
        ORDER BY token_no LIMIT 20
    """, td)

    # ── Queue status breakdown ─────────────────────────────────────────────────
    queue_breakdown = q("""
        SELECT COALESCE(status,'Unknown') AS label, COUNT(*) AS value
        FROM `tabQue` WHERE date=%s
        GROUP BY status
    """, td)

    # ── Vitals by hour today ───────────────────────────────────────────────────
    vitals_hourly = q("""
        SELECT CONCAT(LPAD(HOUR(creation),2,'0'),':00') AS label, COUNT(*) AS value
        FROM `tabVital Signs`
        WHERE DATE(creation)=%s AND docstatus!=2
        GROUP BY HOUR(creation)
        ORDER BY HOUR(creation)
    """, td)

    # ── Patients with no vitals yet today ─────────────────────────────────────
    no_vitals = q("""
        SELECT a.patient_name, a.practitioner_name, a.appointment_time
        FROM `tabPatient Appointment` a
        WHERE a.appointment_date=%s AND a.status='Open'
          AND NOT EXISTS (
              SELECT 1 FROM `tabVital Signs` v WHERE v.patient=a.patient AND DATE(v.creation)=%s
          )
        ORDER BY a.appointment_time LIMIT 10
    """, td, td)

    return {
        "kpis": {
            "queue_waiting": int(queue_waiting),
            "queue_called": int(queue_called),
            "queue_completed": int(queue_completed),
            "queue_total": int(queue_total),
            "vitals_today": int(vitals_today),
            "lab_samples_today": int(lab_samples_today),
            "appointments_today": int(appointments_today),
            "appointments_seen": int(appointments_seen),
        },
        "live_queue": live_queue,
        "queue_breakdown": queue_breakdown,
        "vitals_hourly": vitals_hourly,
        "no_vitals": no_vitals,
    }
