# AUDITORÍA DEL SISTEMA — LifeTrack / Psynántisi
**Fecha:** 21 de marzo 2026
**Auditor:** Claude Sonnet 4.6 (solo lectura — ningún archivo modificado)
**Base de referencia:** `LIFETRACK_REFERENCIA.md` v2.0 APROBADO

---

## 1. ROUTES — Blueprints y Registro

### 1.1 Registro en `main.py`

| Blueprint | Archivo | Registrado | URL Prefix |
|---|---|---|---|
| `patients_bp` | `routes/patients.py` | ✅ | `/patients` |
| `coverages_bp` | `routes/coverages.py` | ✅ | `/coverages` |
| `provider_settings_bp` | `routes/provider_settings.py` | ✅ | — |
| `cms1500_pdf_bp` | `routes/cms1500_pdf.py` | ✅ | — |
| `claim_balance_bp` | `routes/claim_balance.py` | ✅ | — |
| `charge_balance_bp` | `routes/charge_balance.py` | ✅ | — |
| `claim_payments_bp` | `routes/claim_payments.py` | ✅ | — |
| `claim_adjustments_bp` | `routes/claim_adjustments.py` | ✅ | — |
| `claim_financial_summary_bp` | `routes/claim_financial_summary.py` | ✅ | — |
| `payment_balance_bp` | `routes/payment_balance.py` | ✅ | — |
| `claims_overview_bp` | `routes/claims_overview.py` | ✅ | — |
| `snapshots_admin_bp` | `routes/snapshots_admin.py` | ✅ | `/admin/snapshots` |
| `claims_admin_bp` | `routes/claims_admin.py` | ✅ | `/admin/claims` |
| `events_admin_bp` | `routes/events_admin.py` | ✅ | `/admin/events` |
| `dashboard_admin_bp` | `routes/admin_dashboard.py` | ✅ | `/admin` |
| `claims_list_bp` | `routes/admin_claims_list.py` | ✅ | `/admin` |
| `patients_admin_bp` | `routes/admin_patients.py` | ✅ | `/admin/patients` |
| `services_admin_bp` | `routes/admin_services.py` | ✅ | `/admin/services` |
| `finances_admin_bp` | `routes/admin_finances.py` | ✅ | `/admin/finances` |
| `reports_admin_bp` | `routes/admin_reports.py` | ✅ | `/admin/reports` |
| `settings_admin_bp` | `routes/admin_settings.py` | ✅ | `/admin/settings` |
| `encounters_admin_bp` | `routes/admin_encounters.py` | ✅ | `/admin/encounters` |
| `clinical_admin_bp` | `routes/admin_clinical.py` | ✅ | `/admin/clinical` |
| `progress_notes_admin_bp` | `routes/admin_progress_notes.py` | ✅ | `/admin/notes` |
| `notes_editor_admin_bp` | `routes/admin_notes_editor.py` | ✅ | `/admin/notes` |
| `checkin_bp` | `routes/admin_checkin.py` | ✅ | `/admin/checkin` |
| `eob_bp` | `routes/admin_eob.py` | ✅ | `/admin/eob` |
| `appointments_bp` | `routes/admin_appointments.py` | ✅ | `/admin/appointments` |

**✅ Los 28 blueprints están registrados correctamente.**

### 1.2 Imports utilitarios en `main.py`

| Import | Archivo real | Estado |
|---|---|---|
| `from app.views.cms1500_render import get_latest_snapshot_by_claim` | `app/views/cms1500_render.py` | ✅ Existe |
| `from app.utils.snapshot_hash import compute_snapshot_hash` | `app/utils/snapshot_hash.py` | ✅ Existe |

### 1.3 Protección de rutas — decoradores ausentes

| Ruta | Archivo | `@login_required` | `@role_required` |
|---|---|---|---|
| `GET/POST /admin/new` (claim_create) | `admin_claims_list.py:71` | ❌ NINGUNO | ❌ NINGUNO |
| `GET /admin/claims/<id>` | `claims_admin.py:38` | ❌ AUSENTE | ❌ AUSENTE |
| `GET /admin/claims/<id>/cms1500` | `claims_admin.py:158` | ❌ AUSENTE | ❌ AUSENTE |
| `GET/POST /admin/claims/<id>/service/new` | `claims_admin.py:174` | ❌ AUSENTE | ❌ AUSENTE |
| `POST /admin/claims/<id>/lock` | `claims_admin.py` | ❌ AUSENTE | ❌ AUSENTE |
| `GET/POST /admin/claims/<id>/edit` | `claims_admin.py` | ❌ AUSENTE | ❌ AUSENTE |
| `POST /admin/claims/<id>/transition` | `claims_admin.py` | ❌ AUSENTE | ❌ AUSENTE |

