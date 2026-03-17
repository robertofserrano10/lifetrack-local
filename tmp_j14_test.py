from app.db.patients import create_patient
from app.db.coverages import create_coverage
from app.db.claims import create_claim
from app.db.services import create_service
from app.db.charges import create_charge
from app.db.payments import create_payment
from app.db.applications import create_application
from app.db.balances import get_claim_balance
from app.main import app

# create base data
pid = create_patient('J14','Tester','1990-01-01')
cid = create_coverage(pid,'Insurer','PlanA','POL001',None,None,'2026-01-01',None)
claim_id = create_claim(pid,cid)
svc_id = create_service(claim_id,'2026-03-12','99213',1,'','',0,0.0,charge_amount_24f=120.0)
charge_id = create_charge(svc_id,120.0)
payment_id = create_payment(120.0,'check','REF1','2026-03-12')
app_id = create_application(payment_id, charge_id, 120.0)

balance_pre = get_claim_balance(claim_id)
print('BALANCE before lock', balance_pre)

with app.test_client() as c:
    r = c.post(f'/admin/claims/{claim_id}/lock')
    print('lock status', r.status_code, 'location', r.headers.get('Location'))
    r2 = c.get(f'/admin/claims/{claim_id}')
    locked_ok = b'Claim is SAFELY LOCKED' in r2.data
    print('detail shows locked', locked_ok)

# try create service after lock -> should fail
try:
    create_service(claim_id,'2026-03-13','99214',1,'','',0,0.0,charge_amount_24f=100.0)
    print('ERROR: service creation should be blocked on locked claim')
except Exception as e:
    print('blocked service create:', str(e))

print('J14 test completed')
