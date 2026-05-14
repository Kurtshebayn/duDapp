"""
Integration tests for /historico endpoints.

Phase A (RED): All tests fail with 404 because the router is not yet wired.
Phase B (GREEN): All tests pass after orchestrators + router + main.py wire-up.

Fixtures:
  - escenario_historico: creates 2 closed seasons with controlled data and
    returns a rich dict of ids for assertions.

Helpers:
  - _auth_headers(client): logs in as admin and returns Bearer header.
"""

import pytest

from app.models.jugador import Jugador
from app.models.posicion import Posicion
from app.models.reunion import Reunion
from app.models.temporada import EstadoTemporada, Temporada


def _auth_headers(client):
    r = client.post(
        "/auth/login",
        json={"identificador": "admin@dudo.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _crear_temporada(client, headers, nombre, fecha_inicio, jugadores_nombres):
    """Creates a new temporada with the given players. Returns temporada dict."""
    r = client.post(
        "/temporadas",
        json={
            "nombre": nombre,
            "fecha_inicio": fecha_inicio,
            "jugadores": [{"nombre": n} for n in jugadores_nombres],
        },
        headers=headers,
    )
    assert r.status_code == 201, f"crear_temporada failed: {r.text}"
    return r.json()


def _registrar_reunion(client, headers, temporada_id, fecha, posiciones):
    """Registers a meeting. posiciones: list of {id_jugador, es_invitado, posicion}."""
    r = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={"fecha": fecha, "posiciones": posiciones},
        headers=headers,
    )
    assert r.status_code == 201, f"registrar_reunion failed: {r.text}"
    return r.json()


def _cerrar_temporada(client, headers, temporada_id):
    """Closes a temporada. Returns the updated temporada dict."""
    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=headers)
    assert r.status_code == 200, f"cerrar_temporada failed: {r.text}"
    return r.json()


# ---------------------------------------------------------------------------
# Fixture: escenario_historico
#
# Creates:
#   S1: "Liga 2022" (fecha_inicio 2022-01-01)
#     Players: Ana, Bruno, Carlos
#     R1: Ana 1°(15pts), Bruno 2°(14pts), Carlos 3°(13pts)
#     R2: Bruno 1°(15pts), Carlos 2°(14pts), Ana 3°(13pts)
#     R3: Ana 1°(15pts), Bruno 2°(14pts), Carlos 3°(13pts)
#     campeon_id: Ana (set via db)
#
#   S2: "Liga 2023" (fecha_inicio 2023-01-01)
#     Players: Ana, Bruno, Carlos (reused from catalog)
#     R1: Ana 1°(15pts), Bruno 2°(14pts), Carlos 3°(13pts)
#     R2: Carlos 1°(15pts), Ana 2°(14pts), Bruno 3°(13pts)
#     R3: Bruno 1°(15pts), Carlos 2°(14pts), Ana 3°(13pts)
#     campeon_id: Bruno (set via db)
#
# Streak notes:
#   racha_victorias:
#     - Ana wins S1-R1, loses S1-R2, wins S1-R3 + S2-R1 → racha = 2 (S1-R3→S2-R1)
#     - Bruno wins S1-R2, loses S1-R3, loses S2-R1, loses S2-R2, wins S2-R3 → racha = 1
#     - Carlos wins S2-R2 only → racha = 1
#   racha_asistencia (all 3 attended all 6 meetings) → racha = 6 per player
#
# ---------------------------------------------------------------------------


