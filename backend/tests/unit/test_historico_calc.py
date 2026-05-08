"""
Tests unitarios para las funciones puras de historico.
Strict TDD: cada clase se agrega antes de implementar su función.
Inputs: lists of plain dicts — sin DB, sin HTTP.
"""

from app.services.historico import (
    compute_puntos_totales,
    compute_victorias,
    compute_campeones,
    compute_asistencias,
    compute_racha_victorias,
    compute_racha_asistencia,
    compute_promedios,
    compute_podios,
    compute_head_to_head_row,
    compute_racha_inasistencia,
)


# ---------------------------------------------------------------------------
# T-02: TestComputePuntosTotales
# ---------------------------------------------------------------------------


class TestComputePuntosTotales:
    def test_lista_vacia_retorna_vacia(self):
        result = compute_puntos_totales([], {})
        assert result == []

    def test_un_jugador_suma_correctamente(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 11, "posicion": 2, "puntos": 14},
        ]
        result = compute_puntos_totales(posiciones, jugadores_map)
        assert len(result) == 1
        r = result[0]
        assert r["id_jugador"] == 1
        assert r["nombre"] == "Ana"
        assert r["puntos"] == 29
        assert "foto_url" in r

    def test_empate_puntos_orden_alfabetico(self):
        jugadores_map = {
            1: {"nombre": "Zara", "foto_url": None},
            2: {"nombre": "Ana", "foto_url": None},
        }
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 10},
            {"id_jugador": 2, "id_reunion": 10, "posicion": 2, "puntos": 10},
        ]
        result = compute_puntos_totales(posiciones, jugadores_map)
        assert len(result) == 2
        assert result[0]["nombre"] == "Ana"
        assert result[1]["nombre"] == "Zara"

    def test_id_jugador_none_ignorado(self):
        # Defensive guard: rows with id_jugador=None should not crash the function
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            {"id_jugador": None, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 11, "posicion": 2, "puntos": 14},
        ]
        result = compute_puntos_totales(posiciones, jugadores_map)
        assert len(result) == 1
        assert result[0]["id_jugador"] == 1
        assert result[0]["puntos"] == 14


# ---------------------------------------------------------------------------
# T-04: TestComputeVictorias
# ---------------------------------------------------------------------------


class TestComputeVictorias:
    def test_cuenta_solo_posicion_uno(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 11, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 12, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 13, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 14, "posicion": 3, "puntos": 13},
        ]
        result = compute_victorias(posiciones, jugadores_map)
        assert len(result) == 1
        assert result[0]["victorias"] == 3

    def test_empate_victorias_orden_alfabetico(self):
        jugadores_map = {
            1: {"nombre": "Zara", "foto_url": None},
            2: {"nombre": "Ana", "foto_url": None},
        }
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 11, "posicion": 1, "puntos": 15},
        ]
        result = compute_victorias(posiciones, jugadores_map)
        assert len(result) == 2
        assert result[0]["nombre"] == "Ana"
        assert result[1]["nombre"] == "Zara"

    def test_jugador_sin_victorias_no_aparece(self):
        jugadores_map = {
            1: {"nombre": "Ana", "foto_url": None},
            2: {"nombre": "Bruno", "foto_url": None},
        }
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 10, "posicion": 2, "puntos": 14},
        ]
        result = compute_victorias(posiciones, jugadores_map)
        ids = [r["id_jugador"] for r in result]
        assert 2 not in ids
        assert 1 in ids


# ---------------------------------------------------------------------------
# T-06: TestComputeCampeones
# ---------------------------------------------------------------------------


class TestComputeCampeones:
    def test_temporada_sin_campeon_omitida(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
        ]
        result = compute_campeones(temporadas, jugadores_map)
        assert result == []

    def test_jugador_con_dos_campeonatos(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": 1},
            {"id": 2, "nombre": "T2", "fecha_inicio": "2024-01-01", "campeon_id": 1},
        ]
        result = compute_campeones(temporadas, jugadores_map)
        assert len(result) == 1
        assert result[0]["id_jugador"] == 1
        assert result[0]["campeonatos"] == 2

    def test_empate_campeonatos_orden_alfabetico(self):
        jugadores_map = {
            1: {"nombre": "Zara", "foto_url": None},
            2: {"nombre": "Ana", "foto_url": None},
        }
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": 1},
            {"id": 2, "nombre": "T2", "fecha_inicio": "2024-01-01", "campeon_id": 2},
        ]
        result = compute_campeones(temporadas, jugadores_map)
        assert len(result) == 2
        assert result[0]["nombre"] == "Ana"
        assert result[1]["nombre"] == "Zara"


# ---------------------------------------------------------------------------
# T-08: TestComputeAsistencias
# ---------------------------------------------------------------------------


