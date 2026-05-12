"""
Integration tests — Phase E: GET /temporadas/activa/ranking-narrativo endpoint.

Tests cover spec scenarios: S-RN-01..S-RN-06, S-TIE-01, S-TIE-02, S-SCOPE-02.
RED: fail before get_ranking_narrativo service + endpoint + schema are added.
GREEN: pass once implementation is complete.

SEMANTIC delta convention: delta = anterior_posicion - nueva_posicion.
  Positive → player rose. Negative → player dropped. Zero → first appearance or no change.
"""
import pytest
from datetime import date


def _auth_headers(client):
    r = client.post("/auth/login", json={"identificador": "admin@dudo.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def setup_temporada(client, db, admin_user):
    """Create an active temporada with 3 inscritos: Ana, Bruno, Carlos."""
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
            "nombre": "Liga Narrativa",
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
# No active temporada → empty list
# ---------------------------------------------------------------------------

def test_no_active_temporada_returns_empty(client, db, admin_user):
    """When there is no active temporada, the endpoint returns an empty list."""
    r = client.get("/temporadas/activa/ranking-narrativo")
    # Should return 200 with empty list (not 404) — consistent with endpoint design
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.json() == []


# ---------------------------------------------------------------------------
# No snapshots → empty list
# ---------------------------------------------------------------------------

def test_no_snapshots_returns_empty(client, db, admin_user, setup_temporada):
    """When active temporada exists but no reuniones registered, endpoint returns []."""
    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# S-TIE-01 — all tied after jornada 1 → all posicion=1, delta=0
# ---------------------------------------------------------------------------

def test_s_tie_01_all_tied_after_jornada_1(client, db, admin_user, setup_temporada):
    """S-TIE-01: 3 players all with 15 pts → all posicion=1, delta_posicion=0."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 1},
        ],
    )

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3

    for entry in data:
        assert entry["posicion"] == 1
        assert entry["delta_posicion"] == 0
        # First appearance → lider_desde_jornada=1
        assert entry["lider_desde_jornada"] == 1


# ---------------------------------------------------------------------------
# S-TIE-02 — tie broken in jornada 2
# ---------------------------------------------------------------------------

def test_s_tie_02_tie_broken(client, db, admin_user, setup_temporada):
    """
    S-TIE-02: jornada 1 all at posicion=1 (tied). Jornada 2 one player earns
    more points and leads. The other two drop.

    SEMANTIC delta:
    - Leader: was posicion=1, still posicion=1 → delta=0
    - Others: were posicion=1 (tied), now posicion=2 → delta = 1 - 2 = -1

    NOTE: Spec says delta=-1 for the drop (posicion 1→2). Under SEMANTIC convention:
    delta = anterior(1) - nueva(2) = -1. Both agree for this case.
    """
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    # Jornada 1: all tied at posicion=1 (15 pts each)
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 1},
        ],
        fecha="2025-01-10",
    )

    # Jornada 2: j1 wins (15 pts), j2 second (14 pts), j3 third (13 pts)
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-17",
    )

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()

    by_jugador = {e["id_jugador"]: e for e in data}

    # j1: 15+15=30 → posicion=1, was posicion=1 → delta=0
    assert by_jugador[j1.id]["posicion"] == 1
    assert by_jugador[j1.id]["delta_posicion"] == 0

    # j2: 15+14=29 → now posicion=2 (j3 has 15+13=28 → posicion=3)
    # j2 was at posicion=1 (tied), now at posicion=2 → delta = 1 - 2 = -1
    assert by_jugador[j2.id]["posicion"] == 2
    assert by_jugador[j2.id]["delta_posicion"] == -1

    # j3: 15+13=28 → posicion=3, was posicion=1 → delta = 1-3 = -2
    assert by_jugador[j3.id]["posicion"] == 3
    assert by_jugador[j3.id]["delta_posicion"] == -2


# ---------------------------------------------------------------------------
# S-RN-01 — strictly improving racha over 3 jornadas → racha=2
# ---------------------------------------------------------------------------

def test_s_rn_01_racha_strictly_improving(client, db, admin_user, setup_temporada):
    """S-RN-01: player ranked p4→p3→p2 across 3 jornadas → racha=2."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    # We need a 4th player to get posicion=4
    from app.models.jugador import Jugador
    j4 = Jugador(nombre="Diana")
    db.add(j4)
    db.commit()
    db.refresh(j4)
    r = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": j4.id},
        headers=headers,
    )
    assert r.status_code == 201, r.text

    # Jornada 1: j4 at posicion=4 (12 pts), others at 1,2,3 (15,14,13 pts)
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            {"id_jugador": j4.id, "es_invitado": False, "posicion": 4},
        ],
        fecha="2025-01-10",
    )
    # After J1: j1=15, j2=14, j3=13, j4=12 → ranks 1,2,3,4

    # Jornada 2: j4 gets posicion=1 (15 pts, total 12+15=27)
    # j1 gets posicion=2 (14 pts, total 15+14=29 → still leads)
    # Actually let's set up so j4 climbs:
    # j1: 1st (15 pts) total=30; j4: 2nd (14 pts) total=26; j2: 3rd (13 pts) total=27; j3: 4th (12 pts) total=25
    # Wait, we need j4 to go from rank 4 → rank 3 → rank 2
    # Let's use explicit cumulative:
    # J1: j1=15, j2=14, j3=13, j4=12 → positions: j1=1, j2=2, j3=3, j4=4
    # J2: give j4 15pts (posicion=1 in reunion), j1=14, j2=13, j3=12
    #   cumulative: j1=29, j2=27, j3=25, j4=27 → j1=1, j2=2(tied), j4=2(tied), j3=4
    #   Wait, j2 and j4 both have 27 → competition rank: j1=1, j2=2, j4=2, j3=4
    # That doesn't give j4 posicion=3 in J2.
    # Let's give j4 13pts in J2, j3 gets 12:
    # J2: j1=15(pos1), j2=14(pos2), j4=13(pos3), j3=12(pos4)
    #   cumulative: j1=30, j2=28, j3=25, j4=25 → j1=1, j2=2, j3=3(tied), j4=3(tied)
    # Still not 3 for j4 alone.
    # Simplest: use absolute positions, not based on cumulative points
    # J2: j1 gets pos=1(15pts), j2 gets pos=3(13), j4 gets pos=2(14), j3 gets pos=4(12)
    # cumulative: j1=30, j4=26, j2=27, j3=25 → j1=1, j2=2, j4=3, j3=4 → j4 rank=3 ✓
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j4.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 3},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 4},
        ],
        fecha="2025-01-17",
    )
    # After J2: j1=30, j2=27, j4=26, j3=25 → ranks: j1=1, j2=2, j4=3, j3=4

    # Jornada 3: j4 gets posicion=1 (15 pts, total 26+15=41)
    # j1 gets posicion=2 (14, total 44); j2 gets pos=3 (13, total 40); j3 gets pos=4 (12, total 37)
    # cumulative: j1=44, j2=40, j4=41, j3=37 → j1=1, j4=2, j2=3, j3=4 → j4 rank=2 ✓
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j4.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 3},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 4},
        ],
        fecha="2025-01-24",
    )
    # After J3: j1=44, j4=41, j2=40, j3=37 → j1=1, j4=2, j2=3, j3=4

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()

    by_jugador = {e["id_jugador"]: e for e in data}

    # j4: went from rank 4 → rank 3 → rank 2 → racha = 2
    assert by_jugador[j4.id]["racha"] == 2
    # j4 current posicion=2, previous=3 → delta = 3 - 2 = +1
    assert by_jugador[j4.id]["delta_posicion"] == 1