@pytest.fixture
def escenario_historico(client, db, admin_user):
    """Two closed seasons with controlled results. Returns dict with ids."""
    headers = _auth_headers(client)

    # --- Season 1 ---
    s1 = _crear_temporada(client, headers, "Liga 2022", "2022-01-01", ["Ana", "Bruno", "Carlos"])
    s1_id = s1["id"]

    # Get player ids from DB (created in order)
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_ana = jugadores[0].id
    id_bruno = jugadores[1].id
    id_carlos = jugadores[2].id

    # S1-R1: Ana 1, Bruno 2, Carlos 3
    r1 = _registrar_reunion(client, headers, s1_id, "2022-01-10", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_carlos, "es_invitado": False, "posicion": 3},
    ])

    # S1-R2: Bruno 1, Carlos 2, Ana 3
    r2 = _registrar_reunion(client, headers, s1_id, "2022-01-17", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_carlos, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 3},
    ])

    # S1-R3: Ana 1, Bruno 2, Carlos 3
    r3 = _registrar_reunion(client, headers, s1_id, "2022-01-24", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_carlos, "es_invitado": False, "posicion": 3},
    ])

    _cerrar_temporada(client, headers, s1_id)

    # Set campeon_id = Ana in S1
    db.query(Temporada).filter(Temporada.id == s1_id).update({"campeon_id": id_ana})
    db.commit()

    # --- Season 2 ---
    s2 = _crear_temporada(client, headers, "Liga 2023", "2023-01-01", ["Ana", "Bruno", "Carlos"])
    s2_id = s2["id"]

    # S2-R1: Ana 1, Bruno 2, Carlos 3
    r4 = _registrar_reunion(client, headers, s2_id, "2023-01-09", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_carlos, "es_invitado": False, "posicion": 3},
    ])

    # S2-R2: Carlos 1, Ana 2, Bruno 3
    r5 = _registrar_reunion(client, headers, s2_id, "2023-01-16", [
        {"id_jugador": id_carlos, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 3},
    ])

    # S2-R3: Bruno 1, Carlos 2, Ana 3
    r6 = _registrar_reunion(client, headers, s2_id, "2023-01-23", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_carlos, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 3},
    ])

    _cerrar_temporada(client, headers, s2_id)

    # Set campeon_id = Bruno in S2
    db.query(Temporada).filter(Temporada.id == s2_id).update({"campeon_id": id_bruno})
    db.commit()

    return {
        "s1_id": s1_id,
        "s2_id": s2_id,
        "id_ana": id_ana,
        "id_bruno": id_bruno,
        "id_carlos": id_carlos,
        "r1_id": r1["id"],
        "r2_id": r2["id"],
        "r3_id": r3["id"],
        "r4_id": r4["id"],
        "r5_id": r5["id"],
        "r6_id": r6["id"],
    }


# ---------------------------------------------------------------------------
# T-20: resumen sin temporadas cerradas → 200 + 8 empty arrays
# ---------------------------------------------------------------------------


def test_resumen_sin_temporadas_cerradas(client):
    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()
    expected_keys = {
        "puntos_totales", "victorias", "campeones", "asistencias",
        "racha_victorias", "racha_asistencia", "promedios", "podios",
        "racha_inasistencia",
    }
    assert set(data.keys()) == expected_keys
    for key in expected_keys:
        assert data[key] == [], f"Expected {key} to be [], got {data[key]}"


# ---------------------------------------------------------------------------
# T-21: resumen estructura completa → 8 keys, all lists
# ---------------------------------------------------------------------------


def test_resumen_estructura_completa(client, db, admin_user, escenario_historico):
    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()
    expected_keys = {
        "puntos_totales", "victorias", "campeones", "asistencias",
        "racha_victorias", "racha_asistencia", "promedios", "podios",
        "racha_inasistencia",
    }
    assert set(data.keys()) == expected_keys
    for key in expected_keys:
        assert isinstance(data[key], list), f"Expected {key} to be a list"
        assert data[key] is not None, f"Expected {key} to not be None"


# ---------------------------------------------------------------------------
# T-22: temporada activa no afecta métricas (C1)
# ---------------------------------------------------------------------------


def test_resumen_temporada_activa_no_afecta(client, db, admin_user):
    headers = _auth_headers(client)

    # Create and close S1 with Ana
    s1 = _crear_temporada(client, headers, "Liga 2022", "2022-01-01", ["Ana"])
    s1_id = s1["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_ana = jugadores[0].id

    _registrar_reunion(client, headers, s1_id, "2022-01-10", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
    ])
    _cerrar_temporada(client, headers, s1_id)
    db.query(Temporada).filter(Temporada.id == s1_id).update({"campeon_id": id_ana})
    db.commit()

    # Get R1 (before active season)
    r1 = client.get("/historico/resumen")
    assert r1.status_code == 200
    data1 = r1.json()

    # Create active season and register a meeting
    s2 = _crear_temporada(client, headers, "Liga 2023", "2023-01-01", ["Ana"])
    s2_id = s2["id"]
    _registrar_reunion(client, headers, s2_id, "2023-01-10", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
    ])
    # S2 remains ACTIVE

    # Get R2 (after active season has a meeting)
    r2 = client.get("/historico/resumen")
    assert r2.status_code == 200
    data2 = r2.json()

    # Metrics must be identical — active season data does not affect historico
    assert data1 == data2, "Active season affected historico metrics (violates C1)"