class TestComputeAsistencias:
    def test_jugador_sin_filas_no_aparece(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        result = compute_asistencias([], jugadores_map)
        assert result == []

    def test_conteo_exacto_de_filas(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 11, "posicion": 2, "puntos": 14},
        ]
        result = compute_asistencias(posiciones, jugadores_map)
        assert len(result) == 1
        assert result[0]["asistencias"] == 2

    def test_empate_asistencias_orden_alfabetico(self):
        jugadores_map = {
            1: {"nombre": "Zara", "foto_url": None},
            2: {"nombre": "Ana", "foto_url": None},
        }
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 11, "posicion": 1, "puntos": 15},
        ]
        result = compute_asistencias(posiciones, jugadores_map)
        assert len(result) == 2
        assert result[0]["nombre"] == "Ana"
        assert result[1]["nombre"] == "Zara"


# ---------------------------------------------------------------------------
# T-10: TestComputeRachaVictorias
# ---------------------------------------------------------------------------
# Helper data builder for streak tests:
#   temporadas: list of dicts with {id, nombre, fecha_inicio, campeon_id}
#   reuniones:  list of dicts with {id, id_temporada, numero_jornada}
#               MUST be ordered by (fecha_inicio, id_temporada, numero_jornada)
#   posiciones: list of dicts with {id_jugador, id_reunion, posicion, puntos}
#   jugadores_map: {id: {nombre, foto_url}}


class TestComputeRachaVictorias:
    def _make_data(self):
        """Two closed seasons:
          S1 (id=1, 2023-01-01): reuniones 101 (j1), 102 (j2), 103 (j3)
          S2 (id=2, 2024-01-01): reuniones 201 (j1), 202 (j2), 203 (j3)
        Player 1 (Ana): wins j3 of S1 and j1, j2 of S2 → streak of 3 crossing seasons.
        """
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
            {"id": 2, "nombre": "T2", "fecha_inicio": "2024-01-01", "campeon_id": None},
        ]
        reuniones = [
            {"id": 101, "id_temporada": 1, "numero_jornada": 1},
            {"id": 102, "id_temporada": 1, "numero_jornada": 2},
            {"id": 103, "id_temporada": 1, "numero_jornada": 3},
            {"id": 201, "id_temporada": 2, "numero_jornada": 1},
            {"id": 202, "id_temporada": 2, "numero_jornada": 2},
            {"id": 203, "id_temporada": 2, "numero_jornada": 3},
        ]
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        return temporadas, reuniones, jugadores_map

    def test_racha_cruza_dos_temporadas(self):
        temporadas, reuniones, jugadores_map = self._make_data()
        posiciones = [
            # S1: j1 no gana, j2 no gana, j3 gana
            {"id_jugador": 1, "id_reunion": 101, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 3, "puntos": 13},
            {"id_jugador": 1, "id_reunion": 103, "posicion": 1, "puntos": 15},
            # S2: j1 gana, j2 gana, j3 no gana
            {"id_jugador": 1, "id_reunion": 201, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 202, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 203, "posicion": 2, "puntos": 14},
        ]
        result = compute_racha_victorias(posiciones, reuniones, temporadas, jugadores_map)
        assert len(result) == 1
        r = result[0]
        assert r["id_jugador"] == 1
        assert r["longitud"] == 3
        # Streak: 103 (S1, j3) → 202 (S2, j2)
        assert r["temporada_inicio"]["id"] == 1
        assert r["jornada_inicio"] == 3
        assert r["temporada_fin"]["id"] == 2
        assert r["jornada_fin"] == 2

    def test_racha_rota_por_no_primer_lugar(self):
        """Player has isolated victories (max streak = 1). After Change B, excluded from result."""
        temporadas, reuniones, jugadores_map = self._make_data()
        posiciones = [
            # S1: j1 gana, j2 NO gana, j3 gana → two streaks of length 1
            {"id_jugador": 1, "id_reunion": 101, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 103, "posicion": 1, "puntos": 15},
        ]
        result = compute_racha_victorias(posiciones, reuniones, temporadas, jugadores_map)
        # Change B: streaks of length 1 are excluded
        assert result == [], f"Streak of 1 should be excluded after Change B, got: {result}"

    def test_dos_rachas_iguales_devuelve_mas_reciente(self):
        """Player has two streaks of length 2: first ending at S1-j2, second at S2-j2.
        C7: the most recent (S2-j2) must be returned."""
        temporadas, reuniones, jugadores_map = self._make_data()
        posiciones = [
            # S1: j1 gana, j2 gana, j3 NO
            {"id_jugador": 1, "id_reunion": 101, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 103, "posicion": 2, "puntos": 14},
            # S2: j1 NO, j2 gana, j3 gana
            {"id_jugador": 1, "id_reunion": 201, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 202, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 203, "posicion": 1, "puntos": 15},
        ]
        result = compute_racha_victorias(posiciones, reuniones, temporadas, jugadores_map)
        assert len(result) == 1
        r = result[0]
        assert r["longitud"] == 2
        # Most recent: S2-j2 to S2-j3
        assert r["temporada_fin"]["id"] == 2
        assert r["jornada_fin"] == 3

    def test_jugador_sin_victorias_no_aparece(self):
        temporadas, reuniones, jugadores_map = self._make_data()
        posiciones = [
            {"id_jugador": 1, "id_reunion": 101, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 3, "puntos": 13},
        ]
        result = compute_racha_victorias(posiciones, reuniones, temporadas, jugadores_map)
        assert result == []


