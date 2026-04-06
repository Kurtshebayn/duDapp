# Estrategia de Testing — v1

**Enfoque:** TDD pragmático. Los tests se escriben antes de la implementación, enfocados en reglas de negocio críticas y flujos de alto riesgo. No se testean trivialidades (getters, setters, validaciones básicas de campos).

## Nivel 1 — Tests unitarios (backend)

Testean la lógica de negocio en aislamiento, sin base de datos ni HTTP.

**Reglas de negocio a testear:**

- **Cálculo de puntos:** posición 1 = 15 puntos, posición 2 = 14, posición N = 15 - (N-1). Validar con diferentes cantidades de participantes.
- **Invitados consumen puntos:** si un invitado ocupa la posición 1, recibe 15 puntos. El jugador regular en posición 2 recibe 14 puntos, no 15.
- **Ausentes reciben 0:** jugadores inscritos que no participan en una reunión tienen 0 puntos para esa reunión.
- **Visibilidad en tabla:** jugadores con 0 asistencias y 0 puntos no aparecen en el ranking. Aparecen recién al registrar su primera asistencia.
- **Invitados fuera de la tabla:** los invitados nunca aparecen en la tabla de posiciones de la temporada, independientemente de cuántas reuniones participen.
- **Cálculo de estadísticas:** asistencias = cantidad de reuniones donde el jugador tiene posición registrada. Promedio = puntos totales / asistencias. Jugador con más inasistencias = total de reuniones - asistencias.
- **Restricción de temporada activa:** no puede haber más de una temporada activa simultáneamente.
- **Temporada cerrada inmutable:** una vez cerrada, no se pueden agregar, editar ni eliminar reuniones de esa temporada.

**Herramienta sugerida:** pytest (estándar en Python, simple, buena integración con FastAPI).

## Nivel 2 — Tests de integración (API + base de datos)

Testean flujos completos a través de la API con una base de datos de prueba real (PostgreSQL de test).

**Flujos críticos a testear:**

- **Crear temporada:** POST con nombre y jugadores → temporada creada con estado activa, jugadores inscritos. Intentar crear otra temporada activa → error.
- **Registrar reunión:** POST con posiciones de jugadores e invitados → puntos calculados correctamente, tabla de posiciones actualizada. Validar que jugadores no incluidos quedan con 0 puntos.
- **Editar reunión:** PUT con posiciones modificadas → puntos recalculados, tabla actualizada con nuevos valores.
- **Cerrar temporada:** POST para cerrar → estado cambia a cerrada, top 3 generado correctamente. Intentar registrar reunión en temporada cerrada → error.
- **Consultar tabla de posiciones:** GET → solo muestra jugadores con al menos 1 asistencia, ordenados por puntos totales, invitados excluidos.
- **Consultar estadísticas:** GET → promedios y conteos calculados correctamente.
- **Autenticación:** requests sin JWT a endpoints protegidos → rechazados. Requests con JWT válido → aceptados.

**Herramienta sugerida:** pytest + httpx (cliente async para testear endpoints FastAPI) + base de datos PostgreSQL de test que se limpia entre tests.

## Nivel 3 — Tests E2E

Fuera del MVP. Se incorporarán cuando la aplicación esté estable y se necesite validar flujos completos desde el navegador (drag & drop, navegación, compartir link).

**Herramienta candidata para futuro:** Playwright o Cypress.

## Principios de testing para el proyecto

- Cada regla de negocio documentada tiene al menos un test que la valida.
- Los tests se escriben antes de la implementación (TDD). Se define primero qué debe pasar, después se escribe el código que lo hace pasar.
- Los tests son la fuente de verdad: si un test pasa, el comportamiento es correcto. Si falla, el código es incorrecto, no el test (salvo que la regla de negocio haya cambiado).
- La base de datos de test se resetea entre cada test de integración para evitar dependencias entre tests.
