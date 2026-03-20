LIFETRACK — FASES COMPLETAS DEL PROYECTO

✅ FASES COMPLETADAS
Fundación

Fase A — Estructura inicial del proyecto
Fase B — Modelo de pacientes
Fase C — Modelo de coberturas

Motor Financiero

Fase D — Charges
Fase E — Payments
Fase F — Applications
Fase G — Adjustments

Claims Engine

Fase H — Claims lifecycle

Clearinghouse Core

Fase I — CMS-1500 snapshot
Fase J — Snapshot freeze
Fase K — Snapshot hashing
Fase L — Snapshot versioning
Fase M — Snapshot PDF export

Auditoría

Fase N — Event ledger + performed_by (quién hizo qué)

Admin UI

Fase O — Admin dashboard
Fase P — Patients UI (formulario completo con dirección, casilla 5)
Fase Q — Services UI
Fase R — Claims UI (claim detail, claim edit, claim lock)
Fase S — Finances UI
Fase T — Reports UI
Fase U — Settings UI (Provider Settings, Users management)

Seguridad

Fase V — Authentication
Fase W — Role security (ADMIN, DRA, FACTURADOR, RECEPCION)

Clinical Base

Fase X — Clinical navigation
Fase Y — Encounters engine
Fase Z — Progress notes
Fase AA — Note editor

Clinical Avanzado

Fase J5 — Clinical Signature Engine (firmar nota, bloquear edición)
Fase J6 — Addendum Engine (correcciones legales al final de nota)
Fase J7 — Clinical Timeline (expediente cronológico por paciente)
Fase J8 — Encounter Creation UI
Fase J9 — Service Linking (encounter → service)
Fase J10 — Doctor Dashboard
Fase J11 — Clinical Audit Trail
Fase J12 — UX Professionalization (logout, active menu, badges)
Fase J13 — Patient Chart (expediente completo)
Fase J14 — Safety Locks (protecciones clínicas y financieras)

CMS-1500 Completa

Fase CMS1 — Casillas 1-3 (plan, paciente, DOB/sex)
Fase CMS2 — Casillas 4, 6, 7 (insured name, relationship, address)
Fase CMS3 — Casilla 5 (patient address — dirección del paciente)
Fase CMS4 — Casilla 8 (patient status — checkboxes)
Fase CMS5 — Casillas 10, 14-23, 27 (claim edit form completo)
Fase CMS6 — Casilla 21 A-L (diagnósticos ICD-10 múltiples)
Fase CMS7 — Casilla 24F (charges amount)
Fase CMS8 — Casillas 25, 31, 32, 33 (provider settings)


🔄 FASES PENDIENTES
Fase BB — Claim Scrubber ← PRÓXIMA
Objetivo: Validar el claim antes de bloquearlo para evitar rechazos.
El sistema debe verificar automáticamente que no falta nada crítico antes
de generar el CMS-1500. Funciona como el "claim scrubbing" que hacen los
clearinghouses reales.
Qué valida:

Paciente tiene nombre, DOB, sexo, dirección
Coverage tiene insurer, plan, policy number, insured name
Claim tiene al menos un diagnóstico ICD-10 (casilla 21A)
Claim tiene al menos un service con CPT válido
Service tiene charge amount mayor a 0
Provider settings tiene NPI, Tax ID, billing name, facility
Todos los campos críticos de la CMS-1500 están completos

Qué produce:

Lista de errores que BLOQUEAN el envío (campos obligatorios)
Lista de advertencias que NO bloquean pero deben revisarse
Badge visual en el claim: LISTO PARA ENVIAR / TIENE ERRORES / TIENE ADVERTENCIAS

Resultado: El facturador sabe exactamente qué falta antes de imprimir la 1500.

Fase BC — Flujo de Check-in (Recepción)
Objetivo: Una sola pantalla para registrar la llegada de un paciente.
Flujo:

Recepcionista busca paciente por nombre
Sistema muestra estado del paciente:

