# LIFETRACK — HOJA DE RUTA HACIA PRODUCCIÓN Y PRODUCTO
## Plan completo · Puerto Rico · Marzo 2026
*20 horas semanales · Local-first · Multi-oficina desde el inicio*

---

## VISIÓN

LifeTrack es el único sistema de facturación médica local diseñado
específicamente para oficinas de psicología en Puerto Rico.

No requiere internet. No depende de terceros. Los datos del paciente
nunca salen de la oficina. El CMS-1500 sale correcto la primera vez.

---

## ESTADO ACTUAL

✅ Núcleo financiero — charges, payments, applications, adjustments
✅ CMS-1500 snapshot inmutable con SHA-256
✅ Claim Scrubber — valida antes de enviar
✅ Flujo clínico — encounter, nota SOAP, firma, addendum
✅ Check-in con elegibilidad, copago, referido, documentos
✅ Ready for Billing — gate de control
✅ Claim desde Encounter — trazabilidad completa
✅ EOB Processing — pago del seguro aplicado correctamente
✅ Agenda — appointments con visibilidad por rol
✅ Reportes financieros — 4 reportes en español
✅ Búsqueda global de pacientes
✅ Consentimientos imprimibles — HIPAA + Consentimiento Informado
✅ Dashboards por rol — ADMIN, DRA, RECEPCION, FACTURADOR
✅ Test E2E — 17/17 pasos verdes

---

## FASES PENDIENTES

---

### FASE P1 — LIMPIEZA Y CONFIGURACIÓN PARA PRODUCCIÓN
**Tiempo estimado: 1 semana**
**Prioridad: CRÍTICA — hacer esto antes de usar el sistema**

**P1-1: Limpiar base de datos de prueba**
- Script que elimina todos los datos de prueba
- Conserva solo los usuarios reales y el Provider Settings
- Deja la DB limpia para el primer día de uso real

**P1-2: Configurar Provider Settings real**
- Nombre real de la doctora y credenciales
- NPI real
- Tax ID real
- Dirección real de la facilidad
- Firma digital (nombre en texto por ahora)

**P1-3: Crear usuarios de producción**
- Cambiar contraseña del ADMIN
- Crear usuario DRA con contraseña segura
- Crear usuario FACTURADOR con contraseña segura
- Eliminar usuarios de prueba

**P1-4: Clave secreta de producción**
- Reemplazar `dev-secret-key` con clave aleatoria de 32 caracteres
- Guardar la clave en archivo `.env` fuera del repositorio
- Nunca subir la clave a GitHub

---

### FASE P2 — SEGURIDAD Y ESTABILIDAD
**Tiempo estimado: 1-2 semanas**
**Prioridad: CRÍTICA para producción**

**P2-1: Servidor de producción**
- Reemplazar Flask dev server con Waitress (Windows-compatible)
- Script de inicio: `start_lifetrack.bat`
- Auto-inicio con Windows al encender la computadora

**P2-2: Backup automático**
- Script que copia `lifetrack.db` a una carpeta de backup cada día
- Mantiene los últimos 30 días de backups
- Alerta visual en el sistema si el último backup tiene más de 48 horas

**P2-3: HTTPS local (opcional pero recomendado)**
- Certificado auto-firmado para conexión local segura
- Evita que otros dispositivos en la red accedan sin autorización

**P2-4: Logs de seguridad**
- Registrar intentos de login fallidos
- Bloquear IP después de 5 intentos fallidos
- Log de acceso por usuario y hora

**P2-5: Validación de contraseñas**
- Contraseñas mínimo 8 caracteres
- Requerir cambio de contraseña en primer login
- Expiración de sesión después de inactividad

---

### FASE P3 — FLUJO Y UX PROFESIONAL
**Tiempo estimado: 2 semanas**
**Prioridad: ALTA — impacta la experiencia diaria**

**P3-1: Flujo guiado de check-in**
- Cuando la recepcionista busca un paciente que tiene cita hoy,
  el sistema lo sugiere automáticamente
- Botón "Check-in rápido" desde la agenda

**P3-2: Conexión Agenda → Check-in**
- Al hacer check-in desde una cita, el appointment se actualiza
  a status ARRIVED automáticamente
- La cita aparece marcada en la agenda

**P3-3: Notificaciones en dashboard**
- DRA: badge rojo cuando hay pacientes esperando
- FACTURADOR: badge rojo cuando hay encounters Ready for Billing
- RECEPCION: indicador de sala de espera en tiempo real

**P3-4: Flujo post-sesión para DRA**
- Al completar el encounter, sistema pregunta:
  "¿Desea agendar próxima cita ahora?"
- Pre-llena la fecha sugerida (2 semanas por defecto)
- El appointment queda vinculado al encounter

**P3-5: Historial del paciente integrado**
- Vista unificada: demographics + coverages + appointments +
  encounters + notas + claims + pagos
- En una sola página, ordenado cronológicamente

**P3-6: Mensajes de error amigables**
- Reemplazar errores técnicos de Python con mensajes en español
- Página 404 y 500 con diseño de Psynántisi

