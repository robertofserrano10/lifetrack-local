from app.db import *
from app.db.cms1500_snapshot import generate_cms1500_snapshot
from app.db.claims import update_claim_operational_status


def main():
    print("=== TEST G25: OPERATIONAL STATE MACHINE ===")

    # Crear claim limpio
    pid = create_patient("State", "Machine", "1990-01-01")
    cov = create_coverage(
        pid, "Test", "Plan", "P1", "G1", "I1", "2025-01-01", None
    )
    claim = create_claim(pid, cov)

    # Estado inicial debe ser DRAFT
    claim_data = get_claim_by_id(claim)
    assert claim_data["status"] == "DRAFT"
    print("OK: estado inicial DRAFT")

    # Transición válida: DRAFT → READY
    update_claim_operational_status(claim, "READY")
    assert get_claim_by_id(claim)["status"] == "READY"
    print("OK: DRAFT → READY")

    # READY → SUBMITTED
    update_claim_operational_status(claim, "SUBMITTED")
    assert get_claim_by_id(claim)["status"] == "SUBMITTED"
    print("OK: READY → SUBMITTED")

    # SUBMITTED → PAID
    update_claim_operational_status(claim, "PAID")
    assert get_claim_by_id(claim)["status"] == "PAID"
    print("OK: SUBMITTED → PAID")

    # Intentar transición inválida
    try:
        update_claim_operational_status(claim, "READY")
        raise AssertionError("FAIL: permitió transición inválida")
    except ValueError:
        print("OK: transición inválida bloqueada")

    # Crear otro claim para probar bloqueo por snapshot
    pid2 = create_patient("State", "SnapshotBlock", "1990-01-01")
    cov2 = create_coverage(
        pid2, "Test", "Plan", "P1", "G1", "I1", "2025-01-01", None
    )
    claim2 = create_claim(pid2, cov2)

    generate_cms1500_snapshot(claim2)

    try:
        update_claim_operational_status(claim2, "READY")
        raise AssertionError("FAIL: permitió cambio con snapshot")
    except ValueError:
        print("OK: bloqueo por snapshot funcionando")

    print("G25 PASSED ✅")


if __name__ == "__main__":
    main()