¿Tiene coverage vigente? ✅ / ⚠️ Vence pronto / ❌ No tiene
¿Tiene claim abierto? ✅ / ❌ Crear nuevo
¿Falta algún dato para la 1500? Lista de advertencias


Recordatorios automáticos:

"Solicitar copia de tarjeta del plan médico"
"Verificar que el plan esté activo"
"Confirmar dirección del paciente"
"Obtener copago si aplica"


Botón: "Registrar visita de hoy" → crea encounter automáticamente

Resultado: Recepcionista hace todo desde una pantalla sin saltar menús.

Fase BD — Dashboard Operacional por Rol
Objetivo: Cada usuario ve lo que necesita al entrar al sistema.
RECEPCION: Pacientes de hoy, citas pendientes, check-in rápido
DRA: Notas sin firmar, encounters del día, pacientes en sesión
FACTURADOR: Claims pendientes de envío, errores del scrubber, pagos por aplicar
ADMIN: Resumen general, alertas del sistema, estado financiero

Fase BE — EOB / Remittance Processing
Objetivo: Registrar el pago del seguro cuando llega el EOB.
Flujo:

Facturador recibe EOB del seguro
Entra al claim correspondiente
Registra:

Monto pagado por el seguro
Ajuste contractual (diferencia entre lo facturado y lo permitido)
Responsabilidad del paciente si aplica


Sistema calcula balance final automáticamente
Claim pasa a status PAID si balance = 0

Resultado: Trazabilidad completa del pago, balance correcto en la 1500.

Fase BF — Búsqueda y Filtros Globales
Objetivo: Poder encontrar cualquier paciente, claim o nota rápidamente.
Qué incluye:

Búsqueda de paciente por nombre desde cualquier pantalla
Filtro de claims por status (DRAFT, SUBMITTED, PAID, DENIED)
Filtro de claims por fecha
Filtro de encounters por fecha y paciente


Fase BG — Reportes Clínicos y Financieros
Objetivo: Reportes útiles para la operación de la oficina.
Reportes:

Claims por período (cuánto se facturó, cuánto se cobró)
Claims pendientes de cobro por aseguradora
Pacientes activos vs inactivos
Servicios más frecuentes (CPT más usado)
Balance por paciente


Fase BH — Navegación Horizontal (UI)
Objetivo: Cambiar el menú de sidebar vertical a navegación horizontal.
Solo CSS — no toca lógica. El menú pasa de estar a la izquierda a estar
en la parte superior de forma horizontal.

Fase BI — Impresión y Exportes
Objetivo: Poder imprimir o exportar información clínica y financiera.
Incluye:

Imprimir nota clínica firmada (ya existe parcialmente)
Exportar historial de claims a PDF
Exportar EOB registrados
Exportar lista de pacientes


Fase BJ — Integración Final Clínica-Operacional
Objetivo: Alinear completamente el flujo doctor → recepción → facturación.
El sistema debe guiar a cada rol en su trabajo sin que tengan que saber
cómo funciona el sistema internamente.

📋 ORDEN DE EJECUCIÓN RECOMENDADO
BB  Claim Scrubber          ← EMPEZAMOS AQUÍ
BC  Check-in Recepción
BD  Dashboard por Rol
BE  EOB / Remittance
BF  Búsqueda y Filtros
BG  Reportes
BH  Navegación Horizontal
BI  Impresión y Exportes
BJ  Integración Final

🏗️ ARQUITECTURA DEL SISTEMA
Paciente llega
↓
Check-in (BC) → Recepcionista registra llegada
↓
Encounter → Doctora abre sesión
↓
Progress Note → Nota SOAP firmada
↓
Service + CPT + ICD-10 → Servicio facturado
↓
Charge → Cargo financiero
↓
Claim → Claim scrubber (BB) valida todo
↓
CMS-1500 → Generado sin errores
↓
Envío manual al seguro
↓
EOB llega (BE) → Payment registrado y aplicado
↓
Balance final

Última actualización: Marzo 2026