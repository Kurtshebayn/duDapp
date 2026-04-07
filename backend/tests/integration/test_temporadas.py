import pytest
from datetime import date


@pytest.fixture
def auth_headers(client, admin_user):
    r = client.post("/auth/login", json={"identificador": "admin@dudo.com", "password": "admin123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def jugadores_en_db(db):
    from app.models.jugador import Jugador
    jugadores = [Jugador(nombre="Ana"), Jugador(nombre="Bruno"), Jugador(nombre="Carlos")]
    db.add_all(jugadores)
    db.commit()
    for j in jugadores:
        db.refresh(j)
    return jugadores


def test_crear_temporada_con_jugadores_existentes(client, auth_headers, jugadores_en_db):
    ids = [j.id for j in jugadores_en_db]
    r = client.post(
        "/temporadas",
        json={"nombre": "Liga 2024", "fecha_inicio": "2024-01-01", "jugadores": [{"id": i} for i in ids]},
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["nombre"] == "Liga 2024"
    assert data["estado"] == "activa"
    assert "fecha_inicio" in data


def test_crear_temporada_con_jugadores_nuevos(client, auth_headers):
    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga 2024",
            "fecha_inicio": "2024-01-01",
            "jugadores": [{"nombre": "Nuevo1"}, {"nombre": "Nuevo2"}],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["estado"] == "activa"


def test_crear_temporada_falla_si_ya_hay_activa(client, auth_headers, jugadores_en_db):
    ids = [j.id for j in jugadores_en_db]
    payload = {"nombre": "Liga", "fecha_inicio": "2024-01-01", "jugadores": [{"id": i} for i in ids]}
    client.post("/temporadas", json=payload, headers=auth_headers)
    r = client.post("/temporadas", json=payload, headers=auth_headers)
    assert r.status_code == 400


def test_crear_temporada_sin_autenticacion(client, jugadores_en_db):
    ids = [j.id for j in jugadores_en_db]
    r = client.post(
        "/temporadas",
        json={"nombre": "Liga", "fecha_inicio": "2024-01-01", "jugadores": [{"id": i} for i in ids]},
    )
    assert r.status_code == 401


def test_cerrar_temporada(client, auth_headers, jugadores_en_db):
    ids = [j.id for j in jugadores_en_db]
    crear = client.post(
        "/temporadas",
        json={"nombre": "Liga", "fecha_inicio": "2024-01-01", "jugadores": [{"id": i} for i in ids]},
        headers=auth_headers,
    )
    temporada_id = crear.json()["id"]

    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["estado"] == "cerrada"


def test_cerrar_temporada_ya_cerrada_falla(client, auth_headers, jugadores_en_db):
    ids = [j.id for j in jugadores_en_db]
    crear = client.post(
        "/temporadas",
        json={"nombre": "Liga", "fecha_inicio": "2024-01-01", "jugadores": [{"id": i} for i in ids]},
        headers=auth_headers,
    )
    temporada_id = crear.json()["id"]
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 400
