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
    assert "tied_players" not in data


# ── T-09: POST /temporadas/{id}/campeon integration tests ─────────────────────


def _cerrar_temporada_con_posiciones(client, auth_headers, jugadores_en_db, db, posiciones_data):
    """
    Helper: creates a temporada, seeds posiciones directly, then closes it.
    Returns (temporada_id, jugadores) where jugadores = [j_ana, j_bruno, j_carlos].
    posiciones_data: list of (jugador_index, puntos) tuples (index into jugadores_en_db).
    """
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    pos_with_ids = [(jugadores_en_db[idx].id, puntos) for idx, puntos in posiciones_data]
    _seed_reunion_con_posiciones(db, temporada_id, pos_with_ids)
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    return temporada_id


def test_designar_campeon_happy_path_setea_campeon_id(client, auth_headers, jugadores_en_db, db):
    """AC-4: closed season, player with max pts → 200, campeon_id set."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    j_ana, j_bruno, j_carlos = jugadores_en_db
    # 2-way tie → campeon_id stays null after close; then designate Ana
    _seed_reunion_con_posiciones(db, temporada_id, [(j_ana.id, 15), (j_bruno.id, 15), (j_carlos.id, 13)])
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    r = client.post(
        f"/temporadas/{temporada_id}/campeon",
        json={"id_jugador": j_ana.id},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["campeon_id"] == j_ana.id
    assert data["estado"] == "cerrada"
    assert "tied_players" not in data


def test_designar_campeon_requiere_jwt_401(client, jugadores_en_db, db, auth_headers):
    """SC-15: POST /campeon without JWT → 401."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    j_ana = jugadores_en_db[0]
    _seed_reunion_con_posiciones(db, temporada_id, [(j_ana.id, 15)])
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    r = client.post(
        f"/temporadas/{temporada_id}/campeon",
        json={"id_jugador": j_ana.id},
    )
    assert r.status_code == 401


def test_designar_campeon_temporada_inexistente_404(client, auth_headers):
    """Non-existent temporada → 404."""
    r = client.post(
        "/temporadas/99999/campeon",
        json={"id_jugador": 1},
        headers=auth_headers,
    )
    assert r.status_code == 404


def test_designar_campeon_temporada_activa_422_mensaje_exacto(client, auth_headers, jugadores_en_db):
    """AC-7 / SC-09: active temporada → 422 with exact Spanish message."""
    ids = [j.id for j in jugadores_en_db]
    r_crear = client.post(
        "/temporadas",
        json={"nombre": "Liga", "fecha_inicio": "2024-01-01", "jugadores": [{"id": i} for i in ids]},
        headers=auth_headers,
    )
    temporada_id = r_crear.json()["id"]

    r = client.post(
        f"/temporadas/{temporada_id}/campeon",
        json={"id_jugador": jugadores_en_db[0].id},
        headers=auth_headers,
    )
    assert r.status_code == 422
    assert r.json()["detail"] == "No se puede designar campeón en una temporada que no está cerrada."


def test_designar_campeon_jugador_no_inscripto_422_mensaje_exacto(client, auth_headers, jugadores_en_db, db):
    """AC-6 / SC-07: player not enrolled → 422 with exact Spanish message."""
    # Only inscribe Ana, then close
    j_ana = jugadores_en_db[0]
    r_crear = client.post(
        "/temporadas",
        json={"nombre": "Liga", "fecha_inicio": "2024-01-01", "jugadores": [{"id": j_ana.id}]},
        headers=auth_headers,
    )
    temporada_id = r_crear.json()["id"]
    _seed_reunion_con_posiciones(db, temporada_id, [(j_ana.id, 15)])
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    # Try to designate Bruno (not enrolled)
    j_bruno = jugadores_en_db[1]
    r = client.post(
        f"/temporadas/{temporada_id}/campeon",
        json={"id_jugador": j_bruno.id},
        headers=auth_headers,
    )
    assert r.status_code == 422
    expected_msg = f"El jugador {j_bruno.id} no está inscripto en la temporada {temporada_id}."
    assert r.json()["detail"] == expected_msg