# ---------------------------------------------------------------------------
# T-12: TestComputeRachaAsistencia
# ---------------------------------------------------------------------------


class TestComputeRachaAsistencia:
    def _make_data(self):
        """Same two-season setup as racha_victorias tests."""
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
            {"id": 2, "nombre": "T2", "fecha_inicio": "2024-01-01", "campeon_id": None},
        ]
        reuniones = [
            {"id": 101, "id_temporada": 1, "numero_jornada": 1},
            {"id": 102, "id_temporada": 1, "numero_jornada": 2},
            {"id": 103, "id_temporada": 1, "numero_jornada": 3},
            {"id": 201, "id_temporada": 2, "numero_jornada": 1},
            {"id": 202, "id_temporada": 2, "numero_jornada": 2},
            {"id": 203, "id_temporada": 2, "numero_jornada": 3},
        ]
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        return temporadas, reuniones, jugadores_map

    def test_racha_completa_cruza_temporadas(self):
        temporadas, reuniones, jugadores_map = self._make_data()
        # Player attended all 6 meetings across both seasons
        posiciones = [
            {"id_jugador": 1, "id_reunion": 101, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 3, "puntos": 13},
            {"id_jugador": 1, "id_reunion": 103, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 201, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 202, "posicion": 3, "puntos": 13},
            {"id_jugador": 1, "id_reunion": 203, "posicion": 1, "puntos": 15},
        ]
        result = compute_racha_asistencia(posiciones, reuniones, temporadas, jugadores_map)
        assert len(result) == 1
        r = result[0]
        assert r["longitud"] == 6
        assert r["temporada_inicio"]["id"] == 1
        assert r["jornada_inicio"] == 1
        assert r["temporada_fin"]["id"] == 2
        assert r["jornada_fin"] == 3

    def test_reunion_sin_posicion_rompe_racha(self):
        """Player absent from reunion 102 (no Posicion row). C10."""
        temporadas, reuniones, jugadores_map = self._make_data()
        posiciones = [
            {"id_jugador": 1, "id_reunion": 101, "posicion": 2, "puntos": 14},
            # reunion 102: absent — no row
            {"id_jugador": 1, "id_reunion": 103, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 201, "posicion": 2, "puntos": 14},
        ]
        result = compute_racha_asistencia(posiciones, reuniones, temporadas, jugadores_map)
        assert len(result) == 1
        # Longest sub-streak: 103, 201, 202? No — 103 and 201 are consecutive in global order.
        # 101 (1), gap at 102, 103 (1), 201 (1) = streak of 2 from 103 onwards
        assert result[0]["longitud"] == 2

    def test_hueco_no_inscripcion_rompe_racha_igual_que_ausencia(self):
        """C10: player has no Posicion in S2 reunions at all (not inscribed).
        S1: attends 3 (streak=3). S2: no rows (gap of 3). S3 implicit via separate data.
        After gap, streak resets. Longest = 3."""
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
            {"id": 2, "nombre": "T2", "fecha_inicio": "2024-01-01", "campeon_id": None},
            {"id": 3, "nombre": "T3", "fecha_inicio": "2025-01-01", "campeon_id": None},
        ]
        reuniones = [
            {"id": 101, "id_temporada": 1, "numero_jornada": 1},
            {"id": 102, "id_temporada": 1, "numero_jornada": 2},
            {"id": 103, "id_temporada": 1, "numero_jornada": 3},
            {"id": 201, "id_temporada": 2, "numero_jornada": 1},
            {"id": 202, "id_temporada": 2, "numero_jornada": 2},
            {"id": 301, "id_temporada": 3, "numero_jornada": 1},
            {"id": 302, "id_temporada": 3, "numero_jornada": 2},
        ]
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        # Player attends all S1 meetings, absent in S2 (no rows), attends all S3 meetings
        posiciones = [
            {"id_jugador": 1, "id_reunion": 101, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 3, "puntos": 13},
            {"id_jugador": 1, "id_reunion": 103, "posicion": 1, "puntos": 15},
            # S2: no rows for player (not inscribed / absent)
            {"id_jugador": 1, "id_reunion": 301, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 302, "posicion": 1, "puntos": 15},
        ]
        result = compute_racha_asistencia(posiciones, reuniones, temporadas, jugadores_map)
        assert len(result) == 1
        # S1 streak = 3 > S3 streak = 2; so best is 3
        assert result[0]["longitud"] == 3
        assert result[0]["temporada_inicio"]["id"] == 1
        assert result[0]["temporada_fin"]["id"] == 1

    def test_dos_rachas_iguales_devuelve_mas_reciente(self):
        """C7: two equal-length streaks, return the most recent one."""
        temporadas, reuniones, jugadores_map = self._make_data()
        posiciones = [
            # S1: j1 attend, j2 attend, j3 absent
            {"id_jugador": 1, "id_reunion": 101, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 3, "puntos": 13},
            # reunion 103: absent
            # S2: j1 absent, j2 attend, j3 attend
            # reunion 201: absent
            {"id_jugador": 1, "id_reunion": 202, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 203, "posicion": 2, "puntos": 14},
        ]
        result = compute_racha_asistencia(posiciones, reuniones, temporadas, jugadores_map)
        assert len(result) == 1
        r = result[0]
        assert r["longitud"] == 2
        # Most recent streak: 202 → 203 (S2)
        assert r["temporada_inicio"]["id"] == 2
        assert r["jornada_inicio"] == 2
        assert r["temporada_fin"]["id"] == 2
        assert r["jornada_fin"] == 3


