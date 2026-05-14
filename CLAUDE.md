# duDapp — Liga de Dudo

## Qué es este proyecto

Plataforma web para gestionar una liga de Dudo (juego de dados). Un administrador registra los resultados de reuniones semanales y cualquier persona puede consultar la tabla de posiciones, resultados y estadísticas mediante un link público.

## Stack técnico

- **Backend:** FastAPI (Python) desplegado en Render
- **Frontend:** React (SPA) desplegado en Vercel
- **Base de datos:** PostgreSQL en Neon (serverless)
- **Autenticación:** JWT propia (un solo admin)
- **ORM:** SQLAlchemy con migraciones Alembic

## Reglas de negocio críticas (no violar nunca)

- El primer lugar siempre recibe 15 puntos, el segundo 14, posición N = 15 - (N-1)
- Los invitados ocupan posiciones y consumen puntos, pero NUNCA aparecen en la tabla de posiciones
- Los jugadores ausentes reciben 0 puntos
- Los jugadores inscritos con 0 asistencias y 0 puntos NO se muestran en la tabla — aparecen al registrar su primera asistencia
- Solo puede existir una temporada activa a la vez
- Una temporada cerrada es inmutable — no se pueden agregar, editar ni eliminar reuniones
- En caso de empate al cierre, se resuelve por enfrentamiento directo
- Se admite incorporar jugadores a la temporada activa después de iniciada. El jugador tardío computa como ausente (0 puntos) en las reuniones previas a su inscripción. Su promedio se calcula sobre sus asistencias reales (puntos / asistencias).

## Modelo de datos

- **Usuario:** id, email, contraseña (hasheada), nombre
- **Jugador:** id, nombre (reutilizable entre temporadas)
- **Temporada:** id, nombre, fecha_inicio, estado (activa/cerrada), id_usuario
- **Inscripción:** id, id_temporada, id_jugador
- **Reunión:** id, id_temporada, numero_jornada, fecha
- **Posición:** id, id_reunión, id_jugador (nullable), es_invitado (boolean), posición, puntos

Si es_invitado = true → id_jugador es null.
Si es_invitado = false → id_jugador apunta al jugador inscrito.

## Estadísticas (se calculan con queries, no se almacenan)

- Asistencias = cantidad de reuniones donde el jugador tiene posición registrada
- Promedio = puntos totales / asistencias
- Ranking = ordenar por puntos totales acumulados
- Jugador con más inasistencias = total reuniones - asistencias

## Metodología de desarrollo

- **TDD pragmático:** tests ANTES de implementación, enfocados en reglas de negocio y flujos críticos
- **SDD:** toda implementación nace de las especificaciones en /docs
- NO testear trivialidades (getters, setters, validaciones básicas)

## Estructura del backend

- `app/models/` — Modelos SQLAlchemy (tablas)
- `app/schemas/` — Schemas Pydantic (validación de requests y responses)
- `app/routers/` — Endpoints HTTP agrupados por dominio
- `app/services/` — Lógica de negocio pura (testeable sin API ni DB)
- `app/auth/` — Autenticación JWT
- `tests/unit/` — Tests de lógica de negocio en aislamiento
- `tests/integration/` — Tests de flujos completos (API + DB)

## Cómo trabajar en este proyecto

1. Antes de implementar cualquier feature, leer el caso de uso correspondiente en /docs/casos-de-uso.md
2. Escribir los tests primero (TDD)
3. Implementar hasta que los tests pasen
4. La lógica de negocio va en services/, NO en routers/
5. Los routers solo reciben requests, llaman a services, y devuelven responses
6. Correr los tests después de cada cambio: `cd backend && pytest`

## Variables de entorno

Las credenciales y secrets se manejan con archivos .env que NO están en el repositorio.
El archivo .env NUNCA debe ser leído, mostrado ni logueado por el agente.
Si necesitas configurar una variable de entorno, indica qué variable se necesita y qué formato debe tener, pero NO accedas al contenido del archivo .env.

Variables esperadas:
- DATABASE_URL — conexión a PostgreSQL
- JWT_SECRET — clave para firmar tokens
- CORS_ORIGINS — dominios permitidos del frontend

## Fase actual: Fase 7 — Post-launch (completa)

App en producción (Render + Vercel + Neon). **Backlog vacío** — todos los items priorizados se shipearon. Próximo paso del proyecto: definir Phase 8 o capturar nuevos requirements.

Notas:
- R-05 (documentar reset de contraseña) está **fuera de scope** por decisión explícita del usuario. No proponerlo en backlogs futuros aunque siga apareciendo en docs antiguas.
- R-04 (drag & drop mobile) fue validado manualmente y queda cerrado.

## Fases completadas

