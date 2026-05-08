# CLAUDE.md — Instrucciones para agentes en lifetrack-local

Este archivo configura el comportamiento de Claude Code en el proyecto LifeTrack-local.
Lee este archivo ANTES de cualquier accion en el repo.

---

## 1. Fuente de verdad arquitectonica

**Lee SIEMPRE primero:** `README.md` de este proyecto.

Contiene 28 secciones de **reglas inmutables**:
- Modelo ledger (charges / payments / applications / adjustments)
- Balance derivado (NUNCA persistido)
- Snapshots CMS-1500 inmutables con hash SHA256
- CMS-1500 NO es fuente de verdad financiera
- Estados duales: estado_operacional vs estado_financiero
- Fases congeladas
- Reglas de auditoria

Documentos secundarios:
- `LIFETRACK_REFERENCIA.md`, `LIFETRACK_ROADMAP.md`, `FASES_LIFETRACK.md`, `Fases.md`, `Fases1.md`
- `AUDITORIA_2026_03_21.md`

**Si una accion viola alguna regla del README, la accion se rechaza.**

---

## 2. Stack del proyecto

```
Lenguaje:        Python
Tests:           scripts/test_phase_X.py (NO usar npm test, NO usar pytest desde REPL)
DB:              SQLite local (schema.sql se actualiza al cambiar estructura)
Estructura:      app/ domain/ scripts/ storage/ exports/ docs/
Entry-points:    create_db.py, check_db.py
```

### Comandos overrides (vs ejemplos de skills genericas)

| Skill dice | En este proyecto se usa |
|-----------|------------------------|
| `npm test` | `python scripts/test_phase_X.py` |
| `npm run lint` | (no aplica — Python; usar ruff/black si configurado) |
| `npm audit` | `pip-audit` o `safety check` (si instalado) |
| `git status / add / commit / push` | igual (regla 27 README) |

### Cuando los SKILL.md muestran codigo TypeScript/JavaScript

Tropicaliza mentalmente: TS interfaces → Python dataclasses, `describe/it` → pytest funcs, `bcrypt`/`prisma` → equivalentes Python (`bcrypt`, SQLAlchemy o sqlite3). Los **principios** del skill aplican; los **snippets** son referenciales.

---

## 3. Skills disponibles en este proyecto

Carpeta: `.claude/skills/` — **21 skills** instaladas (suite completa addyosmani/agent-skills).
Carpeta: `.claude/agents/` — 3 personas (code-reviewer, test-engineer, security-auditor).
Carpeta: `.claude/references/` — 5 checklists (testing, security, performance, accessibility, orchestration).

Skills se activan por triggers en su frontmatter `description`. NO hay que invocarlas manualmente — Claude las descubre por contexto.

### Prioridad por fase del proyecto

**Tier 1 — Critico siempre (cualquier cambio al ledger / snapshot):**
- `spec-driven-development` — spec antes de codigo
- `test-driven-development` — RED-GREEN-REFACTOR + Prove-It para bugs
- `code-review-and-quality` — 5-axis review antes de merge
- `security-and-hardening` — sistema con PHI + datos financieros
- `git-workflow-and-versioning` — commits atomicos, cierre de fase

**Tier 2 — Por fase:**
- Fase 1 (congelar nucleo): Tier 1 completo + `incremental-implementation`
- Fase 2 (builder CMS unico): + `documentation-and-adrs` (registrar decision de unificacion), `code-simplification`
- Fase 3 (campos CMS): + `incremental-implementation`, `debugging-and-error-recovery`
- Fase 4 (impresion/PDF): + `debugging-and-error-recovery`, `browser-testing-with-devtools` (si renderiza HTML)
- Fase 5 (UX por roles): + `frontend-ui-engineering`, `api-and-interface-design`
- Fase 6 (EOB/EOM manual): + `spec-driven-development`, `planning-and-task-breakdown`

**Tier 3 — Disponibles pero rara vez relevantes en scope actual:**
- `idea-refine` — vision ya anclada
- `shipping-and-launch` — voto "especifico primero", sin shipping aun
- `ci-cd-and-automation` — sistema local single-tenant
- `deprecation-and-migration` — sin legacy
- `performance-optimization` — sin perf reportado
- `source-driven-development` — util para framework decisions
- `context-engineering` — meta-skill
- `using-agent-skills` — meta-skill sobre skills

Cada skill tiene `Common Rationalizations` (excusas con rebuttals) — usalas para auto-revision.

---

## 4. Reglas inmutables de colaboracion