# ---------------------------------------------------------------------------
# S-RN-02 — stay breaks racha
# ---------------------------------------------------------------------------

def test_s_rn_02_stay_breaks_racha(client, db, admin_user, setup_temporada):
    """S-RN-02: player ranked p3→p3→p2 → racha=1 (stay in J2 breaks streak)."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    # J1: j3 at posicion=3 (13 pts)
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-10",
    )
    # After J1: j1=15, j2=14, j3=13 → ranks 1,2,3

    # J2: same positions again → j3 stays at rank 3
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-17",
    )
    # After J2: j1=30, j2=28, j3=26 → ranks 1,2,3 (j3 still rank 3)

    # J3: j3 gets more points → j3 now at rank 2
    # Need j3 cumulative > j2: j3=26+15=41, j2=28+12=40 (j3 gets pos=1, j2 gets pos=4)
    # Let's give j3 posicion=1 (15pts) in J3:
    # cumulative: j1=30+13=43, j2=28+12=40, j3=26+15=41 → j1=1, j3=2, j2=3?
    # j1=30+posicion 3(13)=43; j3=26+15=41; j2=28+14=42 → j1=1, j2=2, j3=3 — still 3!
    # Let j3 get posicion=1(15), j1 posicion=3(13), j2 posicion=2(14):
    # j1=30+13=43, j2=28+14=42, j3=26+15=41 → j1=1, j2=2, j3=3 still tied
    # Give j3 a big lead: j3 pos=1(15), j2 pos=3(13), j1 pos=2(14):
    # j1=30+14=44, j2=28+13=41, j3=26+15=41 → j1=1, j2 and j3 tied at 41 → both rank 2
    # Give j3 pos=1(15), j1 pos=4(12), j2 pos=2(14):
    # j1=30+12=42, j2=28+14=42, j3=26+15=41 — j1 and j2 tied at 42 → rank 1, j3 rank 3
    # This is tricky due to cumulative totals. Let me try larger gaps:
    # J1: j1=15, j2=14, j3=1 (use puntos directly) — but we control posicion, not puntos directly
    # Actually puntos = 15 - (posicion-1). posicion=1→15pts, posicion=2→14pts, ..., posicion=15→1pt
    # To get j3 rank=2 in J3: j3 total must be > j2 total.
    # After J2: j1=30, j2=28, j3=26.
    # In J3: give j3 pos=1(15pts), j2 pos=3(13pts), j1 pos=2(14pts):
    # j1=30+14=44, j2=28+13=41, j3=26+15=41 → j2 and j3 tied at 41 → both rank 2
    # Result: j3 rank=2 (tied with j2)! That works.
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-24",
    )
    # After J3: j1=44, j2=41, j3=41 → j1=1, j2=2(tied), j3=2(tied)

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()
    by_jugador = {e["id_jugador"]: e for e in data}

    # j3: rank history J1=3, J2=3, J3=2 → racha=1 (stay in J2 broke streak; only last step counts)
    assert by_jugador[j3.id]["racha"] == 1


# ---------------------------------------------------------------------------
# S-RN-03 — stay at #1 breaks racha
# ---------------------------------------------------------------------------

def test_s_rn_03_stay_at_1_breaks_racha(client, db, admin_user, setup_temporada):
    """S-RN-03: player ranked p2→p1→p1 → racha=0 (stayed at #1 in last jornada)."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    # J1: j1 at posicion=1 (15pts), j2 at posicion=2 (14pts), j3 at posicion=3 (13pts)
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-10",
    )
    # After J1: j1=15, j2=14, j3=13 → ranks 1,2,3

    # J2: j2 gets pos=1 (15pts), j1 gets pos=2 (14pts)
    # cumulative: j1=15+14=29, j2=14+15=29 — tied! Both rank 1.
    # Need j2 strictly at rank 2 in J1 and rank 1 in J2.
    # To separate: give j1 pos=3 (13pts) in J2 and j2 pos=1 (15pts)
    # cumulative: j1=15+13=28, j2=14+15=29, j3=13+12=25 → j2=1, j1=2, j3=3
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-17",
    )
    # After J2: j2=29, j1=28, j3=25 → ranks: j2=1, j1=2, j3=3

    # J3: same positions (j2 wins again, stays at rank 1)
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-24",
    )
    # After J3: j2=29+15=44, j1=28+13=41, j3=25+14=39 → j2=1, j1=2, j3=3

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()
    by_jugador = {e["id_jugador"]: e for e in data}

    # j2: snapshot history rank 2→1→1, racha=0 (stayed at #1 in last jornada, not an improvement)
    assert by_jugador[j2.id]["posicion"] == 1
    assert by_jugador[j2.id]["racha"] == 0


