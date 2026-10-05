# Feature: scoring-mode-per-season

## Objective
Let the admin choose, per season, how meeting points are computed.

## Problem / Why
Today points are hardcoded: position N = 15 - (N-1) (`backend/app/services/puntos.py`).
The league wants a new mode where first place gets as many points as there are
participants in that meeting (6 players -> 6, 5, 4, 3, 2, 1).

## Decisions (user-confirmed 2026-10-05)
- Mode is stored **per season** and chosen at season creation; immutable afterwards.
- Applies from the next season. There is no active season today, so no recalculation of existing data.
- Existing seasons keep the current mode (`fijo_15`) via migration default.
- Participants count for the new mode = all positions in the meeting, **including guests** (guests occupy positions).

## Scope
- Backend: `scoring_mode` column on Temporada (enum: `fijo_15` default, `por_asistentes`), Alembic migration 0006,
  `calcular_puntos(posicion, modo, total_participantes)`, register/edit meeting use the season mode,
  create-season schema/endpoint accepts the mode, TemporadaResponse exposes it.
- Frontend: create-season form lets the admin pick the mode (default `fijo_15`).
- Out of scope: changing mode of an existing season, recalculating historical data, CSV import behavior
  (imports keep stored points as-is).

## Constraints
- Business logic in `services/`, routers stay thin.
- Closed seasons immutable. Stored `Posicion.puntos` is the source of truth.

## TDD
- Mode: enabled (source: global CLAUDE.md "Strict TDD Mode: enabled" + project CLAUDE.md TDD pragmático).
- Runners: backend `cd backend && pytest`; frontend `cd frontend && npm run test:run`.

## Tasks
- [x] T1 Backend: scoring mode model + migration + service + schemas + tests (route: delegated writer — touches 4+ non-trivial files)
- [x] T2 Frontend: mode selector in create-season form + tests (route: delegated writer — 2+ non-trivial files)
- [x] T3 Docs: update CLAUDE.md business rule + docs/casos-de-uso.md (CU-01/CU-02) (route: inline, mechanical)

## Acceptance criteria
- New season created with `por_asistentes`: meeting with 6 positions stores 6,5,4,3,2,1.
- Season created without mode: behaves exactly as today (15,14,...).
- Editing a meeting recalculates with the season's mode and the new participant count.
- Existing seasons after migration report `fijo_15`.
- Full backend and frontend suites green.

## Delivery
- Forecast ~350-450 authored lines; strategy: ask-on-risk.

## Progress / Evidence
- T1 done — commit `6ebe365` (+258/−11, 11 files). Column named `temporadas.modo_puntaje` (native enum `modopuntaje`: `fijo_15`, `por_asistentes`) to match Spanish model naming; migration `0006`.
  RED observed (ImportError ModoPuntaje; 4 integration failures). GREEN: `pytest` 368 passed (writer + parent spot check). Alembic single head `0006`; not applied to a real DB yet.
  API: `POST /temporadas` accepts optional `modo_puntaje`; exposed on create/close/champion responses and `GET /temporadas/activa`.
  RDD assess (base main, committed-only, untracked odd/ excluded): medium (`executable_change` migration), review_due=false, `under_budget` (269 lines) → pending in slice.
  Note: CSV import (`reconstruir_posiciones.py`, `import_temporada.py`) still assumes the 15 scale; fine for historical imports, out of scope.

- T2 done — commit `7d66cb4` (+218/−4, 7 files). "Sistema de puntaje" radio group in `CrearTemporada.jsx`, `crearTemporada()` always sends `modo_puntaje`, dashboard shows the active season mode.
  RED observed (radios missing, `modo_puntaje` absent from body, dashboard label missing). GREEN: `npm run test:run` 101 passed (writer + parent spot check); `npm run build` OK; no lint script.
  RDD assess after T2: medium, review_due=true, `slice_budget_reached` (491 lines). Preflight STATUS asked for intended-untracked selection (this doc); submissions rejected as invalid JSON → doc committed with T3 so the candidate has no untracked files, then preflight re-run.
- T3 done — CLAUDE.md business rule + data model, `docs/casos-de-uso.md` (CU-01, CU-02), `docs/modelo-de-datos.md`. Not updated on purpose: `docs/csv-import-format.md` (import still 15-scale), `docs/estrategia-de-testing.md`, `docs/vision.md`.

- Native review (user granted): lineage `review-7a03c69889d12a3a`, 1 lens (reliability), **approved**, acknowledged, authority burned. Reviewed range main..2393dca.
  Non-blocking follow-ups:
  - R3-por-asistentes-gap-positions (WARNING): positions are not validated as contiguous 1..N; an API call with gaps (e.g. 1,2,5) in `por_asistentes` would yield 0/negative points. The admin UI always sends 1..N. Pre-existing for `fijo_15` too (position > 15).
  - R3-migration-backfill-unproved (WARNING): no test applies migration 0006 against Postgres; verify on deploy.
  - R3-close-champion-response-untested (SUGGESTION): `modo_puntaje` in close-season/champion responses not covered by tests.

## Next step
Push + PR is the user's decision. Optional follow-up: validate contiguous positions in meeting input.