### Fase 1 — Cimientos
Backend funcional con DB conectada y CORS resuelto. Proyecto FastAPI inicializado, modelos SQLAlchemy creados, migraciones Alembic configuradas, autenticación JWT implementada.

### Fase 2 — Lógica de negocio
Endpoints del admin y lógica de puntos implementados con TDD. Crear temporada (CU-01), registrar reunión (CU-02), editar reunión (CU-03), cerrar temporada (CU-07). Tests unitarios y de integración validados.

### Fase 3 — Datos públicos
Endpoints de lectura para espectadores implementados. Tabla de posiciones con regla de visibilidad (CU-04), resultados por reunión incluyendo invitados (CU-05), estadísticas de la temporada (CU-06). Tests de integración validados.

### Fase 4 — Frontend base
Aplicación React inicializada con Vite y React Router. Vistas públicas implementadas: tabla de posiciones con medallas, resultados por reunión con badge de invitado, estadísticas con top 3 y tabla completa. Servicio API conectado al backend. Configuración de Vercel lista con rewrites para client-side routing.

### Fase 5 — Frontend admin
Vistas protegidas del administrador implementadas. Login con JWT en localStorage, dashboard con estado de temporada activa, crear temporada con selección de jugadores, registrar y editar reunión con drag & drop (HTML5 DnD), cerrar temporada, compartir link (CU-08). Endpoints adicionales: GET /jugadores, GET /temporadas/activa.

### Fase 6 — Pulido y lanzamiento
App desplegada a producción (Render + Vercel + Neon, 2026-05-11). Drag & drop validado en mobile real (R-04 ✅). Indicador de carga para cold starts implementado (R-01 ✅). Rediseño visual completo: sistema editorial cream/leather aplicado a las 9 páginas + nav, en 3 sprints (A públicas, B nav/auth, C forms admin). R-05 (reset de contraseña) declarado fuera de scope por el usuario.

### Cambios SDD posteriores al roadmap original
- **inscripciones-mitad-temporada** — admin puede crear jugadores e inscribirlos a la temporada activa después de iniciada (regla de negocio actualizada).
- **bulk-import-temporadas** — endpoint admin de importación CSV para 5 temporadas históricas previas al sistema.
- **historico-aggregations** — vista pública de estadísticas cross-temporadas (PR #4, shipped 2026-05-05).
- **sync-docs-to-post-neon-state** — docs y ADRs sincronizados con la migración Render→Neon (2026-05-03).
- **cleanup-estadisticas** — vista pública `/estadisticas` y endpoint `/temporadas/activa/estadisticas` eliminados; `/ranking` cubre el caso de uso tras la unificación del redesign (PR #6, shipped 2026-05-11). Item 1 del backlog Phase 7.
- **position-snapshots** — tabla `posicion_snapshot`, endpoint público `GET /temporadas/activa/ranking-narrativo` (delta_posicion, racha, lider_desde_jornada), y enriquecimiento del endpoint `GET /temporadas/activa/reuniones` con campo `ganador`. Entregado en 3 PRs apilados (#7 modelo+ranking, #8 snapshots+narrativa, #9 endpoints+ganador, 2026-05-11). Items 1 y 2 del backlog Phase 7 completados.
- **frontend-narrativas-y-ganador** — `Ranking.jsx` ahora consume `/temporadas/activa/ranking-narrativo` y renderiza pills "sube N" / "cae N" / "racha de N" / "líder desde J-N" (priority `líder > racha > delta`, cap 2 en tabla, full en podio). `Reuniones.jsx` renderiza avatar del ganador en 4ª columna del grid con placeholder vacío cuando `ganador=null`. Frontend test suite (Vitest + React Testing Library + jsdom) instalada como parte del cambio — 49 tests verdes (6 archivos, 1.43s). PR único con `size:exception` (forecast 486 líneas, ~70% tests). Item 2 del backlog Phase 7 completado.
- **season-tiebreaker-admin-flow** — auto-set de `campeon_id` al cerrar temporada cuando hay un único ganador + endpoint admin idempotente `POST /temporadas/{id}/campeon` para designar campeón en cualquier temporada cerrada (habilita backfill de las 5 históricas sin UI extra). Frontend: `ChampionPickerModal` aparece al cerrar si `tie_detected: true`, lista N empatados, persiste pick vía endpoint. Backend: tie detection en `services/ranking.py` (recomputa por call), Pydantic v2 `@model_serializer(mode='wrap')` en `TemporadaResponse` para omitir `tied_players` cuando es None (patrón `dudapp/patterns/temporada-response-serialization`). Entregado en 2 PRs apilados (#11 backend 612 LOC, #12 frontend 492 LOC, 2026-05-14). 46 tests nuevos (29 backend + 17 frontend), total 341 tests verdes. Último item del backlog Phase 7 completado.

Ver /docs/roadmap.md para detalle completo.