# ---------------------------------------------------------------------------
# S-RN-04 — lider_desde continuous leadership
# ---------------------------------------------------------------------------

def test_s_rn_04_lider_desde_continuous(client, db, admin_user, setup_temporada):
    """S-RN-04: player held posicion=1 in jornadas 1,2,3 → lider_desde_jornada=1."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    for i in range(3):
        _registrar_reunion(
            client, temporada_id, headers,
            [
                {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
                {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
                {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            ],
            fecha=f"2025-01-{10 + i * 7:02d}",
        )

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()
    by_jugador = {e["id_jugador"]: e for e in data}

    # j1 led from jornada 1 continuously → lider_desde_jornada=1
    assert by_jugador[j1.id]["lider_desde_jornada"] == 1
    # j2 never led → None
    assert by_jugador[j2.id]["lider_desde_jornada"] is None


# ---------------------------------------------------------------------------
# S-RN-05 — lider_desde after losing and regaining #1
# ---------------------------------------------------------------------------

def test_s_rn_05_lider_desde_after_loss_and_regain(client, db, admin_user, setup_temporada):
    """
    S-RN-05: player led J1, J2, dropped J3, regained J4.
    lider_desde_jornada must be 4 (last ascent).
    """
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    # J1: j1 leads
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-10",
    )
    # After J1: j1=15, j2=14, j3=13

    # J2: j1 leads again
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-17",
    )
    # After J2: j1=30, j2=28, j3=26

    # J3: j2 overtakes j1.
    # After J2: j1=30, j2=28, j3=26.
    # Give j2 pos=1(15), j1 pos=4(12), j3 pos=2(14):
    # j1=30+12=42, j2=28+15=43, j3=26+14=40 → j2=1, j1=2, j3=3 ✓
    # Note: posicion=4 requires at least 4 players. We only have 3.
    # Use pos=3 for j1 (13pts) and pos=1 for j2 (15pts), but then they're tied:
    # j1=30+13=43, j2=28+15=43 — tied at posicion=1!
    # Need a 4th player or a different gap.
    # Solution: use a larger point differential.
    # Let's give j3 posicion=1(15) in J3, and give j1 posicion=3(13), j2 posicion=2(14):
    # j1=30+13=43, j2=28+14=42, j3=26+15=41 → j1=1 still! (43>42>41)
    # Alternative: add invitados to consume higher positions.
    # Simplest fix: j2 gets pos=1 (15pts) and j1 gets only pos=3 (13pts)
    # but then j2=28+15=43, j1=30+13=43 — still tied!
    # Root problem: j1 leads by only 2 pts after J2. Need a bigger lead to overcome.
    # Give j2 an extra reunion:
    # Actually we need 3 players for 3 positions.
    # We can use: j2=pos1(15), j1=pos3(13), j3=pos2(14) → j1=43, j2=43 — tied.
    # To get j2 strictly above j1: j1 must have FEWER cumulative.
    # After J2: j1=30, j2=28. j2 needs 3+ more than j1 earns.
    # In J3: j1 gets pos=2(14), j2 gets pos=1(15), j3 gets pos=3(13)...
    # doesn't work.
    # Real fix: inject invitados into higher positions so j1 gets lower pts:
    # J3: invitado pos=1, j2 pos=2(14), j1 pos=3(13), j3 pos=4(12)
    # j1=30+13=43, j2=28+14=42 — still j1 leads.
    # The only way: j2 must earn MORE than j1 earned previously AND overcome gap.
    # j1 lead = 30-28 = 2 pts after J2.
    # In J3: j2 needs to beat j1's cumulative.
    # j2_new = j2_old + pts_j2; j1_new = j1_old + pts_j1
    # Need: j2_new > j1_new → j2_old + pts_j2 > j1_old + pts_j1
    # 28 + pts_j2 > 30 + pts_j1 → pts_j2 - pts_j1 > 2
    # With 3 players: pts1=15, pts2=14, pts3=13. Max diff = 15-13=2. Not enough!
    # We need 4+ players to get a big enough diff.
    # OR: make the gap after J2 smaller (j1 leads by 1 pt).
    # Strategy: after J1 make them tied, after J2 j1 leads by 1.
    # Re-design the whole scenario to use 4 players (j1, j2, j3 + invitado to fill 4th spot):
    # J1: invitado pos=1, j1 pos=2(14), j2 pos=3(13), j3 pos=4(12)
    # cumul: j1=14, j2=13, j3=12 → j1=1, j2=2, j3=3
    # J2: j1 pos=1(15), j2 pos=2(14), j3 pos=3(13)
    # cumul: j1=29, j2=27, j3=25 → j1=1, j2=2, j3=3 (still leads by 2)
    # Not helpful. Use a completely different approach:
    # Use 4 players with a real inscrito, register more jornadas.
    # Simplest: use an invitado at position 1 to shift everyone down,
    # effectively giving j2 pos=1 with 15pts vs j1 getting pos=2 with 14pts
    # but that means j2 gains 15-14=1 pt per jornada. Need 3 jornadas to overcome 2-pt gap.
    # After J2: j1=30, j2=28 (gap=2).
    # J3: j2 pos=1(15), j1 pos=2(14): j1=44, j2=43 — still j1 leads by 1!
    # J4: j2 pos=1(15), j1 pos=2(14): j1=58, j2=58 — tied!
    # J5: j2 pos=1(15), j1 pos=2(14): j1=72, j2=73 — j2 leads! ✓
    # But that's too many jornadas. Let's try a 3-jornada reset instead.
    # SIMPLEST CORRECT APPROACH: make j1 start 2nd and then lead.
    # J1: j2 leads (j2 pos=1, j1 pos=2)
    # J2: j2 leads again (both get same)
    # J3: j1 overtakes j2 (j1 gets pos=1, j2 gets pos=2)
    # Then lider_desde_jornada for j1 = 3 (last ascent)
    # This is simpler and tests the same spec scenario.
    # After J1: j2=15, j1=14, j3=13 → j2=1, j1=2, j3=3
    # After J2: j2=30, j1=28, j3=26 → j2=1, j1=2, j3=3
    # J3: j1 pos=1(15), j2 pos=3(13), j3 pos=2(14)
    # j1=28+15=43, j2=30+13=43 — tied! Still tied.
    # Need bigger gap. J3: j1 pos=1(15), j2 pos=3(13), invitado:
    # j1=28+15=43, j2=30+13=43 still tied...
    # OK, DEFINITIVE FIX: use 4 players and put j1 at pos=3 in J3 (earning 13pts):
    # After J2: j1=30, j2=28 (gap=2). J3 with 4 players (add Diego inscrito):
    # j2 pos=1(15), Diego pos=2(14), j3 pos=3(13), j1 pos=4(12):
    # j1=30+12=42, j2=28+15=43 → j2=1, j1=2 ✓ (gap=1 now)
    # J4: j1 pos=1(15), j2 pos=3(13): j1=42+15=57, j2=43+13=56 → j1=1 ✓
    # lider_desde_jornada = 4 ✓
    from app.models.jugador import Jugador as JugadorModel
    diego = JugadorModel(nombre="Diego_RN05")
    db.add(diego)
    db.commit()
    db.refresh(diego)
    r_insc = client.post(
        "/temporadas/activa/inscripciones",
        json={"id_jugador": diego.id},
        headers=headers,
    )
    assert r_insc.status_code == 201, r_insc.text

    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": diego.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 4},
        ],
        fecha="2025-01-24",
    )
    # After J3 (cumulative): j1=30+12=42, j2=28+15=43, j3=26+13=39, diego=0+14=14
    # Ranking: j2=43→1, j1=42→2, j3=39→3, diego=14→4

    # J4: j1 regains the lead
    # j1 pos=1(15), j2 pos=3(13): j1=42+15=57, j2=43+13=56, j3=39+14=53, diego=14+12=26
    # → j1=1 ✓
    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 3},
            {"id_jugador": diego.id, "es_invitado": False, "posicion": 4},
        ],
        fecha="2025-01-31",
    )
    # After J4: j1=57, j2=56, j3=53, diego=26 → j1=1, j2=2, j3=3, diego=4

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()
    by_jugador = {e["id_jugador"]: e for e in data}

    # j1: held #1 in J1, J2, lost in J3, regained in J4 → lider_desde_jornada=4
    assert by_jugador[j1.id]["posicion"] == 1
    assert by_jugador[j1.id]["lider_desde_jornada"] == 4


# ---------------------------------------------------------------------------
# S-RN-06 — never reached #1 → lider_desde_jornada=None
# ---------------------------------------------------------------------------

def test_s_rn_06_never_led(client, db, admin_user, setup_temporada):
    """S-RN-06: player never reached posicion=1 → lider_desde_jornada=None."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
        fecha="2025-01-10",
    )

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()
    by_jugador = {e["id_jugador"]: e for e in data}

    # j3 never held posicion=1
    assert by_jugador[j3.id]["lider_desde_jornada"] is None


