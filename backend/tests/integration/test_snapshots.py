"""
Integration tests — Phase C: Snapshot generation flow.

Tests cover spec scenarios: S-PS-01, S-PS-02, S-PS-03, S-PS-04, S-PS-05, S-PS-06.
RED: all fail before snapshots.py + hooks in reunion.py are implemented.
GREEN: pass once implementation is complete.
"""
import pytest
from datetime import date

from app.models.posicion_snapshot import PosicionSnapshot


def _auth_headers(client):
    r = client.post("/auth/login", json={"identificador": "admin@dudo.com", "password": "admin123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def setup_temporada(client, db, admin_user):
    """
    Creates an active temporada with 3 inscritos: Ana, Bruno, Carlos.
    Returns (temporada_id, headers, jugadores_ids_list).
    """
    from app.models.jugador import Jugador

    headers = _auth_headers(client)

    j1 = Jugador(nombre="Ana")
    j2 = Jugador(nombre="Bruno")
    j3 = Jugador(nombre="Carlos")
    db.add_all([j1, j2, j3])
    db.commit()
    for j in [j1, j2, j3]:
        db.refresh(j)

    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga 2025",
            "fecha_inicio": "2025-01-01",
            "jugadores": [{"id": j1.id}, {"id": j2.id}, {"id": j3.id}],
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    temporada = r.json()
    return temporada["id"], headers, [j1, j2, j3]


def _registrar_reunion(client, temporada_id, headers, posiciones, fecha="2025-01-10"):
    r = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={"fecha": fecha, "posiciones": posiciones},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# S-PS-01 — first reunion, all players attend → 3 snapshot rows
# ---------------------------------------------------------------------------

def test_s_ps_01_first_reunion_creates_snapshots(client, db, admin_user, setup_temporada):
    """S-PS-01: register first reunion with 3 players → 3 snapshot rows with
    correct posicion and puntos_acumulados."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    reunion = _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
    )
    reunion_id = reunion["id"]

    snapshots = db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_reunion == reunion_id
    ).all()

    assert len(snapshots) == 3

    snap_by_jugador = {s.id_jugador: s for s in snapshots}

    # posicion=1 → 15 pts, posicion=2 → 14 pts, posicion=3 → 13 pts
    assert snap_by_jugador[j1.id].posicion == 1
    assert snap_by_jugador[j1.id].puntos_acumulados == 15

    assert snap_by_jugador[j2.id].posicion == 2
    assert snap_by_jugador[j2.id].puntos_acumulados == 14

    assert snap_by_jugador[j3.id].posicion == 3
    assert snap_by_jugador[j3.id].puntos_acumulados == 13


# ---------------------------------------------------------------------------
# S-PS-01b — invitado at posicion=1 must NOT produce a snapshot row
# ---------------------------------------------------------------------------

def test_invitado_excluded_from_snapshots(client, db, admin_user, setup_temporada):
    """Guests never appear in snapshot rows."""
    temporada_id, headers, jugadores = setup_temporada
    j1 = jugadores[0]

    reunion = _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": None, "es_invitado": True, "posicion": 1},
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 2},
        ],
    )
    reunion_id = reunion["id"]

    snapshots = db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_reunion == reunion_id
    ).all()

    # Only one inscrito attended → only 1 snapshot row
    assert len(snapshots) == 1
    assert snapshots[0].id_jugador == j1.id


# ---------------------------------------------------------------------------
# S-PS-02 — edit swaps 1st and 2nd place → snapshot rows reflect new values
# ---------------------------------------------------------------------------

def test_s_ps_02_edit_swaps_positions(client, db, admin_user, setup_temporada):
    """S-PS-02: edit reunion swaps positions → both snapshot rows reflect new values."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    reunion = _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
    )
    reunion_id = reunion["id"]

    # Swap j1 and j2
    r = client.put(
        f"/reuniones/{reunion_id}",
        json={
            "fecha": "2025-01-10",
            "posiciones": [
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 2},
                {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            ],
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text

    snapshots = db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_reunion == reunion_id
    ).all()

    snap_by_jugador = {s.id_jugador: s for s in snapshots}

    # After swap: j2 is at posicion=1 (15 pts), j1 at posicion=2 (14 pts)
    assert snap_by_jugador[j2.id].posicion == 1
    assert snap_by_jugador[j2.id].puntos_acumulados == 15

    assert snap_by_jugador[j1.id].posicion == 2
    assert snap_by_jugador[j1.id].puntos_acumulados == 14


# ---------------------------------------------------------------------------
# S-PS-03 — edit reunion 2 of 5 → ALL snapshots regenerated for all jornadas
# ---------------------------------------------------------------------------

def test_s_ps_03_edit_triggers_full_replay(client, db, admin_user, setup_temporada):
    """S-PS-03: editing reunion 2/5 regenerates ALL snapshot rows for all jornadas."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    # Register 5 reunions
    reuniones = []
    for i in range(5):
        reunion = _registrar_reunion(
            client, temporada_id, headers,
            [
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
                {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            ],
            fecha=f"2025-01-{10 + i:02d}",
        )
        reuniones.append(reunion)

    total_before = db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_temporada == temporada_id
    ).count()
    assert total_before == 15  # 3 players × 5 jornadas

    # Edit reunion 2 (index 1)
    reunion_2_id = reuniones[1]["id"]
    r = client.put(
        f"/reuniones/{reunion_2_id}",
        json={
            "fecha": "2025-01-11",
            "posiciones": [
                # Swap j1 and j2 in reunion 2
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 2},
                {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            ],
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text

    total_after = db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_temporada == temporada_id
    ).count()
    # Still 15 rows (3 × 5) — no orphans, full regeneration
    assert total_after == 15

    # Verify cumulative puntos for reunion 2 snapshot reflects the swap
    snap_r2 = {
        s.id_jugador: s
        for s in db.query(PosicionSnapshot).filter(
            PosicionSnapshot.id_reunion == reunion_2_id
        ).all()
    }
    # j2 wins reunion 2: 15+15=30; j1: 15+14=29... wait:
    # j1 got 15 in reunion 1, 14 in reunion 2 → 29 acumulados
    # j2 got 14 in reunion 1, 15 in reunion 2 → 29 acumulados — tied!
    # competition rank for reunion 2 snapshot: both at 29 → posicion 1 tied
    # Actually j3: 13+13=26 → posicion 3
    assert snap_r2[j1.id].puntos_acumulados == 29
    assert snap_r2[j2.id].puntos_acumulados == 29


# ---------------------------------------------------------------------------
# S-PS-04 — late inscription, no prior attendance → zero snapshots for player
# ---------------------------------------------------------------------------

def test_s_ps_04_late_inscription_no_prior_snapshots(client, db, admin_user, setup_temporada):
    """S-PS-04: late-inscribed player has no snapshots before their first attendance."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    # Register 3 reunions without Diego
    for i in range(3):
        _registrar_reunion(
            client, temporada_id, headers,
            [
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
                {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            ],
            fecha=f"2025-01-{10 + i:02d}",
        )

    # Inscribe Diego to active temporada
    from app.models.jugador import Jugador

    diego = Jugador(nombre="Diego")
    db.add(diego)
    db.commit()
    db.refresh(diego)

    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": diego.id},
        headers=headers,
    )
    assert r.status_code == 201, r.text

    # Diego has zero snapshots (no attendance)
    count = db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_jugador == diego.id
    ).count()
    assert count == 0


# ---------------------------------------------------------------------------
# S-PS-05 — late inscription, first attendance → exactly one snapshot
# ---------------------------------------------------------------------------

def test_s_ps_05_late_inscription_first_attendance(client, db, admin_user, setup_temporada):
    """S-PS-05: late player's first attendance produces exactly one snapshot row."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    # Register 3 reunions without Diego
    for i in range(3):
        _registrar_reunion(
            client, temporada_id, headers,
            [
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
                {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            ],
            fecha=f"2025-01-{10 + i:02d}",
        )

    # Inscribe Diego
    from app.models.jugador import Jugador

    diego = Jugador(nombre="Diego")
    db.add(diego)
    db.commit()
    db.refresh(diego)

    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": diego.id},
        headers=headers,
    )
    assert r.status_code == 201, r.text

    # Register reunion 4 with Diego participating
    reunion = _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            {"id_jugador": diego.id, "es_invitado": False, "posicion": 4},
        ],
        fecha="2025-01-13",
    )
    reunion_id = reunion["id"]

    # Diego has exactly 1 snapshot (for reunion 4 only)
    diego_snaps = db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_jugador == diego.id
    ).all()
    assert len(diego_snaps) == 1
    assert diego_snaps[0].id_reunion == reunion_id

    # No snapshots for Diego in the prior 3 reunions
    prior_reunions_with_diego = [
        s for s in diego_snaps
        if s.id_reunion != reunion_id
    ]
    assert len(prior_reunions_with_diego) == 0


# ---------------------------------------------------------------------------
# S-PS-06 — atomicity: DB failure mid-write rolls back snapshots
# ---------------------------------------------------------------------------

def test_s_ps_06_atomicity_rollback(db, admin_user, setup_temporada, monkeypatch):
    """
    S-PS-06: failure during snapshot insert rolls back Posicion rows too.

    Tests atomicity by calling the service layer directly (bypassing HTTP to
    avoid TestClient re-raising the unhandled exception). The SQLAlchemy
    session must roll back when an exception is raised before db.commit().
    """
    from datetime import date as date_type
    from app.models.posicion import Posicion
    import app.services.snapshots as snap_module
    import app.services.reunion as reunion_module
    from app.schemas.reunion import PosicionInput

    temporada_id, headers, jugadores = setup_temporada
    j1 = jugadores[0]

    # Patch the snapshot helper to raise after posiciones are flushed
    def _fail(*args, **kwargs):
        raise RuntimeError("Simulated DB failure during snapshot write")

    monkeypatch.setattr(snap_module, "_generar_snapshots_para_reunion", _fail)

    # Call service directly — the RuntimeError should propagate and the
    # transaction must NOT commit (SQLAlchemy rolls back on exception exit)
    posicion_input = PosicionInput(
        id_jugador=j1.id,
        es_invitado=False,
        posicion=1,
    )
    with pytest.raises(RuntimeError, match="Simulated DB failure"):
        reunion_module.registrar_reunion(
            db,
            temporada_id,
            date_type(2025, 1, 10),
            [posicion_input],
        )

    # Rollback the session (SQLAlchemy keeps the session in a broken state
    # after an unhandled exception — we explicitly rollback to clean it)
    db.rollback()

    # No Posicion rows and no snapshot rows should have been committed
    posicion_count = db.query(Posicion).filter(
        Posicion.id_reunion.isnot(None)
    ).count()
    snapshot_count = db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_temporada == temporada_id
    ).count()
    assert posicion_count == 0
    assert snapshot_count == 0
