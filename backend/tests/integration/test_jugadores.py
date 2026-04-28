import pytest


@pytest.fixture
def auth_headers(client, admin_user):
    r = client.post(
        "/auth/login",
        json={"identificador": "admin@dudo.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_crear_jugador_devuelve_201_con_jugador_creado(client, auth_headers):
    r = client.post("/jugadores", json={"nombre": "Ana"}, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["nombre"] == "Ana"
    assert data["foto_url"] is None
    assert isinstance(data["id"], int)


def test_crear_jugador_aparece_en_listado(client, auth_headers):
    client.post("/jugadores", json={"nombre": "Ana"}, headers=auth_headers)
    r = client.get("/jugadores")
    assert r.status_code == 200
    nombres = [j["nombre"] for j in r.json()]
    assert "Ana" in nombres


def test_crear_jugador_sin_auth_responde_401(client):
    r = client.post("/jugadores", json={"nombre": "Ana"})
    assert r.status_code == 401


def test_crear_jugador_nombre_vacio_responde_422(client, auth_headers):
    r = client.post("/jugadores", json={"nombre": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_crear_jugador_nombre_solo_whitespace_responde_422(client, auth_headers):
    r = client.post("/jugadores", json={"nombre": "   "}, headers=auth_headers)
    assert r.status_code == 422


def test_crear_jugador_nombre_duplicado_exacto_responde_409(client, auth_headers):
    client.post("/jugadores", json={"nombre": "Juan"}, headers=auth_headers)
    r = client.post("/jugadores", json={"nombre": "Juan"}, headers=auth_headers)
    assert r.status_code == 409


def test_crear_jugador_duplicado_case_insensitive_responde_409(client, auth_headers):
    client.post("/jugadores", json={"nombre": "Juan"}, headers=auth_headers)
    r = client.post("/jugadores", json={"nombre": "JUAN"}, headers=auth_headers)
    assert r.status_code == 409


def test_crear_jugador_nombre_se_normaliza_con_strip(client, auth_headers):
    r = client.post("/jugadores", json={"nombre": "  Pedro  "}, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["nombre"] == "Pedro"


def test_crear_jugador_strip_se_aplica_para_dedup(client, auth_headers):
    client.post("/jugadores", json={"nombre": "Maria"}, headers=auth_headers)
    r = client.post("/jugadores", json={"nombre": "  Maria  "}, headers=auth_headers)
    assert r.status_code == 409