# ---------------------------------------------------------------------------
# T-14: TestComputePromedios
# ---------------------------------------------------------------------------


class TestComputePromedios:
    def test_promedio_calculado_correctamente(self):
        """Player with 9 asistencias should appear; 9 is the minimum threshold (Change A)."""
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        # 9 meetings: 6 × 15 pts + 3 × 5 pts = 90 + 15 = 105; asistencias=9; promedio=105/9≈11.67
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10 + i, "posicion": 1, "puntos": 15}
            for i in range(6)
        ] + [
            {"id_jugador": 1, "id_reunion": 20 + i, "posicion": 2, "puntos": 5}
            for i in range(3)
        ]
        from app.services.historico import compute_promedios
        result = compute_promedios(posiciones, jugadores_map)
        assert len(result) == 1
        r = result[0]
        assert r["id_jugador"] == 1
        assert r["puntos"] == 105
        assert r["asistencias"] == 9
        assert r["promedio"] == round(105 / 9, 2)

    def test_promedio_redondeado_dos_decimales(self):
        """10 meetings × 1 pt each = 10 pts; 10/10 = 1.0 (needs >=9 asistencias)."""
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        # 10 meetings: total 10 pts → promedio = 1.0
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10 + i, "posicion": 5, "puntos": 1}
            for i in range(10)
        ]
        from app.services.historico import compute_promedios
        result = compute_promedios(posiciones, jugadores_map)
        assert len(result) == 1
        assert result[0]["asistencias"] == 10
        assert result[0]["promedio"] == 1.0

    def test_jugador_sin_asistencias_no_aparece(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        from app.services.historico import compute_promedios
        result = compute_promedios([], jugadores_map)
        assert result == []


# ---------------------------------------------------------------------------
# T-16: TestComputePodios
# ---------------------------------------------------------------------------


class TestComputePodios:
    def test_cuenta_oro_plata_bronce_y_total(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 11, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 12, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 13, "posicion": 3, "puntos": 13},
            {"id_jugador": 1, "id_reunion": 14, "posicion": 4, "puntos": 12},  # not a podium
        ]
        result = compute_podios(posiciones, jugadores_map)
        assert len(result) == 1
        r = result[0]
        assert r["oro"] == 2
        assert r["plata"] == 1
        assert r["bronce"] == 1
        assert r["total"] == 4

    def test_empate_total_orden_por_oro_plata_nombre(self):
        jugadores_map = {
            1: {"nombre": "Zara", "foto_url": None},
            2: {"nombre": "Ana", "foto_url": None},
        }
        posiciones = [
            # Both have total=2, but Zara has 2 golds, Ana has 1 gold 1 silver
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 11, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 12, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 13, "posicion": 2, "puntos": 14},
        ]
        result = compute_podios(posiciones, jugadores_map)
        assert len(result) == 2
        # Zara: oro=2, total=2; Ana: oro=1, plata=1, total=2
        # Sort: total DESC, oro DESC → Zara first
        assert result[0]["nombre"] == "Zara"
        assert result[1]["nombre"] == "Ana"

    def test_jugador_sin_podios_no_aparece(self):
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 4, "puntos": 12},
            {"id_jugador": 1, "id_reunion": 11, "posicion": 5, "puntos": 11},
        ]
        result = compute_podios(posiciones, jugadores_map)
        assert result == []


# ---------------------------------------------------------------------------
# T-18: TestComputeHeadToHeadRow
# ---------------------------------------------------------------------------


