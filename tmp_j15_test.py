from app.db.patients import create_patient
from app.db.coverages import create_coverage
from app.db.claims import create_claim
from app.db.services import create_service
from app.db.charges import create_charge
from app.db.cms1500_snapshot import generate_cms1500_snapshot, get_latest_snapshot_by_claim
from app.db.progress_notes import create_note, get_notes_by_encounter, sign_note, get_note_by_id
from app.db.encounters import create_encounter
from app.main import app

# Prepare test data
pid = create_patient('J15','Tester','1990-01-01')
coverage_id = create_coverage(pid,'Insurer','PlanA','POL001',None,None,'2026-01-01',None)
claim_id = create_claim(pid,coverage_id)
encounter_id = create_encounter(pid,'2026-03-12',provider_id=None)

# Create clinical note
note_id = create_note(
    encounter_id,
    patient_name='Test Patient',
    record_number='RN12345',
    date_of_service='2026-03-12',
    start_time='10:00',
    end_time='10:50',
    service_type='Individual',
    cpt_code='90834',
    diagnosis_code='F41.1',
    provider_name='Dr. Test',
    provider_credentials='PhD',
    subjective='Paciente reporta aumento de ansiedad durante la semana.',
    objective='Apariencia adecuada, contacto visual normal, discurso congruente.',
    assessment='Ansiedad moderada persistente; progresión en manejo de pensamientos automáticos.',
    plan='Continuar con CBT enfocada en reestructuración cognitiva; tarea: registro de pensamientos.',
)
notes = get_notes_by_encounter(encounter_id)
assert len(notes) == 1
print('Note created:', notes[0]['note_text'])

# Sign note
sign_note(note_id)
signed_note = get_note_by_id(note_id)
assert signed_note['signed'] == 1
print('Note signed at', signed_note['signed_at'])

# Create a service and snapshot for CMS1500 view
service_id = create_service(claim_id,'2026-03-12','99213',1,'','',0,0.0,charge_amount_24f=120.0)
charge_id = create_charge(service_id, 120.0)

snapshot = generate_cms1500_snapshot(claim_id)
latest = get_latest_snapshot_by_claim(claim_id)
assert latest is not None
print('CMS1500 snapshot version', latest.get('version_number'))

# Flask test client for route responses
with app.test_client() as c:
    # Login as admin for protected routes
    login_res = c.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert login_res.status_code in (200, 302)

    r = c.get(f'/admin/encounters/{encounter_id}')
    assert r.status_code == 200
    assert b'Progress Notes' in r.data

    r2 = c.get(f'/admin/notes/view/{note_id}')
    assert r2.status_code == 200
    assert b'Clinical Note' in r2.data

    r3 = c.get(f'/admin/claims/{claim_id}/cms1500')
    assert r3.status_code == 200
    assert b'CMS-1500 Preview' in r3.data

print('J15 test completed successfully')
