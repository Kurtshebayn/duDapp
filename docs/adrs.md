# ADRs (Architecture Decision Records) — v1

## ADR-01 — Patrón arquitectónico: SPA + API REST + Base de datos relacional

**Contexto:** duDapp necesita servir dos experiencias (admin y espectador) con datos compartidos, permitir acceso público sin cuenta, y ser desplegada con costos mínimos. Se evaluaron tres opciones.

**Opciones evaluadas:**
- (A) SPA + API REST + BD relacional — componentes independientes, control total, mayor aprendizaje
- (B) Frontend + BaaS (Firebase/Supabase) — desarrollo más rápido, menos control, dependencia de proveedor
- (C) Framework full-stack (Next.js) — despliegue unificado, pero mezcla responsabilidades

**Decisión:** Opción A.

**Justificación:** El objetivo del proyecto incluye aprendizaje. La separación en tres componentes independientes da control total sobre cada pieza, permite reemplazar o escalar cualquier capa sin afectar las demás, y prepara la arquitectura para agregar WebSockets a futuro. La complejidad adicional respecto a un BaaS es manejable dado que el modelo de datos es simple y la carga es mínima.

**Consecuencias:** Se mantienen dos deployments separados (frontend y backend). Se requiere configurar CORS entre frontend y backend. El admin es responsable de operar ambos servicios.

---

## ADR-02 — Backend: FastAPI (Python)

**Contexto:** El backend debe exponer una API REST, integrarse con PostgreSQL, ser desplegable gratuitamente, y a futuro soportar WebSockets.

**Opciones evaluadas:**
- Python con FastAPI — documentación OpenAPI automática, buen soporte en agentes de desarrollo, WebSockets nativo
- Node.js con Express — un solo lenguaje en todo el stack, ecosistema npm enorme, async nativo
- Go — máximo rendimiento, binarios livianos, pero verboso y ecosistema más limitado

**Decisión:** Python con FastAPI.

**Justificación:** La documentación OpenAPI automática que genera FastAPI es una ventaja directa para el desarrollo con agentes, ya que provee una especificación legible por máquina de toda la API. Soporta WebSockets nativamente para la evolución futura. La diferencia de rendimiento respecto a Node.js o Go es irrelevante para la escala del proyecto (menos de 10 usuarios concurrentes). Go fue descartado porque su fortaleza en rendimiento y concurrencia no se justifica para este MVP.

**Consecuencias:** Se usan dos lenguajes en el proyecto (Python en backend, JavaScript en frontend). Se requiere familiaridad con el ecosistema Python (pip, virtualenvs). SQLAlchemy será el ORM para interactuar con PostgreSQL.

---

## ADR-03 — Frontend: React (SPA)

**Contexto:** El frontend debe ser responsive (mobile-first para el admin), soportar drag & drop como interacción central para el registro de reuniones, y ser desplegable gratuitamente.

**Opciones evaluadas:**
- React — ecosistema más grande, librerías maduras de drag & drop, mejor soporte en agentes de desarrollo
- Vue — curva de aprendizaje más suave, buena documentación, ecosistema más pequeño
- Svelte — sintaxis más simple, mejor rendimiento, ecosistema significativamente menor

**Decisión:** React.

**Justificación:** El drag & drop es un feature central del producto (CU-02 y CU-03). React tiene las librerías más maduras para esto (dnd-kit, react-beautiful-dnd). Además, los agentes de desarrollo tienen más datos de entrenamiento con React, lo que facilita el desarrollo asistido. El ecosistema más grande reduce el riesgo de quedarse sin solución para problemas específicos.

**Consecuencias:** JSX como sintaxis de templating. Se deben tomar decisiones adicionales sobre routing (React Router) y manejo de estado. Mayor verbosidad que Vue o Svelte para componentes simples.

---

## ADR-04 — Base de datos: PostgreSQL

**Contexto:** El modelo de datos es relacional con entidades claramente definidas (temporadas, reuniones, posiciones, jugadores). Se necesitan consultas estadísticas (promedios, rankings, conteos).

