"""
Tests de integración para POST /temporadas/activa/inscripciones (Phase 3.1)
+ regresión de ranking con jugador tardío (Phase 3.2).
"""
import pytest


def _auth_headers(client):
    r = client.post(
        "/auth/login",
        json={"identificador": "admin@dudo.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _crear_temporada(client, headers, nombres):
    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga Test",
            "fecha_inicio": "2024-01-01",
            "jugadores": [{"nombre": n} for n in nombres],
        },
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


def _crear_jugador(client, headers, nombre):
    r = client.post("/jugadores", json={"nombre": nombre}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def _registrar_reunion(client, headers, temporada_id, fecha, posiciones_jugadores):
    """posiciones_jugadores: lista de id_jugador en orden 1°, 2°, 3°..."""
    posiciones = [
        {"id_jugador": id_j, "es_invitado": False, "posicion": idx + 1}
        for idx, id_j in enumerate(posiciones_jugadores)
    ]
    r = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={"fecha": fecha, "posiciones": posiciones},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture
def auth_headers(client, admin_user):
    return _auth_headers(client)


@pytest.fixture
def escenario_simple(client, db, admin_user):
    """Temporada activa con 3 jugadores inscritos, sin reuniones."""
    from app.models.jugador import Jugador

    headers = _auth_headers(client)
    temporada_id = _crear_temporada(client, headers, ["Ana", "Bruno", "Carlos"])
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    return {
        "temporada_id": temporada_id,
        "headers": headers,
        "id_ana": jugadores[0].id,
        "id_bruno": jugadores[1].id,
        "id_carlos": jugadores[2].id,
    }


# ── 3.1: tests del endpoint POST /temporadas/activa/inscripciones ────────────


def test_inscribir_jugador_en_activa_201(client, escenario_simple):
    headers = escenario_simple["headers"]
    id_diego = _crear_jugador(client, headers, "Diego")

    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_diego},
        headers=headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["id_jugador"] == id_diego
    assert data["id_temporada"] == escenario_simple["temporada_id"]
    assert isinstance(data["id"], int)


def test_inscribir_aumenta_la_lista_de_inscritos_de_la_temporada(client, escenario_simple):
    headers = escenario_simple["headers"]
    id_diego = _crear_jugador(client, headers, "Diego")

    # baseline: 3 jugadores inscritos
    pre = client.get("/temporadas/activa").json()
    assert len(pre["jugadores"]) == 3

    client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_diego},
        headers=headers,
    )

    post = client.get("/temporadas/activa").json()
    assert len(post["jugadores"]) == 4
    nombres = [j["nombre"] for j in post["jugadores"]]
    assert "Diego" in nombres


def test_inscribir_sin_auth_responde_401(client, escenario_simple):
    id_diego = _crear_jugador(client, escenario_simple["headers"], "Diego")
    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_diego},
    )
    assert r.status_code == 401


def test_inscribir_jugador_inexistente_responde_404(client, escenario_simple):
    headers = escenario_simple["headers"]
    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": 9999},
        headers=headers,
    )
    assert r.status_code == 404


def test_inscribir_sin_temporada_activa_responde_404(client, admin_user):
    headers = _auth_headers(client)
    id_x = _crear_jugador(client, headers, "X")
    # No hay temporada activa
    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_x},
        headers=headers,
    )
    assert r.status_code == 404


def test_inscribir_jugador_ya_inscrito_responde_409(client, escenario_simple):
    headers = escenario_simple["headers"]
    # Ana ya está inscrita en escenario_simple
    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": escenario_simple["id_ana"]},
        headers=headers,
    )
    assert r.status_code == 409


def test_inscribir_temporada_cerrada_responde_404(client, escenario_simple):
    headers = escenario_simple["headers"]
    temporada_id = escenario_simple["temporada_id"]

    # Cerrar la temporada
    cerrar = client.post(f"/temporadas/{temporada_id}/cerrar", headers=headers)
    assert cerrar.status_code == 200

    id_diego = _crear_jugador(client, headers, "Diego")
    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_diego},
        headers=headers,
    )
    assert r.status_code == 404


# ── 3.2: regresión de ranking con jugador tardío ─────────────────────────────


def test_tardio_aparece_en_ranking_solo_con_sus_puntos_reales(client, escenario_simple):
    """
    2 reuniones previas (sin Diego), inscribir Diego, 1 reunión más donde Diego sale 1°.
    Diego debe aparecer en ranking con puntos=15 y asistencias=1.
    Ana, Bruno, Carlos no se ven afectados.
    """
    headers = escenario_simple["headers"]
    id_ana, id_bruno, id_carlos = (
        escenario_simple["id_ana"],
        escenario_simple["id_bruno"],
        escenario_simple["id_carlos"],
    )
    temporada_id = escenario_simple["temporada_id"]

    # Reunión 1: Ana 1°, Bruno 2°, Carlos 3°
    _registrar_reunion(client, headers, temporada_id, "2024-01-10", [id_ana, id_bruno, id_carlos])
    # Reunión 2: Bruno 1°, Carlos 2°, Ana 3°
    _registrar_reunion(client, headers, temporada_id, "2024-01-17", [id_bruno, id_carlos, id_ana])

    # Inscribir Diego (tardío)
    id_diego = _crear_jugador(client, headers, "Diego")
    client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_diego},
        headers=headers,
    )

    # Reunión 3: Diego 1°, Ana 2°
    _registrar_reunion(client, headers, temporada_id, "2024-01-24", [id_diego, id_ana])

    r = client.get("/temporadas/activa/ranking")
    assert r.status_code == 200
    ranking = {entry["nombre"]: entry for entry in r.json()}

    # Diego: solo participó en reunión 3 (1° = 15 pts)
    assert "Diego" in ranking
    assert ranking["Diego"]["puntos"] == 15
    assert ranking["Diego"]["asistencias"] == 1

    # Ana: 1° + 3° + 2° = 15 + 13 + 14 = 42 pts en 3 asistencias
    assert ranking["Ana"]["puntos"] == 15 + 13 + 14
    assert ranking["Ana"]["asistencias"] == 3


