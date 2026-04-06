# Casos de Uso Principales — v1

## CU-01 — Crear temporada

Actor: Administrador. El admin inicia una nueva temporada asignándole un nombre y seleccionando los jugadores que participarán. La fecha de inicio se registra automáticamente. Los jugadores son reutilizables entre temporadas — si ya existen en el sistema, se seleccionan; si son nuevos, se crean con su nombre. Una vez creada, la temporada queda activa y lista para recibir reuniones. Solo puede haber una temporada activa a la vez.

## CU-02 — Registrar reunión

Actor: Administrador. El admin abre la temporada activa y crea una nueva reunión. El sistema muestra a todos los jugadores inscritos en la temporada. El admin arrastra los jugadores que asistieron hacia las posiciones (1ro, 2do, 3ro...) mediante drag & drop. Existe un elemento "Invitado" siempre disponible que puede arrastrarse múltiples veces si asisten varios invitados. Los jugadores no posicionados quedan automáticamente como ausentes con 0 puntos. Al confirmar, el sistema calcula los puntos automáticamente: posición 1 = 15 puntos, posición 2 = 14, y así sucesivamente. La reunión queda registrada y la tabla de posiciones se actualiza al instante.

## CU-03 — Editar reunión registrada

Actor: Administrador. El admin puede volver a una reunión ya registrada para corregir errores — reordenar posiciones, agregar o quitar jugadores, agregar o quitar invitados. Los puntos se recalculan automáticamente y la tabla se actualiza.

## CU-04 — Consultar tabla de posiciones

Actor: Espectador. Cualquier persona accede al link de la liga y ve la tabla de posiciones actualizada de la temporada activa. La tabla muestra el ranking por puntos totales, con el nombre de cada jugador, sus puntos acumulados, y su cantidad de asistencias. Los invitados no aparecen en esta tabla. Los jugadores inscritos que no hayan asistido a ninguna reunión (0 asistencias, 0 puntos) tampoco se muestran — aparecen recién cuando registran su primera asistencia.

## CU-05 — Consultar resultados por reunión

Actor: Espectador. El espectador puede navegar entre las reuniones de la temporada y ver el resultado de cada una: qué jugadores participaron, en qué posición quedaron y cuántos puntos recibieron. Los invitados sí aparecen aquí, identificados como tales.

## CU-06 — Consultar estadísticas de la temporada

Actor: Espectador. El espectador accede a una vista de estadísticas que muestra como mínimo: cantidad de asistencias por jugador, promedio de puntos según asistencias, el top 3 de la temporada, el jugador con mejor promedio y el jugador con más inasistencias.

## CU-07 — Cerrar temporada

Actor: Administrador. Al finalizar las reuniones, el admin cierra la temporada. El sistema genera el resumen final destacando el top 3 y las estadísticas destacadas. Si hay empate en puntos, el sistema señala que debe resolverse por enfrentamiento directo. Una vez cerrada, la temporada pasa a ser histórica y no se puede modificar.

## CU-08 — Compartir liga

Actor: Administrador. El admin puede copiar o compartir un link público de la liga para enviarlo por WhatsApp u otros medios. Quien reciba el link accede directamente a la vista de espectador sin necesidad de cuenta.
