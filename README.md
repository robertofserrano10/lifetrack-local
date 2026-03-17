# LifeTrack — Reglas Inmutables del Sistema (Documento Maestro para Agentes)

Este documento define **todas las reglas arquitectónicas, operativas y de desarrollo** del sistema LifeTrack.  
Cualquier agente, desarrollador o sistema automatizado que interactúe con este repositorio **debe respetar estas invariantes sin excepción**.

El objetivo de estas reglas es preservar:

- integridad financiera
- auditabilidad legal
- reproducibilidad técnica
- estabilidad del sistema
- coherencia arquitectónica

Si una modificación viola alguna de estas reglas, **la modificación se considera inválida**.

---

# 1. Principio Arquitectónico Central

LifeTrack está construido sobre un **modelo financiero tipo ledger**.

Este modelo separa completamente:

- deuda
- dinero
- aplicación de dinero

El sistema **nunca mezcla estos conceptos directamente**.

Esto evita:

- mezcla financiera
- balances corruptos
- errores acumulativos
- inconsistencias contables.

---

# 2. Entidades Financieras del Sistema

Las entidades financieras fundamentales del sistema son:


charges
payments
applications
adjustments


Definición:


charge = deuda generada por un servicio clínico
payment = dinero recibido
application = vínculo entre un pago y un cargo
adjustment = corrección financiera auditada


---

# 3. Regla de Separación Financiera

Regla estructural:


Un cargo no conoce pagos.
Un pago no conoce servicios.


La única relación válida entre dinero y deuda es:


application {
payment_id
charge_id
amount
}


Esto significa:


payment → dinero disponible
charge → deuda pendiente
application → reducción de deuda


Sin una aplicación:

- el cargo permanece como deuda
- el pago permanece como dinero disponible.

Eliminar una aplicación restaura el estado original.

Este diseño elimina estructuralmente la mezcla financiera.

---

# 4. Generación de Cargos

Los cargos se generan automáticamente al registrar servicios clínicos.

Proceso:


service → charge


Un servicio clínico siempre produce un cargo financiero.

Campos típicos de un cargo:


charge_id
claim_id
service_id
amount
date


El cargo representa **deuda pendiente**.

---

# 5. Registro de Pagos

Los pagos representan dinero recibido.

Ejemplos:

- cheque
- EFT
- efectivo
- pago del paciente
- pago de aseguradora

Cuando un pago entra al sistema se guarda como:


payment.status = UNAPPLIED


Campos mínimos de un pago:


payment_id
amount
date
reference
source


Un pago **no impacta ninguna deuda automáticamente**.

---

# 6. Aplicación de Pagos

La aplicación de pagos es el único mecanismo que permite que el dinero reduzca deuda.

Proceso obligatorio:


1 registrar pago
2 pago queda no aplicado
3 usuario selecciona pago
4 usuario selecciona cargo
5 usuario especifica monto
6 sistema crea application


La aplicación contiene:


application_id
payment_id
charge_id
amount
timestamp
user_id


Validaciones obligatorias:


applied_amount ≤ remaining_payment
applied_amount ≤ remaining_charge


Toda aplicación es:

- auditada
- reversible
- trazable.

---

# 7. Invariantes Financieras

Reglas duras del sistema:


Un pago no puede aplicarse por encima de su monto original.

Un cargo no puede recibir aplicaciones superiores a su monto original.

Un pago puede aplicarse a múltiples cargos.

Un cargo puede recibir múltiples pagos.

Cada claim tiene su propio conjunto de cargos, pagos y aplicaciones.

No puede existir contaminación financiera entre claims.


---

# 8. Estado Financiero Derivado

El sistema **no persiste balances**.

Los balances se calculan dinámicamente.

Fórmulas:


Balance = Σ cargos − Σ aplicaciones
Credito = Σ pagos − Σ aplicaciones


Estados posibles:


balance > 0 → ABIERTO

balance = 0 AND pagos_no_aplicados = 0 → CERRADO

balance = 0 AND pagos_no_aplicados > 0 → CON_CREDITO


Regla absoluta:


El estado financiero nunca se guarda en base de datos.
Siempre se calcula desde las transacciones.


Esto elimina:

- errores acumulativos
- cierres falsos
- estados corruptos.

---

# 9. Créditos

Si ocurre:


balance = 0
pagos_no_aplicados > 0


El claim entra en estado:


CON_CREDITO


El sistema **no redistribuye créditos automáticamente**.

Opciones del usuario:


aplicar crédito a otro cargo
emitir reembolso
dejar crédito pendiente


---

# 10. Flujo Financiero Completo

Flujo estructural del sistema:


Servicio Clínico
↓
Genera Cargo (deuda)

