from app.db.claims import get_claim_by_id
from app.db.services import update_service_box20
from app.db import generate_cms1500_snapshot


def main():
    # Claim 1 debe existir por bootstrap
    claim = get_claim_by_id(1)
    assert claim is not None, "❌ Claim 1 no existe"

    # Validar claim-level fields
    assert "referring_provider_name" in claim, "❌ Falta campo claim referring_provider_name"
    assert "reserved_local_use_19" in claim, "❌ Falta campo claim reserved_local_use_19"
    assert "resubmission_code_22" in claim, "❌ Falta campo claim resubmission_code_22"
    assert "original_ref_no_22" in claim, "❌ Falta campo claim original_ref_no_22"
    assert "prior_authorization_23" in claim, "❌ Falta campo claim prior_authorization_23"

    # Service box 20: probamos update en service 1
    ok = update_service_box20(service_id=1, outside_lab_20=1, lab_charges_20=25.00)
    assert ok is True, "❌ No se pudo actualizar Box 20 en service 1"

    r = generate_cms1500_snapshot(1)
    snap = r["snapshot"]

    # Snapshot debe traer claim_cms
    assert "claim_cms" in snap, "❌ Snapshot no incluye claim_cms"
    assert snap["claim_cms"]["box17_referring_provider"]["name"] is not None, "❌ Snapshot box17 name vacío"
    assert snap["claim_cms"]["box23_prior_authorization"] is not None, "❌ Snapshot box23 vacío"

    # Service debe reflejar box20
    svc = snap["services"][0]
    assert "outside_lab_20" in svc, "❌ Service snapshot no incluye outside_lab_20"
    assert "lab_charges_20" in svc, "❌ Service snapshot no incluye lab_charges_20"
    assert int(svc["outside_lab_20"]) == 1, "❌ outside_lab_20 no reflejó el update"
    assert float(svc["lab_charges_20"]) == 25.0, "❌ lab_charges_20 no reflejó el update"

    print("✅ OK: Claim fields 17/19/22/23 + Service box20 presentes y snapshot los lee")


if __name__ == "__main__":
    main()
