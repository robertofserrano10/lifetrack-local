FASES FALTANTES — EXPLICADAS PASO A PASO

ESTADO ACTUAL
- J5: planeado
- J6: planeado
- J7: planeado
- J8: completado (encounters)
- J9: completado (encounter->service linking)
- J10, J11, J12, J13: completados
- J14: completado (Safety Locks, freeze rules)

FASE J5 — Clinical Signature Engine
Objetivo

Convertir una nota clínica en registro médico legal.

Problema que resuelve

Ahora mismo una nota se puede crear, pero todavía no existe el momento formal de:

firmarla

cerrarla legalmente

impedir edición posterior

Sin eso, la nota sigue siendo solo un borrador.

Qué se debe construir

Campo de firma lógica en progress_notes

signed

signed_at

status

Ruta para firmar una nota

recibe note_id

cambia estado de DRAFT a SIGNED

guarda timestamp

UI con botón Sign Note

solo visible si la nota está en DRAFT

solo para ADMIN y DRA

Regla de bloqueo

si la nota está SIGNED, ya no puede editarse

Flujo esperado
Create Note
→ Edit Note
→ Sign Note
→ Note Locked
Resultado final

La nota deja de ser editable y se convierte en expediente clínico formal.

FASE J6 — Addendum Engine
Objetivo

Permitir correcciones clínicas sin alterar la nota firmada.

Problema que resuelve

En medicina, una nota firmada no se modifica directamente.
Si falta algo o hay que aclarar algo, se agrega un addendum.

Qué se debe construir

Extender progress_notes con:

parent_note_id nullable

Definir dos tipos de nota:

nota original

addendum

Ruta para crear addendum

recibe note_id original

crea nueva nota vinculada

UI

botón Add Addendum solo en notas firmadas

mostrar relación visual entre original y addendum

Flujo esperado
Signed Note
→ Add Addendum
→ New linked entry
Resultado final

La nota original queda intacta y el expediente conserva integridad legal.

FASE J7 — Clinical Timeline
Objetivo

Construir una vista cronológica del historial clínico del paciente.

Problema que resuelve

Ahora la información clínica está separada en pantallas aisladas:

encounters

notes

servicios

claims

Hace falta una vista unificada.

Qué se debe construir

Nueva pantalla /admin/clinical

Query que reúna eventos clínicos por paciente

Orden cronológico descendente

Mostrar:

encounter

note

signed note

addendum

service asociado

claim asociado

snapshot si existe

Flujo esperado
Patient Clinical Activity
→ chronological timeline
Resultado final

La doctora y admin pueden ver el historial clínico en secuencia real.

FASE J8 — Encounter Creation UI
Objetivo

Permitir crear encounters desde la interfaz.

...

FASE J14 — Safety Locks
Objetivo

Asegurar que los claims con snapshot queden inmutables en el _core billing_ y cumplir with freezing rules.

Problema que resuelve

En el estado anterior, los datos se podían seguir editando tras el cierre monetario y no había señal de bloqueo visible en UI.

Qué se debe construir

- En `claim_detail` agregar botón "Lock Claim (Create Snapshot)"
- Botón visible solo cuando `is_claim_locked` es False
- Acción POST /admin/claims/<id>/lock -> `generate_cms1500_snapshot`
- Registrar evento `claim_manual_lock` en `event_ledger`
- Cuando el claim está locked, bloquear creación de service/charges/payments desde DB ya existe en los repos.

Flujo esperado

Claim DRAFT/READY -> lock manual -> snapshot creado

Resultado final

Claim congelado; cliente ve badge LOCKED y no puede mutar logro financiero.

FASE J8 — Encounter Creation UI
Objetivo

Permitir crear encounters desde la interfaz.

Problema que resuelve

Ahora los encounters existen en DB, pero no tienen flujo normal de creación desde UI.

Qué se debe construir

Pantalla New Encounter

Formulario con:

paciente

fecha

provider

location opcional

status inicial

Ruta POST de creación

Redirección a detalle del encounter o a notas

Flujo esperado
Open Clinical Module
→ New Encounter
→ Save
→ Encounter created
Resultado final

La capa clínica deja de depender de inserts manuales.

FASE J9 — Encounter Detail + Service Linking
Objetivo

Conectar clínico y billing de forma segura.

Problema que resuelve

