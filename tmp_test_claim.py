from app.main import app
from app.db.claims import create_claim
from app.db.patients import create_patient
from app.db.coverages import create_coverage

p = create_patient('Test','User','1990-01-01','M')
cov = create_coverage(p, 'TestIns', 'PlanA', 'POL123', '2025-01-01', None)
cl = create_claim(p, cov)
with app.test_client() as c:
    r = c.get(f'/admin/claims/{cl}')
    print('status', r.status_code)
    assert r.status_code == 200
    assert b'Ver Payments' in r.data
    assert b'Resumen Financiero' in r.data
print('ok')
