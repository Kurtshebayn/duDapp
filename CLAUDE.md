# duDapp — Liga de Dudo

## Qué es este proyecto

Plataforma web para gestionar una liga de Dudo (juego de dados). Un administrador registra los resultados de reuniones semanales y cualquier persona puede consultar la tabla de posiciones, resultados y estadísticas mediante un link público.

## Stack técnico

- **Backend:** FastAPI (Python) desplegado en Render
- **Frontend:** React (SPA) desplegado en Vercel
- **Base de datos:** PostgreSQL en Render
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

## Fase actual: Fase 6 — Pulido y lanzamiento

Objetivo: preparar para uso real.
- Probar drag & drop en dispositivos móviles reales (R-04)
- Implementar indicador de carga para cold starts (R-01)
- Implementar script de backup de base de datos (R-03)
- Documentar proceso de reseteo de contraseña (R-05)
- Desplegar backend en Render y frontend en Vercel

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

Ver /docs/roadmap.md para detalle completo.