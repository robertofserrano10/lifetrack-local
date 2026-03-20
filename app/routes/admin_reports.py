from flask import Blueprint, render_template, request
import sqlite3
from datetime import date
from app.config import DB_PATH
from app.security.auth import login_required, role_required


reports_admin_bp = Blueprint(
    "reports_admin",
    __name__,
    url_prefix="/admin/reports",
)

MESES = {
    "01": "Enero", "02": "Febrero", "03": "Marzo",
    "04": "Abril", "05": "Mayo", "06": "Junio",
    "07": "Julio", "08": "Agosto", "09": "Septiembre",
    "10": "Octubre", "11": "Noviembre", "12": "Diciembre",
}


@reports_admin_bp.route("/")
@login_required
@role_required("ADMIN", "FACTURADOR")
def reports_dashboard():
    today = date.today()
    default_desde = today.replace(month=1, day=1).isoformat()
    default_hasta = today.isoformat()

    desde = request.args.get("desde", default_desde)
    hasta = request.args.get("hasta", default_hasta)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ================================================================
    # REPORTE 1: Reclamaciones por período — facturado vs cobrado
    # Filter: service_date BETWEEN desde AND hasta
    # Two separate queries to avoid double-counting when a charge
    # has multiple payment applications.
    # ================================================================
    cur.execute("""
        SELECT
            strftime('%Y-%m', s.service_date) AS periodo,
            COUNT(DISTINCT cl.id)             AS num_claims,
            COALESCE(SUM(ch.amount), 0)       AS total_facturado
        FROM claims cl
        JOIN services s  ON s.claim_id      = cl.id
        JOIN charges  ch ON ch.service_id   = s.id
        WHERE s.service_date IS NOT NULL
          AND s.service_date BETWEEN ? AND ?
        GROUP BY periodo
        ORDER BY periodo DESC
    """, (desde, hasta))
    billed_by_period = {r["periodo"]: dict(r) for r in cur.fetchall()}

    cur.execute("""
        SELECT
            strftime('%Y-%m', s.service_date)   AS periodo,
            COALESCE(SUM(a.amount_applied), 0)  AS total_cobrado
        FROM services      s
        JOIN charges       ch ON ch.service_id  = s.id
        JOIN applications  a  ON a.charge_id    = ch.id
        WHERE s.service_date IS NOT NULL
          AND s.service_date BETWEEN ? AND ?
        GROUP BY periodo
    """, (desde, hasta))
    for row in cur.fetchall():
        p = row["periodo"]
        if p in billed_by_period:
            billed_by_period[p]["total_cobrado"] = row["total_cobrado"]
        else:
            billed_by_period[p] = {
                "periodo": p,
                "num_claims": 0,
                "total_facturado": 0.0,
                "total_cobrado": row["total_cobrado"],
            }

    claims_by_period = sorted(billed_by_period.values(),
                              key=lambda x: x["periodo"], reverse=True)
    for r in claims_by_period:
        r.setdefault("total_cobrado", 0.0)
        r["balance"] = r["total_facturado"] - r["total_cobrado"]
        try:
            yr, mo = r["periodo"].split("-")
            r["periodo_label"] = f"{MESES.get(mo, mo)} {yr}"
        except Exception:
            r["periodo_label"] = r["periodo"]

    period_totals = {
        "num_claims":      sum(r["num_claims"]      for r in claims_by_period),
        "total_facturado": sum(r["total_facturado"] for r in claims_by_period),
        "total_cobrado":   sum(r["total_cobrado"]   for r in claims_by_period),
        "balance":         sum(r["balance"]         for r in claims_by_period),
    }

    # ================================================================
    # REPORTE 2: Reclamaciones pendientes por aseguradora
    # Shows submitted/denied claims where balance > 0.
    # Subqueries aggregate per claim to prevent duplicate row counts.
    # ================================================================
    cur.execute("""
        SELECT
            cov.insurer_name                                              AS aseguradora,
            COUNT(DISTINCT cl.id)                                         AS num_claims,
            COALESCE(SUM(billed.amount), 0)                               AS total_facturado,
            COALESCE(SUM(paid.amount),   0)                               AS total_cobrado,
            COALESCE(SUM(billed.amount), 0) - COALESCE(SUM(paid.amount), 0) AS balance_pendiente
        FROM claims cl
        JOIN coverages cov ON cov.id = cl.coverage_id
        LEFT JOIN (
            SELECT s.claim_id, SUM(ch.amount) AS amount
            FROM services s JOIN charges ch ON ch.service_id = s.id
            GROUP BY s.claim_id
        ) billed ON billed.claim_id = cl.id
        LEFT JOIN (
            SELECT s.claim_id, COALESCE(SUM(a.amount_applied), 0) AS amount
            FROM services     s
            JOIN charges      ch ON ch.service_id = s.id
            JOIN applications a  ON a.charge_id   = ch.id
            GROUP BY s.claim_id
        ) paid ON paid.claim_id = cl.id
        WHERE cl.status NOT IN ('DRAFT')
        GROUP BY cov.insurer_name
        HAVING (COALESCE(SUM(billed.amount), 0) - COALESCE(SUM(paid.amount), 0)) > 0.005
        ORDER BY balance_pendiente DESC
    """)
    pending_by_insurer = [dict(r) for r in cur.fetchall()]

    # ================================================================
    # REPORTE 3: Códigos CPT más utilizados
    # ================================================================
    cur.execute("""
        SELECT
            s.cpt_code,
            COUNT(*)                        AS frecuencia,
            SUM(s.units_24g)                AS total_unidades,
            COALESCE(SUM(ch.amount), 0)     AS total_facturado
        FROM services s
        LEFT JOIN charges ch ON ch.service_id = s.id
        GROUP BY s.cpt_code
        ORDER BY frecuencia DESC
        LIMIT 20
    """)
    cpt_usage = [dict(r) for r in cur.fetchall()]

    # Max frequency for relative bar rendering in template
    max_frecuencia = cpt_usage[0]["frecuencia"] if cpt_usage else 1

    # ================================================================
    # REPORTE 4: Balance por paciente — pacientes con saldo pendiente
    # ================================================================
    cur.execute("""
        SELECT
            p.id,
            p.last_name || ', ' || p.first_name                              AS paciente,
            COUNT(DISTINCT cl.id)                                             AS num_claims,
            COALESCE(SUM(billed.amount), 0)                                   AS total_facturado,
            COALESCE(SUM(paid.amount),   0)                                   AS total_cobrado,
            COALESCE(SUM(billed.amount), 0) - COALESCE(SUM(paid.amount), 0)  AS balance
        FROM patients p
        JOIN claims cl ON cl.patient_id = p.id
        LEFT JOIN (
            SELECT s.claim_id, SUM(ch.amount) AS amount
            FROM services s JOIN charges ch ON ch.service_id = s.id
            GROUP BY s.claim_id
        ) billed ON billed.claim_id = cl.id
        LEFT JOIN (
            SELECT s.claim_id, COALESCE(SUM(a.amount_applied), 0) AS amount
            FROM services     s
            JOIN charges      ch ON ch.service_id = s.id
            JOIN applications a  ON a.charge_id   = ch.id
            GROUP BY s.claim_id
        ) paid ON paid.claim_id = cl.id
        GROUP BY p.id, p.last_name, p.first_name
        HAVING (COALESCE(SUM(billed.amount), 0) - COALESCE(SUM(paid.amount), 0)) > 0.005
        ORDER BY balance DESC
    """)
    patient_balances = [dict(r) for r in cur.fetchall()]

    conn.close()

    return render_template(
        "admin/reports_dashboard.html",
        desde=desde,
        hasta=hasta,
        claims_by_period=claims_by_period,
        period_totals=period_totals,
        pending_by_insurer=pending_by_insurer,
        cpt_usage=cpt_usage,
        max_frecuencia=max_frecuencia,
        patient_balances=patient_balances,
    )
