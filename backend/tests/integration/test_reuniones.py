import pytest
from datetime import date


@pytest.fixture
def auth_headers(client, admin_user):
    r = client.post("/auth/login", json={"email": "admin@dudo.com", "password": "admin123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def temporada_con_jugadores(client, auth_headers, db):
    from app.models.jugador import Jugador
    jugadores = [Jugador(nombre="Ana"), Jugador(nombre="Bruno"), Jugador(nombre="Carlos")]
    db.add_all(jugadores)
    db.commit()
    for j in jugadores:
        db.refresh(j)

    r = client.post(
        "/temporadas",
        json={"nombre": "Liga 2024", "jugadores": [{"id": j.id} for j in jugadores]},
        headers=auth_headers,
    )
    return r.json(), jugadores


def test_registrar_reunion_calcula_puntos(client, auth_headers, temporada_con_jugadores):
    temporada, jugadores = temporada_con_jugadores
    tid = temporada["id"]
    j1, j2, j3 = jugadores

    r = client.post(
        f"/temporadas/{tid}/reuniones",
        json={
            "fecha": str(date.today()),
            "posiciones": [
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
                {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            ],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["numero_jornada"] == 1

    # Verificar puntos en DB
    from app.models.posicion import Posicion
    from tests.conftest import TestingSessionLocal
    session = TestingSessionLocal()
    posiciones = session.query(Posicion).filter(Posicion.id_reunion == data["id"]).all()
    puntos_por_jugador = {p.id_jugador: p.puntos for p in posiciones}
    assert puntos_por_jugador[j1.id] == 15
    assert puntos_por_jugador[j2.id] == 14
    assert puntos_por_jugador[j3.id] == 13
    session.close()


def test_invitado_consume_posicion_y_puntos(client, auth_headers, temporada_con_jugadores):
    temporada, jugadores = temporada_con_jugadores
    tid = temporada["id"]
    j1 = jugadores[0]

    r = client.post(
        f"/temporadas/{tid}/reuniones",
        json={
            "fecha": str(date.today()),
            "posiciones": [
                {"id_jugador": None, "es_invitado": True, "posicion": 1},
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 2},
            ],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201

    from app.models.posicion import Posicion
    from tests.conftest import TestingSessionLocal
    session = TestingSessionLocal()
    posiciones = session.query(Posicion).filter(Posicion.id_reunion == r.json()["id"]).all()
    invitado = next(p for p in posiciones if p.es_invitado)
    jugador = next(p for p in posiciones if not p.es_invitado)
    assert invitado.puntos == 15
    assert jugador.puntos == 14  # posición 2, no 15
    session.close()


def test_registrar_reunion_en_temporada_cerrada_falla(client, auth_headers, temporada_con_jugadores):
    temporada, jugadores = temporada_con_jugadores
    tid = temporada["id"]
    client.post(f"/temporadas/{tid}/cerrar", headers=auth_headers)

    r = client.post(
        f"/temporadas/{tid}/reuniones",
        json={"fecha": str(date.today()), "posiciones": []},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_editar_reunion_recalcula_puntos(client, auth_headers, temporada_con_jugadores):
    temporada, jugadores = temporada_con_jugadores
    tid = temporada["id"]
    j1, j2 = jugadores[0], jugadores[1]

    crear = client.post(
        f"/temporadas/{tid}/reuniones",
        json={
            "fecha": str(date.today()),
            "posiciones": [
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            ],
        },
        headers=auth_headers,
    )
    reunion_id = crear.json()["id"]

    # Invertir posiciones
    r = client.put(
        f"/reuniones/{reunion_id}",
        json={
            "fecha": str(date.today()),
            "posiciones": [
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 2},
            ],
        },
        headers=auth_headers,
    )
    assert r.status_code == 200

    from app.models.posicion import Posicion
    from tests.conftest import TestingSessionLocal
    session = TestingSessionLocal()
    posiciones = session.query(Posicion).filter(Posicion.id_reunion == reunion_id).all()
    puntos = {p.id_jugador: p.puntos for p in posiciones}
    assert puntos[j2.id] == 15
    assert puntos[j1.id] == 14
    session.close()


def test_editar_reunion_en_temporada_cerrada_falla(client, auth_headers, temporada_con_jugadores):
    temporada, jugadores = temporada_con_jugadores
    tid = temporada["id"]
    j1 = jugadores[0]

    crear = client.post(
        f"/temporadas/{tid}/reuniones",
        json={
            "fecha": str(date.today()),
            "posiciones": [{"id_jugador": j1.id, "es_invitado": False, "posicion": 1}],
        },
        headers=auth_headers,
    )
    reunion_id = crear.json()["id"]
    client.post(f"/temporadas/{tid}/cerrar", headers=auth_headers)

    r = client.put(
        f"/reuniones/{reunion_id}",
        json={
            "fecha": str(date.today()),
            "posiciones": [{"id_jugador": j1.id, "es_invitado": False, "posicion": 1}],
        },
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_numero_jornada_autoincremental(client, auth_headers, temporada_con_jugadores):
    temporada, jugadores = temporada_con_jugadores
    tid = temporada["id"]
    j1 = jugadores[0]
    payload = {
        "fecha": str(date.today()),
        "posiciones": [{"id_jugador": j1.id, "es_invitado": False, "posicion": 1}],
    }
    r1 = client.post(f"/temporadas/{tid}/reuniones", json=payload, headers=auth_headers)
    r2 = client.post(f"/temporadas/{tid}/reuniones", json=payload, headers=auth_headers)

    assert r1.json()["numero_jornada"] == 1
    assert r2.json()["numero_jornada"] == 2
