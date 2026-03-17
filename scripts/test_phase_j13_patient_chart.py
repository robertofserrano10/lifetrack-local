# scripts/test_phase_j13_patient_chart.py
# FASE J13 — Patient Chart

from app.main import app
from app.db.patients import create_patient
from app.db.coverages import create_coverage
from app.db.claims import create_claim
from app.db.encounters import create_encounter
from app.db.services import create_service


def main():
    # setup minimal data
    pid = create_patient("J13", "Paciente", "1980-01-01")
    cov_id = create_coverage(pid, "TestCo", "PlanJ13", "P321", "G1", "I321", "2024-01-01", None)
    claim_id = create_claim(pid, cov_id)
    enc_id = create_encounter(pid, "2026-03-12")

    service_id = create_service(
        claim_id=claim_id,
        service_date="2026-03-14",
        cpt_code="99215",
        units=1,
        diagnosis_code="B00",
        description="Consulta general",
        charge_amount_24f=200.0,
    )

    with app.test_client() as client:
        # login
        resp = client.post("/login", data={"username": "admin", "password": "admin123"})
        assert resp.status_code in (302, 200)

        # patient chart
        res = client.get(f"/admin/patients/{pid}")
        body = res.get_data(as_text=True)
        assert res.status_code == 200
        assert "Patient Chart Timeline" in body
        assert "encounter" in body
        assert "service" in body

    print("TEST PASSED: J13 Patient Chart shows timeline with claim/encounter/service")


if __name__ == "__main__":
    main()
