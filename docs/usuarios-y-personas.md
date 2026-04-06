# Usuarios y Personas — v1

## Persona 1 — El Administrador ("El Comisionado")

Es el organizador de la liga. Una sola persona con cuenta única. Su principal necesidad es registrar los resultados de cada reunión de forma rápida, principalmente desde el celular, muchas veces mientras participa del juego. Ocasionalmente usa computador. Si no puede asistir, alguien anota las posiciones en papel o por mensaje y él las ingresa después. Valora la velocidad y simplicidad por sobre todo — si ingresar resultados toma más de un par de minutos, la herramienta falla. También necesita poder compartir un link fácilmente (por WhatsApp, por ejemplo) para que otros vean la liga.

## Persona 2 — El Espectador ("La Hinchada")

Incluye tanto a los jugadores de la liga como a cualquier persona curiosa. No tienen cuenta, no necesitan registrarse. Acceden por un link compartido. Solo necesitan ver tres cosas: la tabla de posiciones actual, los resultados de cada reunión y las estadísticas de la temporada. Esperan que la información esté actualizada al momento de consultarla. Acceden principalmente desde el celular.

## Decisiones implícitas

Solo existe un rol con permisos de escritura (admin). Todo lo demás es lectura pública. No hay sistema de registro de usuarios ni login para espectadores. La autenticación solo aplica al admin.