El flujo clínico y el de facturación aún viven paralelos.
Falta trazabilidad entre el acto clínico y el servicio CPT facturado.

Qué se debe construir

Campo opcional encounter_id en services

Vista de detalle del encounter

Mostrar dentro del encounter:

notas

servicios ligados

claim asociado si existe

Crear o vincular servicio desde encounter

Regla crítica

encounter_id debe ser opcional para no romper servicios viejos.

Flujo esperado
Encounter
→ Note
→ Service CPT linked
→ Charge
→ Claim
Resultado final

Queda trazabilidad clínica → administrativa sin romper el CMS-1500.

FASE J10 — Doctor Dashboard
Objetivo

Crear el panel real de la doctora.

Problema que resuelve

Ahora Clinical es solo un acceso.
La DRA necesita una vista operativa real.

Qué se debe construir

Dashboard específico con:

encounters de hoy

notas draft

notas sin firmar

pacientes recientes

actividad clínica reciente

Flujo esperado
Login as DRA
→ Doctor Dashboard
→ work queue
Resultado final

La DRA tiene un panel clínico utilizable, no solo navegación.

FASE J11 — Clinical Audit Trail
Objetivo

Agregar auditoría propia del módulo clínico.

Problema que resuelve

El clearinghouse ya tiene event_ledger, pero las acciones clínicas aún no quedan auditadas formalmente.

Qué se debe construir

Tabla clinical_events o integrar eventos clínicos al ledger existente

Registrar:

encounter_created

note_created

note_updated

note_signed

addendum_created

Mostrar auditoría por encounter o por paciente

Flujo esperado
doctor action
→ audit event stored
Resultado final

La capa clínica obtiene trazabilidad legal y operativa.

FASE J12 — UX Professionalization
Objetivo

Mejorar la experiencia visual y operativa del sistema.

Problema que resuelve

Ahora el sistema funciona, pero se ve básico y algunas vistas carecen de claridad.

Qué se debe trabajar

Botón de logout en header

Highlight del menú activo

Empty states claros

Tablas más legibles

Mejor spacing

Mejor jerarquía visual

Búsqueda y filtros

Badges de estado

Mejor dark mode

Resultado final

La aplicación deja de verse “funcional pero simple” y se convierte en herramienta profesional.

FASE J13 — Patient Chart
Objetivo

Crear la vista integral del paciente.

Problema que resuelve

La información del paciente está distribuida en módulos separados.

Qué se debe construir

Una vista que reúna:

demographics

coverages

encounters

progress notes

services

claims

snapshots

activity timeline

Flujo esperado
Open Patient
→ Full chart
Resultado final

El paciente pasa a tener expediente clínico-administrativo consolidado.

FASE J14 — Safety Locks
Objetivo

Cerrar reglas de protección clínica para evitar corrupción del expediente.

Qué se debe bloquear

no editar nota firmada

no borrar nota firmada

no borrar encounter con notas

no borrar encounter con servicios vinculados

no crear addendum sobre draft

no firmar nota vacía

Resultado final

El módulo clínico se vuelve robusto y seguro.

POSIBLES FASES POSTERIORES
FASE K — Integración Clínica-Operacional Final

Aquí se alinea completamente:

doctor workflow

recepción

facturador

admin

para que el sistema se use como producto real.

FASE L — Optimización Legal y Operativa

Ajustes finos:

impresión clínica

exportes

búsqueda avanzada

reportes clínicos

control de consistencia clínica vs billing

ORDEN RECOMENDADO EXACTO

Este es el orden correcto para no romper nada:

J5  Clinical Signature Engine
J6  Addendum Engine
J7  Clinical Timeline
J8  Encounter Creation UI
J9  Encounter Detail + Service Linking
J10 Doctor Dashboard
J11 Clinical Audit Trail
J12 UX Professionalization
J13 Patient Chart
J14 Safety Locks
TRABAJOS CONCRETOS PENDIENTES
Núcleo clínico

firmar nota

bloquear nota firmada

crear addendum

crear encounter desde UI

mostrar detalle encounter

ligar services a encounter

Auditoría

registrar eventos clínicos

mostrar historial clínico

UI

clinical dashboard real

patient chart

logout button

active menu highlight

empty states

filtros y búsqueda

mejora visual general

Integridad

safety locks clínicos

validaciones de firma

validaciones de addendum

validaciones encounter-service