**❌ CRÍTICO: 7 rutas del módulo de claims no tienen ningún tipo de protección de autenticación ni de rol.**
- La ruta `/admin/new` (crear claim) no tiene ni `@login_required` — acceso anónimo posible.
- Las 6 rutas restantes en `claims_admin.py` no tienen ningún decorator — cualquier usuario autenticado con cualquier rol puede acceder a datos financieros, crear servicios, bloquear snapshots o cambiar estados de claims.

---

## 2. FLOW LOGIC — Flujo completo extremo a extremo

Flujo esperado según la referencia:
```
appointment → check-in → visit_session → encounter → progress_note
           → ready_for_billing → claim → snapshot → EOB
```

| Paso | Ruta / Función | Estado | Notas |
|---|---|---|---|
| Crear appointment | `POST /admin/appointments/new` | ✅ | Funciona. Valida paciente y fecha. |
| Ver agenda | `GET /admin/appointments/` | ✅ | Muestra hoy + próximos 30 días agrupados por fecha. |
| Check-in con elegibilidad | `POST /admin/checkin/new` | ✅ | BI-3 completo. Bloquea si `eligibility_verified` no está marcado. |
| Copago → payment no-aplicado | `create_payment()` dentro de checkin | ✅ | Registra payment con referencia "Copago check-in". |
| visit_session → WAITING | `update_visit_status()` | ✅ | Transiciones ARRIVED → CHECKED_IN → WAITING correctas. |
| visit_session → NO_SHOW | `VALID_STATUSES` en `visit_sessions.py` | ⚠️ | `NO_SHOW` **no está** en `VALID_STATUSES` ni en el CHECK constraint de la tabla. El flujo `WAITING → NO_SHOW` definido en la referencia (paso 79) no puede ejecutarse. |
| Encounter abierto por DRA | `POST /admin/encounters/new` | ✅ | Crea con status OPEN. |
| Encounter ↔ visit_session enlace | Ninguno | ⚠️ | Encounter y visit_session **no están vinculados por FK** en la DB. Son entidades paralelas sin conexión directa — el flujo operacional y clínico no están formalmente ligados. |
| Nota SOAP | `POST /admin/notes/create/<encounter_id>` | ✅ | Editor SOAP completo (S/O/A/P). |
| Firma nota | `POST /admin/notes/sign/<note_id>` | ✅ | Bloquea edición después de firma. `signed = true` persistido. |
| Addendum | `POST /admin/notes/addendum/<note_id>` | ✅ | Nueva nota vinculada por `parent_note_id`. |
| **Ready for Billing** | **— ninguna ruta existe —** | ❌ | **BI-4 no implementado.** No existe campo `ready_for_billing` en la tabla `encounters`. No hay gate de validación, no hay verificación de referido antes de billing, no hay UI. |
| Claim desde Encounter | `POST /admin/new` en `claim_create()` | ❌ | **BI-5 no implementado.** El claim se crea desde paciente + cobertura directamente, **sin pasar por un encounter**. Viola la regla crítica: "El claim se crea SIEMPRE desde un encounter con `ready_for_billing = true`". La tabla `claims` no tiene columna `encounter_id`. |
| Agregar servicios/CPT al claim | `POST /admin/claims/<id>/service/new` | ✅ | Funciona (pero sin decoradores de auth — ver sección 1.3). |
| Claim Scrubber | `scrub_claim(claim_id)` | ✅ | Se ejecuta automáticamente en claim_detail. |
| Lock → Snapshot CMS-1500 | `POST /admin/claims/<id>/lock` | ✅ | SHA-256, inmutable, versionado. |
| Transición de estado del claim | `POST /admin/claims/<id>/transition` | ✅ | DRAFT → READY → SUBMITTED → DENIED/PAID con validaciones. |
| EOB processing | `POST /admin/eob/claim/<id>` | ✅ | Crea payment + applications + adjustments por línea de servicio. |
| Aplicar copago al claim | `POST /admin/finances/application/new` | ⚠️ | No hay UI que conecte automáticamente el `copago_payment_id` de visit_session al claim correspondiente. Requiere aplicación manual por el FACTURADOR. |

---

## 3. ROLES — Sidebar y acceso por rol

### RECEPCION