**Opciones evaluadas:**
- PostgreSQL — robusto, consultas estadísticas complejas con SQL, tier gratuito en Neon (serverless)
- SQLite — sin servidor, cero configuración, pero limitado en concurrencia y despliegue

**Decisión:** PostgreSQL.

**Justificación:** Las estadísticas derivadas (promedios de puntos, rankings, conteos de asistencias) son naturales en SQL y PostgreSQL las resuelve eficientemente. SQLite habría requerido migración futura al agregar tiempo real o escalar. Neon ofrece PostgreSQL serverless con tier gratuito estable (sin auto-delete) y escala a cero automáticamente. El costo extra de configuración respecto a SQLite es mínimo.

**Consecuencias:** Se requiere un servicio de hosting para la base de datos (Neon). Se necesita gestionar migraciones de schema. La conexión entre backend (Render) y base de datos (Neon) agrega una dependencia de red entre proveedores.

---

## ADR-05 — Autenticación: JWT propia

**Contexto:** Solo existe un administrador. Se necesita proteger los endpoints de escritura (crear temporada, registrar reunión, editar, cerrar) sin agregar complejidad innecesaria.

**Opciones evaluadas:**
- JWT propia — endpoint de login, token en header, control total
- Proveedor externo (Auth0, Firebase Auth) — login con Google, recuperación de contraseña, manejo de sesiones resuelto
- OAuth directo (Login con Google) — sin contraseñas, pero implementación compleja

**Decisión:** JWT propia.

**Justificación:** Los proveedores externos resuelven problemas que duDapp no tiene (registro masivo, recuperación de contraseña, múltiples proveedores de identidad). Para un solo admin, un endpoint de login que valide credenciales y genere un JWT es la solución más simple y sin dependencias externas. El modelo de usuarios en la base de datos ya está preparado para agregar más admins a futuro.

**Consecuencias:** Se debe implementar hashing de contraseñas (bcrypt). No hay recuperación de contraseña automatizada — si se pierde, se resetea directamente en la base de datos. No hay login social.

---

## ADR-06 — Hosting: Vercel (frontend) + Render (backend + PostgreSQL)

**Contexto:** El proyecto necesita hosting gratuito o de costo mínimo para tres componentes independientes: SPA, API y base de datos.

**Opciones evaluadas:**
- Vercel + Render — frontend optimizado para SPAs en Vercel, backend y BD juntos en Render
- Todo en Render — posible pero Vercel tiene mejor DX para frontends
- Todo en Vercel — Vercel no es ideal para backends Python persistentes
- Railway para backend — tier gratuito más limitado que Render

**Decisión:** Vercel para frontend, Render para backend y PostgreSQL.

**Nota (2026-04-26):** La decisión de alojar PostgreSQL en Render fue supersedida por ADR-09. El backend sigue en Render; la base de datos migró a Neon. Ver ADR-09.

**Justificación:** Vercel está optimizado para SPAs con despliegue automático desde GitHub y CDN global. Render permite tener backend FastAPI y PostgreSQL en el mismo proveedor con tier gratuito, simplificando la operación. Ambos se integran con GitHub para despliegue automático.

**Consecuencias:** Dos proveedores de hosting que mantener. Los tiers gratuitos de Render tienen cold starts (el backend puede tardar unos segundos en responder si lleva rato sin uso). Se depende de la disponibilidad de ambos servicios.

---

## ADR-07 — Tiempo real: Fuera del MVP, arquitectura preparada

**Contexto:** Los espectadores idealmente verían actualizaciones en tiempo real cuando el admin registra resultados. Esto requiere WebSockets o Server-Sent Events.

**Opciones evaluadas:**
- Incluir WebSockets desde el MVP — experiencia ideal pero mayor complejidad
- Excluir del MVP, consulta con recarga manual — más simple, suficiente para la escala actual
- Polling periódico — término medio, pero ineficiente

**Decisión:** Fuera del MVP. Recarga manual. Arquitectura preparada para agregar WebSockets.