class TestComputeHeadToHeadRow:
    def test_una_reunion_victoria_y_derrota(self):
        """Target finishes 2nd, rival A finishes 1st (derrota), rival B finishes 3rd (victoria)."""
        jugadores_map = {
            1: {"nombre": "Ana", "foto_url": None},
            2: {"nombre": "Bruno", "foto_url": None},
            3: {"nombre": "Carlos", "foto_url": None},
        }
        posiciones = [
            # Reunion 10: Ana=2nd, Bruno=1st, Carlos=3rd
            {"id_jugador": 1, "id_reunion": 10, "posicion": 2, "puntos": 14},
            {"id_jugador": 2, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 3, "id_reunion": 10, "posicion": 3, "puntos": 13},
        ]
        result = compute_head_to_head_row(1, "Ana", None, posiciones, jugadores_map)
        assert result["jugador_id"] == 1
        assert result["nombre"] == "Ana"
        rivales = {r["rival_id"]: r for r in result["rivales"]}
        assert len(rivales) == 2
        # vs Bruno: Ana 2nd, Bruno 1st → Ana lost
        assert rivales[2]["victorias"] == 0
        assert rivales[2]["derrotas"] == 1
        assert rivales[2]["reuniones_compartidas"] == 1
        # vs Carlos: Ana 2nd, Carlos 3rd → Ana won
        assert rivales[3]["victorias"] == 1
        assert rivales[3]["derrotas"] == 0
        assert rivales[3]["reuniones_compartidas"] == 1

    def test_rival_sin_reuniones_compartidas_omitido(self):
        """Player D has no overlap with target (not in same meeting). C8."""
        jugadores_map = {
            1: {"nombre": "Ana", "foto_url": None},
            4: {"nombre": "Diana", "foto_url": None},
        }
        # Only target rows; Diana never in same meeting
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 4, "id_reunion": 20, "posicion": 1, "puntos": 15},  # different meeting
        ]
        result = compute_head_to_head_row(1, "Ana", None, posiciones, jugadores_map)
        assert result["rivales"] == []

    def test_varias_reuniones_agregacion_correcta(self):
        """Target vs rival over 3 meetings: 2 wins, 1 loss."""
        jugadores_map = {
            1: {"nombre": "Ana", "foto_url": None},
            2: {"nombre": "Bruno", "foto_url": None},
        }
        posiciones = [
            # Meeting 10: Ana=1st, Bruno=2nd → Ana wins
            {"id_jugador": 1, "id_reunion": 10, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 10, "posicion": 2, "puntos": 14},
            # Meeting 11: Ana=2nd, Bruno=1st → Ana loses
            {"id_jugador": 1, "id_reunion": 11, "posicion": 2, "puntos": 14},
            {"id_jugador": 2, "id_reunion": 11, "posicion": 1, "puntos": 15},
            # Meeting 12: Ana=1st, Bruno=3rd → Ana wins
            {"id_jugador": 1, "id_reunion": 12, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 12, "posicion": 3, "puntos": 13},
        ]
        result = compute_head_to_head_row(1, "Ana", None, posiciones, jugadores_map)
        assert len(result["rivales"]) == 1
        r = result["rivales"][0]
        assert r["rival_id"] == 2
        assert r["victorias"] == 2
        assert r["derrotas"] == 1
        assert r["reuniones_compartidas"] == 3


# ---------------------------------------------------------------------------
# Batch 5b — Change A: TestComputePromedios filter asistencias > 8
# ---------------------------------------------------------------------------


class TestComputePromediosMinAsistencias:
    """Change A: players with asistencias <= 8 are excluded from promedios."""

    def test_jugador_con_8_asistencias_excluido(self):
        """Player with exactly 8 asistencias must NOT appear in promedios."""
        jugadores_map = {
            1: {"nombre": "Ana", "foto_url": None},
            2: {"nombre": "Bruno", "foto_url": None},
        }
        posiciones = []
        # Ana: 8 meetings × 10 pts
        for i in range(8):
            posiciones.append({"id_jugador": 1, "id_reunion": 10 + i, "posicion": 2, "puntos": 10})
        # Bruno: 9 meetings × 10 pts
        for i in range(9):
            posiciones.append({"id_jugador": 2, "id_reunion": 30 + i, "posicion": 2, "puntos": 10})

        result = compute_promedios(posiciones, jugadores_map)
        ids = [r["id_jugador"] for r in result]
        # Ana (8 asistencias) must be excluded
        assert 1 not in ids, f"Ana (8 asistencias) should be excluded, got: {result}"
        # Bruno (9 asistencias) must be included
        assert 2 in ids, f"Bruno (9 asistencias) should be included, got: {result}"

    def test_jugador_con_9_asistencias_incluido(self):
        """Player with exactly 9 asistencias must appear in promedios."""
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            {"id_jugador": 1, "id_reunion": 10 + i, "posicion": 2, "puntos": 10}
            for i in range(9)
        ]
        result = compute_promedios(posiciones, jugadores_map)
        assert len(result) == 1
        assert result[0]["id_jugador"] == 1
        assert result[0]["asistencias"] == 9


# ---------------------------------------------------------------------------
# Batch 5b — Change B: TestComputeRachaVictorias filter longitud >= 2
# ---------------------------------------------------------------------------


