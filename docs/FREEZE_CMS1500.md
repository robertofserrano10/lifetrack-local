# FREEZE OPERATIVO — CMS-1500 SNAPSHOT (LifeTrack)

## Estado
FREEZE ACTIVO

Fecha de activación: _______________
Commit de activación: _______________

---

## Alcance del Freeze

Quedan CONGELADOS e INMUTABLES los siguientes componentes:

1. Snapshot CMS-1500
   - Estructura de datos
   - Campos
   - Semántica definida en SEMANTICA_CMS1500.md
   - Hash y persistencia histórica

2. Render HTML CMS-1500
   - app/templates/cms1500.html
   - Orden de bandas
   - Etiquetas oficiales CMS-1500
   - Layout validado visualmente

3. CSS de impresión
   - app/static/css/cms1500_print.css
   - Reglas de print-hardening
   - Tamaño Letter
   - Anti-overflow y anti-break

4. PDF CMS-1500
   - Ruta /cms1500/<claim_id>/pdf
   - Motor Playwright
   - Uso exclusivo de snapshot existente
   - No recalcula
   - No muta estado

---

## Prohibiciones explícitas (mientras el Freeze esté activo)

❌ Modificar campos del snapshot  
❌ Reordenar bandas  
❌ Cambiar semántica de totales  
❌ Recalcular valores históricos  
❌ Ajustar CSS “porque se ve mejor”  
❌ Introducir lógica condicional nueva  
❌ Reinterpretar CMS-1500 sin fase formal  

Cualquier cambio aquí ROMPE el freeze.

---

## Cambios permitidos POST-FREEZE (no implementados aún)

✔ Resubmission (Casilla 22)  
✔ Integración EOB / ERA  
✔ Pagos y aplicaciones financieras  
✔ Reportes  
✔ UX externa (sin tocar snapshot)

---

## Criterio para romper el Freeze

El Freeze solo puede romperse si:

1. Existe una fase explícita aprobada
2. Se documenta el motivo
3. Se genera un commit dedicado
4. Se actualiza este documento

Sin estos pasos, el Freeze sigue vigente.

---

## Garantía

Este Freeze garantiza que:

- El CMS-1500 emitido hoy será idéntico mañana
- Auditoría legal es reproducible
- No hay deriva semántica
- El sistema es defendible ante terceros

