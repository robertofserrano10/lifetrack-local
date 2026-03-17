from app.db.patients import create_patient
from app.db.coverages import create_coverage
from app.db.claims import create_claim, get_claim_financial_status
from app.db.encounters import create_encounter
from app.db.services import create_service
from app.db.charges import create_charge
from app.db.payments import create_payment
from app.db.applications import create_application
from app.db.balances import get_claim_balance

print('CREANDO DATOS...')
pid = create_patient('Prueba','Usuario','1990-01-01')
print('patient', pid)
cov_id = create_coverage(pid,'Segur','PlanX','POL-123',None,None,'2025-01-01',None)
print('coverage', cov_id)
claim_id = create_claim(pid, cov_id)
print('claim', claim_id)
enc_id = create_encounter(pid,'2026-03-12',provider_id=None)
print('encounter', enc_id)
service_id = create_service(claim_id,'2026-03-12','99213',1,'','',0,0.0, charge_amount_24f=150.00)
print('service', service_id)
charge_id = create_charge(service_id,150.00)
print('charge', charge_id)
payment_id = create_payment(150.00,'check','TEST-001','2026-03-12')
print('payment', payment_id)
app_id = create_application(payment_id, charge_id, 150.00)
print('application', app_id)
cf = get_claim_financial_status(claim_id)
print('claim_fin_status', cf)
cb = get_claim_balance(claim_id)
print('claim_balance', cb)
print('OK')