**Justificación:** Con menos de 10 usuarios concurrentes y actualizaciones que ocurren una vez por semana, el tiempo real no justifica la complejidad adicional en el MVP. La separación frontend/backend ya permite agregar una capa de WebSockets al backend de FastAPI sin modificar la API REST existente ni el frontend de forma estructural.

**Consecuencias:** Los espectadores deben recargar la página para ver actualizaciones. Se acepta esta limitación como tolerable para la escala actual.

---

## ADR-08 — Metodología de desarrollo: TDD + SDD

**Contexto:** Es el primer proyecto de software del desarrollador. Se necesita una metodología que reduzca errores, facilite el desarrollo con agentes, y produzca un sistema confiable.

**Opciones evaluadas:**
- TDD + SDD — especificaciones primero, tests como contratos, implementación guiada por tests
- Desarrollo exploratorio — más rápido al inicio, pero propenso a bugs y deuda técnica
- Solo SDD sin TDD — buena documentación pero sin red de seguridad automatizada

**Decisión:** TDD + SDD combinados.

**Justificación:** SDD asegura que toda decisión técnica nace de una especificación clara, lo cual es crítico para el desarrollo con agentes — los agentes trabajan mejor con instrucciones precisas. TDD complementa esto traduciendo las especificaciones en tests antes de escribir implementación, creando una red de seguridad que detecta regresiones y valida que el comportamiento cumple las reglas de negocio (cálculo de puntos, visibilidad de jugadores, restricciones de temporada). El costo inicial mayor se compensa con menos bugs y refactoring más seguro.

**Consecuencias:** El desarrollo inicial es más lento. Se necesita diseñar la estrategia de testing antes de implementar. El código debe estructurarse para ser testeable (inyección de dependencias, separación de lógica de negocio). Se requiere infraestructura de testing (framework, base de datos de pruebas).

---

## ADR-09 — Migración de base de datos: de Render PostgreSQL a Neon

**Estado:** Aceptado (2026-04-26). Supersede la porción "DB hosting" de ADR-06.

**Contexto:** El tier gratuito de PostgreSQL en Render estaba programado para ser eliminado en mayo 2026. El proyecto dependía de ese tier para la base de datos de producción (ADR-06). Se necesitaba un proveedor con tier gratuito estable (sin auto-delete por inactividad) y backups básicos disponibles. El backend seguiría en Render (compute); solo la base de datos cambiaba de proveedor.

**Opciones evaluadas:**
- Neon — PostgreSQL serverless, scale-to-zero, tier gratuito sin auto-delete, PITR de 24h, conexión vía `DATABASE_URL` estándar sin cambios de código
- Supabase — PostgreSQL administrado, tier gratuito, pero pausa el proyecto tras 7 días de inactividad
- Railway — PostgreSQL, tier gratuito limitado (500 horas/mes), menos estable para proyectos durmientes
- Render tier pago — resuelve el problema pero introduce costo mensual

**Decisión:** Migrar la base de datos a Neon (PostgreSQL serverless).

**Justificación:** Neon ofrece el único tier gratuito sin auto-delete entre las opciones evaluadas. El scale-to-zero de Neon (~5 segundos de cold start en la primera conexión tras inactividad) es un trade-off aceptable frente a la alternativa de perder los datos. La migración no requirió cambios de código — solo actualizar `DATABASE_URL`. El desarrollo local sigue usando SQLite como fallback (vía `config.py`), sin impacto en el workflow de desarrollo.

**Consecuencias:**
- Backend (Render) y base de datos (Neon) ahora viven en proveedores distintos. Latencia de red entre compute y DB es mínima pero existe.
- La primera query tras un período de inactividad puede tomar ~5 segundos adicionales por el cold start de Neon.
- El desarrollo local sigue funcionando con SQLite fallback en `config.py` — sin cambios.
- Backups automáticos siguen siendo responsabilidad del operador (ver R-03 y `backend/scripts/backup_db.py`).
