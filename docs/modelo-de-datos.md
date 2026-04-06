# Modelo de Datos — v1

## Entidad: Usuario

Representa a los administradores del sistema. Atributos: id, email, contraseña (hasheada), nombre. Hoy existe un solo registro. A futuro, cada usuario podría administrar su propia liga.

## Entidad: Jugador

Representa a una persona que participa en ligas. Existe independientemente de las temporadas y es reutilizable. Atributos: id, nombre. A futuro se agrega foto.

## Entidad: Temporada

Representa un ciclo de la liga (~3 meses). Atributos: id, nombre, fecha de inicio (automática), estado (activa/cerrada). Solo puede haber una temporada activa a la vez. Pertenece a un usuario (admin). Al cerrarse, no se puede modificar.

## Entidad: Inscripción (Temporada ↔ Jugador)

Tabla intermedia que registra qué jugadores participan en qué temporada. Atributos: id, id_temporada, id_jugador. Un jugador puede estar inscrito en múltiples temporadas. No se admiten incorporaciones a mitad de temporada (regla de negocio controlada por la aplicación, no por la base de datos).

## Entidad: Reunión

Representa una sesión de juego semanal dentro de una temporada. Atributos: id, id_temporada, número de jornada, fecha. Pertenece a una temporada.

## Entidad: Posición

Representa el resultado de un participante en una reunión específica. Atributos: id, id_reunión, id_jugador (nullable), es_invitado (boolean), posición (1ro, 2do...), puntos (calculados automáticamente). Si es_invitado es verdadero, id_jugador es nulo. Si es_invitado es falso, id_jugador apunta al jugador inscrito. Los puntos se calculan como: 15 - (posición - 1).

## Relaciones

- Un **Usuario** tiene muchas **Temporadas**
- Una **Temporada** tiene muchos **Jugadores** (a través de Inscripción)
- Una **Temporada** tiene muchas **Reuniones**
- Una **Reunión** tiene muchas **Posiciones**
- Una **Posición** pertenece a un **Jugador** (o es invitado)

## Estadísticas derivadas (no se almacenan, se calculan con queries)

- Asistencias por jugador = contar las posiciones donde aparece ese jugador en la temporada
- Promedio de puntos = suma de puntos / cantidad de asistencias
- Ranking = ordenar jugadores por puntos totales acumulados
- Jugador con más inasistencias = total de reuniones menos asistencias de cada jugador
