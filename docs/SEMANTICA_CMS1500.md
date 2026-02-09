# SEMÁNTICA CMS-1500 — LifeTrack

Este documento define la semántica exacta e inmutable de los campos usados
en el Snapshot CMS-1500.  
No describe implementación. Describe SIGNIFICADO.

Este documento es vinculante para el proyecto.

---

## PRINCIPIOS ABSOLUTOS

1. Un Snapshot CMS-1500 es una representación FINAL e INMUTABLE.
2. Un Snapshot NUNCA se recalcula.
3. Un Snapshot NUNCA se corrige.
4. Cualquier cambio financiero posterior NO afecta snapshots previos.
5. El Snapshot es la fuente legal, no el Claim vivo.

---

## ESTRUCTURA GENERAL

El Snapshot contiene:
- Datos del paciente
- Datos del proveedor
- Diagnósticos
- Servicios
- Totales financieros

Todos los valores ya están resueltos al momento del snapshot.

---

## SEMÁNTICA DE TOTALES

### snapshot.totals.total_charge
**Definición:**
Suma total de cargos facturados en el momento del snapshot.

**Propiedades:**
- Valor histórico
- No se recalcula
- No depende de pagos futuros
- Refleja exactamente lo que se reclamó

---

### snapshot.totals.amount_paid
**Definición:**
Monto total pagado APLICADO al claim al momento del snapshot.

**Propiedades:**
- Puede ser 0.00
- Representa pagos existentes hasta ese punto
- No incluye pagos futuros
- No se ajusta retroactivamente

---

### snapshot.totals.balance_due
**Definición:**
Resultado aritmético:


**Propiedades:**
- Valor congelado
- Puede no coincidir con balance actual del claim vivo
- Representa el balance en el instante legal del snapshot

---

## SEMÁNTICA DE SERVICIOS

### s.units
**Definición:**
Cantidad de unidades facturadas para ese CPT en ese servicio.

**Propiedades:**
- Valor declarado al facturar
- No se deriva de tiempo
- No se normaliza luego

---

### s.dx_pointer
**Definición:**
Referencia a letras A–L de la Casilla 21 del CMS-1500.

**Propiedades:**
- Valor textual (ej: "A", "A,B")
- No se valida contra diagnósticos posteriores
- Refleja intención clínica al facturar

---

## SEMÁNTICA DE DIAGNÓSTICOS

### snapshot.diagnoses.[A–L]
**Definición:**
Diagnósticos declarados al momento de crear el snapshot.

**Propiedades:**
- Pueden ser menos de 12
- Las letras no usadas permanecen vacías
- No se rellenan automáticamente

---

## DIFERENCIA CLAVE: CLAIM VS SNAPSHOT

| Aspecto | Claim vivo | Snapshot CMS-1500 |
|------|-----------|-------------------|
| Mutable | Sí | No |
| Recalcula | Sí | No |
| Ajustes | Sí | No |
| Uso legal | No | Sí |

---

## PROHIBICIONES EXPLÍCITAS

Queda prohibido:
- Recalcular totales de un snapshot
- Sincronizar snapshot con claim
- Corregir snapshots
- Usar snapshots como fuente operativa
- Mutar snapshots por pagos tardíos

---

## USO CORRECTO

- UI: solo lectura
- PDF: representación fiel
- Auditoría: fuente primaria
- Disputas: documento final

---

## ESTADO

Documento aprobado.  
Vinculante para todo desarrollo futuro.

FIN
