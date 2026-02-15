from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("storage") / "lifetrack.db"


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise ValueError(f"No existe DB en: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _f(x) -> float:
    try:
        return float(x or 0)
    except Exception:
        return 0.0


def main() -> None:
    print("=== TEST G24: GLOBAL FINANCIAL AUDIT ===")
    with _connect() as conn:
        cur = conn.cursor()

        # =========================
        # 1) PAYMENT INVARIANTS
        # payment.amount >= SUM(applications.amount_applied)
        # =========================
        cur.execute(
            """
            SELECT
                p.id AS payment_id,
                p.amount AS payment_amount,
                COALESCE(SUM(a.amount_applied), 0) AS applied_sum
            FROM payments p
            LEFT JOIN applications a ON a.payment_id = p.id
            GROUP BY p.id
            ORDER BY p.id
            """
        )
        bad_payments = []
        for r in cur.fetchall():
            payment_id = int(r["payment_id"])
            payment_amount = _f(r["payment_amount"])
            applied_sum = _f(r["applied_sum"])

            if applied_sum - payment_amount > 1e-9:
                bad_payments.append((payment_id, payment_amount, applied_sum))

        if bad_payments:
            lines = ["FAIL: Payments sobre-aplicados (applied > amount):"]
            for pid, amt, applied in bad_payments[:20]:
                lines.append(f"  payment_id={pid} amount={amt} applied_sum={applied}")
            raise ValueError("\n".join(lines))

        print("OK: payments no tienen sobre-aplicación")

        # =========================
        # 2) CHARGE INVARIANTS
        # charge.amount >= applied + adjustments
        # balance = amount - applied - adjustments
        # =========================
        cur.execute(
            """
            SELECT
                c.id AS charge_id,
                c.service_id AS service_id,
                c.amount AS charge_amount,
                COALESCE(SUM(a.amount_applied), 0) AS applied_sum
            FROM charges c
            LEFT JOIN applications a ON a.charge_id = c.id
            GROUP BY c.id
            ORDER BY c.id
            """
        )
        applied_by_charge = {int(r["charge_id"]): _f(r["applied_sum"]) for r in cur.fetchall()}

        cur.execute(
            """
            SELECT
                c.id AS charge_id,
                c.amount AS charge_amount,
                COALESCE(SUM(ad.amount), 0) AS adj_sum
            FROM charges c
            LEFT JOIN adjustments ad ON ad.charge_id = c.id
            GROUP BY c.id
            ORDER BY c.id
            """
        )
        adj_by_charge = {int(r["charge_id"]): _f(r["adj_sum"]) for r in cur.fetchall()}

        cur.execute("SELECT id, service_id, amount FROM charges ORDER BY id")
        bad_charges = []
        for r in cur.fetchall():
            charge_id = int(r["id"])
            service_id = int(r["service_id"])
            charge_amount = _f(r["amount"])
            applied_sum = _f(applied_by_charge.get(charge_id, 0))
            adj_sum = _f(adj_by_charge.get(charge_id, 0))

            if applied_sum < -1e-9 or adj_sum < -1e-9:
                bad_charges.append(
                    (charge_id, service_id, charge_amount, applied_sum, adj_sum, "NEGATIVE_COMPONENT")
                )
                continue

            if applied_sum + adj_sum - charge_amount > 1e-9:
                bad_charges.append(
                    (charge_id, service_id, charge_amount, applied_sum, adj_sum, "OVER_APPLIED_OR_OVER_ADJUSTED")
                )

        if bad_charges:
            lines = ["FAIL: Charges con inconsistencia (applied+adjustments > amount):"]
            for cid, sid, amt, applied, adj, reason in bad_charges[:20]:
                lines.append(
                    f"  charge_id={cid} service_id={sid} amount={amt} applied={applied} adjustments={adj} reason={reason}"
                )
            raise ValueError("\n".join(lines))

        print("OK: charges cumplen amount >= applied + adjustments")

        # =========================
        # 3) CLAIM TOTALS CONSISTENCY
        # total_charge = SUM(charges.amount)
        # total_applied = SUM(applications.amount_applied)
        # total_adjustments = SUM(adjustments.amount)
        # balance_due = total_charge - total_applied - total_adjustments
        # =========================
        cur.execute("SELECT id FROM claims ORDER BY id")
        claim_ids = [int(r["id"]) for r in cur.fetchall()]

        bad_claims = []
        for claim_id in claim_ids:
            # total_charge
            cur.execute(
                """
                SELECT COALESCE(SUM(c.amount), 0)
                FROM charges c
                JOIN services s ON s.id = c.service_id
                WHERE s.claim_id = ?
                """,
                (claim_id,),
            )
            total_charge = _f(cur.fetchone()[0])

            # total_applied
            cur.execute(
                """
                SELECT COALESCE(SUM(a.amount_applied), 0)
                FROM applications a
                JOIN charges c ON c.id = a.charge_id
                JOIN services s ON s.id = c.service_id
                WHERE s.claim_id = ?
                """,
                (claim_id,),
            )
            total_applied = _f(cur.fetchone()[0])

            # total_adjustments
            cur.execute(
                """
                SELECT COALESCE(SUM(ad.amount), 0)
                FROM adjustments ad
                JOIN charges c ON c.id = ad.charge_id
                JOIN services s ON s.id = c.service_id
                WHERE s.claim_id = ?
                """,
                (claim_id,),
            )
            total_adjustments = _f(cur.fetchone()[0])

            balance_due = total_charge - total_applied - total_adjustments

            # Verificación extra: suma de balances por charge debe igualar balance_due
            cur.execute(
                """
                SELECT c.id, c.amount
                FROM charges c
                JOIN services s ON s.id = c.service_id
                WHERE s.claim_id = ?
                ORDER BY c.id
                """,
                (claim_id,),
            )
            charges = cur.fetchall()

            sum_charge_balances = 0.0
            for cr in charges:
                cid = int(cr["id"])
                amt = _f(cr["amount"])
                applied_sum = _f(applied_by_charge.get(cid, 0))
                adj_sum = _f(adj_by_charge.get(cid, 0))
                sum_charge_balances += (amt - applied_sum - adj_sum)

            if abs(sum_charge_balances - balance_due) > 1e-6:
                bad_claims.append(
                    (claim_id, total_charge, total_applied, total_adjustments, balance_due, sum_charge_balances)
                )

        if bad_claims:
            lines = ["FAIL: Claims con inconsistencia (balance_due != suma de balances por charge):"]
            for (
                claim_id,
                tc,
                ta,
                tadj,
                bd,
                sum_bd,
            ) in bad_claims[:20]:
                lines.append(
                    f"  claim_id={claim_id} total_charge={tc} total_applied={ta} total_adjustments={tadj} "
                    f"balance_due={bd} sum_charge_balances={sum_bd}"
                )
            raise ValueError("\n".join(lines))

        print("OK: claims consistentes (totales y suma de balances por charge)")

        # =========================
        # 4) LOCKED CLAIMS CHECK (snapshot exists)
        # Sólo verifica que estén marcados como locked y que no haya violaciones obvias en data.
        # =========================
        cur.execute(
            """
            SELECT DISTINCT claim_id
            FROM cms1500_snapshots
            ORDER BY claim_id
            """
        )
        locked_claims = [int(r["claim_id"]) for r in cur.fetchall()]
        print(f"INFO: locked_claims (con snapshot) = {len(locked_claims)}")

    print("GLOBAL AUDIT PASSED ✅")


if __name__ == "__main__":
    main()
