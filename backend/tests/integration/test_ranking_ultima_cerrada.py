"""Integration tests for GET /temporadas/ultima-cerrada/ranking-narrativo.

Covers all 11+ scenarios from REQ-3 in the spec (obs #135).

Test setup pattern: uses the shared fixtures (client, db, auth_headers) from
conftest.py. All DB state is seeded directly via the API or via direct model
insertion.
"""
import pytest
from datetime import date

from app.models.posicion import Posicion
from app.models.posicion_snapshot import PosicionSnapshot
from app.models.reunion import Reunion
from app.models.temporada import EstadoTemporada, Temporada


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def auth_headers(client, admin_user):
    r = client.post(
        "/auth/login",
        json={"identificador": "admin@dudo.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def tres_jugadores(db):
    from app.models.jugador import Jugador

    jugadores = [Jugador(nombre="Ana"), Jugador(nombre="Bruno"), Jugador(nombre="Carlos")]
    db.add_all(jugadores)
    db.commit()
    for j in jugadores:
        db.refresh(j)
    return jugadores


# ── Low-level helpers ─────────────────────────────────────────────────────────


def _crear_temporada_api(client, auth_headers, jugadores, nombre="Liga Test"):
    ids = [j.id for j in jugadores]
    r = client.post(
        "/temporadas",
        json={
            "nombre": nombre,
            "fecha_inicio": "2024-01-01",
            "jugadores": [{"id": i} for i in ids],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


def _seed_reunion(db, temporada_id, posiciones_data, numero_jornada=1, fecha=None):
    """
    Insert a Reunion + Posicion rows directly.
    posiciones_data: list of (jugador_id_or_None, puntos, es_invitado=False).
    Returns reunion_id.
    """
    reunion = Reunion(
        id_temporada=temporada_id,
        numero_jornada=numero_jornada,
        fecha=fecha or date(2024, 1, 7),
    )
    db.add(reunion)
    db.flush()

    for pos_num, row in enumerate(posiciones_data, start=1):
        if len(row) == 2:
            jugador_id, puntos = row
            es_invitado = False
        else:
            jugador_id, puntos, es_invitado = row

        pos = Posicion(
            id_reunion=reunion.id,
            id_jugador=jugador_id if not es_invitado else None,
            es_invitado=es_invitado,
            posicion=pos_num,
            puntos=puntos,
        )
        db.add(pos)

    db.commit()
    db.refresh(reunion)
    return reunion.id


def _seed_snapshot(db, temporada_id, reunion_id, jugador_id, posicion, puntos_acumulados):
    """Insert a PosicionSnapshot row directly."""
    snap = PosicionSnapshot(
        id_temporada=temporada_id,
        id_reunion=reunion_id,
        id_jugador=jugador_id,
        posicion=posicion,
        puntos_acumulados=puntos_acumulados,
    )
    db.add(snap)
    db.commit()


def _cerrar_temporada_db(db, temporada_id, campeon_id=None, fecha_cierre=None):
    """Close a temporada directly in DB (bypassing the service for fixture control)."""
    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    temporada.estado = EstadoTemporada.cerrada
    if campeon_id is not None:
        temporada.campeon_id = campeon_id
    if fecha_cierre is not None:
        temporada.fecha_cierre = fecha_cierre
    db.commit()


def _cerrar_temporada_api(client, auth_headers, temporada_id):
    """Close via API (runs service logic including fecha_cierre=date.today())."""
    r = client.post(f"/temporadas/{temporada_id}/cerrar", headers=auth_headers)
    assert r.status_code == 200
    return r.json()


ENDPOINT = "/temporadas/ultima-cerrada/ranking-narrativo"


# ── REQ-3 scenario: no closed seasons → 404 ──────────────────────────────────


def test_404_cuando_no_hay_temporadas_en_absoluto(client):
    """Empty DB → 404."""
    r = client.get(ENDPOINT)
    assert r.status_code == 404
    assert "detail" in r.json()


def test_404_cuando_solo_hay_temporada_activa(client, auth_headers, tres_jugadores):
    """Active season only, no closed → 404."""
    _crear_temporada_api(client, auth_headers, tres_jugadores)

    r = client.get(ENDPOINT)
    assert r.status_code == 404


# ── REQ-3 scenario: 200 with a closed season ─────────────────────────────────


def test_200_con_una_cerrada(client, auth_headers, tres_jugadores, db):
    """Closed season with posiciones → 200 and correct payload shape."""
    j_ana, j_bruno, j_carlos = tres_jugadores
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)
    _seed_reunion(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 14),
        (j_carlos.id, 13),
    ])
    _cerrar_temporada_api(client, auth_headers, temporada_id)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    data = r.json()

    # Top-level keys
    assert "temporada_id" in data
    assert "temporada_nombre" in data
    assert "fecha_cierre" in data
    assert "campeon" in data
    assert "ranking" in data

    assert data["temporada_id"] == temporada_id
    assert isinstance(data["ranking"], list)
    assert len(data["ranking"]) > 0


# ── REQ-3 scenario: active + closed coexist → returns closed ─────────────────


def test_activa_y_cerrada_coexisten_devuelve_cerrada(client, auth_headers, tres_jugadores, db):
    """When active and closed coexist, endpoint returns the closed one."""
    from app.models.jugador import Jugador

    j_ana, j_bruno, j_carlos = tres_jugadores

    # Create + close first season
    temporada_id_1 = _crear_temporada_api(client, auth_headers, tres_jugadores, nombre="Liga Cerrada")
    _seed_reunion(db, temporada_id_1, [(j_ana.id, 15)])
    _cerrar_temporada_api(client, auth_headers, temporada_id_1)

    # Create a new active season with fresh players
    p = Jugador(nombre="Pedro")
    db.add(p)
    db.commit()
    db.refresh(p)
    r2 = client.post(
        "/temporadas",
        json={"nombre": "Liga Activa", "fecha_inicio": "2025-01-01", "jugadores": [{"id": p.id}]},
        headers=auth_headers,
    )
    assert r2.status_code == 201

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    assert r.json()["temporada_id"] == temporada_id_1


# ── REQ-3 scenario: ordering by fecha_cierre DESC ────────────────────────────


def test_ordering_fecha_cierre_desc_devuelve_mas_reciente(client, auth_headers, tres_jugadores, db):
    """Two closed seasons with distinct fecha_cierre → most recent returned."""
    from app.models.jugador import Jugador

    j_ana, j_bruno, j_carlos = tres_jugadores

    # Older season (fecha_cierre 2026-01-01)
    temporada_id_vieja = _crear_temporada_api(client, auth_headers, tres_jugadores, nombre="Liga 2024")
    _seed_reunion(db, temporada_id_vieja, [(j_ana.id, 15)])
    _cerrar_temporada_db(db, temporada_id_vieja, campeon_id=j_ana.id, fecha_cierre=date(2026, 1, 1))

    # Newer season (fecha_cierre 2026-05-10) — needs fresh jugadores
    p = Jugador(nombre="Pedro")
    db.add(p)
    db.commit()
    db.refresh(p)
    r2 = client.post(
        "/temporadas",
        json={"nombre": "Liga 2025", "fecha_inicio": "2025-01-01", "jugadores": [{"id": p.id}]},
        headers=auth_headers,
    )
    assert r2.status_code == 201
    temporada_id_nueva = r2.json()["id"]
    _seed_reunion(db, temporada_id_nueva, [(p.id, 15)])
    _cerrar_temporada_db(db, temporada_id_nueva, campeon_id=p.id, fecha_cierre=date(2026, 5, 10))

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    assert r.json()["temporada_id"] == temporada_id_nueva


def test_ordering_nulls_last_sobre_fecha_concreta(client, auth_headers, tres_jugadores, db):
    """Closed with NULL fecha_cierre + closed with 2026-05-10 → returns 2026-05-10 season."""
    from app.models.jugador import Jugador

    j_ana = tres_jugadores[0]

    # Null-fecha season
    temporada_id_null = _crear_temporada_api(client, auth_headers, tres_jugadores, nombre="Liga Historica")
    _seed_reunion(db, temporada_id_null, [(j_ana.id, 15)])
    _cerrar_temporada_db(db, temporada_id_null, campeon_id=j_ana.id, fecha_cierre=None)

    # Concrete fecha season
    p = Jugador(nombre="Pedro")
    db.add(p)
    db.commit()
    db.refresh(p)
    r2 = client.post(
        "/temporadas",
        json={"nombre": "Liga Con Fecha", "fecha_inicio": "2026-01-01", "jugadores": [{"id": p.id}]},
        headers=auth_headers,
    )
    assert r2.status_code == 201
    temporada_id_fecha = r2.json()["id"]
    _seed_reunion(db, temporada_id_fecha, [(p.id, 15)])
    _cerrar_temporada_db(db, temporada_id_fecha, campeon_id=p.id, fecha_cierre=date(2026, 5, 10))

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    assert r.json()["temporada_id"] == temporada_id_fecha


def test_ordering_id_desc_entre_nulls(client, auth_headers, tres_jugadores, db):
    """Two closed seasons both NULL fecha_cierre → higher id returned."""
    from app.models.jugador import Jugador

    j_ana = tres_jugadores[0]

    # First closed (lower id)
    temporada_id_1 = _crear_temporada_api(client, auth_headers, tres_jugadores, nombre="Liga 1")
    _seed_reunion(db, temporada_id_1, [(j_ana.id, 15)])
    _cerrar_temporada_db(db, temporada_id_1, campeon_id=j_ana.id, fecha_cierre=None)

    # Second closed (higher id) with fresh jugadores
    p = Jugador(nombre="Pedro")
    db.add(p)
    db.commit()
    db.refresh(p)
    r2 = client.post(
        "/temporadas",
        json={"nombre": "Liga 2", "fecha_inicio": "2025-01-01", "jugadores": [{"id": p.id}]},
        headers=auth_headers,
    )
    assert r2.status_code == 201
    temporada_id_2 = r2.json()["id"]
    _seed_reunion(db, temporada_id_2, [(p.id, 15)])
    _cerrar_temporada_db(db, temporada_id_2, campeon_id=p.id, fecha_cierre=None)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    assert r.json()["temporada_id"] == temporada_id_2


# ── REQ-3 scenario: campeon present / absent ─────────────────────────────────


def test_campeon_embebido_cuando_campeon_id_set(client, auth_headers, tres_jugadores, db):
    """campeon_id set → campeon object with id, nombre, foto_url, puntos, asistencias, promedio."""
    j_ana, j_bruno, j_carlos = tres_jugadores
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)
    _seed_reunion(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 14),
        (j_carlos.id, 13),
    ])
    _cerrar_temporada_api(client, auth_headers, temporada_id)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    data = r.json()
    assert data["campeon"] is not None
    campeon = data["campeon"]
    assert "id" in campeon
    assert "nombre" in campeon
    assert "puntos" in campeon
    assert "asistencias" in campeon
    assert "promedio" in campeon
    # Ana scored 15 pts, 1 asistencia
    assert campeon["nombre"] == "Ana"
    assert campeon["puntos"] == 15
    assert campeon["asistencias"] == 1