### 4a. Delegacion Qwen vs Claude

**Qwen local primero** (puerto 11434, modelo `qwen2.5-coder:7b-instruct-q5_K_M`):
- Resumir docs NO-criticos
- Explicar codigo en general
- Generar tests boilerplate (Claude revisa)
- Drafts de commits/PRs

**Claude (yo) reservado para:**
- Resumir docs CRITICOS (README invariantes, AUDITORIA)
- Code review de cambios al ledger
- Decisiones arquitectonicas
- Cualquier touch a charges/payments/applications/snapshots
- Logica hash/integridad
- **Busqueda semantica + extraer keywords** (riesgo invariantes)

**Razon:** Qwen perdio 4 invariantes resumiendo README (balance no-persistido, CMS no fuente verdad, estados duales, auditoria). Costo de error >>> ahorro tokens en tareas criticas.

### 4b. Pragmatismo sobre rigidez

Si una regla inmutable choca con progreso del proyecto, propongo alternativa practica + trade-off honesto. **Decision final del usuario**, nunca mia.

### 4c. Sin decisiones autonomas en proyecto

Antes de:
- Crear/modificar entidades del ledger
- Cambiar estructura de tablas
- Tocar logica de snapshot/hash
- Aplicar pagos / mover montos
- Modificar fases congeladas

→ **Pedir confirmacion explicita al usuario.**

### 4d. Usuario

Roberto, espanol, nuevo en Claude Code. Explicar paso-a-paso. No asumir conocimiento. Maxima automatizacion del lado del agente.

---

## 5. Decision abierta del proyecto (recordatorio)

Voto vigente del usuario: **"sistema local especifico primero, plataforma despues"**.

NO proceder con features de scope-expansion (multi-tenant, EDI/837/835 auto, EOB-auto, plataforma generica) hasta confirmacion explicita de cambio de scope.

---

## 6. Boundaries

- **Always:** Leer README antes de tocar codigo. Usar Qwen para tareas no-criticas. Tests antes de commit.
- **Ask first:** Cambios al ledger, snapshot logic, hash, schema.sql, fases congeladas, instalacion de dependencias nuevas.
- **Never:** Persistir balance como verdad. Aplicar pagos automaticamente. Recalcular snapshots historicos. Mezclar charges/payments. Comitear secretos. Skip tests.

---

## 7. Workflow recomendado por fase

```
Fase 1 — Congelar nucleo financiero
  /spec   → spec-driven-development genera doc de tests requeridos
  /test   → test-driven-development escribe tests RED para cada invariante
            (crear cargo, aplicar parcial, bloquear sobreaplicacion, balance, credito)
  /build  → implementar GREEN
  /review → code-review-and-quality + security-and-hardening
  /ship   → git-workflow-and-versioning (commit + push)

Fase 2 — Builder unico CMS-1500
  Igual flujo. Spec primero. Tests para vista=snapshot=validacion.

Fases 3-6: igual patron.
```

---

## 8. Compliance gaps — pendientes organizacionales (no codigo)

Tu sistema esta arquitectonicamente alineado con HIPAA Security Rule §164.312(c)(1) (integrity via snapshot inmutable + hash SHA256) y con la auditoria por evento (§164.530). El snapshot versionado es **estandar de la industria** para evidencia legal — no es opcion debil.

Pero faltan items **organizacionales** (no de codigo) para certificacion de cumplimiento. Registralos antes de operar con dinero real:

```
1. Retention policy escrita: snapshots y registros financieros 7-10 anos PR
2. Access control por rol: DRA / RECEPCION / FACTURADOR / ADMIN (Fase 5 lo cubre)
3. Encryption at rest: SQLite en disco contiene PHI -> SQLCipher o BitLocker full-disk Windows
4. Backup policy + offsite: HIPAA contingency plan (§164.308(a)(7))
5. BAA (Business Associate Agreement) con cualquier vendor IT que toque DB
6. Incident response plan: que hacer si DB se compromete
```

**Aviso:** El proyecto NO transmite PHI a terceros (no clearinghouse EDI, no auto-submit 837/835, no auto-aplicacion EOB). Eso reduce significativamente la superficie regulatoria vs un clearinghouse real. **Para certificacion, consultar abogado healthcare en PR.**

Marcos legales aplicables (referencia):
- HIPAA Security/Privacy Rule (federal)
- 45 CFR §164.530(j) — retention 6 anos minimo
- Medicare/Medicaid claim retention 7-10 anos
- Ley PR 194-2000 (Carta de Derechos del Paciente)

---

## FIN