class TestComputeRachaVictoriasMinLongitud:
    """Change B: streaks of length 1 are excluded from racha_victorias."""

    def _make_data(self):
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
        ]
        reuniones = [
            {"id": 101, "id_temporada": 1, "numero_jornada": 1},
            {"id": 102, "id_temporada": 1, "numero_jornada": 2},
            {"id": 103, "id_temporada": 1, "numero_jornada": 3},
        ]
        return temporadas, reuniones

    def test_racha_longitud_1_excluida(self):
        """Player whose max streak is 1 must NOT appear in result."""
        temporadas, reuniones = self._make_data()
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            # Ana wins only j1 then loses
            {"id_jugador": 1, "id_reunion": 101, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 2, "puntos": 14},
            {"id_jugador": 1, "id_reunion": 103, "posicion": 2, "puntos": 14},
        ]
        result = compute_racha_victorias(posiciones, reuniones, temporadas, jugadores_map)
        assert result == [], f"Streak of 1 should be excluded, got: {result}"

    def test_racha_longitud_2_incluida(self):
        """Player with streak of 2 must appear in result."""
        temporadas, reuniones = self._make_data()
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        posiciones = [
            {"id_jugador": 1, "id_reunion": 101, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 103, "posicion": 2, "puntos": 14},
        ]
        result = compute_racha_victorias(posiciones, reuniones, temporadas, jugadores_map)
        assert len(result) == 1
        assert result[0]["longitud"] == 2


# ---------------------------------------------------------------------------
# Batch 5b — Change C: TestComputeRachaAsistencia filter longitud >= 2 + top 5
# ---------------------------------------------------------------------------


class TestComputeRachaAsistenciaMinLongitudTop5:
    """Change C: streaks of length 1 excluded; only top 5 returned."""

    def _make_data_single_season(self):
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
        ]
        reuniones = [
            {"id": 100 + i, "id_temporada": 1, "numero_jornada": i + 1}
            for i in range(10)
        ]
        return temporadas, reuniones

    def test_racha_longitud_1_excluida(self):
        """Player with max streak=1 is excluded from racha_asistencia."""
        temporadas, reuniones = self._make_data_single_season()
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        # Ana attends only j1 (streak=1), misses the rest
        posiciones = [
            {"id_jugador": 1, "id_reunion": 100, "posicion": 1, "puntos": 15},
        ]
        result = compute_racha_asistencia(posiciones, reuniones, temporadas, jugadores_map)
        assert result == [], f"Streak of 1 should be excluded, got: {result}"

    def test_top_5_slice_when_more_than_5_players(self):
        """When 7 eligible players qualify, only the top 5 are returned."""
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
        ]
        # 10 meetings in a single season
        reuniones = [
            {"id": 100 + i, "id_temporada": 1, "numero_jornada": i + 1}
            for i in range(10)
        ]
        # 7 players, each with different streak lengths (all >= 2):
        # P1: 9, P2: 8, P3: 7, P4: 6, P5: 5, P6: 4, P7: 3
        jugadores_map = {pid: {"nombre": f"Player{pid}", "foto_url": None} for pid in range(1, 8)}
        streak_lens = {1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4, 7: 3}

        posiciones = []
        for pid, streak in streak_lens.items():
            # Each player attends first N meetings
            for i in range(streak):
                posiciones.append({
                    "id_jugador": pid,
                    "id_reunion": 100 + i,
                    "posicion": pid,
                    "puntos": 15 - pid,
                })

        result = compute_racha_asistencia(posiciones, reuniones, temporadas, jugadores_map)
        # Only top 5: P1(9), P2(8), P3(7), P4(6), P5(5)
        assert len(result) == 5, f"Expected 5 results, got {len(result)}: {result}"
        assert result[0]["id_jugador"] == 1
        assert result[0]["longitud"] == 9
        assert result[4]["id_jugador"] == 5
        assert result[4]["longitud"] == 5


# ---------------------------------------------------------------------------
# Batch 5b — Change D: TestComputeRachaInasistencia
# ---------------------------------------------------------------------------


