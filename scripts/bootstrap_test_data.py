from app.db import (
    create_patient,
    create_coverage,
)
from app.db.claims import create_claim, update_claim_cms_fields
from app.db.services import create_service
from app.db.charges import create_charge


def main():
    pid = create_patient("Test", "Paciente", "1990-01-01")

    cov_id = create_coverage(
        patient_id=pid,
        insurer_name="TestInsurer",
        plan_name="TestPlan",
        policy_number="P1",
        group_number="G1",
        insured_id="I1",
        start_date="2025-01-01",
        end_date=None,
    )

    claim_id = create_claim(pid, cov_id)

    # Claim-level CMS fields: 17, 19, 22, 23
    update_claim_cms_fields(
        claim_id=claim_id,
        referring_provider_name="Dr. Referidor Ejemplo",
        referring_provider_npi="1999999999",
        reserved_local_use_19="Nota local (opcional)",
        resubmission_code_22=None,
        original_ref_no_22=None,
        prior_authorization_23="AUTH-123",
    )

    svc_id = create_service(
        claim_id=claim_id,
        service_date="2026-02-05",
        cpt_code="90834",
        units=1,
        diagnosis_code="F41.1",
        description="Psychotherapy",
        outside_lab_20=0,
        lab_charges_20=None,
    )

    create_charge(service_id=svc_id, amount=150.00)

    print("BOOTSTRAP OK")
    print("PATIENT_ID:", pid)
    print("COVERAGE_ID:", cov_id)
    print("CLAIM_ID:", claim_id)
    print("SERVICE_ID:", svc_id)


if __name__ == "__main__":
    main()