| Ítem esperado (Referencia) | Presente en sidebar | Acceso correcto |
|---|---|---|
| Buscar paciente (AJAX) | ✅ | ✅ |
| Dashboard | ✅ | ✅ |
| Pacientes | ✅ | ✅ `@role_required("ADMIN","FACTURADOR","RECEPCION")` |
| Check-in | ✅ | ✅ `@role_required("ADMIN","RECEPCION")` |
| Agenda | ✅ | ✅ |

**✅ RECEPCION: Completo y correcto.**

### DRA

| Ítem esperado (Referencia) | Presente en sidebar | Acceso correcto |
|---|---|---|
| Dashboard | ✅ | ✅ |
| Mi Agenda | ✅ | ✅ |
| Encounters | ✅ | ✅ `@role_required("ADMIN","DRA")` |
| Notas | ✅ | ✅ |
| Doctor Dashboard *(extra, no en referencia)* | ✅ bonus | ✅ |

**✅ DRA: Completo y correcto. Un ítem extra (Doctor Dashboard) no especificado en la referencia, pero no problemático.**

### FACTURADOR

| Ítem esperado (Referencia) | Presente en sidebar | Estado |
|---|---|---|
| Buscar paciente (AJAX) | ✅ | ✅ |
| Dashboard | ✅ | ✅ |
| Pacientes | ❌ **FALTA** | ⚠️ Solo visible para ADMIN y RECEPCION en el sidebar |
| Check-in | ❌ **FALTA** | ⚠️ Solo visible para ADMIN y RECEPCION en el sidebar |
| Ready for Billing (badge) | ❌ **FALTA** | ❌ BI-4 no implementado |
| Claims | ✅ | ✅ |
| EOB | ✅ | ✅ |
| Reportes | ✅ | ✅ |

**⚠️ FACTURADOR: Le faltan "Pacientes" y "Check-in" en el sidebar.** El bloque condicional en `admin_base.html` usa `['ADMIN', 'RECEPCION']` para esos ítems, pero la referencia especifica que FACTURADOR también los necesita. "Ready for Billing" no existe aún (BI-4).

### ADMIN

| Ítem esperado (Referencia) | Presente en sidebar | Estado |
|---|---|---|
| Buscar paciente (AJAX) | ✅ | ✅ |
| Dashboard | ✅ | ✅ |
| Pacientes | ✅ | ✅ |
| Check-in | ✅ | ✅ |
| Ready for Billing (badge) | ❌ **FALTA** | ❌ BI-4 no implementado |
| Claims | ✅ | ✅ |
| EOB | ✅ | ✅ |
| Reportes | ✅ | ✅ |
| Agenda (sección Clínico) | ✅ | ✅ |
| Encounters | ✅ | ✅ |
| Notas | ✅ | ✅ |
| Settings | ✅ | ✅ |
| Event Ledger | ✅ | ✅ |

**⚠️ ADMIN: Solo falta "Ready for Billing" (BI-4 pendiente). Todo lo demás correcto.**

---

## 4. DATABASE — Tablas y columnas

### 4.1 Tablas con `_ensure_table()` o `CREATE TABLE IF NOT EXISTS` explícito

| Tabla | Módulo | CREATE TABLE | Columnas notables |
|---|---|---|---|
| `visit_sessions` | `db/visit_sessions.py` | ✅ | id, patient_id, appointment_date, status (CHECK constraint), check_in_time, in_session_time, completed_time, notes, created_by, created_at, updated_at, **eligibility_verified, copago_amount, copago_payment_id, referral_on_file, documents_signed** (BI-3) |
| `appointments` | `db/appointments.py` | ✅ | id, patient_id, encounter_id, scheduled_date, scheduled_time, service_type, status (CHECK constraint), notes, created_by, created_at, updated_at |

### 4.2 Tablas sin `_ensure_table()` (asumen existencia previa en DB)

