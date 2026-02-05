from app.db import generate_cms1500_snapshot


def main():
    r = generate_cms1500_snapshot(1)
    s = r["snapshot"]

    # Diagnósticos (Casilla 21)
    dx = s.get("diagnoses", {})
    assert "A" in dx, "❌ Falta Dx A"
    assert "B" in dx, "❌ Falta Dx B"
    assert "C" in dx, "❌ Falta Dx C"
    assert "D" in dx, "❌ Falta Dx D"

    # Servicios y Dx Pointer (24E)
    for svc in s["services"]:
        assert "dx_pointer" in svc, "❌ Servicio sin dx_pointer"

    print("✅ OK: Casilla 21 (Diagnósticos)")
    print("✅ OK: Casilla 24E (Dx Pointer)")


if __name__ == "__main__":
    main()
