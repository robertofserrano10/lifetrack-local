# scripts/test_phase_g35_create_unlocked_claim.py
# FASE G35 — Crear claim UNLOCKED para probar UI de transiciones
# Escribe SOLO datos mínimos. NO genera snapshot. NO toca claims existentes.

from app.db.patients import create_patient
from app.db.coverages import create_coverage
from app.db.claims import create_claim, get_claim_by_id
from app.db.financial_lock import is_claim_locked

def main():
    pid = create_patient("UI", "Unlocked", "1990-01-01")
    cov_id = create_coverage(
        pid,
        "Test",      # insurer_name
        "Plan",      # plan_name
        "P1",        # policy_number
        "G1",        # group_number
        "I1",        # insured_id
        "2025-01-01",# start_date
        None         # end_date
    )
    claim_id = create_claim(pid, cov_id)

    claim = get_claim_by_id(claim_id)
    locked = is_claim_locked(claim_id)

    print("=== G35 CREATE UNLOCKED CLAIM ===")
    print(f"claim_id={claim_id}")
    print(f"status={claim['status']}")
    print(f"locked={locked}")
    print(f"URL=http://127.0.0.1:5000/admin/claims/{claim_id}")
    print("EXPECTED: locked=False y botones visibles (allowed_transitions)")

if __name__ == "__main__":
    main()
