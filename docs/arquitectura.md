# Arquitectura del Sistema — v1

**Patrón:** SPA + API REST + Base de datos relacional. Tres componentes independientes, cada uno desplegado por separado.

## Componentes

### Frontend — React SPA

Aplicación web responsive que sirve dos experiencias: la vista pública (espectador) con tabla de posiciones, resultados por reunión y estadísticas, y la vista de administración (protegida por login) con registro y edición de reuniones, creación de temporadas y cierre de temporada. Se comunica con el backend exclusivamente a través de llamadas HTTP a la API REST. Desplegada en Vercel.

### Backend — FastAPI (Python)

API REST que expone los endpoints necesarios para todas las operaciones del sistema. Responsabilidades: recibir y validar datos del admin, calcular puntos automáticamente según posición, calcular estadísticas (asistencias, promedios, rankings), servir datos a la vista pública, y autenticar al admin mediante JWT. Genera documentación OpenAPI automáticamente. Desplegado en Render.

### Base de datos — PostgreSQL

Almacena toda la información persistente: jugadores, temporadas, reuniones, posiciones y puntos. Las consultas de estadísticas (promedios, conteos, rankings) se resuelven directamente con SQL. Hospedada en Render.

## Flujo de datos

El espectador abre el link, el frontend carga desde Vercel y hace requests GET al backend en Render, que consulta PostgreSQL y devuelve los datos. El admin se loguea (POST con credenciales, recibe JWT), y todas sus acciones (crear temporada, registrar reunión, etc.) viajan como requests autenticados con el token al backend, que valida, procesa, persiste y responde.

## Decisiones de diseño

El frontend no habla directamente con la base de datos — todo pasa por la API. Esto permite agregar tiempo real (WebSockets) en el futuro sin cambiar el frontend, solo agregando una capa al backend. La autenticación es mínima (un solo usuario con JWT) dado que solo existe un admin. El link público no requiere autenticación alguna.

## Preparación para futuro

La separación frontend/backend permite reemplazar o escalar cualquier componente sin afectar al otro. WebSockets se pueden agregar al backend sin reescribir la API REST existente. El modelo de datos relacional permite agregar nuevas estadísticas con queries SQL sin cambios estructurales.