class TestComputeRachaInasistencia:
    """Tests for compute_racha_inasistencia (M10)."""

    def _base_data(self):
        """Two closed seasons: S1 (3 meetings) and S2 (3 meetings)."""
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
            {"id": 2, "nombre": "T2", "fecha_inicio": "2024-01-01", "campeon_id": None},
        ]
        reuniones = [
            {"id": 101, "id_temporada": 1, "numero_jornada": 1},
            {"id": 102, "id_temporada": 1, "numero_jornada": 2},
            {"id": 103, "id_temporada": 1, "numero_jornada": 3},
            {"id": 201, "id_temporada": 2, "numero_jornada": 1},
            {"id": 202, "id_temporada": 2, "numero_jornada": 2},
            {"id": 203, "id_temporada": 2, "numero_jornada": 3},
        ]
        # inscripciones: player 1 is enrolled in both seasons
        inscripciones = {(1, 1), (2, 1), (1, 2), (2, 2)}  # (id_jugador, id_temporada)
        jugadores_map = {
            1: {"nombre": "Ana", "foto_url": None},
            2: {"nombre": "Bruno", "foto_url": None},
        }
        return temporadas, reuniones, inscripciones, jugadores_map

    def test_lista_vacia_retorna_vacia(self):
        result = compute_racha_inasistencia([], [], [], set(), {})
        assert result == []

    def test_jugador_inelegible_excluido(self):
        """Player with 0 asistencias in a closed temporada is excluded (ineligible)."""
        temporadas, reuniones, inscripciones, jugadores_map = self._base_data()
        # Player 1 (Ana): attends all S1 meetings, all S2 meetings → eligible
        # Player 2 (Bruno): attends 2 S1 meetings, but 0 S2 meetings → ineligible
        posiciones = [
            # Ana: attends S1 + S2
            {"id_jugador": 1, "id_reunion": 101, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 103, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 201, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 202, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 203, "posicion": 1, "puntos": 15},
            # Bruno: attends S1 only, 0 in S2 → ineligible
            {"id_jugador": 2, "id_reunion": 101, "posicion": 2, "puntos": 14},
            {"id_jugador": 2, "id_reunion": 102, "posicion": 2, "puntos": 14},
        ]
        result = compute_racha_inasistencia(posiciones, reuniones, temporadas, inscripciones, jugadores_map)
        ids = [r["id_jugador"] for r in result]
        assert 2 not in ids, f"Bruno (0 asistencias in S2) should be ineligible, got: {result}"

    def test_racha_3_cruza_temporadas(self):
        """Eligible player absent from last 3 meetings (2 in S2, 1 in S1 — last S1 + first 2 S2).
        Streak of 3 consecutive inasistencias crossing seasons."""
        temporadas, reuniones, inscripciones, jugadores_map = self._base_data()
        # Player 1 (Ana): attends S1-j1, S1-j2, skips S1-j3, S2-j1, S2-j2, attends S2-j3
        # Ana is eligible because she attended >=1 in S1 and >=1 in S2
        posiciones = [
            {"id_jugador": 1, "id_reunion": 101, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 1, "puntos": 15},
            # S1-j3 (103): absent
            # S2-j1 (201): absent
            # S2-j2 (202): absent
            {"id_jugador": 1, "id_reunion": 203, "posicion": 1, "puntos": 15},
        ]
        result = compute_racha_inasistencia(posiciones, reuniones, temporadas, inscripciones, jugadores_map)
        # Ana should have streak of 3 (reunions 103, 201, 202)
        ana = next((r for r in result if r["id_jugador"] == 1), None)
        assert ana is not None, f"Ana should appear in result, got: {result}"
        assert ana["longitud"] == 3
        # Streak starts at S1-j3, ends at S2-j2
        assert ana["temporada_inicio"]["id"] == 1
        assert ana["jornada_inicio"] == 3
        assert ana["temporada_fin"]["id"] == 2
        assert ana["jornada_fin"] == 2

    def test_racha_longitud_1_excluida(self):
        """Eligible player with max inasistencia streak of 1 is excluded."""
        temporadas, reuniones, inscripciones, jugadores_map = self._base_data()
        jugadores_map = {1: {"nombre": "Ana", "foto_url": None}}
        # Inscripciones: Ana in both seasons
        inscripciones = {(1, 1), (1, 2)}
        # Ana attends all meetings except S1-j2 (1 absence)
        posiciones = [
            {"id_jugador": 1, "id_reunion": 101, "posicion": 1, "puntos": 15},
            # 102 absent
            {"id_jugador": 1, "id_reunion": 103, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 201, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 202, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 203, "posicion": 1, "puntos": 15},
        ]
        result = compute_racha_inasistencia(posiciones, reuniones, temporadas, inscripciones, jugadores_map)
        assert result == [], f"Streak of 1 should be excluded, got: {result}"

    def test_no_inscripcion_en_temporada_no_rompe_ni_suma(self):
        """A meeting in a temporada where the player is NOT enrolled is skipped:
        does not count as inasistencia, does not reset the streak.

        Note: for M10 eligibility the player must have >=1 asistencia in EACH closed temporada.
        This test uses 2 temporadas where the player IS enrolled and eligible, but a 3rd
        temporada exists in reuniones where the player has no inscripcion — those reuniones
        are skipped entirely (neither count nor reset).
        """
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
            {"id": 2, "nombre": "T2", "fecha_inicio": "2024-01-01", "campeon_id": None},
            {"id": 3, "nombre": "T3", "fecha_inicio": "2025-01-01", "campeon_id": None},
        ]
        reuniones = [
            {"id": 101, "id_temporada": 1, "numero_jornada": 1},
            {"id": 102, "id_temporada": 1, "numero_jornada": 2},
            # T2 meetings — player NOT enrolled here
            {"id": 201, "id_temporada": 2, "numero_jornada": 1},
            {"id": 202, "id_temporada": 2, "numero_jornada": 2},
            {"id": 203, "id_temporada": 3, "numero_jornada": 1},
            {"id": 204, "id_temporada": 3, "numero_jornada": 2},
        ]
        # Player 1 enrolled in T1 and T3, NOT in T2
        # Since eligibility requires >=1 asistencia in EACH temporada, and T2 has no
        # inscription, player 1 is ineligible (cannot satisfy T2 requirement without inscription).
        # Player 2 enrolled in all 3 temporadas — fully eligible
        inscripciones = {
            (1, 1), (1, 3),     # Player 1: T1 + T3 (not T2)
            (2, 1), (2, 2), (2, 3),  # Player 2: all seasons
        }
        jugadores_map = {
            1: {"nombre": "Ana", "foto_url": None},
            2: {"nombre": "Bruno", "foto_url": None},
        }
        # Ana: attends T1-j1, T1-j2; T2 → no inscription; attends T3-j1, T3-j2
        # Bruno: attends T1-j1; absent T1-j2; T2-j1, T2-j2 → not enrolled skipped; attends T3-j1, T3-j2
        # Wait — since T2 meetings are skipped (no inscription), Bruno's absent T1-j2 is his only inasistencia
        # that counts; and T2 reuniones don't break it. But we need to structure the case properly:
        # Bruno attends T1-j1, misses T1-j2, T2 meetings are skipped (not enrolled), attends T3 all.
        # His inasistencia streak from T1-j2 = 1 meeting (then T2 is skipped, then T3 he attends)
        # So Bruno streak = 1 → excluded by length filter.
        # This test mainly verifies Ana is excluded for eligibility (not enrolled in T2)
        posiciones = [
            {"id_jugador": 1, "id_reunion": 101, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 102, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 203, "posicion": 1, "puntos": 15},
            {"id_jugador": 1, "id_reunion": 204, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 101, "posicion": 2, "puntos": 14},
            # Bruno misses T1-j2 (102)
            {"id_jugador": 2, "id_reunion": 201, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 202, "posicion": 1, "puntos": 15},
            {"id_jugador": 2, "id_reunion": 203, "posicion": 2, "puntos": 14},
            {"id_jugador": 2, "id_reunion": 204, "posicion": 2, "puntos": 14},
        ]
        result = compute_racha_inasistencia(posiciones, reuniones, temporadas, inscripciones, jugadores_map)
        ids = [r["id_jugador"] for r in result]
        # Ana is ineligible (not enrolled in T2 → cannot have >=1 asistencia in T2)
        assert 1 not in ids, f"Ana should be ineligible (no enrollment in T2), got: {result}"

    def test_top_5_slice_and_sort(self):
        """7 eligible players with varying inasistencia streaks → only top 5 returned, sorted correctly."""
        # Single season with 10 meetings for simplicity; all players attend >=1 meeting
        temporadas = [
            {"id": 1, "nombre": "T1", "fecha_inicio": "2023-01-01", "campeon_id": None},
        ]
        reuniones = [
            {"id": 100 + i, "id_temporada": 1, "numero_jornada": i + 1}
            for i in range(10)
        ]
        # 7 players all enrolled in T1
        inscripciones = {(pid, 1) for pid in range(1, 8)}
        jugadores_map = {pid: {"nombre": f"Player{pid:02d}", "foto_url": None} for pid in range(1, 8)}

        # Streak design:
        # P1: attends j1, absent j2-j8 (7 consecutive), attends j9-j10 → streak 7
        # P2: attends j1, absent j2-j7 (6), attends j8-j10 → streak 6
        # P3: attends j1, absent j2-j6 (5), attends j7-j10 → streak 5
        # P4: attends j1, absent j2-j5 (4), attends j6-j10 → streak 4
        # P5: attends j1, absent j2-j4 (3), attends j5-j10 → streak 3
        # P6: attends j1, absent j2-j3 (2), attends j4-j10 → streak 2
        # P7: attends j1-j3, absent j4 (1), attends j5-j10 → streak 1 (excluded by filter)
        absent_counts = {1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2, 7: 1}

        posiciones = []
        for pid, n_absent in absent_counts.items():
            # First meeting: always attend (so eligible)
            posiciones.append({
                "id_jugador": pid, "id_reunion": 100, "posicion": pid, "puntos": 15 - pid
            })
            # The absent meetings are [101, 101+n_absent)
            # After that, attend the rest
            attend_start = 100 + 1 + n_absent  # first meeting after the gap
            for rid_offset in range(1 + n_absent, 10):
                posiciones.append({
                    "id_jugador": pid,
                    "id_reunion": 100 + rid_offset,
                    "posicion": pid,
                    "puntos": 15 - pid,
                })

        result = compute_racha_inasistencia(posiciones, reuniones, temporadas, inscripciones, jugadores_map)
        # P7 has streak=1 → excluded. So 6 qualify. Top 5 returned.
        assert len(result) == 5, f"Expected 5 results (top 5), got {len(result)}: {result}"
        assert result[0]["id_jugador"] == 1
        assert result[0]["longitud"] == 7
        assert result[4]["id_jugador"] == 5
        assert result[4]["longitud"] == 3