def test_campeon_null_cuando_empate_sin_designar(client, auth_headers, tres_jugadores, db):
    """campeon_id = NULL (tie, not resolved) → campeon is null in response."""
    j_ana, j_bruno, j_carlos = tres_jugadores
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)
    _seed_reunion(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 15),
        (j_carlos.id, 13),
    ])
    _cerrar_temporada_api(client, auth_headers, temporada_id)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    assert r.json()["campeon"] is None


# ── REQ-3 scenario: fecha_cierre null for historic season ────────────────────


def test_fecha_cierre_null_para_temporada_historica(client, auth_headers, tres_jugadores, db):
    """Closed season with fecha_cierre=NULL → fecha_cierre: null in response (not omitted)."""
    j_ana = tres_jugadores[0]
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)
    _seed_reunion(db, temporada_id, [(j_ana.id, 15)])
    _cerrar_temporada_db(db, temporada_id, campeon_id=j_ana.id, fecha_cierre=None)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    data = r.json()
    assert "fecha_cierre" in data
    assert data["fecha_cierre"] is None


# ── REQ-3 scenario: entries shape ────────────────────────────────────────────


def test_payload_entries_no_contienen_delta_ni_lider(client, auth_headers, tres_jugadores, db):
    """Each entry must NOT have delta_posicion or lider_desde_jornada keys."""
    j_ana, j_bruno, j_carlos = tres_jugadores
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)
    _seed_reunion(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 14),
        (j_carlos.id, 13),
    ])
    _cerrar_temporada_api(client, auth_headers, temporada_id)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    entries = r.json()["ranking"]
    assert len(entries) > 0
    for entry in entries:
        assert "delta_posicion" not in entry
        assert "lider_desde_jornada" not in entry