Pago recibido
↓
Pago no aplicado

Aplicación manual
(payment + cargo)

Motor financiero
(balance derivado)

Estado final
ABIERTO / CERRADO / CON_CREDITO


---

# 11. CMS-1500

El CMS-1500 es el documento de facturación médica estándar.

En LifeTrack el CMS-1500 se genera desde:


snapshot congelado


El CMS-1500 contiene:

- datos del paciente
- proveedor
- aseguradora
- servicios
- diagnósticos
- estado financiero.

---

# 12. Snapshot CMS-1500

El snapshot es una copia congelada del estado del claim.

Contiene:


claim data
patient data
provider data
services
diagnosis
financial state
timestamp
version
hash


Reglas:


Los snapshots son inmutables.

Nunca se editan.

Nunca se recalculan.

Nunca se regeneran sobre el mismo registro.


Si el claim cambia:


se crea un snapshot nuevo
nueva versión
nuevo hash


---

# 13. Hash de Integridad

Cada snapshot genera un hash:


hash = SHA256(snapshot_json)


El hash garantiza:

- integridad legal
- detección de manipulación
- auditoría histórica.

---

# 14. CMS-1500 no es fuente de verdad

Regla fundamental:


El CMS-1500 no es la fuente de verdad financiera.


La fuente de verdad siempre es:


charges
payments
applications


El CMS-1500 es únicamente:


representación congelada del estado en ese momento


---

# 15. Reapertura Manual

Existe un flag en claims:


reapertura_manual


Cuando este flag está activo:


el claim no puede cerrarse automáticamente


El cierre manual solo hace:


reapertura_manual = false


No modifica:


transacciones
aplicaciones
balances


El estado final depende únicamente de los números.

---

# 16. Estados del Claim

El sistema maneja dos estados independientes:


estado_operacional
estado_financiero


Ejemplo:


operacional = SUBMITTED
financiero = ABIERTO


Estos estados **no deben mezclarse**.

---

# 17. Auditoría

Toda acción financiera genera un evento de auditoría.

Ejemplos:


payment_created
application_created
application_deleted
adjustment_created
claim_closed
snapshot_generated


Cada evento contiene:


timestamp
user_id
entity_id
payload


---

# 18. Regla de Fases del Proyecto

El proyecto se desarrolla por fases controladas.

Ejemplo:


FASE A → base del sistema
FASE B → layout CMS1500
FASE C → impresión
FASE G → snapshot
FASE H → UI operacional


Cada fase tiene límites estrictos.

Una fase **no modifica componentes de otra fase**.

---

# 19. Regla de Congelación de Fases

Una fase se considera cerrada cuando:


pruebas en verde
commit realizado
fase congelada


Una fase congelada **no se modifica**.

---

# 20. Regla de Pruebas

Las pruebas deben ejecutarse mediante scripts dedicados.

Ejemplo:


scripts/test_phase_X.py


Nunca ejecutar pruebas directamente en REPL.

---

# 21. Reglas de Base de Datos

Cuando se modifica estructura de base de datos:


schema.sql debe actualizarse


En fases tempranas:


la base de datos se recrea


Migraciones se reservan para fases maduras.

---

# 22. Firma CMS-1500

Las casillas de firma del CMS-1500 son:


Box 12
Box 13


En el sistema se usan como:


Signature on File


Las firmas reales se mantienen fuera del sistema.

El sistema solo registra:


signature_status
signature_date
signature_type


---

# 23. Resubmission (CMS-1500 Box 22)

Soporte futuro:


resubmission_code
original_reference


Esto se implementará en una fase posterior.

---

# 24. Roles de Usuario

La interfaz operacional se implementa en la FASE H.

Roles definidos:


DRA
RECEPCION
FACTURADOR
ADMIN


Cada rol tiene:

- visibilidad específica
- permisos específicos.

---

# 25. Reglas de Desarrollo para Agentes

Un agente que modifique el sistema debe cumplir:


No inventar estructuras.

No asumir rutas.

No asumir dependencias.

Trabajar solo con información explícita del repositorio.


---

# 26. Regla de CSS de Impresión

Las fases de impresión **no pueden modificar HTML ni lógica**.

Solo CSS.

Ejemplo:


cms1500_print.css


---

# 27. Regla de Git

Al cerrar una fase:


git status
git add .
git commit -m "fase X completada"
git push


---

# 28. Garantía del Sistema

Si todas las invariantes se respetan:


no existe mezcla financiera
no existen balances falsos
no existe corrupción contable


El sistema puede operar con dinero real.

La arquitectura es:


ledger auditado
estado derivado
snapshots legales
auditoría completa


---

# FIN DEL DOCUMENTO