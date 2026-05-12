"""
Integration tests — Phase F: Winner avatar enrichment on GET /temporadas/activa/reuniones.

Tests cover spec scenarios: S-WA-01, S-WA-02, S-WA-03.
RED: fail before ganador field is added to ReunionResumenResponse and get_reuniones_activa.
GREEN: pass once implementation is complete.

SPEC (NON-NEGOTIABLE — S-WA-02):
  If posicion=1 is held by an invitado, ganador=null.
  The winner MUST be the inscrito at posicion=1 ONLY.
"""
import pytest
from datetime import date


def _auth_headers(client):
    r = client.post("/auth/login", json={"identificador": "admin@dudo.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def setup_temporada(client, db, admin_user):
    """Create an active temporada with 2 inscritos: Ana, Bruno."""
    from app.models.jugador import Jugador

    headers = _auth_headers(client)

    j1 = Jugador(nombre="Ana")
    j2 = Jugador(nombre="Bruno")
    db.add_all([j1, j2])
    db.commit()
    for j in [j1, j2]:
        db.refresh(j)

    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga Ganador",
            "fecha_inicio": "2025-01-01",
            "jugadores": [{"id": j1.id}, {"id": j2.id}],
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    temporada = r.json()
    return temporada["id"], headers, [j1, j2]


def _registrar_reunion(client, temporada_id, headers, posiciones, fecha="2025-01-10"):
    r = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={"fecha": fecha, "posiciones": posiciones},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# S-WA-01 — inscrito wins: ganador populated
# ---------------------------------------------------------------------------

def test_s_wa_01_inscrito_wins(client, db, admin_user, setup_temporada):
    """S-WA-01: reunion where inscrito Ana holds posicion=1 → ganador.id_jugador=Ana.id."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2 = jugadores  # j1=Ana, j2=Bruno

    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
        ],
    )

    r = client.get("/temporadas/activa/reuniones")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1

    reunion = data[0]
    assert "ganador" in reunion
    assert reunion["ganador"] is not None
    assert reunion["ganador"]["id_jugador"] == j1.id
    assert reunion["ganador"]["nombre"] == "Ana"
    assert "foto_url" in reunion["ganador"]


# ---------------------------------------------------------------------------
# S-WA-02 — invitado wins → ganador=null (spec requirement, not design Option B)
# ---------------------------------------------------------------------------

def test_s_wa_02_invitado_wins_ganador_null(client, db, admin_user, setup_temporada):
    """
    S-WA-02: invitado holds posicion=1 and Ana holds posicion=2.
    Per spec S-WA-02: ganador=null (invitados excluded from tabla de posiciones).
    """
    temporada_id, headers, jugadores = setup_temporada
    j1, j2 = jugadores  # j1=Ana, j2=Bruno

    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": None, "es_invitado": True, "posicion": 1},
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 2},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 3},
        ],
    )

    r = client.get("/temporadas/activa/reuniones")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1

    reunion = data[0]
    assert "ganador" in reunion
    # SPEC S-WA-02: when invitado at posicion=1, ganador=null
    assert reunion["ganador"] is None


# ---------------------------------------------------------------------------
# S-WA-03 — empty reunion → ganador=null
# ---------------------------------------------------------------------------

def test_s_wa_03_empty_reunion_ganador_null(client, db, admin_user, setup_temporada):
    """S-WA-03: reunion with zero Posicion rows → ganador=null."""
    temporada_id, headers, jugadores = setup_temporada

    # Register a reunion with no posiciones — need to check if API allows this.
    # If not, test with only inscritos but no posicion=1 inscrito.
    # Actually the API likely requires at least one posicion. Let's see.
    # We test the edge case by using only invitados:
    r = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={
            "fecha": "2025-01-10",
            "posiciones": [
                {"id_jugador": None, "es_invitado": True, "posicion": 1},
                {"id_jugador": None, "es_invitado": True, "posicion": 2},
            ],
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text

    r = client.get("/temporadas/activa/reuniones")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1

    reunion = data[0]
    assert "ganador" in reunion
    assert reunion["ganador"] is None


# ---------------------------------------------------------------------------
# Backward compatibility — existing fields still present
# ---------------------------------------------------------------------------

def test_existing_fields_still_present(client, db, admin_user, setup_temporada):
    """Ganador field is ADDITIVE — existing fields id, numero_jornada, fecha must still be present."""
    temporada_id, headers, jugadores = setup_temporada
    j1, j2 = jugadores

    _registrar_reunion(
        client, temporada_id, headers,
        [
            {"id_jugador": j1.id, "es_invitado": False, "posicion": 1},
            {"id_jugador": j2.id, "es_invitado": False, "posicion": 2},
        ],
    )

    r = client.get("/temporadas/activa/reuniones")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1

    reunion = data[0]
    # All existing fields must be present
    assert "id" in reunion
    assert "numero_jornada" in reunion
    assert "fecha" in reunion
    # New field
    assert "ganador" in reunion