def test_tardio_sin_asistencias_no_aparece_en_ranking(client, escenario_simple):
    """
    Inscribir Diego como tardío pero sin que juegue ninguna reunión adicional.
    Diego NO debe aparecer en ranking (regla existente preservada).
    """
    headers = escenario_simple["headers"]
    temporada_id = escenario_simple["temporada_id"]
    id_ana, id_bruno, id_carlos = (
        escenario_simple["id_ana"],
        escenario_simple["id_bruno"],
        escenario_simple["id_carlos"],
    )

    # 2 reuniones previas
    _registrar_reunion(client, headers, temporada_id, "2024-01-10", [id_ana, id_bruno, id_carlos])
    _registrar_reunion(client, headers, temporada_id, "2024-01-17", [id_bruno, id_carlos, id_ana])

    # Inscribir Diego pero NO jugar más reuniones
    id_diego = _crear_jugador(client, headers, "Diego")
    client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_diego},
        headers=headers,
    )

    r = client.get("/temporadas/activa/ranking")
    nombres = [e["nombre"] for e in r.json()]
    assert "Diego" not in nombres
    # Pero los demás SÍ aparecen
    assert "Ana" in nombres
    assert "Bruno" in nombres
    assert "Carlos" in nombres


def test_tardio_promedio_usa_solo_asistencias_reales(client, escenario_simple):
    """
    5 reuniones previas (sin Diego), inscribir Diego, 2 reuniones más donde Diego sale 1°.
    Diego puntos=30 / asistencias=2 → promedio derivado 15.0 (NO 30/7).
    Validado contra /ranking: el endpoint expone puntos y asistencias reales;
    el promedio se deriva client-side.
    """
    headers = escenario_simple["headers"]
    temporada_id = escenario_simple["temporada_id"]
    id_ana, id_bruno, id_carlos = (
        escenario_simple["id_ana"],
        escenario_simple["id_bruno"],
        escenario_simple["id_carlos"],
    )

    # 5 reuniones previas
    for i, fecha in enumerate(["2024-01-10", "2024-01-17", "2024-01-24", "2024-01-31", "2024-02-07"]):
        _registrar_reunion(client, headers, temporada_id, fecha, [id_ana, id_bruno, id_carlos])

    # Inscribir Diego
    id_diego = _crear_jugador(client, headers, "Diego")
    client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_diego},
        headers=headers,
    )

    # 2 reuniones más donde Diego sale 1°
    _registrar_reunion(client, headers, temporada_id, "2024-02-14", [id_diego, id_ana])
    _registrar_reunion(client, headers, temporada_id, "2024-02-21", [id_diego, id_bruno])

    r = client.get("/temporadas/activa/ranking")
    assert r.status_code == 200
    diego = next(entry for entry in r.json() if entry["nombre"] == "Diego")

    # Diego: 15 + 15 = 30 pts en 2 asistencias → promedio derivado 15.0
    assert diego["puntos"] == 30
    assert diego["asistencias"] == 2
    assert diego["puntos"] / diego["asistencias"] == 15.0


def test_tardio_no_se_suma_a_reuniones_previas(client, escenario_simple):
    """
    5 reuniones previas, inscribir Diego, 2 reuniones donde juega.
    Diego asistencias=2 (NO 7); las reuniones previas NO se le suman.
    Ana asistencias=6 (5 previas + 1 nueva donde se enfrenta a Diego).
    """
    headers = escenario_simple["headers"]
    temporada_id = escenario_simple["temporada_id"]
    id_ana, id_bruno, id_carlos = (
        escenario_simple["id_ana"],
        escenario_simple["id_bruno"],
        escenario_simple["id_carlos"],
    )

    for fecha in ["2024-01-10", "2024-01-17", "2024-01-24", "2024-01-31", "2024-02-07"]:
        _registrar_reunion(client, headers, temporada_id, fecha, [id_ana, id_bruno, id_carlos])

    id_diego = _crear_jugador(client, headers, "Diego")
    client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": id_diego},
        headers=headers,
    )

    _registrar_reunion(client, headers, temporada_id, "2024-02-14", [id_diego, id_ana])
    _registrar_reunion(client, headers, temporada_id, "2024-02-21", [id_diego, id_bruno])

    r = client.get("/temporadas/activa/ranking")
    ranking = {entry["nombre"]: entry for entry in r.json()}

    # Diego: solo cuenta sus 2 asistencias reales (las previas NO se le suman)
    assert ranking["Diego"]["asistencias"] == 2
    # Ana: 5 previas + 1 nueva = 6
    assert ranking["Ana"]["asistencias"] == 6
