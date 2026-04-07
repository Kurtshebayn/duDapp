import pytest


def _auth_headers(client):
    r = client.post("/auth/login", json={"email": "admin@dudo.com", "password": "admin123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def temporada_con_datos(client, admin_user):
    """Temporada activa con 3 jugadores y 2 reuniones (incluyendo un invitado)."""
    headers = _auth_headers(client)

    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga 2024",
            "jugadores": [{"nombre": "Ana"}, {"nombre": "Bruno"}, {"nombre": "Carlos"}],
        },
        headers=headers,
    )
    temporada = r.json()
    temporada_id = temporada["id"]

    # Necesitamos los IDs de los jugadores creados
    from app.models.jugador import Jugador
    from app.database import SessionLocal
    # Usamos el mismo client que ya tiene la db sobreescrita, buscamos via el roster
    # Registramos primera reunión: Ana 1°, Bruno 2°, Invitado 3°, Carlos ausente
    r1 = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={
            "fecha": "2024-01-10",
            "posiciones": [
                {"id_jugador": None, "es_invitado": False, "posicion": 1},  # placeholder Ana
                {"id_jugador": None, "es_invitado": False, "posicion": 2},  # placeholder Bruno
                {"id_jugador": None, "es_invitado": True, "posicion": 3},
            ],
        },
        headers=headers,
    )
    # Obtenemos IDs reales desde la DB a través del endpoint de ranking (aún no existe)
    # En cambio, usamos el fixture db para obtenerlos
    return {"temporada_id": temporada_id, "headers": headers}


@pytest.fixture
def escenario(client, db, admin_user):
    """Fixture completo con IDs accesibles."""
    from app.models.jugador import Jugador

    headers = _auth_headers(client)

    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga 2024",
            "jugadores": [{"nombre": "Ana"}, {"nombre": "Bruno"}, {"nombre": "Carlos"}],
        },
        headers=headers,
    )
    temporada_id = r.json()["id"]

    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_ana, id_bruno, id_carlos = jugadores[0].id, jugadores[1].id, jugadores[2].id

    # Reunión 1: Ana 1°, Bruno 2°, Invitado 3° — Carlos ausente
    r1 = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={
            "fecha": "2024-01-10",
            "posiciones": [
                {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
                {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
                {"id_jugador": None, "es_invitado": True, "posicion": 3},
            ],
        },
        headers=headers,
    )

    # Reunión 2: Carlos 1°, Ana 2° — Bruno ausente
    r2 = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={
            "fecha": "2024-01-17",
            "posiciones": [
                {"id_jugador": id_carlos, "es_invitado": False, "posicion": 1},
                {"id_jugador": id_ana, "es_invitado": False, "posicion": 2},
            ],
        },
        headers=headers,
    )

    return {
        "temporada_id": temporada_id,
        "reunion1_id": r1.json()["id"],
        "reunion2_id": r2.json()["id"],
        "id_ana": id_ana,
        "id_bruno": id_bruno,
        "id_carlos": id_carlos,
    }


# ── CU-04: Tabla de posiciones ────────────────────────────────────────────────


def test_ranking_retorna_jugadores_con_asistencias(client, escenario):
    r = client.get("/temporadas/activa/ranking")
    assert r.status_code == 200
    data = r.json()
    # Ana (2 asistencias), Bruno (1), Carlos (1) — los 3 aparecen
    assert len(data) == 3
    nombres = [e["nombre"] for e in data]
    assert "Ana" in nombres
    assert "Bruno" in nombres
    assert "Carlos" in nombres


def test_ranking_excluye_invitados(client, escenario):
    r = client.get("/temporadas/activa/ranking")
    assert r.status_code == 200
    nombres = [e["nombre"] for e in r.json()]
    assert "Invitado" not in nombres


