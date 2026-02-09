# CMS-1500 Snapshot — Freeze Técnico (FASE E1)

## 1. Definición
El CMS-1500 Snapshot es una **representación legal inmutable** de un claim.
Una vez generado, **no se recalcula, no se edita y no se sobrescribe**.

Toda vista HTML y todo PDF **leen exactamente el mismo snapshot**.

---

## 2. Inmutabilidad (REGLA ABSOLUTA)
Después de creado un snapshot:

- ❌ No se vuelve a calcular.
- ❌ No se actualiza si cambian datos del paciente, cobertura o proveedor.
- ❌ No se corrige visualmente “a mano”.
- ❌ No se reutiliza para otros claims.

Cualquier corrección requiere:
➡️ nuevo snapshot  
➡️ nueva referencia  
➡️ nuevo PDF

---

## 3. Fuentes permitidas
El snapshot puede ser consumido únicamente por:

- `/cms1500/<claim_id>` (HTML read-only)
- `/cms1500/<claim_id>/pdf` (PDF legal)

Ambas rutas deben:
- Leer el mismo snapshot
- No mutar estado
- No escribir en DB

---

## 4. Separación de responsabilidades
- **Datos vivos**: Patient, Coverage, Claim, Service
- **Documento legal**: CMS-1500 Snapshot

Nunca se mezclan.

---

## 5. Implicaciones legales
El PDF generado desde el snapshot:
- Representa lo enviado a la aseguradora
- Es auditable
- Es trazable
- Tiene prioridad sobre datos vivos

---

## 6. Estado del proyecto
- Render HTML: ✅ FASE C1
- PDF legal: ✅ FASE C2
- Limpieza visual: ✅ FASE C3
- Congelación técnica: ✅ FASE E1

A partir de este punto:
➡️ cualquier cambio al CMS-1500 requiere nueva fase.