---

### FASE P4 — FUNCIONALIDAD CLÍNICA COMPLETA
**Tiempo estimado: 1-2 semanas**
**Prioridad: ALTA**

**P4-1: Campo "unknown" en eventos**
- Corregir que el sistema siempre capture el usuario real
  en eventos como Ready for Billing
- Afecta: event_ledger, ready_for_billing_by

**P4-2: Impresión de nota clínica**
- Botón "Imprimir Nota" en nota firmada
- Formato profesional con logo Psynántisi
- Incluye: datos del paciente, SOAP, firma de la doctora

**P4-3: Manejo de No-Show**
- Cuando se marca NO_SHOW en check-in:
  - Appointment pasa a NO_SHOW
  - Opción de reagendar directamente
  - Registro en event_ledger

**P4-4: Filtros en listas**
- Claims: filtrar por status, fecha, aseguradora
- Pacientes: filtrar por nombre, aseguradora
- Appointments: filtrar por fecha, status

**P4-5: Nota de cancelación de política**
- Cuando hay un NO_SHOW, opción de registrar
  cargo de cancelación tardía si aplica

---

### FASE P5 — REPORTES Y MÉTRICAS
**Tiempo estimado: 1 semana**
**Prioridad: MEDIA**

**P5-1: Reporte de productividad**
- Sesiones por mes
- Ingresos brutos vs cobrado
- Tasa de cobro por aseguradora

**P5-2: Reporte de aging**
- Claims pendientes por antigüedad (30, 60, 90+ días)
- Qué aseguradoras deben más

**P5-3: Reporte de agenda**
- No-shows por período
- Pacientes más frecuentes
- Horas pico de la semana

**P5-4: Export a Excel/CSV**
- Cualquier reporte exportable
- Para contabilidad externa

---

### FASE P6 — PRODUCTO MULTI-OFICINA
**Tiempo estimado: 1 semana**
**Prioridad: MEDIA — para cuando quieras venderlo**

**P6-1: Instalador**
- Script de instalación para Windows
  que configura Python, dependencias y la DB
- Sin necesidad de conocimiento técnico

**P6-2: Configuración de primera vez**
- Wizard de setup al primer inicio:
  1. Nombre de la práctica
  2. Datos del provider (NPI, Tax ID, dirección)
  3. Crear usuario ADMIN
  4. Listo

**P6-3: Branding configurable**
- Nombre de la práctica configurable desde Settings
- Logo uploadable desde Settings
- El sistema se adapta a cualquier oficina

**P6-4: Guía de instalación**
- Documento PDF de 5 páginas
- Cómo instalar, cómo hacer backup,
  cómo crear usuarios, qué hacer si algo falla

**P6-5: Precio y licencia**
- El sistema es local — no hay subscripción mensual
- Modelo sugerido: pago único de instalación +
  soporte anual opcional

---

### FASE P7 — PULIDO FINAL
**Tiempo estimado: 1 semana**
**Prioridad: MEDIA**

**P7-1: Testing con usuarios reales**
- Sesión de prueba con la doctora
- Sesión de prueba con la recepcionista
- Documentar confusiones y corregirlas

**P7-2: Guía de usuario**
- Una página por rol
- En español, sin lenguaje técnico
- Con capturas de pantalla del sistema real

**P7-3: Velocidad**
- Identificar páginas lentas
- Agregar índices en DB donde necesario
- Optimizar queries pesados

**P7-4: Compatibilidad**
- Probar en Chrome, Edge y Firefox
- Probar en pantallas pequeñas (tablets)

---

## ORDEN DE EJECUCIÓN RECOMENDADO

```
SEMANA 1:   P1 completo (limpieza + configuración)
SEMANA 2:   P2-1, P2-2, P2-4, P2-5 (seguridad básica)
SEMANA 3:   P3-1, P3-2, P3-3, P3-4 (flujo UX)
SEMANA 4:   P4-1, P4-2, P4-3 (clínico completo)
SEMANA 5:   P3-5, P3-6, P4-4, P4-5 (pulido)
SEMANA 6:   P5 completo (reportes)
SEMANA 7:   P6 completo (producto)
SEMANA 8:   P7 completo (testing y entrega)
```

**Total estimado: 8 semanas a 20 horas semanales**

---

## LO QUE HACE A LIFETRACK DIFERENTE

| Característica | LifeTrack | Sistemas típicos |
|---------------|-----------|------------------|
| 100% local, sin internet | ✅ | ❌ mayoría en la nube |
| Diseñado para PR | ✅ | ❌ genérico USA |
| CMS-1500 inmutable con hash | ✅ | ❌ editable |
| Claim Scrubber antes de enviar | ✅ | ⚠️ básico |
| Flujo clínico → billing integrado | ✅ | ❌ separados |
| Precio único sin subscripción | ✅ | ❌ $200-500/mes |
| Datos nunca salen de la oficina | ✅ | ❌ en servidores de terceros |

---

*Este documento es la hoja de ruta del producto.*
*Actualizar al completar cada fase.*
*Última actualización: Marzo 2026*