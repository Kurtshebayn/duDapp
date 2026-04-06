# Roadmap de Implementación — v1

## Fase 1 — Cimientos (backend)

**Objetivo:** tener un backend funcional con la base de datos conectada y CORS resuelto.

- Inicializar proyecto FastAPI con estructura de carpetas
- Configurar conexión a PostgreSQL (SQLAlchemy)
- Configurar CORS desde el día uno (R-02)
- Crear modelos de base de datos (Usuario, Jugador, Temporada, Inscripción, Reunión, Posición)
- Implementar migraciones de schema (Alembic)
- Implementar autenticación JWT (login del admin)
- Desplegar en Render con PostgreSQL — validar que responde

**Victoria temprana:** el backend está vivo en internet y el admin puede loguearse.

## Fase 2 — Lógica de negocio (backend)

**Objetivo:** implementar todos los endpoints del admin y la lógica de puntos, siguiendo TDD.

- Tests unitarios para cálculo de puntos, invitados, ausentes, visibilidad
- Endpoint: crear temporada con jugadores (CU-01)
- Endpoint: registrar reunión con posiciones y cálculo automático de puntos (CU-02)
- Endpoint: editar reunión (CU-03)
- Endpoint: cerrar temporada (CU-07)
- Tests de integración para cada flujo

**Victoria temprana:** toda la lógica de negocio funciona y está validada por tests.

## Fase 3 — Datos públicos (backend)

**Objetivo:** implementar los endpoints de lectura que usará el espectador.

- Endpoint: tabla de posiciones con regla de visibilidad (CU-04)
- Endpoint: resultados por reunión incluyendo invitados (CU-05)
- Endpoint: estadísticas de la temporada (CU-06)
- Tests de integración para consultas

**Victoria temprana:** la API está completa. Todo lo que el frontend necesita ya existe.

## Fase 4 — Frontend base

**Objetivo:** tener la aplicación React funcionando con navegación y las vistas públicas.

- Inicializar proyecto React, configurar routing
- Vista pública: tabla de posiciones
- Vista pública: resultados por reunión
- Vista pública: estadísticas
- Conectar con la API del backend
- Desplegar en Vercel

**Victoria temprana:** cualquier persona puede abrir el link y ver la liga.

## Fase 5 — Frontend admin

**Objetivo:** implementar las vistas protegidas del administrador.

- Pantalla de login
- Vista: crear temporada y seleccionar jugadores
- Vista: registrar reunión con drag & drop (CU-02) — el feature más crítico y riesgoso
- Vista: editar reunión (CU-03)
- Vista: cerrar temporada (CU-07)
- Botón de compartir link (CU-08)

**Victoria temprana:** el MVP está completo y funcional.

## Fase 6 — Pulido y lanzamiento

**Objetivo:** preparar para uso real.

- Probar drag & drop en dispositivos móviles reales (R-04)
- Implementar indicador de carga para cold starts (R-01)
- Implementar script de backup de base de datos (R-03)
- Documentar proceso de reseteo de contraseña (R-05)
- Crear el usuario admin inicial en producción
- Lanzar con la liga de Dudo real
