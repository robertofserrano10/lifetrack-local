# LIFETRACK — PSYNÁNTISI
## Documento de Referencia del Sistema
*Puerto Rico · Marzo 2026 · v2.0 APROBADO*

---

## 1. LA OFICINA

**Nombre:** Psynántisi  
**Tipo:** Oficina de psicología privada — Puerto Rico  
**Aseguradoras:** Triple-S, MCS, Humana (principales en PR)  
**Propósito del sistema:** Clearinghouse local para generar CMS-1500 sin errores y reducir denegaciones

---

## 2. PERSONAS QUE USAN EL SISTEMA

| Rol | Quién es | Qué hace en el sistema |
|-----|----------|------------------------|
| ADMIN | Roberto (dueño) | Todo — configuración, usuarios, reportes |
| DRA | Doctora | Agenda, encounters, notas SOAP, firma, próxima cita |
| RECEPCION | Recepcionista | Check-in, pacientes, copago — SIN acceso a finanzas |
| FACTURADOR | Facturador/Recepcionista | Check-in + claims + EOB + reportes (misma persona hoy) |

**Nota importante:** FACTURADOR y RECEPCION pueden ser la misma persona.  
Cuando llegue la recepcionista futura, solo tendrá rol RECEPCION — sin acceso financiero.

---

## 3. FLUJO COMPLETO DE UNA VISITA

```
PASO  ROL              ACCIÓN                              ESTADO RESULTANTE
────  ───────────      ──────────────────────────────      ─────────────────────
1     RECEPCION        Busca paciente en sistema           —
2     RECEPCION        Verifica cita del día               —
3     RECEPCION        Verifica elegibilidad (manual)      eligibility_verified = true
4     RECEPCION        Registra copago si aplica           payment creado (no aplicado)
5     RECEPCION        Verifica referido si el plan pide   referral_on_file = true/false
6     RECEPCION        Entrega y marca documentos          hipaa ✓, consent ✓
7     RECEPCION        Hace CHECK-IN                       visit_session: WAITING
8     DRA              Ve paciente en su dashboard         —
9     DRA              Abre encounter                      visit_session: IN_SESSION
10    DRA              Escribe nota SOAP                   encounter: IN_PROGRESS
11    DRA              Agenda próxima cita                 appointment creado
12    DRA              Firma nota                          progress_note: signed = true
13    DRA              Cierra encounter                    visit_session: COMPLETED
14    FACTURADOR       Ve encounter en "Ready for Billing" —
15    FACTURADOR       Verifica nota firmada + referido    —
16    FACTURADOR       Marca "Ready for Billing"           encounter: ready_for_billing
17    FACTURADOR       Crea claim DESDE el encounter       claim: DRAFT
18    FACTURADOR       Agrega CPT + ICD-10                 services + diagnoses
19    FACTURADOR       Corre Claim Scrubber                errores/advertencias
20    FACTURADOR       Lock + genera CMS-1500              snapshot inmutable
21    FACTURADOR       Cambia status a SUBMITTED           claim: SUBMITTED
22    FACTURADOR       Envía CMS-1500 por correo           — (proceso manual externo)
23    FACTURADOR       Recibe EOB del seguro               —
24    FACTURADOR       Registra pago del seguro            payment + applications
25    FACTURADOR       Aplica copago si había              application del copago
26    Sistema          Calcula balance final               claim: PAID si balance = 0
```

---

## 4. ESTADOS DE CADA ENTIDAD

### visit_session (check-in)
```
ARRIVED → CHECKED_IN → WAITING → IN_SESSION → COMPLETED
                                            → CANCELLED
                                            → NO_SHOW
```
| Transición | Responsable | Cuándo |
|-----------|-------------|--------|
| ARRIVED → CHECKED_IN | RECEPCION | Al completar formularios y copago |
| CHECKED_IN → WAITING | Automático | Al completar check-in |
| WAITING → IN_SESSION | DRA | Al abrir encounter |
| IN_SESSION → COMPLETED | DRA | Al cerrar encounter |
| WAITING → NO_SHOW | RECEPCION | Si paciente no se presenta |
| NO_SHOW | Sistema | Cancela appointment asociado automáticamente |

### encounter
```
OPEN → IN_PROGRESS → SIGNED → READY_FOR_BILLING → BILLED
```

### progress_note (nota SOAP)
```
DRAFT → SIGNED (inmutable después de firma)
```
- Nota firmada no se puede editar
- Correcciones solo mediante addendum

### appointment (cita)
```
SCHEDULED → CONFIRMED → ARRIVED → COMPLETED
                               → CANCELLED
                               → NO_SHOW
```