def test_payload_entries_contienen_racha(client, auth_headers, tres_jugadores, db):
    """Each entry MUST have a racha key."""
    j_ana, j_bruno, j_carlos = tres_jugadores
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)
    _seed_reunion(db, temporada_id, [
        (j_ana.id, 15),
        (j_bruno.id, 14),
        (j_carlos.id, 13),
    ])
    _cerrar_temporada_api(client, auth_headers, temporada_id)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    entries = r.json()["ranking"]
    for entry in entries:
        assert "racha" in entry
        assert isinstance(entry["racha"], int)


def test_racha_computada_desde_snapshots(client, auth_headers, tres_jugadores, db):
    """racha reflects snapshot history — player with strictly improving cumulative rank
    has racha > 0. compute_racha counts strictly-improving consecutive positions from end.

    Uses the API to register reuniones so that snapshot generation is triggered
    (direct DB seeding bypasses _generar_snapshots_para_reunion).

    Scenario: Ana goes 3rd → 2nd → 1st across 3 jornadas (cumulative rank improves
    strictly each time). compute_racha will return 2.
    """
    j_ana, j_bruno, j_carlos = tres_jugadores
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)

    def _registrar_via_api(posiciones):
        """Register a reunion via the API (triggers snapshot generation)."""
        r = client.post(
            f"/temporadas/{temporada_id}/reuniones",
            json={"fecha": "2024-01-07", "posiciones": posiciones},
            headers=auth_headers,
        )
        assert r.status_code == 201, r.json()

    # J1: Carlos 1st (15pts), Bruno 2nd (14pts), Ana 3rd (13pts)
    # Cumulative after J1: Carlos=15, Bruno=14, Ana=13 → ranks: Carlos=1, Bruno=2, Ana=3
    _registrar_via_api([
        {"id_jugador": j_carlos.id, "es_invitado": False, "posicion": 1},
        {"id_jugador": j_bruno.id, "es_invitado": False, "posicion": 2},
        {"id_jugador": j_ana.id, "es_invitado": False, "posicion": 3},
    ])

    # J2: Ana 1st (15pts), Carlos 2nd (14pts), Bruno 3rd (13pts)
    # Cumulative after J2: Ana=28, Carlos=29, Bruno=27 → ranks: Carlos=1, Ana=2, Bruno=3
    # Ana snapshot rank: 2 (improved from 3 → strictly better)
    _registrar_via_api([
        {"id_jugador": j_ana.id, "es_invitado": False, "posicion": 1},
        {"id_jugador": j_carlos.id, "es_invitado": False, "posicion": 2},
        {"id_jugador": j_bruno.id, "es_invitado": False, "posicion": 3},
    ])

    # J3: Ana 1st (15pts), Bruno 2nd (14pts), Carlos 3rd (13pts)
    # Cumulative after J3: Ana=43, Carlos=42, Bruno=41 → ranks: Ana=1, Carlos=2, Bruno=3
    # Ana snapshot rank: 1 (improved from 2 → strictly better)
    _registrar_via_api([
        {"id_jugador": j_ana.id, "es_invitado": False, "posicion": 1},
        {"id_jugador": j_bruno.id, "es_invitado": False, "posicion": 2},
        {"id_jugador": j_carlos.id, "es_invitado": False, "posicion": 3},
    ])

    # Ana cumulative snapshot history: [pos=3, pos=2, pos=1] → racha=2
    _cerrar_temporada_api(client, auth_headers, temporada_id)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    entries = r.json()["ranking"]
    ana_entry = next(e for e in entries if e["nombre"] == "Ana")
    assert ana_entry["racha"] == 2