| Tabla | Módulo | Estado | Migraciones |
|---|---|---|---|
| `patients` | `db/patients.py` | ✅ | `_ensure_patient_address_columns()` — migra address, city, state, zip_code, phone |
| `coverages` | `db/coverages.py` | ✅ | `referral_required INTEGER DEFAULT 0` migrado desde `visit_sessions._ensure_table()` (BI-3) |
| `encounters` | `db/encounters.py` | ⚠️ | Sin `_ensure_table()`. **No tiene columnas** `ready_for_billing`, `ready_for_billing_at`, `ready_for_billing_by` requeridas por la referencia para BI-4 |
| `progress_notes` | `db/progress_notes.py` | ✅ | `_ensure_progress_notes_schema()` — migra 16 columnas SOAP: patient_name, record_number, date_of_service, start_time, end_time, service_type, cpt_code, diagnosis_code, provider_name, provider_credentials, subjective, objective, assessment, plan, note_text, parent_note_id |
| `claims` | `db/claims.py` | ✅ | `_ensure_diagnosis_columns()` — migra diagnosis_1..12 y campos CMS-1500. **Falta columna `encounter_id`** para BI-5 |
| `services` | `db/services.py` | ✅ | Asumida existente |
| `charges` | `db/charges.py` | ✅ | Verificación de financial lock en cada escritura |
| `payments` | `db/payments.py` | ✅ | ALLOWED_METHODS = {cash, check, eft, other} |
| `applications` | `db/applications.py` | ✅ | |
| `adjustments` | `db/adjustments.py` | ✅ | |
| `cms1500_snapshots` | `db/cms1500_snapshot.py` | ✅ | Versionado, SHA-256, inmutable |
| `event_ledger` | `db/event_ledger.py` | ✅ | Append-only, auditado |

### 4.3 Columnas faltantes identificadas

| Tabla | Columnas faltantes | Impacto |
|---|---|---|
| `encounters` | `ready_for_billing INTEGER DEFAULT 0` | ❌ BI-4 no puede implementarse |
| `encounters` | `ready_for_billing_at TEXT` | ❌ BI-4 no puede implementarse |
| `encounters` | `ready_for_billing_by TEXT` | ❌ BI-4 no puede implementarse |
| `claims` | `encounter_id INTEGER` (FK a encounters) | ❌ BI-5 no puede implementarse |
| `visit_sessions` | `NO_SHOW` en CHECK constraint y en VALID_STATUSES | ⚠️ El flujo `WAITING → NO_SHOW` no puede ejecutarse |

### 4.4 Invariantes financieros verificados

| Invariante | Estado |
|---|---|
| Financial lock — `is_claim_locked()` verifica snapshot antes de cada write | ✅ |
| SHA-256 canonical JSON en snapshot | ✅ |
| Snapshot inmutable — no se puede agregar services/charges/applications post-lock | ✅ |
| Event Ledger append-only | ✅ |
| `create_payment()` rechaza amount <= 0 y method inválido | ✅ |

---

## 5. PIEZAS FALTANTES — Fases pendientes de implementación

### BI-4: Ready for Billing ❌ NO IMPLEMENTADO

**Qué falta en la base de datos:**
- Columnas `ready_for_billing INTEGER DEFAULT 0`, `ready_for_billing_at TEXT`, `ready_for_billing_by TEXT` en tabla `encounters`
- Migración `ALTER TABLE encounters ADD COLUMN ...` en `db/encounters.py`

**Qué falta en el backend:**
- Función `mark_ready_for_billing(encounter_id, marked_by)` en `db/encounters.py`
- Gate de validación que verifique ANTES de permitir marcar:
  1. Nota firmada (`progress_notes.signed = true` para el encounter)
  2. Encounter tiene `encounter_date` y `patient_id`
  3. Si `coverage.referral_required = true` → verificar `visit_session.referral_on_file = true`
- Errores específicos por cada condición fallida (no un error genérico)
- Ruta `POST /admin/encounters/<id>/ready-for-billing` en `admin_encounters.py`
- `@role_required("ADMIN","FACTURADOR")` — solo FACTURADOR puede marcarlo (nunca automático)

**Qué falta en el frontend:**
- Botón "Marcar Ready for Billing" en `encounter_detail.html` (visible solo para FACTURADOR/ADMIN)
- Mensajes de error específicos si falla la validación
- Badge con contador en sidebar para FACTURADOR y ADMIN
- Listado o filtro de encounters con `ready_for_billing = true` en `encounters_list.html`
- Alerta visual en dashboard de FACTURADOR

### BI-5: Claim desde Encounter ❌ NO IMPLEMENTADO

**Problema actual:**
El claim se crea en `POST /admin/new` a partir de `patient_id + coverage_id` directamente, sin ningún vínculo con un encounter. Viola la regla crítica: *"El claim se crea SIEMPRE desde un encounter con `ready_for_billing = true`"*.

**Qué falta:**
- Columna `encounter_id INTEGER` (FK a encounters) en tabla `claims`
- Migración `ALTER TABLE claims ADD COLUMN encounter_id INTEGER` en `db/claims.py`
- Actualizar `create_claim(patient_id, coverage_id, encounter_id)` para recibir y guardar `encounter_id`
- Ruta `POST /admin/encounters/<id>/create-claim` en `admin_encounters.py`
  - Verificar que `encounter.ready_for_billing = true` antes de crear
  - Heredar `patient_id`, `coverage_id`, `encounter_id` del encounter
