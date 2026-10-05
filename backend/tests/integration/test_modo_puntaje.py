"""Integration tests for the per-season scoring mode (`modo_puntaje`).

- fijo_15 (default): position N = 15 - (N-1).
- por_asistentes: position 1 = total participants in the meeting (guests included),
  i.e. puntos = total - posicion + 1, where total = highest registered position
  (partial saves give final points to the bottom positions).
"""
from datetime import date

import pytest

from app.models.posicion import Posicion


@pytest.fixture
def auth_headers(client, admin_user):
    r = client.post("/auth/login", json={"identificador": "admin@dudo.com", "password": "admin123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def jugadores(db):
    from app.models.jugador import Jugador

    js = [Jugador(nombre=n) for n in ("Ana", "Bruno", "Carlos", "Diego", "Elena")]
    db.add_all(js)
    db.commit()
    for j in js:
        db.refresh(j)
    return js


def _crear_temporada(client, headers, jugadores, **extra):
    body = {
        "nombre": "Liga 2027",
        "fecha_inicio": "2027-01-01",
        "jugadores": [{"id": j.id} for j in jugadores],
        **extra,
    }
    return client.post("/temporadas", json=body, headers=headers)


def _posiciones_seis_con_invitado(jugadores):
    # Guest takes position 3; five enrolled players fill the rest.
    ids = [j.id for j in jugadores]
    return [
        {"id_jugador": ids[0], "es_invitado": False, "posicion": 1},
        {"id_jugador": ids[1], "es_invitado": False, "posicion": 2},
        {"id_jugador": None, "es_invitado": True, "posicion": 3},
        {"id_jugador": ids[2], "es_invitado": False, "posicion": 4},
        {"id_jugador": ids[3], "es_invitado": False, "posicion": 5},
        {"id_jugador": ids[4], "es_invitado": False, "posicion": 6},
    ]


def _puntos_por_posicion(db, reunion_id):
    db.expire_all()
    rows = db.query(Posicion).filter(Posicion.id_reunion == reunion_id).order_by(Posicion.posicion).all()
    return [p.puntos for p in rows]


def test_crear_temporada_por_asistentes_expone_modo(client, auth_headers, jugadores):
    r = _crear_temporada(client, auth_headers, jugadores, modo_puntaje="por_asistentes")
    assert r.status_code == 201
    assert r.json()["modo_puntaje"] == "por_asistentes"

    activa = client.get("/temporadas/activa")
    assert activa.status_code == 200
    assert activa.json()["modo_puntaje"] == "por_asistentes"


def test_crear_temporada_sin_modo_usa_fijo_15(client, auth_headers, jugadores, db):
    r = _crear_temporada(client, auth_headers, jugadores)
    assert r.status_code == 201
    assert r.json()["modo_puntaje"] == "fijo_15"

    reunion = client.post(
        f"/temporadas/{r.json()['id']}/reuniones",
        json={"fecha": str(date.today()), "posiciones": _posiciones_seis_con_invitado(jugadores)},
        headers=auth_headers,
    )
    assert reunion.status_code == 201
    assert _puntos_por_posicion(db, reunion.json()["id"]) == [15, 14, 13, 12, 11, 10]


def test_crear_temporada_modo_invalido_devuelve_422(client, auth_headers, jugadores):
    r = _crear_temporada(client, auth_headers, jugadores, modo_puntaje="doble_o_nada")
    assert r.status_code == 422


def test_por_asistentes_registrar_y_editar_recalcula_con_total(client, auth_headers, jugadores, db):
    temporada = _crear_temporada(client, auth_headers, jugadores, modo_puntaje="por_asistentes").json()

    reunion = client.post(
        f"/temporadas/{temporada['id']}/reuniones",
        json={"fecha": str(date.today()), "posiciones": _posiciones_seis_con_invitado(jugadores)},
        headers=auth_headers,
    )
    assert reunion.status_code == 201
    reunion_id = reunion.json()["id"]
    # Guest counts as a participant and consumes points (3rd place -> 4).
    assert _puntos_por_posicion(db, reunion_id) == [6, 5, 4, 3, 2, 1]

    ids = [j.id for j in jugadores]
    editada = client.put(
        f"/reuniones/{reunion_id}",
        json={
            "fecha": str(date.today()),
            "posiciones": [
                {"id_jugador": ids[3], "es_invitado": False, "posicion": 1},
                {"id_jugador": None, "es_invitado": True, "posicion": 2},
                {"id_jugador": ids[0], "es_invitado": False, "posicion": 3},
                {"id_jugador": ids[1], "es_invitado": False, "posicion": 4},
            ],
        },
        headers=auth_headers,
    )
    assert editada.status_code == 200
    assert _puntos_por_posicion(db, reunion_id) == [4, 3, 2, 1]


def _registrar(client, headers, temporada_id, posiciones):
    r = client.post(
        f"/temporadas/{temporada_id}/reuniones",
        json={"fecha": str(date.today()), "posiciones": posiciones},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_por_asistentes_guardado_parcial_solo_ultimo_puesto_recibe_1(client, auth_headers, jugadores, db):
    # Admin UI sends only filled slots with their slot index: last place alone in slot 6.
    temporada = _crear_temporada(client, auth_headers, jugadores, modo_puntaje="por_asistentes").json()
    reunion_id = _registrar(client, auth_headers, temporada["id"], [
        {"id_jugador": jugadores[4].id, "es_invitado": False, "posicion": 6},
    ])
    assert _puntos_por_posicion(db, reunion_id) == [1]


def test_por_asistentes_guardado_parcial_dos_ultimos_puestos(client, auth_headers, jugadores, db):
    temporada = _crear_temporada(client, auth_headers, jugadores, modo_puntaje="por_asistentes").json()
    reunion_id = _registrar(client, auth_headers, temporada["id"], [
        {"id_jugador": jugadores[3].id, "es_invitado": False, "posicion": 5},
        {"id_jugador": jugadores[4].id, "es_invitado": False, "posicion": 6},
    ])
    assert _puntos_por_posicion(db, reunion_id) == [2, 1]


def test_por_asistentes_guardado_parcial_solo_primer_puesto_no_es_negativo(client, auth_headers, jugadores, db):
    temporada = _crear_temporada(client, auth_headers, jugadores, modo_puntaje="por_asistentes").json()
    reunion_id = _registrar(client, auth_headers, temporada["id"], [
        {"id_jugador": jugadores[0].id, "es_invitado": False, "posicion": 1},
    ])
    assert _puntos_por_posicion(db, reunion_id) == [1]


def test_por_asistentes_editar_completando_reunion_recalcula(client, auth_headers, jugadores, db):
    temporada = _crear_temporada(client, auth_headers, jugadores, modo_puntaje="por_asistentes").json()
    reunion_id = _registrar(client, auth_headers, temporada["id"], [
        {"id_jugador": jugadores[3].id, "es_invitado": False, "posicion": 5},
        {"id_jugador": jugadores[4].id, "es_invitado": False, "posicion": 6},
    ])

    editada = client.put(
        f"/reuniones/{reunion_id}",
        json={"fecha": str(date.today()), "posiciones": _posiciones_seis_con_invitado(jugadores)},
        headers=auth_headers,
    )
    assert editada.status_code == 200
    assert _puntos_por_posicion(db, reunion_id) == [6, 5, 4, 3, 2, 1]
