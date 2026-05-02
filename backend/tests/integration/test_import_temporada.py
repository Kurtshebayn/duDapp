"""Integration tests for POST /temporadas/import endpoint.

Tests T-IMP-42 through T-IMP-61 (SCN-IMP-01 through SCN-IMP-17 + shape + 401).
Run: pytest backend/tests/integration/test_import_temporada.py
"""
from datetime import date

import pytest

from app.models.inscripcion import Inscripcion
from app.models.jugador import Jugador
from app.models.posicion import Posicion
from app.models.reunion import Reunion
from app.models.temporada import EstadoTemporada, Temporada


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _csv_bytes(headers: list[str], rows: list[list[int]], sep: str = ";") -> bytes:
    """Build CSV bytes with the given separator (default `;`), no BOM."""
    lines = [sep.join(headers)]
    for r in rows:
        lines.append(sep.join(str(v) for v in r))
    return "\n".join(lines).encode("utf-8")


def _csv_bytes_bom(headers: list[str], rows: list[list[int]]) -> bytes:
    return b"\xef\xbb\xbf" + _csv_bytes(headers, rows)


def _post_import(client, auth_headers, csv_bytes, nombre="Temp Test", fecha="2022-01-01",
                 campeon_nombre=None):
    files = {"archivo": ("import.csv", csv_bytes, "text/csv")}
    data = {"nombre": nombre, "fecha_inicio": fecha}
    if campeon_nombre is not None:
        data["campeon_nombre"] = campeon_nombre
    return client.post("/temporadas/import", files=files, data=data, headers=auth_headers)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_headers(client, admin_user):
    r = client.post("/auth/login", json={"identificador": "admin@dudo.com", "password": "admin123"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def jugadores_seed(db):
    """Three players in the catalogue, reusable as CSV headers."""
    jugadores = [
        Jugador(nombre="Ana"),
        Jugador(nombre="Beto"),
        Jugador(nombre="Carla"),
    ]
    db.add_all(jugadores)
    db.commit()
    for j in jugadores:
        db.refresh(j)
    return jugadores  # [Ana, Beto, Carla]


@pytest.fixture
def temporada_existente(db, admin_user):
    """Pre-existing closed Temporada to trigger 409 in SCN-IMP-08."""
    t = Temporada(
        nombre="Liga 2023",
        fecha_inicio=date(2023, 1, 1),
        estado=EstadoTemporada.cerrada,
        id_usuario=admin_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def temporada_activa_previa(client, auth_headers, jugadores_seed):
    """Active season already in DB — used in SCN-IMP-13."""
    r = client.post(
        "/temporadas",
        json={
            "nombre": "Liga Activa",
            "fecha_inicio": "2026-01-01",
            "jugadores": [{"id": jugadores_seed[0].id}],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, f"Failed to create active season: {r.text}"
    return r.json()


# ---------------------------------------------------------------------------
# T-IMP-61 — 401 test (no auth)
# ---------------------------------------------------------------------------

class TestImportSinToken:
    """T-IMP-61 — SCN-IMP-14: no auth → 401."""

    def test_import_sin_token_devuelve_401(self, client, jugadores_seed):
        csv = _csv_bytes(["Ana"], [[15]])
        files = {"archivo": ("import.csv", csv, "text/csv")}
        data = {"nombre": "X", "fecha_inicio": "2022-01-01"}
        r = client.post("/temporadas/import", files=files, data=data)
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# T-IMP-42 — SCN-IMP-01: happy path, no guests
# ---------------------------------------------------------------------------

class TestImportHappyPathSinInvitados:
    """T-IMP-42."""

    def test_import_happy_path_sin_invitados(self, client, auth_headers, jugadores_seed, db):
        csv = _csv_bytes(["Ana", "Beto", "Carla"], [[15, 14, 13], [15, 14, 13]])
        r = _post_import(client, auth_headers, csv, nombre="Temporada 2022", fecha="2022-04-01")

        assert r.status_code == 201, r.text
        body = r.json()

        # Season state
        assert body["estado"] == "cerrada"
        assert body["campeon_id"] is None
        assert body["nombre"] == "Temporada 2022"

        # Counts from DB
        temporadas = db.query(Temporada).all()
        assert len(temporadas) == 1
        t = temporadas[0]
        assert t.estado == EstadoTemporada.cerrada

        inscripciones = db.query(Inscripcion).filter(Inscripcion.id_temporada == t.id).all()
        assert len(inscripciones) == 3

        reuniones = db.query(Reunion).filter(Reunion.id_temporada == t.id).all()
        assert len(reuniones) == 2
        # All reuniones have fecha=None
        for reu in reuniones:
            assert reu.fecha is None

        posiciones = (
            db.query(Posicion)
            .join(Reunion)
            .filter(Reunion.id_temporada == t.id)
            .all()
        )
        assert len(posiciones) == 6
        for p in posiciones:
            assert p.es_invitado is False

        assert body["resumen_import"]["invitados_inferidos"] == 0
        assert body["resumen_import"]["reuniones_creadas"] == 2
        assert body["resumen_import"]["jugadores_inscriptos"] == 3
        assert body["resumen_import"]["posiciones_creadas"] == 6


# ---------------------------------------------------------------------------
# T-IMP-43 — SCN-IMP-02: one guest inferred
# ---------------------------------------------------------------------------

class TestImportConUnInvitado:
    """T-IMP-43."""

    def test_import_happy_path_con_un_invitado(self, client, auth_headers, jugadores_seed, db):
        # Ana=15, Beto=13 → gap at position 2 (expected score 14) → 1 guest
        csv = _csv_bytes(["Ana", "Beto"], [[15, 13]])
        r = _post_import(client, auth_headers, csv)

        assert r.status_code == 201, r.text
        body = r.json()
        assert body["resumen_import"]["invitados_inferidos"] == 1

        # Verify DB: 3 posicion rows for the one reunion
        t_id = body["id"]
        reuniones = db.query(Reunion).filter(Reunion.id_temporada == t_id).all()
        assert len(reuniones) == 1

        posiciones = (
            db.query(Posicion)
            .join(Reunion)
            .filter(Reunion.id_temporada == t_id)
            .order_by(Posicion.posicion)
            .all()
        )
        assert len(posiciones) == 3
        # pos 1: Ana (15, not invitado)
        assert posiciones[0].puntos == 15
        assert posiciones[0].es_invitado is False
        # pos 2: guest (14, invitado)
        assert posiciones[1].puntos == 14
        assert posiciones[1].es_invitado is True
        assert posiciones[1].id_jugador is None
        # pos 3: Beto (13, not invitado)
        assert posiciones[2].puntos == 13
        assert posiciones[2].es_invitado is False


# ---------------------------------------------------------------------------
# T-IMP-44 — SCN-IMP-03: multiple consecutive guests
# ---------------------------------------------------------------------------

class TestImportConInvitadosConsecutivos:
    """T-IMP-44."""

    def test_import_con_invitados_consecutivos(self, client, auth_headers, jugadores_seed, db):
        # Ana=15, Beto=11 → gap of 3 (positions 2,3,4 are guests)
        csv = _csv_bytes(["Ana", "Beto"], [[15, 11]])
        r = _post_import(client, auth_headers, csv)

        assert r.status_code == 201, r.text
        body = r.json()
        assert body["resumen_import"]["invitados_inferidos"] == 3

        t_id = body["id"]
        posiciones = (
            db.query(Posicion)
            .join(Reunion)
            .filter(Reunion.id_temporada == t_id)
            .order_by(Posicion.posicion)
            .all()
        )
        assert len(posiciones) == 5
        guests = [p for p in posiciones if p.es_invitado]
        assert len(guests) == 3
        guest_puntos = sorted([g.puntos for g in guests], reverse=True)
        assert guest_puntos == [14, 13, 12]


# ---------------------------------------------------------------------------
# T-IMP-45 — SCN-IMP-04: absences + guest in same meeting
# ---------------------------------------------------------------------------

class TestImportConAusenciasYInvitados:
    """T-IMP-45."""

    def test_import_con_ausencias_y_invitados_mezclados(self, client, auth_headers, jugadores_seed, db):
        # Ana=15, Beto=13, Carla=0 → Carla absent, guest at pos 2
        csv = _csv_bytes(["Ana", "Beto", "Carla"], [[15, 13, 0]])
        r = _post_import(client, auth_headers, csv)

        assert r.status_code == 201, r.text
        body = r.json()
        assert body["resumen_import"]["invitados_inferidos"] == 1

        t_id = body["id"]
        posiciones = (
            db.query(Posicion)
            .join(Reunion)
            .filter(Reunion.id_temporada == t_id)
            .order_by(Posicion.posicion)
            .all()
        )
        # 3 posiciones: Ana, guest, Beto — NOT Carla
        assert len(posiciones) == 3
        player_ids = [p.id_jugador for p in posiciones if not p.es_invitado]
        assert len(player_ids) == 2  # Ana and Beto


# ---------------------------------------------------------------------------
# T-IMP-46 — SCN-IMP-05: champion override valid
# ---------------------------------------------------------------------------

class TestImportConCampeonValido:
    """T-IMP-46."""

    def test_import_con_campeon_valido_setea_campeon_id(self, client, auth_headers, jugadores_seed, db):
        ana = jugadores_seed[0]  # Ana
        csv = _csv_bytes(["Ana", "Beto"], [[15, 14]])

        # Exact case
        r = _post_import(client, auth_headers, csv, campeon_nombre="Ana")
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["campeon_id"] == ana.id

    def test_import_con_campeon_valido_case_insensitive(self, client, auth_headers, jugadores_seed, db):
        ana = jugadores_seed[0]  # Ana
        csv = _csv_bytes(["Ana", "Beto"], [[15, 14]])
        r = _post_import(client, auth_headers, csv, nombre="Temp 2", campeon_nombre="ana")
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["campeon_id"] == ana.id


# ---------------------------------------------------------------------------
# T-IMP-47 — SCN-IMP-07: no champion → campeon_id=NULL
# ---------------------------------------------------------------------------

class TestImportSinCampeon:
    """T-IMP-47."""

    def test_import_sin_campeon_deja_campeon_id_null(self, client, auth_headers, jugadores_seed):
        csv = _csv_bytes(["Ana", "Beto"], [[15, 14]])
        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 201, r.text
        assert r.json()["campeon_id"] is None


# ---------------------------------------------------------------------------
# T-IMP-48 — SCN-IMP-08: duplicate season name → 409
# ---------------------------------------------------------------------------

class TestImportNombreDuplicado:
    """T-IMP-48."""

    def test_import_con_nombre_duplicado_devuelve_409(
        self, client, auth_headers, jugadores_seed, temporada_existente, db
    ):
        csv = _csv_bytes(["Ana"], [[15]])
        r = _post_import(client, auth_headers, csv, nombre="Liga 2023")
        assert r.status_code == 409, r.text
        assert r.json()["detail"]["code"] == "temporada_duplicada"

        # No new records created
        assert db.query(Temporada).count() == 1  # only the pre-seeded one
        assert db.query(Inscripcion).count() == 0
        assert db.query(Reunion).count() == 0
        assert db.query(Posicion).count() == 0


# ---------------------------------------------------------------------------
# T-IMP-49 — SCN-IMP-09: unresolved players, ALL reported at once
# ---------------------------------------------------------------------------

class TestImportJugadoresNoResueltos:
    """T-IMP-49."""

    def test_import_jugadores_no_resueltos_lista_completa(self, client, auth_headers, jugadores_seed):
        # GhostA and GhostB don't exist in DB
        csv = _csv_bytes(["Ana", "GhostA", "GhostB"], [[15, 14, 13]])
        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 422, r.text
        detail = r.json()["detail"]
        assert detail["code"] == "jugadores_no_resueltos"
        nombres = detail["nombres"]
        assert "GhostA" in nombres
        assert "GhostB" in nombres
        assert len(nombres) == 2


# ---------------------------------------------------------------------------
# T-IMP-50 — SCN-IMP-10: invalid scores reported all at once
# ---------------------------------------------------------------------------

class TestImportPuntajesInvalidos:
    """T-IMP-50."""

    def test_import_puntajes_invalidos_reporta_todos(self, client, auth_headers, jugadores_seed):
        # Row 1: Ana has "?" (invalid), Row 2: Beto has "-3" (invalid)
        csv = b"Ana;Beto\n?;14\n15;-3\n"
        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 422, r.text
        detail = r.json()["detail"]
        assert detail["code"] == "puntaje_invalido"
        errores = detail["errores"]
        assert len(errores) == 2
        fila_columna = [(e["fila"], e["columna"]) for e in errores]
        assert (1, "Ana") in fila_columna
        assert (2, "Beto") in fila_columna


# ---------------------------------------------------------------------------
# T-IMP-51 — SCN-IMP-11: all-absent meeting
# ---------------------------------------------------------------------------

class TestImportReunionTodosAusentes:
    """T-IMP-51."""

    def test_import_reunion_todos_ausentes(self, client, auth_headers, jugadores_seed):
        csv = _csv_bytes(["Ana", "Beto"], [[0, 0]])
        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 422, r.text
        detail = r.json()["detail"]
        assert detail["code"] == "reunion_todos_ausentes"
        assert detail["fila"] == 1


# ---------------------------------------------------------------------------
# T-IMP-52 — SCN-IMP-12: rollback on mid-import failure
# ---------------------------------------------------------------------------

class TestImportRollbackTotal:
    """T-IMP-52."""

    def test_import_rollback_total_si_falla_a_mitad(self, client, auth_headers, jugadores_seed, db):
        # 6 data rows: rows 1-4 valid, row 5 has "?" for Ana
        rows = [
            [15, 14],
            [15, 14],
            [14, 13],
            [13, 12],
            # row 5: invalid
        ]
        lines = ["Ana;Beto"]
        for r_vals in rows:
            lines.append(";".join(str(v) for v in r_vals))
        lines.append("?;14")  # row 5 — invalid
        lines.append("13;12")  # row 6 — valid
        csv = "\n".join(lines).encode("utf-8")

        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 422, r.text

        # DB must be clean — zero records from this import
        assert db.query(Temporada).count() == 0
        assert db.query(Inscripcion).count() == 0
        assert db.query(Reunion).count() == 0
        assert db.query(Posicion).count() == 0


# ---------------------------------------------------------------------------
# T-IMP-53 — SCN-IMP-06: champion not in headers
# ---------------------------------------------------------------------------

class TestImportCampeonNoInscripto:
    """T-IMP-53."""

    def test_import_con_campeon_no_inscripto(self, client, auth_headers, jugadores_seed, db):
        csv = _csv_bytes(["Ana", "Beto"], [[15, 14]])
        r = _post_import(client, auth_headers, csv, campeon_nombre="Carlos")
        assert r.status_code == 422, r.text
        assert r.json()["detail"]["code"] == "campeon_no_inscripto"

        # No records created
        assert db.query(Temporada).count() == 0
        assert db.query(Inscripcion).count() == 0
        assert db.query(Reunion).count() == 0
        assert db.query(Posicion).count() == 0


# ---------------------------------------------------------------------------
# T-IMP-54 — SCN-IMP-13: active season present, import does not interfere
# ---------------------------------------------------------------------------

class TestImportConTemporadaActivaPrevia:
    """T-IMP-54."""

    def test_import_con_temporada_activa_previa_no_la_modifica(
        self, client, auth_headers, jugadores_seed, temporada_activa_previa, db
    ):
        csv = _csv_bytes(["Ana", "Beto"], [[15, 14]])
        r = _post_import(client, auth_headers, csv, nombre="Historica 2020", fecha="2020-01-01")
        assert r.status_code == 201, r.text

        body = r.json()
        assert body["estado"] == "cerrada"

        # Active season must remain unchanged
        activa = db.query(Temporada).filter(
            Temporada.estado == EstadoTemporada.activa
        ).first()
        assert activa is not None
        assert activa.nombre == "Liga Activa"


# ---------------------------------------------------------------------------
# T-IMP-55 — SCN-IMP-17: duplicate scores in a row
# ---------------------------------------------------------------------------

class TestImportPuntajesDuplicados:
    """T-IMP-55."""

    def test_import_puntajes_duplicados_en_fila(self, client, auth_headers, jugadores_seed):
        # Ana=15, Beto=15 in same row
        csv = _csv_bytes(["Ana", "Beto"], [[15, 15]])
        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 422, r.text
        detail = r.json()["detail"]
        assert detail["code"] == "puntajes_duplicados"
        assert "fila" in detail
        assert detail["fila"] == 1
        assert "valor" in detail
        assert detail["valor"] == 15


# ---------------------------------------------------------------------------
# T-IMP-56 — SCN-IMP-16: case-insensitive player matching
# ---------------------------------------------------------------------------

class TestImportMatchJugadorCaseInsensitive:
    """T-IMP-56."""

    def test_import_match_jugador_case_insensitive(self, client, auth_headers, jugadores_seed, db):
        # Jugador "Ana" in DB; CSV header is "ana" (lowercase)
        csv = _csv_bytes(["ana", "Beto"], [[15, 14]])
        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 201, r.text

        # Inscription links to the correct jugador
        t_id = r.json()["id"]
        inscripciones = db.query(Inscripcion).filter(Inscripcion.id_temporada == t_id).all()
        assert len(inscripciones) == 2

        # The "ana" header should have resolved to jugador "Ana" (id=jugadores_seed[0].id)
        ana_id = jugadores_seed[0].id
        inscribed_ids = {i.id_jugador for i in inscripciones}
        assert ana_id in inscribed_ids


# ---------------------------------------------------------------------------
# T-IMP-57 — SCN-IMP-15: non-UTF-8 file → 422 csv_encoding_invalid
# ---------------------------------------------------------------------------

class TestImportCsvNoUtf8:
    """T-IMP-57."""

    def test_import_csv_no_utf8_devuelve_422(self, client, auth_headers, jugadores_seed):
        # Bytes with invalid UTF-8 sequence
        invalid_bytes = b"\xff\xfe Ana;Beto\n15;14\n"
        r = _post_import(client, auth_headers, invalid_bytes)
        assert r.status_code == 422, r.text
        assert r.json()["detail"]["code"] == "csv_encoding_invalid"


# ---------------------------------------------------------------------------
# T-IMP-58 — response shape includes resumen_import
# ---------------------------------------------------------------------------

class TestImportResponseShape:
    """T-IMP-58."""

    def test_import_response_shape_incluye_resumen_import(self, client, auth_headers, jugadores_seed):
        csv = _csv_bytes(["Ana", "Beto"], [[15, 14], [15, 14]])
        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 201, r.text
        body = r.json()

        # Top-level fields
        assert "id" in body
        assert "nombre" in body
        assert "fecha_inicio" in body
        assert "estado" in body
        assert "campeon_id" in body

        # Nested resumen_import
        assert "resumen_import" in body
        ri = body["resumen_import"]
        assert "jugadores_inscriptos" in ri
        assert "reuniones_creadas" in ri
        assert "posiciones_creadas" in ri
        assert "invitados_inferidos" in ri

        assert ri["jugadores_inscriptos"] > 0
        assert ri["reuniones_creadas"] > 0
        assert ri["posiciones_creadas"] > 0


# ---------------------------------------------------------------------------
# T-IMP-59 — reuniones created with fecha=NULL
# ---------------------------------------------------------------------------

class TestImportReunionFechaNula:
    """T-IMP-59."""

    def test_import_reunion_creada_con_fecha_null(self, client, auth_headers, jugadores_seed, db):
        csv = _csv_bytes(["Ana", "Beto"], [[15, 14], [15, 14]])
        r = _post_import(client, auth_headers, csv)
        assert r.status_code == 201, r.text

        t_id = r.json()["id"]
        reuniones = db.query(Reunion).filter(Reunion.id_temporada == t_id).all()
        assert len(reuniones) > 0
        for reu in reuniones:
            assert reu.fecha is None