def test_ranking_excluye_jugadores_sin_asistencias(client, admin_user):
    headers = _auth_headers(client)
    client.post(
        "/temporadas",
        json={"nombre": "Liga", "jugadores": [{"nombre": "X"}, {"nombre": "Y"}]},
        headers=headers,
    )
    r = client.get("/temporadas/activa/ranking")
    assert r.status_code == 200
    assert r.json() == []


def test_ranking_sin_temporada_activa_retorna_404(client):
    r = client.get("/temporadas/activa/ranking")
    assert r.status_code == 404


def test_ranking_ordenado_por_puntos_descendente(client, escenario):
    r = client.get("/temporadas/activa/ranking")
    data = r.json()
    # Ana: 15 + 14 = 29 pts, Carlos: 15 pts, Bruno: 14 pts
    assert data[0]["nombre"] == "Ana"
    assert data[0]["puntos"] == 29
    assert data[0]["asistencias"] == 2
    assert data[1]["puntos"] > data[2]["puntos"]


# ── CU-05: Resultados por reunión ────────────────────────────────────────────


def test_listar_reuniones_temporada_activa(client, escenario):
    r = client.get("/temporadas/activa/reuniones")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["numero_jornada"] == 1
    assert data[1]["numero_jornada"] == 2


def test_listar_reuniones_sin_temporada_activa_retorna_404(client):
    r = client.get("/temporadas/activa/reuniones")
    assert r.status_code == 404


def test_resultados_reunion_incluye_posiciones_y_puntos(client, escenario):
    r = client.get(f"/reuniones/{escenario['reunion1_id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["numero_jornada"] == 1
    assert len(data["posiciones"]) == 3
    primera = next(p for p in data["posiciones"] if p["posicion"] == 1)
    assert primera["puntos"] == 15
    assert primera["nombre"] == "Ana"


def test_resultados_reunion_incluye_invitados_identificados(client, escenario):
    r = client.get(f"/reuniones/{escenario['reunion1_id']}")
    posiciones = r.json()["posiciones"]
    invitados = [p for p in posiciones if p["es_invitado"]]
    assert len(invitados) == 1
    assert invitados[0]["nombre"] == "Invitado"


def test_resultados_reunion_not_found(client):
    r = client.get("/reuniones/9999")
    assert r.status_code == 404


# ── CU-06: Estadísticas ───────────────────────────────────────────────────────


def test_estadisticas_estructura_completa(client, escenario):
    r = client.get("/temporadas/activa/estadisticas")
    assert r.status_code == 200
    data = r.json()
    assert "ranking" in data
    assert "top3" in data
    assert "mejor_promedio" in data
    assert "mas_inasistencias" in data


def test_estadisticas_ranking_incluye_promedio_e_inasistencias(client, escenario):
    r = client.get("/temporadas/activa/estadisticas")
    entry = r.json()["ranking"][0]  # Ana
    assert "promedio" in entry
    assert "inasistencias" in entry
    assert entry["promedio"] == round(29 / 2, 2)
    assert entry["inasistencias"] == 0


def test_estadisticas_top3(client, escenario):
    r = client.get("/temporadas/activa/estadisticas")
    data = r.json()
    assert len(data["top3"]) == 3
    assert data["top3"][0]["nombre"] == "Ana"


def test_estadisticas_mejor_promedio(client, escenario):
    r = client.get("/temporadas/activa/estadisticas")
    data = r.json()
    # Ana: 29/2=14.5, Carlos: 15/1=15.0, Bruno: 14/1=14.0
    assert data["mejor_promedio"]["nombre"] == "Carlos"
    assert data["mejor_promedio"]["promedio"] == 15.0


def test_estadisticas_mas_inasistencias(client, escenario):
    r = client.get("/temporadas/activa/estadisticas")
    data = r.json()
    # 2 reuniones: Bruno faltó 1, Carlos faltó 1, Ana faltó 0
    assert data["mas_inasistencias"]["inasistencias"] == 1


def test_estadisticas_sin_temporada_activa_retorna_404(client):
    r = client.get("/temporadas/activa/estadisticas")
    assert r.status_code == 404
