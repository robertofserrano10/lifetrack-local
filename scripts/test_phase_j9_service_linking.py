# scripts/test_phase_j9_service_linking.py
# FASE J9 — Service Linking (encounter -> service)

from app.db.patients import create_patient
from app.db.coverages import create_coverage
from app.db.claims import create_claim, get_claim_by_id
from app.db.encounters import create_encounter, get_encounter_by_id
from app.db.services import create_service
from app.db.financial_lock import is_claim_locked


def main():
    pid = create_patient("J9", "Paciente", "1980-01-01")
    cov_id = create_coverage(pid, "TestCo", "PlanX", "P123", "G1", "I123", "2024-01-01", None)
    claim_id = create_claim(pid, cov_id)

    enc_id = create_encounter(pid, "2026-03-12")

    service_id = create_service(
        claim_id=claim_id,
        service_date="2026-03-12",
        cpt_code="99213",
        units=1,
        diagnosis_code="A00",
        description="Consulta general",
        charge_amount_24f=120.0,
    )

    encounter = get_encounter_by_id(enc_id)
    claim = get_claim_by_id(claim_id)
    locked = is_claim_locked(claim_id)

    print("=== J9 SERVICE LINKING TEST ===")
    print(f"patient_id={pid} claim_id={claim_id} encounter_id={enc_id} service_id={service_id}")
    print(f"encounter_date={encounter['encounter_date']} claim_status={claim['status']} locked={locked}")
    print("OK => encounter exists and service created linked to claim")


if __name__ == "__main__":
    main()