def test_designar_campeon_jugador_sin_maximo_puntaje_422_mensaje_exacto(client, auth_headers, jugadores_en_db, db):
    """AC-5 / SC-08: enrolled player but not max-pts holder → 422 with exact message."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    j_ana, j_bruno, j_carlos = jugadores_en_db
    # Ana clear winner, Bruno 2nd
    _seed_reunion_con_posiciones(db, temporada_id, [(j_ana.id, 15), (j_bruno.id, 14), (j_carlos.id, 13)])
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    # Try to designate Bruno (2nd place, not max-pts)
    r = client.post(
        f"/temporadas/{temporada_id}/campeon",
        json={"id_jugador": j_bruno.id},
        headers=auth_headers,
    )
    assert r.status_code == 422
    expected_msg = f"El jugador {j_bruno.id} no está entre los primeros del ranking final de la temporada {temporada_id}."
    assert r.json()["detail"] == expected_msg


def test_designar_campeon_idempotente_mismo_jugador_200(client, auth_headers, jugadores_en_db, db):
    """AC-8 / SC-05: same player twice → 200 both times, idempotent."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    j_ana, j_bruno, _ = jugadores_en_db
    _seed_reunion_con_posiciones(db, temporada_id, [(j_ana.id, 15), (j_bruno.id, 15)])
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    r1 = client.post(f"/temporadas/{temporada_id}/campeon", json={"id_jugador": j_ana.id}, headers=auth_headers)
    assert r1.status_code == 200
    assert r1.json()["campeon_id"] == j_ana.id

    r2 = client.post(f"/temporadas/{temporada_id}/campeon", json={"id_jugador": j_ana.id}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["campeon_id"] == j_ana.id


def test_designar_campeon_permite_cambiar_a_otro_empatado(client, auth_headers, jugadores_en_db, db):
    """AC-9 / SC-06: change champion to another tied player → 200, campeon_id updated."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    j_ana, j_bruno, _ = jugadores_en_db
    _seed_reunion_con_posiciones(db, temporada_id, [(j_ana.id, 15), (j_bruno.id, 15)])
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    client.post(f"/temporadas/{temporada_id}/campeon", json={"id_jugador": j_ana.id}, headers=auth_headers)

    r = client.post(f"/temporadas/{temporada_id}/campeon", json={"id_jugador": j_bruno.id}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["campeon_id"] == j_bruno.id


def test_designar_campeon_historica_backfill_ganador_unico(client, auth_headers, jugadores_en_db, db):
    """SC-11: historical closed season, single max-pts player, no prior campeon_id."""
    # Create a temporada without reuniones → close with empty ranking → campeon_id stays null
    j_ana = jugadores_en_db[0]
    r_crear = client.post(
        "/temporadas",
        json={"nombre": "Liga Historica", "fecha_inicio": "2020-01-01", "jugadores": [{"id": j_ana.id}]},
        headers=auth_headers,
    )
    temporada_id = r_crear.json()["id"]
    # Seed a reunion so Ana has pts (but close without auto-set by nulling after)
    _seed_reunion_con_posiciones(db, temporada_id, [(j_ana.id, 15)])
    # Close: Ana is single winner → auto-set, but let's test via direct designation too
    # For the backfill test: close with no posiciones so campeon_id stays null
    # Then manually set via /campeon endpoint
    from app.models.temporada import EstadoTemporada, Temporada
    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    temporada.estado = EstadoTemporada.cerrada
    db.commit()

    r = client.post(
        f"/temporadas/{temporada_id}/campeon",
        json={"id_jugador": j_ana.id},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["campeon_id"] == j_ana.id


def test_designar_campeon_body_invalido_422_pydantic(client, auth_headers, jugadores_en_db, db):
    """SC-10: body {} or id_jugador:'abc' → 422 pydantic default."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    # Empty body
    r = client.post(f"/temporadas/{temporada_id}/campeon", json={}, headers=auth_headers)
    assert r.status_code == 422

    # Non-integer id_jugador
    r2 = client.post(f"/temporadas/{temporada_id}/campeon", json={"id_jugador": "abc"}, headers=auth_headers)
    assert r2.status_code == 422


def test_designar_campeon_no_modifica_otros_campos(client, auth_headers, jugadores_en_db, db):
    """REQ-10: setting campeon_id doesn't change any other Temporada, Reunion, or Posicion fields."""
    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    j_ana, j_bruno, _ = jugadores_en_db
    _seed_reunion_con_posiciones(db, temporada_id, [(j_ana.id, 15), (j_bruno.id, 15)])
    client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)

    from app.models.posicion import Posicion
    from app.models.reunion import Reunion
    from app.models.temporada import Temporada

    posiciones_antes = db.query(Posicion).count()
    reuniones_antes = db.query(Reunion).count()

    r = client.post(f"/temporadas/{temporada_id}/campeon", json={"id_jugador": j_ana.id}, headers=auth_headers)
    assert r.status_code == 200

    # Reuniones and posiciones unchanged
    db.expire_all()
    assert db.query(Posicion).count() == posiciones_antes
    assert db.query(Reunion).count() == reuniones_antes

    # Temporada state unchanged except campeon_id
    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    assert temporada.estado.value == "cerrada"
    assert temporada.campeon_id == j_ana.id


# ── REQ-2: cerrar_temporada sets fecha_cierre ─────────────────────────────────


def test_cerrar_temporada_setea_fecha_cierre_con_ganador_unico(client, auth_headers, jugadores_en_db, db):
    """REQ-2 scenario: close without tie → fecha_cierre == date.today()."""
    from datetime import date
    from app.models.temporada import Temporada

    temporada_id = _crear_temporada_con_jugadores(client, auth_headers, jugadores_en_db)
    j_ana, j_bruno, j_carlos = jugadores_en_db
    _seed_reunion_con_posiciones(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 14),
        (j_carlos.id, 13),
    ])

    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["estado"] == "cerrada"

    db.expire_all()
    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    assert temporada.fecha_cierre == date.today()


def test_cerrar_temporada_setea_fecha_cierre_con_empate(client, auth_headers, jugadores_en_db, db):
    """REQ-2 scenario: close with tie → fecha_cierre == date.today(), campeon_id stays None."""
    from datetime import date
    from app.models.temporada import Temporada

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

    db.expire_all()
    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    assert temporada.fecha_cierre == date.today()
