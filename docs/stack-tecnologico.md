# Stack Tecnológico — v1

| Capa | Tecnología | Justificación |
|---|---|---|
| Frontend | React (SPA) | Ecosistema más grande para componentes UI, librerías maduras de drag & drop (crítico para CU-02), mejor soporte en agentes de desarrollo |
| Backend | FastAPI (Python) | Framework liviano para API REST, documentación OpenAPI automática (facilita desarrollo con agentes), soporte nativo para WebSockets a futuro |
| Base de datos | PostgreSQL | Modelo de datos relacional, consultas estadísticas complejas resueltas con SQL, tier gratuito disponible en Render |
| Autenticación | JWT propia | Un solo admin, sin necesidad de proveedores externos. Endpoint de login que genera token, validación por header en requests protegidos |
| Hosting frontend | Vercel | Despliegue automático desde GitHub, tier gratuito, subdominios incluidos, optimizado para SPAs |
| Hosting backend + DB | Render | Backend y PostgreSQL en el mismo proveedor, tier gratuito, simplifica operación |
| Control de versiones | GitHub | Repositorio del proyecto, integración directa con Vercel y Render para despliegue automático |

**Fuera del MVP (documentado para futuro):** WebSockets para tiempo real, almacenamiento de imágenes para fotos de jugadores, dominio propio.
