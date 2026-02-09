# Núcleo Financiero — LifeTrack (FASE F1)

## Principios Inmutables
- El snapshot CMS-1500 es solo lectura.
- Ningún pago recalcula cargos históricos.
- Todo movimiento financiero es trazable.
- Todo balance se deriva, no se persiste como verdad absoluta.

---

## Entidades

### Charge
Representa un cargo facturable originado por un servicio.
- id
- claim_id
- snapshot_hash
- service_id (opcional)
- amount
- created_at

### Payment
Representa dinero recibido.
- id
- source (patient, insurer, other)
- method (cash, check, eft, credit)
- reference (check #, eft id)
- amount
- received_at

### Application
Aplica un Payment a uno o más Charges.
- id
- payment_id
- charge_id
- amount_applied
- applied_at

### Balance
Valor DERIVADO, no persistido.
- balance = sum(charges) - sum(applications)

---

## Reglas Críticas
- Un Payment puede aplicarse a múltiples Charges.
- Un Charge puede recibir múltiples Applications.
- Nunca se edita un Charge; se corrige con ajustes futuros.
- Credits existen cuando amount_applied < payment.amount.

---

## Relación con CMS-1500
- Charges se originan desde servicios del snapshot.
- snapshot_hash se guarda para auditoría.
- Si el snapshot cambia (nueva versión), se generan nuevos Charges.
- Charges antiguos NO se borran.

---

## Prohibiciones
- No editar snapshot.
- No recalcular CMS-1500.
- No persistir balances finales como verdad única.

---

## Auditoría
- Todo Payment debe cuadrar contra Applications.
- Todo Balance debe ser reproducible por cálculo.