# ── REQ-3 scenario: guests excluded ──────────────────────────────────────────


def test_invitados_excluidos_de_entries(client, auth_headers, tres_jugadores, db):
    """Guests who participated must NOT appear in ranking entries."""
    j_ana, j_bruno, j_carlos = tres_jugadores
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)

    # Mix real players + one invitado
    reunion = Reunion(id_temporada=temporada_id, numero_jornada=1, fecha=date(2024, 1, 7))
    db.add(reunion)
    db.flush()

    db.add(Posicion(id_reunion=reunion.id, id_jugador=j_ana.id, es_invitado=False, posicion=1, puntos=15))
    db.add(Posicion(id_reunion=reunion.id, id_jugador=None, es_invitado=True, posicion=2, puntos=14))
    db.add(Posicion(id_reunion=reunion.id, id_jugador=j_bruno.id, es_invitado=False, posicion=3, puntos=13))
    db.commit()

    _cerrar_temporada_api(client, auth_headers, temporada_id)

    r = client.get(ENDPOINT)
    assert r.status_code == 200
    entries = r.json()["ranking"]
    for entry in entries:
        assert entry.get("es_invitado", False) is False
        # All entries must have id_jugador (non-null)
        assert entry.get("id_jugador") is not None


# ── Additional: public endpoint requires no auth ─────────────────────────────


def test_endpoint_es_publico_no_requiere_auth(client, auth_headers, tres_jugadores, db):
    """Endpoint must be accessible without Authorization header."""
    j_ana = tres_jugadores[0]
    temporada_id = _crear_temporada_api(client, auth_headers, tres_jugadores)
    _seed_reunion(db, temporada_id, [(j_ana.id, 15)])
    _cerrar_temporada_api(client, auth_headers, temporada_id)

    # Call without auth_headers
    r = client.get(ENDPOINT)
    assert r.status_code == 200