### claim
```
DRAFT → READY → SUBMITTED → PAID
                          → DENIED → READY (resubmisión)
```

---

## 5. REGLAS DE NEGOCIO CRÍTICAS

### Elegibilidad
- Campo obligatorio: `eligibility_verified = true`
- Registrado por: RECEPCION antes del check-in
- Sin verificación → no se puede hacer check-in
- No hay integración automática con aseguradoras — solo confirmación manual

### Copago
- Depende del plan — no es fijo
- Se cobra ANTES de la sesión
- Se registra como `payment` con estado no-aplicado
- Se aplica al claim después via `application`
- Nunca se conecta automáticamente

### Referido
- Depende del plan
- Campo `referral_required` en coverage
- Campo `referral_on_file` en visit_session
- Si `required = true` y `on_file = false`:
  - NO bloquea el encounter clínico
  - SÍ bloquea "Ready for Billing"
  - Muestra alerta visual prominente en dashboard y encounter

### Ready for Billing
- **Responsable único: FACTURADOR**
- **Nunca automático** — ni siquiera al firmar la nota
- El sistema VERIFICA antes de permitirlo:
  1. Nota firmada (`signed = true`)
  2. Encounter tiene fecha y paciente
  3. Si referido requerido → `referral_on_file = true`
- Si alguna condición falla → error específico, no permite avanzar

### Claim desde Encounter
- El claim se crea SIEMPRE desde un encounter con `ready_for_billing = true`
- Nunca desde cero sin contexto clínico
- El claim hereda: patient_id, coverage_id, encounter_id
- CPT + ICD-10 los asigna el FACTURADOR (no la DRA)

### Nota clínica
- La DRA escribe el contexto clínico (SOAP)
- La DRA firma → nota bloqueada, no editable
- Correcciones → addendum (nota nueva vinculada)
- La DRA NO asigna CPT ni ICD-10 — eso es billing

### Snapshot CMS-1500
- Se genera al hacer "Lock" del claim
- Es inmutable — SHA-256 hash
- Una vez bloqueado: no se pueden agregar services, charges, applications
- Versionado: resubmisión genera version N+1

---

## 6. ENTIDADES DE LA BASE DE DATOS

### Tablas existentes (no tocar lógica)
```
users               → roles y autenticación
patients            → demographics + address + phone
coverages           → seguro + insured info + referral_required
encounters          → visita clínica
progress_notes      → nota SOAP + firma + addendum
visit_sessions      → check-in operacional
claims              → claim financiero + diagnoses 1-12
services            → CPT codes por claim
charges             → deuda creada por servicio
payments            → dinero recibido
applications        → pago aplicado a cargo
adjustments         → ajuste contractual
cms1500_snapshots   → snapshot inmutable CMS-1500
event_ledger        → auditoría de todo
```

### Tablas nuevas (pendientes de implementar)
```
appointments        → citas formales
  patient_id
  encounter_id (nullable — null si es primera cita)
  scheduled_date    → YYYY-MM-DD
  scheduled_time    → HH:MM
  service_type      → "Evaluación", "Seguimiento", "Crisis", etc.
  status            → SCHEDULED|CONFIRMED|ARRIVED|COMPLETED|CANCELLED|NO_SHOW
  notes
  created_by
```

### Campos nuevos en visit_sessions (pendientes)
```
eligibility_verified    BOOLEAN DEFAULT 0
copago_amount           REAL DEFAULT 0
copago_payment_id       INTEGER (FK payments, nullable)
referral_on_file        BOOLEAN DEFAULT 0
documents_signed        TEXT (JSON: {"hipaa": bool, "consent": bool})
```

### Campos nuevos en encounters (pendientes)
```
ready_for_billing       BOOLEAN DEFAULT 0
ready_for_billing_at    TEXT
ready_for_billing_by    TEXT
```

---

## 7. PALETA DE COLORES PSYNÁNTISI

```css
/* Colores de marca */
--psy-navy:       #201751;   /* Azul oscuro — primario */
--psy-coral:      #EA6852;   /* Coral — acento principal */
--psy-coral-mid:  #F8A183;   /* Coral medio — hover, badges */
--psy-coral-soft: #FDCDA8;   /* Melocotón — backgrounds suaves */
--psy-blue-light: #A1BDE3;   /* Azul claro — sidebar text, secundario */

/* Sistema — Light Mode */
--accent:         #EA6852;
--accent-hover:   #d4563f;
--accent-soft:    rgba(253, 205, 168, 0.25);
--bg:             #F9F7F5;
--card-bg:        #FFFFFF;
--text:           #1a1a2e;
--sidebar-bg:     #201751;
--sidebar-text:   #A1BDE3;
--header-bg:      #201751;
--border:         #e8e0d8;
--shadow:         0 2px 8px rgba(32, 23, 81, 0.08);

/* Sistema — Dark Mode */
--bg:             #0f0e1a;
--card-bg:        #1a1833;
--text:           #f0eee8;
--sidebar-bg:     #160f3a;
--sidebar-text:   #A1BDE3;
--header-bg:      #160f3a;
--border:         #2a2550;
--shadow:         0 2px 8px rgba(0, 0, 0, 0.3);
```

