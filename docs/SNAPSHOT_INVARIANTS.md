# SNAPSHOT CMS-1500 — Invariantes Técnicas (LifeTrack)

## 1. Definición

Un **Snapshot CMS-1500** es una representación **final, legal e inmutable** de un claim en un momento específico del tiempo.

El snapshot:
- Se genera una sola vez.
- No se recalcula.
- No se edita.
- No se vuelve a renderizar con datos vivos.

El snapshot existe para **auditoría, respaldo legal y trazabilidad**.

---

## 2. Qué NO es un Snapshot

El snapshot CMS-1500 **NO** es:
- Un preview editable.
- Un estado vivo del claim.
- Un reflejo dinámico del sistema financiero.
- Un reporte recalculable.
- Un documento dependiente de la UI.
- Un objeto que responde a cambios posteriores.

---

## 3. Invariantes Absolutas (Reglas Inquebrantables)

Las siguientes reglas **no pueden romperse** bajo ninguna circunstancia:

1. Un snapshot CMS-1500 **nunca se recalcula**.
2. El snapshot **no ejecuta lógica financiera**.
3. El snapshot **no depende de estado en memoria**.
4. El snapshot **no depende de la UI**.
5. El snapshot **no muta** aunque:
   - Cambien tarifas.
   - Cambien CPT.
   - Cambien ICD-10.
   - Se registren pagos.
   - Se apliquen ajustes.
   - Se modifique el claim original.
6. HTML y PDF **leen exactamente la misma fuente de snapshot**.
7. El snapshot **no escribe datos**.
8. El snapshot **no genera nuevos snapshots**.
9. El snapshot **no se sincroniza** con estados financieros futuros.
10. El snapshot **es solo lectura**.

Si alguna de estas reglas se rompe, el sistema **pierde validez legal**.

---

## 4. Rutas Autorizadas

Las únicas rutas permitidas para un snapshot CMS-1500 son:

- `/cms1500/<claim_id>`
- `/cms1500/<claim_id>/pdf`

Estas rutas:
- Solo leen.
- No mutan.
- No recalculan.
- No generan estado.

---

## 5. Rutas Prohibidas

Están explícitamente prohibidas:
- Rutas de update.
- Rutas de delete.
- Rutas de regenerate.
- Rutas de preview dinámico.
- Rutas que mezclen snapshot con estado vivo.

---

## 6. Relación con el Sistema Financiero

El snapshot CMS-1500 es **consecuencia**, nunca causa.

El flujo correcto es:
Sistema financiero → Snapshot → Auditoría / PDF / Archivo legal

Nunca:
Snapshot → Sistema financiero

Cambios financieros posteriores **no afectan** snapshots existentes.

---

## 7. Riesgos Mitigados por este Diseño

Este modelo evita:
- Re-render accidental.
- Re-cálculo silencioso.
- Corrupción histórica.
- Dependencia de estado vivo.
- Refactors peligrosos.
- “Optimizaciones” futuras que rompan legalidad.

---

## 8. Regla de Oro

> Si un cambio rompe cualquiera de estas invariantes,  
> **el cambio es inválido**, aunque compile y “funcione”.

La corrección legal tiene prioridad absoluta sobre:
- Performance.
- UX.
- Limpieza de código.
- Conveniencia técnica.
