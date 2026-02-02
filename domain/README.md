# LifeTrack — Modelo de Dominio (Canónico)

## Objetivo
Registrar el flujo clínico y de facturación para producir una CMS-1500 auditable,
sin clearinghouse, con trazabilidad completa (quién, cuándo, qué cambió).

## Entidades Núcleo (MVP)
1) Patient
- Identidad del paciente y demografía mínima.
- NO contiene finanzas.

2) Coverage
- Aseguradora + plan + póliza + grupo + asegurado.
- Un paciente puede tener 0..N coverages.

3) Claim
- Caso facturable (contenedor).
- Se relaciona con 1 Patient y (opcional) 1 Coverage activo al momento.

4) Service (ServiceLine)
- Evento/servicio clínico facturable dentro de un Claim.
- Fecha de servicio, CPT/HCPCS, unidades, diagnóstico(s).

5) Charge
- Cargo monetario por Service (lo que se factura).
- Se deriva típicamente de tarifa * unidades, pero la tarifa se almacena explícita.

6) Payment
- Dinero recibido (de paciente o aseguradora).
- Nunca se “pega” directo al balance; se aplica.

7) Application
- Aplicación de un Payment a uno o más Charges.
- Es la fuente auditada de cómo baja el balance.

8) Adjustment (opcional MVP)
- Ajustes por contrato, write-off, etc.
- Se aplican como movimientos separados (no editar cargos retroactivamente).

9) Cms1500Snapshot
- Representación final del claim para someter.
- Inmutable: se genera y se guarda; no se recalcula.

## Estados (principio)
- Estado operacional: progreso del caso (draft, ready, submitted, etc.)
- Estado financiero: derivado de Charges - Applications - Adjustments
- Nunca persistir el estado financiero como “verdad”; se calcula desde movimientos.

## Relaciones (resumen)
Patient 1 --- N Coverage
Patient 1 --- N Claim
Claim 1 --- N Service
Service 1 --- 1 Charge
Payment 1 --- N Application
Application N --- 1 Charge (o 1 Application puede dividirse; se define luego)
Claim 1 --- N Cms1500Snapshot

## Reglas mínimas
- Nada se borra físicamente; solo soft delete + auditoría.
- Todo cambio importante requiere timestamp + actor (usuario).
- CMS-1500 snapshot es inmutable: si cambia algo, se genera uno nuevo.
