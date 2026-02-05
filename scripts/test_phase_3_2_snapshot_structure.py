from app.db import generate_cms1500_snapshot


def main():
    # Usamos un claim existente (ajusta si tu claim_id no es 1)
    CLAIM_ID = 1

    r = generate_cms1500_snapshot(CLAIM_ID)
    snapshot = r["snapshot"]

    assert "patient" in snapshot, "❌ Falta patient"
    assert "insurance" in snapshot, "❌ Falta insurance"
    assert "diagnoses" in snapshot, "❌ Falta diagnoses"
    assert "services" in snapshot, "❌ Falta services"
    assert "totals" in snapshot, "❌ Falta totals"
    assert "provider" in snapshot, "❌ Falta provider"
    assert "meta" in snapshot, "❌ Falta meta"

    print("OK: patient presente")
    print("OK: insurance presente")
    print("OK: diagnoses presente")
    print("OK: services presente")
    print("OK: totals presente")
    print("OK: provider presente")
    print("OK: meta presente")


if __name__ == "__main__":
    main()
