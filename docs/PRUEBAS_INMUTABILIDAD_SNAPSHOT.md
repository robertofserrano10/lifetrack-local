# PRUEBAS DE INMUTABILIDAD — SNAPSHOT CMS-1500  
FASE D2 — Evidencia Operacional

## Propósito
Este documento demuestra, mediante pruebas manuales controladas, que el Snapshot CMS-1500 es **inmutable** una vez creado.

Un snapshot:
- NO se recalcula
- NO se modifica
- NO refleja cambios posteriores en el Claim vivo
- Representa la versión legal final del CMS-1500

---

## Definiciones Clave

**Claim vivo**  
Entidad editable que puede cambiar por pagos, ajustes o correcciones.

**Snapshot CMS-1500**  
Representación congelada del claim en un momento específico, usada para:
- Auditoría
- Archivo legal
- Reimpresión
- PDF oficial

---

## Entorno de Pruebas

- Sistema: LifeTrack Local
- Base de datos: SQLite
- Motor PDF: Playwright (Chromium)
- Fecha de pruebas: ____________
- Tester: ____________

---

## Escenario A — Pago Posterior al Snapshot

### Objetivo
Verificar que un pago nuevo NO altera un snapshot existente.

### Pasos
1. Seleccionar un Claim con snapshot existente.
2. Generar PDF del snapshot:
3. Registrar valores observados:
- Total Charge: ____________
- Amount Paid: ____________
- Balance Due: ____________

4. Aplicar un pago nuevo al Claim vivo.
5. Volver a generar el PDF del snapshot.

### Resultado Esperado
- Los valores del snapshot **NO cambian**.
- El PDF es idéntico al original.

### Resultado Observado
- ☐ Snapshot inalterado  
- ☐ Snapshot modificado (ERROR)

Notas:
______________________________________________________

---

## Escenario B — Edición del Claim Vivo

### Objetivo
Confirmar que cambios estructurales del claim NO afectan snapshots previos.

### Pasos
1. Modificar el Claim vivo:
- CPT
- Unidades
- Diagnosis Pointer
2. Verificar que el Claim vivo refleja los cambios.
3. Generar nuevamente el PDF del snapshot original.

### Resultado Esperado
- Snapshot NO refleja los cambios del claim vivo.

### Resultado Observado
- ☐ Snapshot intacto  
- ☐ Snapshot alterado (ERROR)

Notas:
______________________________________________________

---

## Escenario C — Creación de Nuevo Snapshot

### Objetivo
Confirmar que un snapshot nuevo NO sobrescribe snapshots anteriores.

### Pasos
1. Crear un nuevo snapshot del mismo Claim.
2. Comparar:
- Snapshot anterior
- Snapshot nuevo

### Resultado Esperado
- Snapshot anterior intacto
- Snapshot nuevo refleja estado actualizado

### Resultado Observado
- ☐ Comportamiento correcto  
- ☐ Snapshot previo alterado (ERROR)

Notas:
______________________________________________________

---

## Conclusión Final

☐ El sistema cumple con inmutabilidad total del Snapshot CMS-1500  
☐ El sistema NO cumple (bloqueante legal)

---

## Firma de Validación

Tester: ___________________________  
Fecha: ____________________________  
Firma: ____________________________

---

## Estado de la Fase

FASE D2: ☐ EN PROGRESO ☐ VERDE ☐ BLOQUEADA