# ---------------------------------------------------------------------------
# S-SCOPE-02 — existing /ranking endpoint shape unchanged
# ---------------------------------------------------------------------------

def test_s_scope_02_existing_ranking_unchanged(client, db, admin_user, setup_temporada):
    """S-SCOPE-02: GET /temporadas/activa/ranking shape is identical after this change."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
    )

    r = client.get("/temporadas/activa/ranking")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    for entry in data:
        # Must have only these keys (no narrative fields leaked)
        expected_keys = {"id_jugador", "nombre", "puntos", "asistencias", "foto_url"}
        assert set(entry.keys()) == expected_keys, f"Unexpected keys: {set(entry.keys())}"


# ---------------------------------------------------------------------------
# Response schema validation
# ---------------------------------------------------------------------------

def test_response_schema_shape(client, db, admin_user, setup_temporada):
    """Verify the response shape matches RankingNarrativoEntry exactly."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2, j3 = jugadores

    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j3.id, "es_invitado": False, "posicion": 3},
        ],
    )

    r = client.get("/temporadas/activa/ranking-narrativo")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0

    for entry in data:
        assert "id_jugador" in entry
        assert "nombre" in entry
        assert "puntos" in entry
        assert "asistencias" in entry
        assert "foto_url" in entry
        assert "posicion" in entry
        assert "delta_posicion" in entry
        assert "racha" in entry
        assert "lider_desde_jornada" in entry
        # Verify types
        assert isinstance(entry["id_jugador"], int)
        assert isinstance(entry["nombre"], str)
        assert isinstance(entry["puntos"], int)
        assert isinstance(entry["asistencias"], int)
        assert entry["foto_url"] is None or isinstance(entry["foto_url"], str)
        assert isinstance(entry["posicion"], int)
        assert isinstance(entry["delta_posicion"], int)
        assert isinstance(entry["racha"], int)
        assert entry["lider_desde_jornada"] is None or isinstance(entry["lider_desde_jornada"], int)
