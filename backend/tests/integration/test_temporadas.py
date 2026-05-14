import pytest
from datetime import date

from app.models.posicion import Posicion
from app.models.reunion import Reunion


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


# ── Phase 6: Reuso de jugador existente al crear temporada ───────────────────


def test_crear_temporada_reusa_jugador_existente_por_nombre(client, auth_headers, jugadores_en_db):
    """Crear temporada con un nombre que YA existe en el catálogo debe REUSAR
    al jugador existente, no crear duplicado."""
    pre = client.get("/jugadores").json()
    assert len(pre) == 3
    assert sum(1 for j in pre if j["nombre"] == "Ana") == 1

    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga 2024",
            "fecha_inicio": "2024-01-01",
            "jugadores": [{"nombre": "Ana"}],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201

    post = client.get("/jugadores").json()
    assert len(post) == 3, "No debería haberse creado un Ana duplicado"
    assert sum(1 for j in post if j["nombre"] == "Ana") == 1


def test_crear_temporada_reuso_es_case_insensitive_con_strip(client, auth_headers, jugadores_en_db):
    """'  ANA  ' debe reusar al jugador 'Ana' existente (case-insensitive + strip)."""
    pre = client.get("/jugadores").json()
    assert len(pre) == 3

    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga 2024",
            "fecha_inicio": "2024-01-01",
            "jugadores": [{"nombre": "  ANA  "}],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201

    post = client.get("/jugadores").json()
    nombres = sorted([j["nombre"] for j in post])
    assert nombres == ["Ana", "Bruno", "Carlos"], "No debería haberse creado '  ANA  ' ni 'ANA'"


def test_crear_temporada_mezcla_id_nombre_existente_reusado_y_nombre_nuevo(
    client, auth_headers, jugadores_en_db
):
    """Mezcla: {id: Ana}, {nombre: 'bruno'} (existente case-insensitive), {nombre: 'Diego'} (nuevo)."""
    id_ana = jugadores_en_db[0].id

    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga 2024",
            "fecha_inicio": "2024-01-01",
            "jugadores": [
                {"id": id_ana},
                {"nombre": "bruno"},
                {"nombre": "Diego"},
            ],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201

    post = client.get("/jugadores").json()
    nombres = sorted([j["nombre"] for j in post])
    assert nombres == ["Ana", "Bruno", "Carlos", "Diego"], (
        "Diego debe agregarse, Bruno reusarse, no debe haber duplicados"
    )


# ── Helpers for seeding closed-season scenarios ───────────────────────────────


def _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db):
    """Creates a temporada with all 3 jugadores_en_db. Returns temporada_id."""
    ids = [j.id for j in jugadores_en_db]
    r = client.post(
        "/temporadas",
        json={"nombre": "Liga Test", "fecha_inicio": "2024-01-01", "jugadores": [{"id": i} for i in ids]},
        headers=auth_headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


def _seed_reunion_con_posiciones(db, temporada_id, posiciones_data):
    """
    Seeds a Reunion row + Posicion rows for a temporada.
    posiciones_data: list of (jugador_id, puntos) tuples.
    Returns the Reunion id.
    """
    from sqlalchemy.orm import Session

    reunion = Reunion(id_temporada=temporada_id, numero_jornada=1, fecha=date(2024, 1, 7))
    db.add(reunion)
    db.flush()

    for pos_num, (jugador_id, puntos) in enumerate(posiciones_data, start=1):
        pos = Posicion(
            id_reunion=reunion.id,
            id_jugador=jugador_id,
            es_invitado=False,
            posicion=pos_num,
            puntos=puntos,
        )
        db.add(pos)

    db.commit()
    db.refresh(reunion)
    return reunion.id


# ── T-05: cerrar_temporada tie detection tests ────────────────────────────────


def test_cerrar_temporada_con_ganador_unico_setea_campeon_id(client, auth_headers, jugadores_en_db, db):
    """AC-2: single winner → campeon_id auto-set, tie_detected false, tied_players absent."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)

    # Ana 15pts, Bruno 14pts, Carlos 13pts — Ana is clear winner
    j_ana, j_bruno, j_carlos = jugadores_en_db
    _seed_reunion_con_posiciones(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 14),
        (j_carlos.id, 13),
    ])

    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["estado"] == "cerrada"
    assert data["campeon_id"] == j_ana.id
    assert data["tie_detected"] is False
    assert "tied_players" not in data


def test_cerrar_temporada_sin_asistencias_campeon_id_null_tie_false(client, auth_headers, jugadores_en_db):
    """REQ-1 edge / SC-12: no posiciones → campeon_id null, tie_detected false, tied_players absent."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)

    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["estado"] == "cerrada"
    assert data["campeon_id"] is None
    assert data["tie_detected"] is False
    assert "tied_players" not in data


def test_cerrar_temporada_empate_2_way_campeon_null_tied_players(client, auth_headers, jugadores_en_db, db):
    """AC-3 / SC-02: 2-way tie → campeon_id null, tie_detected true, tied_players with 2 entries."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)

    j_ana, j_bruno, j_carlos = jugadores_en_db
    _seed_reunion_con_posiciones(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 15),
        (j_carlos.id, 13),
    ])

    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["estado"] == "cerrada"
    assert data["campeon_id"] is None
    assert data["tie_detected"] is True
    assert "tied_players" in data
    assert len(data["tied_players"]) == 2
    tied_ids = {p["id_jugador"] for p in data["tied_players"]}
    assert tied_ids == {j_ana.id, j_bruno.id}


def test_cerrar_temporada_empate_3_way_devuelve_3_jugadores(client, auth_headers, jugadores_en_db, db):
    """SC-03: 3-way tie → tied_players has 3 entries."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)

    j_ana, j_bruno, j_carlos = jugadores_en_db
    _seed_reunion_con_posiciones(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 15),
        (j_carlos.id, 15),
    ])

    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["tie_detected"] is True
    assert len(data["tied_players"]) == 3


def test_tied_players_ausente_del_json_cuando_sin_empate(client, auth_headers, jugadores_en_db, db):
    """REQ-6: tied_players key must be absent from JSON when no tie (not null, not empty list)."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)

    j_ana, j_bruno, j_carlos = jugadores_en_db
    _seed_reunion_con_posiciones(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 14),
        (j_carlos.id, 13),
    ])

    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 200
    assert "tied_players" not in r.json()


def test_crear_temporada_devuelve_campeon_id_null_y_tie_detected_false(client, auth_headers, jugadores_en_db):
    """AC-1: POST /temporadas returns campeon_id: null and tie_detected: false."""
    ids = [j.id for j in jugadores_en_db]
    r = client.post(
        "/temporadas",
        json={"nombre": "Liga 2024", "fecha_inicio": "2024-01-01", "jugadores": [{"id": i} for i in ids]},
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["campeon_id"] is None
    assert data["tie_detected"] is False