# ---------------------------------------------------------------------------
# T-23: campeones omite temporada sin campeon_id (C5)
# ---------------------------------------------------------------------------


def test_campeones_omite_temporada_sin_campeon(client, db, admin_user):
    headers = _auth_headers(client)

    # S1: closed, campeon_id remains NULL.
    # No reuniones/posiciones → empty ranking → cerrar_temporada auto-set skipped.
    # This models a historical imported season where no champion was designated.
    s1 = _crear_temporada(client, headers, "Liga 2022", "2022-01-01", ["Ana"])
    s1_id = s1["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_ana = jugadores[0].id
    _cerrar_temporada(client, headers, s1_id)
    # campeon_id stays NULL (empty ranking → no auto-set)

    # S2: closed, campeon_id = Ana (auto-set via the single-winner path)
    s2 = _crear_temporada(client, headers, "Liga 2023", "2023-01-01", ["Ana"])
    s2_id = s2["id"]
    _registrar_reunion(client, headers, s2_id, "2023-01-10", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
    ])
    _cerrar_temporada(client, headers, s2_id)
    # campeon_id is auto-set to Ana by cerrar_temporada (single winner)

    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()
    campeones = data["campeones"]
    # Only 1 entry — S1 with NULL campeon_id must be omitted
    assert len(campeones) == 1, f"Expected 1 campeon entry, got {len(campeones)}: {campeones}"
    assert campeones[0]["id_jugador"] == id_ana
    assert campeones[0]["campeonatos"] == 1


# ---------------------------------------------------------------------------
# T-24: racha victorias cruza temporadas (C2)
# ---------------------------------------------------------------------------


