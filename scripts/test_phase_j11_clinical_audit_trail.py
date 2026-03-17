# scripts/test_phase_j11_clinical_audit_trail.py
# FASE J11 — Clinical Audit Trail

from app.db.patients import create_patient
from app.db.coverages import create_coverage
from app.db.claims import create_claim
from app.db.encounters import create_encounter
from app.db.services import create_service
from app.db.event_ledger import list_events_admin


def main():
    pid = create_patient("J11", "Paciente", "1980-01-01")
    cov_id = create_coverage(pid, "TestCo", "PlanY", "P321", "G1", "I321", "2024-01-01", None)
    claim_id = create_claim(pid, cov_id)
    encounter_id = create_encounter(pid, "2026-03-12")

    service_id = create_service(
        claim_id=claim_id,
        service_date="2026-03-12",
        cpt_code="99214",
        units=2,
        diagnosis_code="A01",
        description="Consulta urgencia",
        charge_amount_24f=220.0,
    )

    events_enc = list_events_admin(limit=10, offset=0, entity_type="encounter", entity_id=encounter_id)
    events_srv = list_events_admin(limit=10, offset=0, entity_type="service", entity_id=service_id)

    print("=== J11 CLINICAL AUDIT TRAIL TEST ===")
    print(f"encounter_id={encounter_id}, events_enc={len(events_enc)}")
    print(f"service_id={service_id}, events_srv={len(events_srv)}")
    
    assert len(events_enc) >= 1, "No se registró evento para encounter"
    assert len(events_srv) >= 1, "No se registró evento para service"

    print("TEST PASSED")


if __name__ == '__main__':
    main()
