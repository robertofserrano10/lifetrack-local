from app.db import (
    create_patient, create_coverage,
    create_claim,
    create_service,
    create_charge,
    create_payment,
    create_application,
    create_adjustment,
    generate_cms1500_snapshot,
)

def main():
    # 1) Paciente + cubierta + claim
    pid = create_patient("Test", "Totals", "1990-01-01")
    cov = create_coverage(
        patient_id=pid,
        insurer_name="TestInsurer",
        plan_name="TestPlan",
        policy_number="P1",
        group_number="G1",
        insured_id="I1",
        start_date="2025-01-01",
        end_date=None,
    )
    claim_id = create_claim(pid, cov)

    # 2) Servicio asociado al claim (según tu create_service actual)
    service_id = create_service(
        claim_id=claim_id,
        service_date="2026-02-04",
        cpt_code="90834",
        units=1,
        diagnosis_code="F41.1",
        description="Servicio prueba totals",
    )

    # 3) Charge $150
    charge_id = create_charge(service_id=service_id, amount=150.00)

    # 4) Payment $150 y Application $100 (parcial)
    payment_id = create_payment(
        amount=150.00,
        method="check",
        reference="EOB-TOTALS-001",
        received_date="2026-02-04",
    )
    _app_id = create_application(payment_id=payment_id, charge_id=charge_id, amount_applied=100.00)

    # 5) Adjustment $50 (write-off)
    _adj_id = create_adjustment(charge_id=charge_id, amount=50.00, reason="Write-off contractual")

    # 6) Snapshot y totales esperados:
    # total_charge = 150
    # amount_paid  = 100  (applied)
    # adjustments  = 50   (write-off)
    # balance_due  = 0
    r = generate_cms1500_snapshot(claim_id)
    totals = r["snapshot"]["totals"]

    print("SNAPSHOT HASH:", r["hash"])
    print("TOTALS:", totals)

    assert float(totals["total_charge"]) == 150.0, "total_charge debe ser 150"
    assert float(totals["amount_paid"]) == 100.0, "amount_paid debe ser 100"
    assert float(totals["total_adjustments"]) == 50.0, "total_adjustments debe ser 50"
    assert float(totals["balance_due"]) == 0.0, "balance_due debe ser 0"

    print("✅ OK: Totales 28–30 calculados correctamente")

if __name__ == "__main__":
    main()
