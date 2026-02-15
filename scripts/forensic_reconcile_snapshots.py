# scripts/forensic_reconcile_snapshots.py
# FASE G26A — Forensic reconcile (MODELO A)
# Regla: si existe snapshot, el estado financiero DB debe alinearse al snapshot.
# - Borra events post-snapshot (applications, adjustments, charges) del claim
# - Restaura charges faltantes para igualar snapshot.total_charge (best-effort)
# - NO inventa pagos/adjustments faltantes si snapshot los tiene y DB no

import json
import sqlite3
from typing import Any, Dict, List, Tuple

DB_PATH = "storage/lifetrack.db"


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON;")
    return c


def fetch_latest_snapshot(c: sqlite3.Connection, claim_id: int) -> Dict[str, Any] | None:
    cur = c.cursor()
    cur.execute(
        """
        SELECT id, claim_id, snapshot_json, snapshot_hash, created_at
        FROM cms1500_snapshots
        WHERE claim_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (int(claim_id),),
    )
    r = cur.fetchone()
    if not r:
        return None
    payload = json.loads(r["snapshot_json"])
    return {
        "snapshot_id": int(r["id"]),
        "claim_id": int(r["claim_id"]),
        "created_at": r["created_at"],  # 'YYYY-MM-DD HH:MM:SS' by schema default
        "snapshot_hash": r["snapshot_hash"],
        "snapshot": payload,
    }


def db_totals(c: sqlite3.Connection, claim_id: int) -> Dict[str, float]:
    cur = c.cursor()

    cur.execute(
        """
        SELECT COALESCE(SUM(ch.amount), 0) AS total_charge
        FROM charges ch
        JOIN services s ON s.id = ch.service_id
        WHERE s.claim_id = ?
        """,
        (int(claim_id),),
    )
    total_charge = float(cur.fetchone()["total_charge"])

    cur.execute(
        """
        SELECT COALESCE(SUM(a.amount_applied), 0) AS total_applied
        FROM applications a
        JOIN charges ch ON ch.id = a.charge_id
        JOIN services s ON s.id = ch.service_id
        WHERE s.claim_id = ?
        """,
        (int(claim_id),),
    )
    total_applied = float(cur.fetchone()["total_applied"])

    cur.execute(
        """
        SELECT COALESCE(SUM(ad.amount), 0) AS total_adjustments
        FROM adjustments ad
        JOIN charges ch ON ch.id = ad.charge_id
        JOIN services s ON s.id = ch.service_id
        WHERE s.claim_id = ?
        """,
        (int(claim_id),),
    )
    total_adjustments = float(cur.fetchone()["total_adjustments"])

    balance_due = float(total_charge - total_applied - total_adjustments)

    return {
        "total_charge": round(total_charge, 2),
        "total_applied": round(total_applied, 2),
        "total_adjustments": round(total_adjustments, 2),
        "balance_due": round(balance_due, 2),
    }


def snapshot_totals(snapshot: Dict[str, Any]) -> Dict[str, float]:
    t = snapshot.get("totals") or {}
    total_charge = float(t.get("total_charge") or 0.0)
    total_applied = float(t.get("amount_paid") or 0.0)
    total_adjustments = float(t.get("adjustments") or 0.0)
    balance_due = float(t.get("balance_due") or 0.0)
    return {
        "total_charge": round(total_charge, 2),
        "total_applied": round(total_applied, 2),
        "total_adjustments": round(total_adjustments, 2),
        "balance_due": round(balance_due, 2),
    }


def approx_equal(a: float, b: float, tol: float = 0.01) -> bool:
    return abs(float(a) - float(b)) <= tol


def find_mismatched_claims(c: sqlite3.Connection) -> List[Tuple[int, Dict[str, Any], Dict[str, float], Dict[str, float]]]:
    cur = c.cursor()
    cur.execute("SELECT DISTINCT claim_id FROM cms1500_snapshots ORDER BY claim_id")
    claim_ids = [int(r["claim_id"]) for r in cur.fetchall()]

    mismatches = []
    for cid in claim_ids:
        latest = fetch_latest_snapshot(c, cid)
        if not latest:
            continue
        snap = latest["snapshot"]
        st = snapshot_totals(snap)
        dt = db_totals(c, cid)

        ok = (
            approx_equal(st["total_charge"], dt["total_charge"])
            and approx_equal(st["total_applied"], dt["total_applied"])
            and approx_equal(st["total_adjustments"], dt["total_adjustments"])
            and approx_equal(st["balance_due"], dt["balance_due"])
        )
        if not ok:
            mismatches.append((cid, latest, st, dt))

    return mismatches


def delete_post_snapshot_events(c: sqlite3.Connection, claim_id: int, snap_created_at: str) -> Dict[str, int]:
    """
    Modelo A: no puede haber mutación financiera post-snapshot.
    Se eliminan:
    - applications creadas después del snapshot (por charges del claim)
    - adjustments creados después del snapshot (por charges del claim)
    - charges creados después del snapshot (por services del claim)
    """
    cur = c.cursor()

    # charges del claim
    cur.execute(
        """
        SELECT ch.id AS charge_id
        FROM charges ch
        JOIN services s ON s.id = ch.service_id
        WHERE s.claim_id = ?
        """,
        (int(claim_id),),
    )
    charge_ids = [int(r["charge_id"]) for r in cur.fetchall()]
    if not charge_ids:
        charge_ids = []

    deleted_apps = 0
    deleted_adjs = 0
    deleted_charges = 0

    # Delete post-snapshot applications for claim charges
    if charge_ids:
        q_marks = ",".join(["?"] * len(charge_ids))
        cur.execute(
            f"""
            DELETE FROM applications
            WHERE charge_id IN ({q_marks})
              AND datetime(created_at) > datetime(?)
            """,
            (*charge_ids, snap_created_at),
        )
        deleted_apps = cur.rowcount

        cur.execute(
            f"""
            DELETE FROM adjustments
            WHERE charge_id IN ({q_marks})
              AND datetime(created_at) > datetime(?)
            """,
            (*charge_ids, snap_created_at),
        )
        deleted_adjs = cur.rowcount

    # Delete post-snapshot charges (and any dependent rows if FK is not enforced)
    cur.execute(
        """
        SELECT ch.id AS charge_id
        FROM charges ch
        JOIN services s ON s.id = ch.service_id
        WHERE s.claim_id = ?
          AND datetime(ch.created_at) > datetime(?)
        """,
        (int(claim_id), snap_created_at),
    )
    post_charge_ids = [int(r["charge_id"]) for r in cur.fetchall()]
    if post_charge_ids:
        q_marks2 = ",".join(["?"] * len(post_charge_ids))

        # defensive: delete children first (in case FK not enforced somewhere)
        cur.execute(f"DELETE FROM applications WHERE charge_id IN ({q_marks2})", (*post_charge_ids,))
        deleted_apps += cur.rowcount

        cur.execute(f"DELETE FROM adjustments WHERE charge_id IN ({q_marks2})", (*post_charge_ids,))
        deleted_adjs += cur.rowcount

        cur.execute(f"DELETE FROM charges WHERE id IN ({q_marks2})", (*post_charge_ids,))
        deleted_charges = cur.rowcount

    return {
        "deleted_applications": deleted_apps,
        "deleted_adjustments": deleted_adjs,
        "deleted_charges": deleted_charges,
    }


def ensure_charge_totals_match_snapshot(c: sqlite3.Connection, claim_id: int, snap_created_at: str, snap: Dict[str, Any]) -> Dict[str, Any]:
    """
    Restaura charges faltantes para que SUM(charges.amount) == snapshot.totals.total_charge.
    Best-effort:
    - Si snapshot.services tiene charge_amount_24f > 0, se usa como target por service.
    - Si no, se asigna el delta al primer service existente del claim.
    """
    cur = c.cursor()

    st = snapshot_totals(snap)
    target_total_charge = float(st["total_charge"])

    # Recalcular DB después de borrados
    dt = db_totals(c, claim_id)
    current_total_charge = float(dt["total_charge"])

    delta = round(target_total_charge - current_total_charge, 2)
    if approx_equal(delta, 0.0):
        return {"restored": False, "inserted_charges": 0, "delta": 0.0}

    if delta < 0:
        # DB tiene más charge que snapshot (debería haberse eliminado arriba si era post-snapshot)
        # No adivinamos cuál borrar si es pre-snapshot.
        raise ValueError(
            f"Claim {claim_id}: DB total_charge ({current_total_charge}) > snapshot ({target_total_charge}). "
            "No se borra data pre-snapshot automáticamente."
        )

    # Map service targets desde snapshot si existen
    snap_services = snap.get("services") or []
    service_ids_in_snap = [int(s["id"]) for s in snap_services if s.get("id") is not None]

    # Filtrar a services que existen hoy en DB
    existing_service_ids: List[int] = []
    if service_ids_in_snap:
        q = ",".join(["?"] * len(service_ids_in_snap))
        cur.execute(f"SELECT id FROM services WHERE id IN ({q}) AND claim_id = ?", (*service_ids_in_snap, int(claim_id)))
        existing_service_ids = [int(r["id"]) for r in cur.fetchall()]

    if not existing_service_ids:
        # fallback: cualquier service del claim
        cur.execute("SELECT id FROM services WHERE claim_id = ? ORDER BY id LIMIT 1", (int(claim_id),))
        r = cur.fetchone()
        if not r:
            raise ValueError(f"Claim {claim_id}: no hay services en DB para restaurar charges.")
        existing_service_ids = [int(r["id"])]

    inserted = 0

    # Si hay targets por service, intentamos restaurar hasta alcanzar esos targets.
    targets_by_service: Dict[int, float] = {}
    for s in snap_services:
        sid = s.get("id")
        if sid is None:
            continue
        sid = int(sid)
        if sid not in existing_service_ids:
            continue
        ca = s.get("charge_amount_24f")
        if ca is None:
            continue
        try:
            fca = float(ca)
        except Exception:
            continue
        if fca > 0:
            targets_by_service[sid] = round(fca, 2)

    # Si targets están vacíos, metemos todo el delta en el primer service.
    if not targets_by_service:
        sid = existing_service_ids[0]
        cur.execute(
            """
            INSERT INTO charges (service_id, amount, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (sid, float(delta), snap_created_at, snap_created_at),
        )
        inserted += 1
        return {"restored": True, "inserted_charges": inserted, "delta": float(delta), "mode": "single_service_delta", "service_id": sid}

    # Restaurar por service basado en target - existente
    remaining = float(delta)

    for sid, target in targets_by_service.items():
        if remaining <= 0:
            break

        cur.execute("SELECT COALESCE(SUM(amount),0) AS s FROM charges WHERE service_id = ?", (int(sid),))
        existing_sum = float(cur.fetchone()["s"])
        needed = round(target - existing_sum, 2)

        if needed <= 0:
            continue

        to_insert = needed if needed <= remaining else remaining
        to_insert = round(to_insert, 2)
        if to_insert <= 0:
            continue

        cur.execute(
            """
            INSERT INTO charges (service_id, amount, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (int(sid), float(to_insert), snap_created_at, snap_created_at),
        )
        inserted += 1
        remaining = round(remaining - to_insert, 2)

    # Si aún queda delta, lo ponemos en el primer service (no inventamos otro breakdown)
    if remaining > 0:
        sid = existing_service_ids[0]
        cur.execute(
            """
            INSERT INTO charges (service_id, amount, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (int(sid), float(remaining), snap_created_at, snap_created_at),
        )
        inserted += 1

    return {"restored": True, "inserted_charges": inserted, "delta": float(delta), "mode": "targets_by_service"}


def reconcile() -> int:
    c = conn()
    try:
        mismatches = find_mismatched_claims(c)
        if not mismatches:
            print("OK: No hay inconsistencias contra snapshots (latest por claim).")
            return 0

        print("INCONSISTENCIAS DETECTADAS (latest snapshot por claim):")
        for cid, latest, st, dt in mismatches:
            print(f"- claim_id={cid} snapshot_id={latest['snapshot_id']} snap_created_at={latest['created_at']}")
            print(f"  SNAP: {st}")
            print(f"  DB  : {dt}")

        print("\nAPLICANDO RECONCILIACIÓN (MODELO A)...\n")

        for cid, latest, st, dt in mismatches:
            snap_created_at = latest["created_at"]
            snap = latest["snapshot"]

            # 1) eliminar eventos post-snapshot
            deleted = delete_post_snapshot_events(c, cid, snap_created_at)
            print(f"[claim {cid}] deleted post-snapshot: {deleted}")

            # 2) si snapshot exige payments/adjustments y DB se quedó corto, no inventamos
            dt_after = db_totals(c, cid)
            if float(dt_after["total_applied"]) < float(st["total_applied"]) - 0.01:
                raise ValueError(
                    f"Claim {cid}: DB amount_paid ({dt_after['total_applied']}) < snapshot ({st['total_applied']}). "
                    "No se puede reconstruir applications sin detalle. Requiere restore desde backup."
                )
            if float(dt_after["total_adjustments"]) < float(st["total_adjustments"]) - 0.01:
                raise ValueError(
                    f"Claim {cid}: DB adjustments ({dt_after['total_adjustments']}) < snapshot ({st['total_adjustments']}). "
                    "No se puede reconstruir adjustments sin detalle. Requiere restore desde backup."
                )

            # 3) restaurar charges faltantes (best-effort)
            restored = ensure_charge_totals_match_snapshot(c, cid, snap_created_at, snap)
            print(f"[claim {cid}] charges reconcile: {restored}")

            # 4) validar match final
            final_dt = db_totals(c, cid)
            ok = (
                approx_equal(st["total_charge"], final_dt["total_charge"])
                and approx_equal(st["total_applied"], final_dt["total_applied"])
                and approx_equal(st["total_adjustments"], final_dt["total_adjustments"])
                and approx_equal(st["balance_due"], final_dt["balance_due"])
            )
            if not ok:
                raise ValueError(
                    f"Claim {cid}: aún mismatch tras reconcile.\n"
                    f"SNAP={st}\nDB={final_dt}"
                )

            print(f"[claim {cid}] OK final totals match snapshot.")

        c.commit()
        print("\nRECONCILIACIÓN COMPLETA ✅")
        return 0

    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(reconcile())