def test_racha_victorias_cruza_temporadas(client, db, admin_user):
    """
    S1: 3 meetings. Player A wins last meeting of S1.
    S2: 3 meetings. Player A wins first 2 meetings of S2.
    → streak = 3 (last of S1 + first 2 of S2), crossing temporadas.
    """
    headers = _auth_headers(client)

    s1 = _crear_temporada(client, headers, "Liga 2022", "2022-01-01", ["AnaZ", "Bruno"])
    s1_id = s1["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_anaz = jugadores[0].id
    id_bruno = jugadores[1].id

    # S1-R1: Bruno wins
    _registrar_reunion(client, headers, s1_id, "2022-01-10", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_anaz, "es_invitado": False, "posicion": 2},
    ])
    # S1-R2: Bruno wins
    _registrar_reunion(client, headers, s1_id, "2022-01-17", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_anaz, "es_invitado": False, "posicion": 2},
    ])
    # S1-R3: AnaZ wins (streak start)
    _registrar_reunion(client, headers, s1_id, "2022-01-24", [
        {"id_jugador": id_anaz, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
    ])
    _cerrar_temporada(client, headers, s1_id)
    db.query(Temporada).filter(Temporada.id == s1_id).update({"campeon_id": id_anaz})
    db.commit()

    s2 = _crear_temporada(client, headers, "Liga 2023", "2023-01-01", ["AnaZ", "Bruno"])
    s2_id = s2["id"]
    # S2-R1: AnaZ wins (streak continues)
    _registrar_reunion(client, headers, s2_id, "2023-01-09", [
        {"id_jugador": id_anaz, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
    ])
    # S2-R2: AnaZ wins (streak = 3)
    _registrar_reunion(client, headers, s2_id, "2023-01-16", [
        {"id_jugador": id_anaz, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
    ])
    # S2-R3: Bruno wins (streak ends)
    _registrar_reunion(client, headers, s2_id, "2023-01-23", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_anaz, "es_invitado": False, "posicion": 2},
    ])
    _cerrar_temporada(client, headers, s2_id)
    db.query(Temporada).filter(Temporada.id == s2_id).update({"campeon_id": id_bruno})
    db.commit()

    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()

    racha = data["racha_victorias"]
    anaz_racha = next((x for x in racha if x["id_jugador"] == id_anaz), None)
    assert anaz_racha is not None, f"AnaZ not in racha_victorias: {racha}"
    assert anaz_racha["longitud"] == 3, f"Expected longitud=3, got {anaz_racha['longitud']}"
    assert anaz_racha["temporada_inicio"]["id"] == s1_id, (
        f"Expected temporada_inicio={s1_id}, got {anaz_racha['temporada_inicio']['id']}"
    )
    assert anaz_racha["temporada_fin"]["id"] == s2_id, (
        f"Expected temporada_fin={s2_id}, got {anaz_racha['temporada_fin']['id']}"
    )


# ---------------------------------------------------------------------------
# T-25: racha asistencia se rompe por inasistencia
# ---------------------------------------------------------------------------


def test_racha_asistencia_se_rompe_por_inasistencia(client, db, admin_user):
    """
    Player attends 5 meetings, absent in 1, attends 3 more.
    Expected max attendance streak = 5.
    """
    headers = _auth_headers(client)

    # Single closed season with 9 meetings
    s = _crear_temporada(client, headers, "Liga Asistencia", "2022-01-01", ["Pepe", "Otro"])
    s_id = s["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_pepe = jugadores[0].id
    id_otro = jugadores[1].id

    fechas = [
        "2022-01-10", "2022-01-17", "2022-01-24",
        "2022-01-31", "2022-02-07",  # Pepe attends these 5
        "2022-02-14",                 # Pepe ABSENT → only Otro
        "2022-02-21", "2022-02-28", "2022-03-07",  # Pepe attends these 3
    ]

    for i, fecha in enumerate(fechas):
        if i < 5:
            # Pepe attends
            _registrar_reunion(client, headers, s_id, fecha, [
                {"id_jugador": id_pepe, "es_invitado": False, "posicion": 1},
                {"id_jugador": id_otro, "es_invitado": False, "posicion": 2},
            ])
        elif i == 5:
            # Pepe absent (only Otro plays)
            _registrar_reunion(client, headers, s_id, fecha, [
                {"id_jugador": id_otro, "es_invitado": False, "posicion": 1},
            ])
        else:
            # Pepe attends again (last 3)
            _registrar_reunion(client, headers, s_id, fecha, [
                {"id_jugador": id_pepe, "es_invitado": False, "posicion": 1},
                {"id_jugador": id_otro, "es_invitado": False, "posicion": 2},
            ])

    _cerrar_temporada(client, headers, s_id)
    db.query(Temporada).filter(Temporada.id == s_id).update({"campeon_id": id_pepe})
    db.commit()

    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()

    racha = data["racha_asistencia"]
    pepe_racha = next((x for x in racha if x["id_jugador"] == id_pepe), None)
    assert pepe_racha is not None, f"Pepe not in racha_asistencia: {racha}"
    # Max streak is 5 (meetings 1-5), not 3 (meetings 7-9) — 5 > 3
    assert pepe_racha["longitud"] == 5, f"Expected longitud=5, got {pepe_racha['longitud']}"


# ---------------------------------------------------------------------------
# T-26: racha asistencia no distingue no-inscripcion (C10)
# ---------------------------------------------------------------------------


def test_racha_asistencia_no_distingue_no_inscripcion(client, db, admin_user):
    """
    Player inscribed in S1 (3 meetings, all attended),
    NOT inscribed in S2 (2 meetings),
    inscribed in S3 (2 meetings, all attended).
    Expected: racha = 3 (S1 only) — gap in S2 breaks the streak (C10).
    """
    headers = _auth_headers(client)

    # S1: Pepe + Otro (3 meetings)
    s1 = _crear_temporada(client, headers, "Liga S1", "2021-01-01", ["Pepe", "Otro"])
    s1_id = s1["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_pepe = jugadores[0].id
    id_otro = jugadores[1].id

    for fecha in ["2021-01-10", "2021-01-17", "2021-01-24"]:
        _registrar_reunion(client, headers, s1_id, fecha, [
            {"id_jugador": id_pepe, "es_invitado": False, "posicion": 1},
            {"id_jugador": id_otro, "es_invitado": False, "posicion": 2},
        ])
    _cerrar_temporada(client, headers, s1_id)
    db.query(Temporada).filter(Temporada.id == s1_id).update({"campeon_id": id_pepe})
    db.commit()

    # S2: only Otro (Pepe NOT inscribed) — 2 meetings
    s2 = _crear_temporada(client, headers, "Liga S2", "2022-01-01", ["Otro"])
    s2_id = s2["id"]
    for fecha in ["2022-01-10", "2022-01-17"]:
        _registrar_reunion(client, headers, s2_id, fecha, [
            {"id_jugador": id_otro, "es_invitado": False, "posicion": 1},
        ])
    _cerrar_temporada(client, headers, s2_id)
    db.query(Temporada).filter(Temporada.id == s2_id).update({"campeon_id": id_otro})
    db.commit()

    # S3: Pepe + Otro (2 meetings)
    s3 = _crear_temporada(client, headers, "Liga S3", "2023-01-01", ["Pepe", "Otro"])
    s3_id = s3["id"]
    jugadores_s3 = db.query(Jugador).filter(Jugador.id.in_([id_pepe, id_otro])).all()
    for fecha in ["2023-01-10", "2023-01-17"]:
        _registrar_reunion(client, headers, s3_id, fecha, [
            {"id_jugador": id_pepe, "es_invitado": False, "posicion": 1},
            {"id_jugador": id_otro, "es_invitado": False, "posicion": 2},
        ])
    _cerrar_temporada(client, headers, s3_id)
    db.query(Temporada).filter(Temporada.id == s3_id).update({"campeon_id": id_pepe})
    db.commit()

    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()

    racha = data["racha_asistencia"]
    pepe_racha = next((x for x in racha if x["id_jugador"] == id_pepe), None)
    assert pepe_racha is not None, f"Pepe not in racha_asistencia: {racha}"
    # S2 gap breaks the streak — max streak should be 3 (S1), NOT 5 (S1+S3 combined)
    assert pepe_racha["longitud"] == 3, (
        f"Expected longitud=3 (C10: gap in S2 breaks streak), got {pepe_racha['longitud']}"
    )


# ---------------------------------------------------------------------------
# T-27: orden empates alfabético (C6)
# ---------------------------------------------------------------------------


def test_orden_empates_alfabetico(client, db, admin_user):
    """
    Zara and Ana have equal victorias count.
    Expected: 'Ana' appears before 'Zara' in the victorias list.
    """
    headers = _auth_headers(client)

    s = _crear_temporada(client, headers, "Liga Empate", "2022-01-01", ["Zara", "Ana", "Bruno"])
    s_id = s["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_zara = jugadores[0].id
    id_ana = jugadores[1].id
    id_bruno = jugadores[2].id

    # R1: Zara 1° (victoria para Zara)
    _registrar_reunion(client, headers, s_id, "2022-01-10", [
        {"id_jugador": id_zara, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 3},
    ])
    # R2: Ana 1° (victoria para Ana) → tie in victorias: Zara=1, Ana=1
    _registrar_reunion(client, headers, s_id, "2022-01-17", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_zara, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 3},
    ])
    _cerrar_temporada(client, headers, s_id)
    db.query(Temporada).filter(Temporada.id == s_id).update({"campeon_id": id_ana})
    db.commit()

    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()

    victorias = data["victorias"]
    nombres = [v["nombre"] for v in victorias]
    assert "Ana" in nombres
    assert "Zara" in nombres
    idx_ana = nombres.index("Ana")
    idx_zara = nombres.index("Zara")
    assert idx_ana < idx_zara, (
        f"Expected Ana before Zara (alphabetical tie-break C6), got order: {nombres}"
    )

    # Also verify puntos_totales has alphabetical tie-break
    # Ana: 14+15=29, Zara: 15+14=29 → tie → alphabetical
    puntos = data["puntos_totales"]
    nombres_puntos = [p["nombre"] for p in puntos if p["nombre"] in ("Ana", "Zara")]
    if len(nombres_puntos) == 2:
        assert nombres_puntos[0] == "Ana", (
            f"Expected Ana before Zara in puntos_totales, got {nombres_puntos}"
        )


# ---------------------------------------------------------------------------
# T-28: h2h jugador no existe → 404
# ---------------------------------------------------------------------------


def test_h2h_jugador_no_existe(client):
    r = client.get("/historico/head-to-head/99999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# T-29: h2h jugador sin reuniones → rivales vacío
# ---------------------------------------------------------------------------


def test_h2h_jugador_sin_reuniones(client, db, admin_user):
    """Player exists and is inscribed in a closed season but has no Posicion rows."""
    headers = _auth_headers(client)

    # Create closed season with player but NO meetings registered
    s = _crear_temporada(client, headers, "Liga Vacia", "2022-01-01", ["SinJuego"])
    s_id = s["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_sin_juego = jugadores[0].id

    # Close without any meetings
    _cerrar_temporada(client, headers, s_id)

    r = client.get(f"/historico/head-to-head/{id_sin_juego}")
    assert r.status_code == 200
    data = r.json()
    assert data["jugador_id"] == id_sin_juego
    assert data["rivales"] == [], f"Expected empty rivales, got {data['rivales']}"


# ---------------------------------------------------------------------------
# T-30: h2h omite rival sin reuniones compartidas (C8)
# ---------------------------------------------------------------------------


def test_h2h_omite_rival_sin_compartidas(client, db, admin_user):
    """
    Target attended meetings in S1; Player D was inscribed only in S2 (no overlap).
    Player D must NOT appear in Target's rivales list.
    """
    headers = _auth_headers(client)

    # S1: Target + Rival1 (meet together)
    s1 = _crear_temporada(client, headers, "Liga S1", "2022-01-01", ["Target", "Rival1"])
    s1_id = s1["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_target = jugadores[0].id
    id_rival1 = jugadores[1].id

    _registrar_reunion(client, headers, s1_id, "2022-01-10", [
        {"id_jugador": id_target, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_rival1, "es_invitado": False, "posicion": 2},
    ])
    _cerrar_temporada(client, headers, s1_id)
    db.query(Temporada).filter(Temporada.id == s1_id).update({"campeon_id": id_target})
    db.commit()

    # S2: only PlayerD (Target not present)
    s2 = _crear_temporada(client, headers, "Liga S2", "2023-01-01", ["PlayerD"])
    s2_id = s2["id"]
    jugadores_s2 = db.query(Jugador).filter(Jugador.nombre == "PlayerD").first()
    id_player_d = jugadores_s2.id

    _registrar_reunion(client, headers, s2_id, "2023-01-10", [
        {"id_jugador": id_player_d, "es_invitado": False, "posicion": 1},
    ])
    _cerrar_temporada(client, headers, s2_id)
    db.query(Temporada).filter(Temporada.id == s2_id).update({"campeon_id": id_player_d})
    db.commit()

    r = client.get(f"/historico/head-to-head/{id_target}")
    assert r.status_code == 200
    data = r.json()

    rival_ids = [rv["rival_id"] for rv in data["rivales"]]
    assert id_player_d not in rival_ids, (
        f"PlayerD (id={id_player_d}) should not appear in rivales (no shared meetings C8), "
        f"got: {data['rivales']}"
    )
    # Rival1 should appear
    assert id_rival1 in rival_ids, f"Rival1 should appear in rivales, got: {rival_ids}"


# ---------------------------------------------------------------------------
# T-31: h2h orden y conteo correctos
# ---------------------------------------------------------------------------


def test_h2h_orden_y_conteo(client, db, admin_user):
    """
    3 meetings, Target vs Rival1 and Rival2.
    R1: Target 1st, Rival1 2nd, Rival2 3rd → target beats both
    R2: Target 1st, Rival1 2nd  (Rival2 absent)
    R3: Rival1 1st, Target 2nd (Rival2 absent)
    → Rival1: 3 shared, Target 2 wins 1 loss
    → Rival2: 1 shared, Target 1 win 0 loss
    Order: Rival1 first (3 shared > 1 shared)
    """
    headers = _auth_headers(client)

    s = _crear_temporada(client, headers, "Liga H2H", "2022-01-01", ["Target", "Rival1", "Rival2"])
    s_id = s["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_target = jugadores[0].id
    id_rival1 = jugadores[1].id
    id_rival2 = jugadores[2].id

    # R1: Target 1, Rival1 2, Rival2 3
    _registrar_reunion(client, headers, s_id, "2022-01-10", [
        {"id_jugador": id_target, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_rival1, "es_invitado": False, "posicion": 2},
        {"id_jugador": id_rival2, "es_invitado": False, "posicion": 3},
    ])
    # R2: Target 1, Rival1 2 (Rival2 absent)
    _registrar_reunion(client, headers, s_id, "2022-01-17", [
        {"id_jugador": id_target, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_rival1, "es_invitado": False, "posicion": 2},
    ])
    # R3: Rival1 1, Target 2 (Rival2 absent)
    _registrar_reunion(client, headers, s_id, "2022-01-24", [
        {"id_jugador": id_rival1, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_target, "es_invitado": False, "posicion": 2},
    ])
    _cerrar_temporada(client, headers, s_id)
    db.query(Temporada).filter(Temporada.id == s_id).update({"campeon_id": id_rival1})
    db.commit()

    r = client.get(f"/historico/head-to-head/{id_target}")
    assert r.status_code == 200
    data = r.json()

    rivales = data["rivales"]
    assert len(rivales) == 2, f"Expected 2 rivals, got {len(rivales)}: {rivales}"

    # First rival should be Rival1 (3 shared meetings)
    assert rivales[0]["rival_id"] == id_rival1
    assert rivales[0]["reuniones_compartidas"] == 3
    assert rivales[0]["victorias"] == 2   # Target beat Rival1 in R1 and R2
    assert rivales[0]["derrotas"] == 1    # Rival1 beat Target in R3

    # Second rival should be Rival2 (1 shared meeting)
    assert rivales[1]["rival_id"] == id_rival2
    assert rivales[1]["reuniones_compartidas"] == 1
    assert rivales[1]["victorias"] == 1   # Target beat Rival2 in R1
    assert rivales[1]["derrotas"] == 0


# ---------------------------------------------------------------------------
# T-32: determinismo con temporadas misma fecha_inicio (R2)
# ---------------------------------------------------------------------------


def test_determinismo_temporadas_misma_fecha_inicio(client, db, admin_user):
    """
    Two closed seasons with identical fecha_inicio but different ids.
    Calling GET /historico/resumen twice must return identical responses (R2).
    """
    headers = _auth_headers(client)

    # S1: fecha_inicio = 2022-01-01
    s1 = _crear_temporada(client, headers, "Liga A", "2022-01-01", ["Ana", "Bruno"])
    s1_id = s1["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_ana = jugadores[0].id
    id_bruno = jugadores[1].id

    _registrar_reunion(client, headers, s1_id, "2022-01-10", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
    ])
    _cerrar_temporada(client, headers, s1_id)
    db.query(Temporada).filter(Temporada.id == s1_id).update({"campeon_id": id_ana})
    db.commit()

    # S2: same fecha_inicio = 2022-01-01 (different id)
    s2 = _crear_temporada(client, headers, "Liga B", "2022-01-01", ["Ana", "Bruno"])
    s2_id = s2["id"]
    _registrar_reunion(client, headers, s2_id, "2022-02-10", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 2},
    ])
    _cerrar_temporada(client, headers, s2_id)
    db.query(Temporada).filter(Temporada.id == s2_id).update({"campeon_id": id_bruno})
    db.commit()

    # Call twice — responses must be identical
    r1 = client.get("/historico/resumen")
    r2 = client.get("/historico/resumen")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json(), "Response was not deterministic across calls (R2)"


# ---------------------------------------------------------------------------
# M10: racha_inasistencia integration tests (Batch 5b — Change E)
# ---------------------------------------------------------------------------


def test_racha_inasistencia_filtra_no_elegibles(client, db, admin_user):
    """
    Player who skipped an entire closed season is EXCLUDED from racha_inasistencia.
    Player who attended >=1 meeting in each closed season IS included if they have
    a cross-season inasistencia streak of length >= 2.

    Setup:
      S1: Pepe + Otro — 3 meetings. Pepe attends all 3.
      S2: only Otro (Pepe NOT inscribed). 2 meetings.
      S3: Pepe + Otro — 3 meetings. Pepe attends meeting 1, absent meetings 2+3.

    Pepe:
      - Not enrolled in S2 → ineligible for M10 (cannot have >=1 asistencia in S2).
      - Must NOT appear in racha_inasistencia.

    Otro:
      - Enrolled in all 3 seasons, attends >=1 in each → eligible.
      - S1: all 3 attended. S2: all 2 attended. S3: Otro attends all 3 (Pepe absent).
      - Outro's absences: none — so his inasistencia streak = 0 → won't appear.
      - We verify result list excludes Pepe.
    """
    headers = _auth_headers(client)

    s1 = _crear_temporada(client, headers, "Liga S1", "2021-01-01", ["Pepe", "Outro"])
    s1_id = s1["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_pepe = jugadores[0].id
    id_outro = jugadores[1].id

    for fecha in ["2021-01-10", "2021-01-17", "2021-01-24"]:
        _registrar_reunion(client, headers, s1_id, fecha, [
            {"id_jugador": id_pepe, "es_invitado": False, "posicion": 1},
            {"id_jugador": id_outro, "es_invitado": False, "posicion": 2},
        ])
    _cerrar_temporada(client, headers, s1_id)
    db.query(Temporada).filter(Temporada.id == s1_id).update({"campeon_id": id_pepe})
    db.commit()

    # S2: only Outro (Pepe NOT inscribed)
    s2 = _crear_temporada(client, headers, "Liga S2", "2022-01-01", ["Outro"])
    s2_id = s2["id"]
    for fecha in ["2022-01-10", "2022-01-17"]:
        _registrar_reunion(client, headers, s2_id, fecha, [
            {"id_jugador": id_outro, "es_invitado": False, "posicion": 1},
        ])
    _cerrar_temporada(client, headers, s2_id)
    db.query(Temporada).filter(Temporada.id == s2_id).update({"campeon_id": id_outro})
    db.commit()

    # S3: Pepe + Outro
    s3 = _crear_temporada(client, headers, "Liga S3", "2023-01-01", ["Pepe", "Outro"])
    s3_id = s3["id"]
    for fecha in ["2023-01-10", "2023-01-17", "2023-01-24"]:
        _registrar_reunion(client, headers, s3_id, fecha, [
            {"id_jugador": id_pepe, "es_invitado": False, "posicion": 1},
            {"id_jugador": id_outro, "es_invitado": False, "posicion": 2},
        ])
    _cerrar_temporada(client, headers, s3_id)
    db.query(Temporada).filter(Temporada.id == s3_id).update({"campeon_id": id_pepe})
    db.commit()

    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()

    racha_in = data["racha_inasistencia"]
    player_ids = [x["id_jugador"] for x in racha_in]
    assert id_pepe not in player_ids, (
        f"Pepe should be ineligible for M10 (not enrolled in S2), "
        f"but appears in racha_inasistencia: {racha_in}"
    )


def test_racha_inasistencia_elegible_con_racha(client, db, admin_user):
    """
    Player eligible for M10 with a cross-season inasistencia streak of 3 appears with
    correct metadata.

    Setup:
      S1: Ana + Bruno — 3 meetings. Ana attends j1, j2; absent j3.
      S2: Ana + Bruno — 3 meetings. Ana absent j1, j2; attends j3.
      → Ana's inasistencia streak: S1-j3, S2-j1, S2-j2 = 3 consecutive absences.
      Ana is eligible: attends >=1 in S1 (j1,j2) and >=1 in S2 (j3).
    """
    headers = _auth_headers(client)

    s1 = _crear_temporada(client, headers, "Liga 2022", "2022-01-01", ["Ana", "Bruno"])
    s1_id = s1["id"]
    jugadores = db.query(Jugador).order_by(Jugador.id).all()
    id_ana = jugadores[0].id
    id_bruno = jugadores[1].id

    # S1-R1: Ana 1, Bruno 2
    _registrar_reunion(client, headers, s1_id, "2022-01-10", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
    ])
    # S1-R2: Ana 1, Bruno 2
    _registrar_reunion(client, headers, s1_id, "2022-01-17", [
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 2},
    ])
    # S1-R3: only Bruno (Ana absent)
    _registrar_reunion(client, headers, s1_id, "2022-01-24", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
    ])
    _cerrar_temporada(client, headers, s1_id)
    db.query(Temporada).filter(Temporada.id == s1_id).update({"campeon_id": id_ana})
    db.commit()

    s2 = _crear_temporada(client, headers, "Liga 2023", "2023-01-01", ["Ana", "Bruno"])
    s2_id = s2["id"]
    # S2-R1: only Bruno (Ana absent)
    _registrar_reunion(client, headers, s2_id, "2023-01-09", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
    ])
    # S2-R2: only Bruno (Ana absent)
    _registrar_reunion(client, headers, s2_id, "2023-01-16", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
    ])
    # S2-R3: Ana 2, Bruno 1 (Ana breaks streak by attending)
    _registrar_reunion(client, headers, s2_id, "2023-01-23", [
        {"id_jugador": id_bruno, "es_invitado": False, "posicion": 1},
        {"id_jugador": id_ana, "es_invitado": False, "posicion": 2},
    ])
    _cerrar_temporada(client, headers, s2_id)
    db.query(Temporada).filter(Temporada.id == s2_id).update({"campeon_id": id_bruno})
    db.commit()

    r = client.get("/historico/resumen")
    assert r.status_code == 200
    data = r.json()

    racha_in = data["racha_inasistencia"]
    ana_entry = next((x for x in racha_in if x["id_jugador"] == id_ana), None)
    assert ana_entry is not None, f"Ana should appear in racha_inasistencia: {racha_in}"
    assert ana_entry["longitud"] == 3, (
        f"Expected Ana streak=3 (S1-j3 + S2-j1 + S2-j2), got {ana_entry['longitud']}"
    )
    assert ana_entry["temporada_inicio"]["id"] == s1_id, (
        f"Expected temporada_inicio={s1_id}, got {ana_entry['temporada_inicio']['id']}"
    )
    assert ana_entry["jornada_inicio"] == 3
    assert ana_entry["temporada_fin"]["id"] == s2_id
    assert ana_entry["jornada_fin"] == 2