- UI: botón "Crear Claim" en `encounter_detail.html` visible solo cuando `ready_for_billing = true`
- El flujo antiguo de crear claim desde `/admin/new` (sin encounter) debería quedar deprecado o eliminado

### BI-6: Consentimientos imprimibles ❌ NO IMPLEMENTADO

**Qué falta:**
- Plantillas HTML imprimibles para formulario HIPAA y consentimiento informado
- Ruta de generación (ej. `GET /admin/patients/<id>/consent/hipaa`)
- Botón en check-in o patient_detail para imprimir/generar PDF

### Nota sobre `visit_session → NO_SHOW` ⚠️

Según la referencia (sección 4, tabla de transiciones):
- `WAITING → NO_SHOW` — responsable: RECEPCION
- `NO_SHOW → cancela appointment asociado` — automático

**Estado actual:** `NO_SHOW` no está en `VALID_STATUSES` de `visit_sessions.py` ni en el CHECK constraint de la tabla. Debe agregarse.

### Nota sobre copago no conectado automáticamente ⚠️

El flujo BI-3 registra correctamente el `copago_payment_id` en `visit_session`, pero no existe ningún mecanismo que conecte ese payment al claim cuando se procesa el EOB. El FACTURADOR debe aplicarlo manualmente desde `/admin/finances/application/new`. Según la referencia (paso 25), esto es intencional: *"Aplica copago si había — application del copago"* es un paso manual del FACTURADOR. Sin embargo, no hay UI que le facilite ese paso mostrando el copago pendiente del visit_session asociado al claim.

---

## RESUMEN EJECUTIVO

```
ÍTEM                                            ESTADO
─────────────────────────────────────────────────────────────────
Registro de blueprints (28/28)                  ✅ COMPLETO
Imports utilitarios en main.py                  ✅ OK
Autenticación en claims_admin.py (7 rutas)      ❌ SIN PROTECCIÓN
claim_create() sin @login_required              ❌ ACCESO ANÓNIMO POSIBLE
Flujo check-in BI-3 (elegibilidad/copago/docs)  ✅ COMPLETO
Flujo appointment BI-2                          ✅ COMPLETO
Flujo encounter / notas SOAP                    ✅ COMPLETO
Firma de nota + addendum                        ✅ COMPLETO
Snapshot CMS-1500 + SHA-256 + financial lock    ✅ COMPLETO
Claim Scrubber                                  ✅ COMPLETO
EOB processing                                  ✅ COMPLETO
Event Ledger (audit trail)                      ✅ COMPLETO
visit_session NO_SHOW en VALID_STATUSES         ⚠️ FALTA
Encounter ↔ visit_session vínculo por FK        ⚠️ NO VINCULADOS
Copago → aplicar al claim (UI facilitadora)     ⚠️ MANUAL SIN GUÍA
Sidebar FACTURADOR: Pacientes y Check-in        ⚠️ FALTA en template
DB encounters: columnas ready_for_billing       ❌ NO EXISTEN
DB claims: columna encounter_id                 ❌ NO EXISTE
DB coverages: referral_required                 ✅ MIGRATION EN PLACE
BI-4 Ready for Billing (gate completo)          ❌ NO IMPLEMENTADO
BI-5 Claim desde Encounter                      ❌ NO IMPLEMENTADO
BI-6 Consentimientos imprimibles                ❌ NO IMPLEMENTADO
```

### Prioridades de acción recomendadas

**Urgente — Seguridad**
1. Agregar `@login_required` y `@role_required("ADMIN","FACTURADOR")` a las 6 rutas de `claims_admin.py`
2. Agregar `@login_required` y `@role_required("ADMIN","FACTURADOR")` a `claim_create()` en `admin_claims_list.py`

**Funcionalidad pendiente (en orden)**
3. **BI-4** — Columnas en `encounters` + función `mark_ready_for_billing()` + gate de validación + UI + badge en sidebar
4. **BI-5** — Columna `encounter_id` en `claims` + flujo de creación desde encounter
5. Agregar `NO_SHOW` a `VALID_STATUSES` de visit_sessions y al CHECK constraint de la tabla
6. Agregar Pacientes y Check-in al sidebar del rol FACTURADOR en `admin_base.html`
7. **BI-6** — Consentimientos imprimibles (HIPAA, consentimiento informado)

---

*Documento generado por auditoría automática — solo lectura.*
*Referencia: `LIFETRACK_REFERENCIA.md` v2.0 — Psynántisi, Puerto Rico, Marzo 2026*
