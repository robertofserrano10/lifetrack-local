import json
import hashlib
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

DB_PATH = "storage/lifetrack.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r["name"] for r in cur.fetchall()]
    return column in cols


def _sum_float(rows, key: str) -> float:
    total = 0.0
    for r in rows:
        v = r[key]
        if v is None:
            continue
        total += float(v)
    return float(total)


def _canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def get_latest_snapshot_by_claim(claim_id: int) -> Optional[Dict[str, Any]]:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, claim_id, snapshot_json, snapshot_hash, created_at
            FROM cms1500_snapshots
            WHERE claim_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (claim_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        payload = json.loads(row["snapshot_json"])
        return {
            "id": row["id"],
            "claim_id": row["claim_id"],
            "snapshot": payload,
            "snapshot_hash": row["snapshot_hash"],
            "created_at": row["created_at"],
        }
    finally:
        conn.close()


def generate_cms1500_snapshot(claim_id: int) -> Dict[str, Any]:
    """
    Genera snapshot inmutable CMS-1500 para un claim y lo persiste con hash.
    REGLA: snapshot NO inventa datos: si faltan, quedan None/'—' en UI.
    """
    conn = _conn()
    try:
        cur = conn.cursor()

        # -------------------------
        # Claim + Patient + Coverage
        # -------------------------
        cur.execute(
            """
            SELECT
                c.*,
                p.first_name AS p_first_name,
                p.last_name AS p_last_name,
                p.date_of_birth AS p_dob,
                p.sex AS p_sex,
                p.marital_status AS p_marital_status,
                p.employment_status AS p_employment_status,
                p.student_status AS p_student_status,

                cov.insurer_name AS cov_insurer_name,
                cov.plan_name AS cov_plan_name,
                cov.insured_id AS cov_insured_id,
                cov.insured_first_name AS cov_insured_first_name,
                cov.insured_last_name AS cov_insured_last_name,
                cov.relationship_to_insured AS cov_relationship_to_insured,
                cov.policy_number AS cov_policy_number,
                cov.group_number AS cov_group_number,
                cov.other_health_plan_11d AS cov_other_health_plan_11d,

                cov.insured_address AS cov_insured_address,
                cov.insured_city AS cov_insured_city,
                cov.insured_state AS cov_insured_state,
                cov.insured_zip AS cov_insured_zip
            FROM claims c
            JOIN patients p ON p.id = c.patient_id
            JOIN coverages cov ON cov.id = c.coverage_id
            WHERE c.id = ?
            """,
            (claim_id,),
        )
        base = cur.fetchone()
        if not base:
            raise ValueError("Claim no existe")

        # -------------------------
        # Provider settings (GLOBAL)
        # -------------------------
        cur.execute(
            """
            SELECT *
            FROM provider_settings
            WHERE active = 1
            ORDER BY id DESC
            LIMIT 1
            """
        )
        ps = cur.fetchone()

        provider = {
            "signature": (ps["signature"] if ps else "Signature on File"),
            "signature_date": (ps["signature_date"] if ps else None),
            "facility": {
                "name": (ps["facility_name"] if ps else None),
                "address": (ps["facility_address"] if ps else None),
                "city": (ps["facility_city"] if ps else None),
                "state": (ps["facility_state"] if ps else None),
                "zip": (ps["facility_zip"] if ps else None),
            },
            "billing": {
                "name": (ps["billing_name"] if ps else None),
                "npi": (ps["billing_npi"] if ps else None),
                "tax_id": (ps["billing_tax_id"] if ps else None),
                "address": (ps["billing_address"] if ps else None),
                "city": (ps["billing_city"] if ps else None),
                "state": (ps["billing_state"] if ps else None),
                "zip": (ps["billing_zip"] if ps else None),
            },
        }

        # -------------------------
        # Services (24A–24J + 20)
        # -------------------------
        cur.execute(
            """
            SELECT *
            FROM services
            WHERE claim_id = ?
            ORDER BY service_date ASC, id ASC
            """,
            (claim_id,),
        )
        service_rows = cur.fetchall()

        # Detect “old vs new” column names (para no romper si cambió algo)
        has_units = _table_has_column(conn, "services", "units")
        has_units_24g = _table_has_column(conn, "services", "units_24g")
        has_charge_amount_24f = _table_has_column(conn, "services", "charge_amount_24f")
        has_diag_pointer_24e = _table_has_column(conn, "services", "diagnosis_pointer_24e")
        has_diagnosis_code = _table_has_column(conn, "services", "diagnosis_code")

        services = []
        for s in service_rows:
            units_val = None
            if has_units_24g:
                units_val = s["units_24g"]
            elif has_units:
                units_val = s["units"]

            charge_val = None
            if has_charge_amount_24f:
                charge_val = s["charge_amount_24f"]

            dx_pointer_val = None
            if has_diag_pointer_24e:
                dx_pointer_val = s["diagnosis_pointer_24e"]

            diagnosis_code_val = None
            if has_diagnosis_code:
                diagnosis_code_val = s["diagnosis_code"]

            services.append(
                {
                    "id": s["id"],
                    "service_date": s["service_date"],
                    "place_of_service_24b": (s["place_of_service_24b"] if "place_of_service_24b" in s.keys() else None),
                    "emergency_24c": (s["emergency_24c"] if "emergency_24c" in s.keys() else 0),
                    "cpt_code": s["cpt_code"],
                    "modifiers": [
                        (s["modifier1"] if "modifier1" in s.keys() else None),
                        (s["modifier2"] if "modifier2" in s.keys() else None),
                        (s["modifier3"] if "modifier3" in s.keys() else None),
                        (s["modifier4"] if "modifier4" in s.keys() else None),
                    ],
                    "dx_pointer": dx_pointer_val,
                    "diagnosis_code": diagnosis_code_val,  # si existe, lo guardamos
                    "charge_amount_24f": charge_val,
                    "units": units_val,
                    "epsdt_24h": (s["epsdt_24h"] if "epsdt_24h" in s.keys() else None),
                    "id_qualifier_24i": (s["id_qualifier_24i"] if "id_qualifier_24i" in s.keys() else None),
                    "rendering_npi_24j": (s["rendering_npi_24j"] if "rendering_npi_24j" in s.keys() else None),
                    # Box 20 (service-level)
                    "outside_lab_20": bool(s["outside_lab_20"]) if "outside_lab_20" in s.keys() else False,
                    "lab_charges_20": (s["lab_charges_20"] if "lab_charges_20" in s.keys() else None),
                }
            )

        # -------------------------
        # Diagnoses (21 A–L)
        # Regla: NO inventar. Si no hay diagnóstico extra, quedan None.
        # Preferimos:
        # 1) columnas claim-level (si existen) diagnosis_21a... (si algún día las agregas)
        # 2) fallback: primer diagnosis_code disponible en services (si existe)
        # -------------------------
        diagnoses = {k: None for k in list("ABCDEFGHIJKL")}

        # claim-level optional columns (si existen)
        for idx, letter in enumerate("ABCDEFGHIJKL", start=1):
            col = f"diagnosis_{idx}"
            if _table_has_column(conn, "claims", col):
                val = base[col]
                diagnoses[letter] = val

        # fallback mínimo: si no hay ninguna diagnosis y services tiene diagnosis_code, usar la primera
        if all(v is None for v in diagnoses.values()) and has_diagnosis_code:
            for s in service_rows:
                if s["diagnosis_code"]:
                    diagnoses["A"] = s["diagnosis_code"]
                    break

        # -------------------------
        # Totals 28–30 (finanzas)
        # total_charge = SUM(charges.amount) si existe; si no, SUM(services.charge_amount_24f)
        # amount_paid  = SUM(applications.amount_applied)
        # adjustments  = SUM(adjustments.amount)
        # balance_due  = total_charge - amount_paid - adjustments
        # -------------------------
        cur.execute(
            """
            SELECT amount
            FROM charges
            WHERE service_id IN (SELECT id FROM services WHERE claim_id = ?)
            """,
            (claim_id,),
        )
        charge_rows = cur.fetchall()
        if charge_rows:
            total_charge = _sum_float(charge_rows, "amount")
        else:
            total_charge = 0.0
            for s in services:
                if s.get("charge_amount_24f") is not None:
                    total_charge += float(s["charge_amount_24f"])

        cur.execute(
            """
            SELECT amount_applied
            FROM applications
            WHERE charge_id IN (SELECT id FROM charges WHERE service_id IN (SELECT id FROM services WHERE claim_id = ?))
            """,
            (claim_id,),
        )
        app_rows = cur.fetchall()
        amount_paid = _sum_float(app_rows, "amount_applied")

        cur.execute(
            """
            SELECT amount
            FROM adjustments
            WHERE charge_id IN (SELECT id FROM charges WHERE service_id IN (SELECT id FROM services WHERE claim_id = ?))
            """,
            (claim_id,),
        )
        adj_rows = cur.fetchall()
        adjustments_total = _sum_float(adj_rows, "amount")

        balance_due = float(total_charge - amount_paid - adjustments_total)

        totals = {
            "total_charge": float(round(total_charge, 2)),
            "amount_paid": float(round(amount_paid, 2)),
            "adjustments": float(round(adjustments_total, 2)),
            "balance_due": float(round(balance_due, 2)),
        }

        # -------------------------
        # Snapshot object (1–33)
        # -------------------------
        insured_name = " ".join(
            [
                (base["cov_insured_first_name"] or "").strip(),
                (base["cov_insured_last_name"] or "").strip(),
            ]
        ).strip() or None

        snapshot = {
            "meta": {
                "claim_id": base["id"],
                "created_at": datetime.utcnow().isoformat(),
                "version": "B1",
            },
            "claim": {
                "id": base["id"],
                "patient_id": base["patient_id"],
                "coverage_id": base["coverage_id"],
                "claim_number": base["claim_number"],
                "status": base["status"],
                # 10, 14–23, 26, 27 (claim-level)
                "related_employment_10a": base["related_employment_10a"] if "related_employment_10a" in base.keys() else 0,
                "related_auto_10b": base["related_auto_10b"] if "related_auto_10b" in base.keys() else 0,
                "related_other_10c": base["related_other_10c"] if "related_other_10c" in base.keys() else 0,
                "related_state_10d": base["related_state_10d"] if "related_state_10d" in base.keys() else None,
                "date_current_illness_14": base["date_current_illness_14"] if "date_current_illness_14" in base.keys() else None,
                "other_date_15": base["other_date_15"] if "other_date_15" in base.keys() else None,
                "unable_work_from_16": base["unable_work_from_16"] if "unable_work_from_16" in base.keys() else None,
                "unable_work_to_16": base["unable_work_to_16"] if "unable_work_to_16" in base.keys() else None,
                "referring_provider_name_17": base["referring_provider_name"] if "referring_provider_name" in base.keys() else None,
                "referring_provider_npi_17": base["referring_provider_npi"] if "referring_provider_npi" in base.keys() else None,
                "hosp_from_18": base["hosp_from_18"] if "hosp_from_18" in base.keys() else None,
                "hosp_to_18": base["hosp_to_18"] if "hosp_to_18" in base.keys() else None,
                "reserved_local_use_19": base["reserved_local_use_19"] if "reserved_local_use_19" in base.keys() else None,
                "resubmission_code_22": base["resubmission_code_22"] if "resubmission_code_22" in base.keys() else None,
                "original_ref_no_22": base["original_ref_no_22"] if "original_ref_no_22" in base.keys() else None,
                "prior_authorization_23": base["prior_authorization_23"] if "prior_authorization_23" in base.keys() else None,
                "patient_account_no_26": base["patient_account_no_26"] if "patient_account_no_26" in base.keys() else None,
                "accept_assignment_27": base["accept_assignment_27"] if "accept_assignment_27" in base.keys() else 1,
            },
            "patient": {
                "first_name": base["p_first_name"],
                "last_name": base["p_last_name"],
                "date_of_birth": base["p_dob"],
                "sex": base["p_sex"],
                "marital_status": base["p_marital_status"],
                "employment_status": base["p_employment_status"],
                "student_status": base["p_student_status"],
            },
            "insurance": {
                "insurer_name": base["cov_insurer_name"],
                "plan_name": base["cov_plan_name"],
                "insured_id": base["cov_insured_id"],
                "insured_name": insured_name,
                "relationship_to_insured": base["cov_relationship_to_insured"],
                "policy_number": base["cov_policy_number"],
                "group_number": base["cov_group_number"],
                "other_health_plan_11d": base["cov_other_health_plan_11d"],
                "insured_address": {
                    "address": base["cov_insured_address"],
                    "city": base["cov_insured_city"],
                    "state": base["cov_insured_state"],
                    "zip": base["cov_insured_zip"],
                },
            },
            "diagnoses": diagnoses,   # 21 A–L
            "services": services,     # 24A–24J + 20
            "totals": totals,         # 28–30 (+ adjustments)
            "provider": provider,     # 31–33
        }

        snapshot_json = _canonical_json(snapshot)
        snapshot_hash = _sha256(snapshot_json)

        cur.execute(
            """
            INSERT INTO cms1500_snapshots (claim_id, snapshot_json, snapshot_hash)
            VALUES (?, ?, ?)
            """,
            (claim_id, snapshot_json, snapshot_hash),
        )
        conn.commit()

        return {"snapshot": snapshot, "snapshot_hash": snapshot_hash}
    finally:
        conn.close()
# ============================================================
# FASE G29 — Snapshot Index / Listing Layer (READ-ONLY)
# ============================================================

def list_snapshots_admin() -> list[dict]:
    """
    Lista administrativa de snapshots.
    Solo lectura. No recalcula nada.
    """

    conn = _conn()
    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                s.id AS snapshot_id,
                s.claim_id,
                s.snapshot_hash,
                s.created_at,
                c.status AS claim_status
            FROM cms1500_snapshots s
            JOIN claims c ON c.id = s.claim_id
            ORDER BY s.id DESC
            """
        )

        rows = cur.fetchall()

        result = []
        for r in rows:
            result.append(
                {
                    "snapshot_id": r["snapshot_id"],
                    "claim_id": r["claim_id"],
                    "snapshot_hash": r["snapshot_hash"],
                    "created_at": r["created_at"],
                    "claim_status": r["claim_status"],
                    "locked": True,
                }
            )

        return result

    finally:
        conn.close()

# ============================================================
# FASE G31 — Snapshot Detail (READ-ONLY)
# ============================================================

def get_snapshot_by_id(snapshot_id: int) -> Optional[Dict[str, Any]]:
    """
    Devuelve snapshot específico por ID.
    Solo lectura.
    No recalcula nada.
    """

    conn = _conn()
    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, claim_id, snapshot_json, snapshot_hash, created_at
            FROM cms1500_snapshots
            WHERE id = ?
            """,
            (snapshot_id,),
        )

        row = cur.fetchone()
        if not row:
            return None

        payload = json.loads(row["snapshot_json"])

        return {
            "id": row["id"],
            "claim_id": row["claim_id"],
            "snapshot": payload,
            "snapshot_hash": row["snapshot_hash"],
            "created_at": row["created_at"],
            "locked": True,
        }

    finally:
        conn.close()