### Logo
- Archivo: `Psynántisi_Logo-9.png` (versión con colores de marca)
- Ubicación en sistema: sidebar, discreto, sin llamar atención
- Alternativa dark mode: `Psynántisi_Logo-10.png` (versión blanca)

---

## 8. SIDEBAR POR ROL

### RECEPCION
```
[Logo Psynántisi]
🔍 Buscar paciente
─────────────────
📊 Dashboard
👤 Pacientes
🚪 Check-in
📅 Agenda
```

### DRA
```
[Logo Psynántisi]
─────────────────
📊 Dashboard
📅 Mi Agenda
🩺 Encounters
📝 Notas
```

### FACTURADOR
```
[Logo Psynántisi]
🔍 Buscar paciente
─────────────────
📊 Dashboard
👤 Pacientes
🚪 Check-in
✅ Ready for Billing  ← badge con número pendiente
📄 Claims
💵 EOB
📊 Reportes
```

### ADMIN
```
[Logo Psynántisi]
🔍 Buscar paciente
─────────────────
📊 Dashboard
👤 Pacientes
🚪 Check-in
✅ Ready for Billing
📄 Claims
💵 EOB
📊 Reportes
── Clínico ──────
📅 Agenda
🩺 Encounters
📝 Notas
── Admin ─────────
⚙️  Settings
📋 Event Ledger
```

---

## 9. DASHBOARDS POR ROL

### RECEPCION
- Agenda del día (appointments de hoy)
- Sala de espera (visit_sessions activos)
- Botón rápido "Registrar llegada"

### DRA
- Mi agenda (appointments de hoy + próximos)
- Pacientes esperando (WAITING)
- Paciente en sesión (IN_SESSION)
- Notas sin firmar (urgente)

### FACTURADOR
- Encounters Ready for Billing (con badge de alerta)
- Claims pendientes de envío (DRAFT)
- EOBs pendientes de aplicar
- Pendiente de cobro total ($)

### ADMIN
- Resumen general
- Alertas del sistema
- Acceso rápido a todo

---

## 10. FASES DE IMPLEMENTACIÓN PENDIENTES

```
✅ COMPLETADO:
  BB — Claim Scrubber
  BC — Check-in básico
  BD — Dashboards por rol
  BE — EOB Processing
  BF — Búsqueda global
  BG — Reportes
  BH — Navegación sidebar por rol

PENDIENTE (en orden):
  BI-1 — Colores y logo Psynántisi
  BI-2 — Appointments (tabla + UI)
  BI-3 — Check-in mejorado (elegibilidad, copago, referido, documentos)
  BI-4 — Ready for Billing (gate de control en encounters)
  BI-5 — Claim desde Encounter (flujo correcto)
  BI-6 — Consentimientos imprimibles (HIPAA, consentimiento informado)
  BJ   — Integración final y pruebas end-to-end
```

---

## 11. ARQUITECTURA TÉCNICA

```
Stack:        Python + Flask + SQLite + Jinja2
Sin ORM:      Raw SQL con sqlite3.Row
Sin async:    Completamente síncrono
Auth:         Session-based con @login_required + @role_required
DB:           storage/lifetrack.db (archivo único)
Migraciones:  _ensure_*_columns() en cada módulo DB (backward compat)
Lock:         Financial lock en Python antes de cada write (no DB constraint)
Hash:         SHA-256 canonical JSON para snapshot integrity
```

---

## 12. INVARIANTES QUE NO SE TOCAN

1. **Motor financiero** — charges, payments, applications, adjustments — lógica intacta
2. **Snapshot CMS-1500** — inmutable, hashed, versionado — no se modifica
3. **Claim Scrubber** — solo se expande con nuevas validaciones
4. **Event Ledger** — append-only, todo queda auditado
5. **Financial Lock** — una vez hay snapshot, el claim es inmutable
6. **Separación de dominios** — operacional / clínico / financiero — nunca mezclar

---

*Este documento es la fuente de verdad del proyecto.*  
*Ante cualquier duda de implementación, consultar aquí primero.*  
*Última actualización: Marzo 2026*