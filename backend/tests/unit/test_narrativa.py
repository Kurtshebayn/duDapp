"""
Unit tests — Phase D: Narrative computation pure functions.

Tests cover spec scenarios S-RN-01 through S-RN-06.
All functions use SEMANTIC delta convention:
  delta = anterior_posicion - nueva_posicion
  Positive → rose, Negative → dropped, 0 → first appearance or unchanged.

See decisions-supplement engram #98.

RED: all fail before narrativa.py is created.
GREEN: pass once narrativa.py is implemented.
"""
import pytest

from app.services.narrativa import (
    compute_delta_posicion,
    compute_racha,
    compute_lider_desde_jornada,
)


# ===========================================================================
# compute_delta_posicion
# SEMANTIC convention: delta = anterior_posicion - nueva_posicion
# ===========================================================================

class TestComputeDeltaPosicion:

    def test_empty_history_returns_zero(self):
        """Empty history → 0 (first appearance rule)."""
        assert compute_delta_posicion([]) == 0

    def test_single_entry_returns_zero(self):
        """Single snapshot → 0 (first appearance, no prior to compare)."""
        history = [{"numero_jornada": 1, "posicion": 3}]
        assert compute_delta_posicion(history) == 0

    def test_rose_two_positions(self):
        """rank 3 → 1: anterior=3, nueva=1 → delta = 3 - 1 = +2 (SEMANTIC: rose)."""
        history = [
            {"numero_jornada": 1, "posicion": 3},
            {"numero_jornada": 2, "posicion": 1},
        ]
        assert compute_delta_posicion(history) == 2

    def test_dropped_two_positions(self):
        """rank 1 → 3: anterior=1, nueva=3 → delta = 1 - 3 = -2 (SEMANTIC: dropped)."""
        history = [
            {"numero_jornada": 1, "posicion": 1},
            {"numero_jornada": 2, "posicion": 3},
        ]
        assert compute_delta_posicion(history) == -2

    def test_same_rank_returns_zero(self):
        """Same position two jornadas → delta = 0."""
        history = [
            {"numero_jornada": 1, "posicion": 2},
            {"numero_jornada": 2, "posicion": 2},
        ]
        assert compute_delta_posicion(history) == 0

    def test_rose_one_position(self):
        """rank 2 → 1: delta = 2 - 1 = +1."""
        history = [
            {"numero_jornada": 1, "posicion": 2},
            {"numero_jornada": 2, "posicion": 1},
        ]
        assert compute_delta_posicion(history) == 1

    def test_dropped_one_position(self):
        """rank 1 → 2: delta = 1 - 2 = -1."""
        history = [
            {"numero_jornada": 1, "posicion": 1},
            {"numero_jornada": 2, "posicion": 2},
        ]
        assert compute_delta_posicion(history) == -1

    def test_uses_last_two_entries_only(self):
        """Delta is computed only from the last two entries, not the whole history."""
        history = [
            {"numero_jornada": 1, "posicion": 5},
            {"numero_jornada": 2, "posicion": 4},
            {"numero_jornada": 3, "posicion": 2},
        ]
        # anterior=4 (jornada 2), nueva=2 (jornada 3) → delta = 4 - 2 = +2
        assert compute_delta_posicion(history) == 2

    def test_s_tie_02_drop_from_tied_1_to_2(self):
        """
        S-TIE-02 SEMANTIC: player at tied posicion=1 (j1) drops to posicion=2 (j2).
        anterior=1, nueva=2 → delta = 1 - 2 = -1.

        NOTE: This test documents the SEMANTIC convention override from
        decisions-supplement engram #98. The original spec S-TIE-02 text stated
        delta_posicion=-1 for this scenario, which coincidentally matches SEMANTIC
        (anterior=1, nueva=2 → 1-2 = -1). Both conventions agree for this case.
        """
        history = [
            {"numero_jornada": 1, "posicion": 1},  # tied at 1
            {"numero_jornada": 2, "posicion": 2},  # dropped to 2
        ]
        # SEMANTIC: anterior=1, nueva=2 → delta = 1 - 2 = -1
        assert compute_delta_posicion(history) == -1


# ===========================================================================
# compute_racha
# Counts consecutive jornadas from the end where posicion STRICTLY improved
# (decreased numerically). Staying or worsening breaks the streak.
# Decision #2: strictly improving.
# ===========================================================================

class TestComputeRacha:

    def test_empty_history_returns_zero(self):
        assert compute_racha([]) == 0

    def test_single_entry_returns_zero(self):
        """Single snapshot → 0 (no prior jornada to compare against)."""
        history = [{"numero_jornada": 1, "posicion": 3}]
        assert compute_racha(history) == 0

    def test_s_rn_01_two_consecutive_improvements(self):
        """S-RN-01: player ranked p4 → p3 → p2 → racha=2."""
        history = [
            {"numero_jornada": 1, "posicion": 4},
            {"numero_jornada": 2, "posicion": 3},
            {"numero_jornada": 3, "posicion": 2},
        ]
        assert compute_racha(history) == 2

    def test_s_rn_02_stay_breaks_racha(self):
        """S-RN-02: player ranked p3 → p3 → p2 → racha=1 (stay breaks streak)."""
        history = [
            {"numero_jornada": 1, "posicion": 3},
            {"numero_jornada": 2, "posicion": 3},
            {"numero_jornada": 3, "posicion": 2},
        ]
        assert compute_racha(history) == 1

    def test_s_rn_03_stay_at_1_breaks_racha(self):
        """S-RN-03: player ranked p2 → p1 → p1 → racha=0 (staying at #1 breaks streak)."""
        history = [
            {"numero_jornada": 1, "posicion": 2},
            {"numero_jornada": 2, "posicion": 1},
            {"numero_jornada": 3, "posicion": 1},
        ]
        assert compute_racha(history) == 0

    def test_drop_breaks_racha(self):
        """p3 → p2 → p4 → racha=0 (final step is a drop)."""
        history = [
            {"numero_jornada": 1, "posicion": 3},
            {"numero_jornada": 2, "posicion": 2},
            {"numero_jornada": 3, "posicion": 4},
        ]
        assert compute_racha(history) == 0

    def test_three_consecutive_improvements(self):
        """p5 → p4 → p3 → p2 → racha=3."""
        history = [
            {"numero_jornada": 1, "posicion": 5},
            {"numero_jornada": 2, "posicion": 4},
            {"numero_jornada": 3, "posicion": 3},
            {"numero_jornada": 4, "posicion": 2},
        ]
        assert compute_racha(history) == 3

    def test_improvement_broken_by_drop_in_middle(self):
        """p5 → p3 → p4 → p2 → racha=1 (last step improves, prior step dropped)."""
        history = [
            {"numero_jornada": 1, "posicion": 5},
            {"numero_jornada": 2, "posicion": 3},
            {"numero_jornada": 3, "posicion": 4},  # drop breaks it
            {"numero_jornada": 4, "posicion": 2},  # improvement after break
        ]
        # Counting back from end: j4 better than j3 (2 < 4) → +1; j3 worse than j2 (4 > 3) → STOP
        assert compute_racha(history) == 1

    def test_all_same_posicion_returns_zero(self):
        """All jornadas same posicion → racha=0 (no improvement ever)."""
        history = [
            {"numero_jornada": i + 1, "posicion": 2}
            for i in range(5)
        ]
        assert compute_racha(history) == 0


# ===========================================================================
# compute_lider_desde_jornada
# Returns numero_jornada of the FIRST jornada in the current contiguous block
# of posicion=1 at the end of history. None if not currently at posicion=1.
# Decision #3: last ascent — if player lost and regained #1, return the regain.
# ===========================================================================

class TestComputeLiderDesdeJornada:

    def test_empty_history_returns_none(self):
        assert compute_lider_desde_jornada([]) is None

    def test_never_at_1_returns_none(self):
        """S-RN-06: player never reached posicion=1."""
        history = [
            {"numero_jornada": 1, "posicion": 2},
            {"numero_jornada": 2, "posicion": 3},
        ]
        assert compute_lider_desde_jornada(history) is None

    def test_current_not_at_1_returns_none(self):
        """Was at #1 earlier but not currently → None."""
        history = [
            {"numero_jornada": 1, "posicion": 1},
            {"numero_jornada": 2, "posicion": 2},
        ]
        assert compute_lider_desde_jornada(history) is None

    def test_s_rn_04_continuous_lead(self):
        """S-RN-04: held posicion=1 in jornadas 5,6,7,8 → lider_desde=5."""
        history = [
            {"numero_jornada": 1, "posicion": 3},
            {"numero_jornada": 2, "posicion": 2},
            {"numero_jornada": 3, "posicion": 2},
            {"numero_jornada": 4, "posicion": 2},
            {"numero_jornada": 5, "posicion": 1},
            {"numero_jornada": 6, "posicion": 1},
            {"numero_jornada": 7, "posicion": 1},
            {"numero_jornada": 8, "posicion": 1},
        ]
        assert compute_lider_desde_jornada(history) == 5

    def test_s_rn_05_lost_and_regained(self):
        """S-RN-05: held #1 in J5-J7, lost J8, regained J10 → lider_desde=10."""
        history = [
            {"numero_jornada": 5, "posicion": 1},
            {"numero_jornada": 6, "posicion": 1},
            {"numero_jornada": 7, "posicion": 1},
            {"numero_jornada": 8, "posicion": 2},  # lost
            {"numero_jornada": 9, "posicion": 2},
            {"numero_jornada": 10, "posicion": 1},  # regained
        ]
        assert compute_lider_desde_jornada(history) == 10

    def test_single_entry_at_1(self):
        """Single jornada at posicion=1 → lider_desde=that jornada."""
        history = [{"numero_jornada": 3, "posicion": 1}]
        assert compute_lider_desde_jornada(history) == 3

    def test_all_at_1(self):
        """All jornadas at posicion=1 → lider_desde = first jornada."""
        history = [
            {"numero_jornada": 1, "posicion": 1},
            {"numero_jornada": 2, "posicion": 1},
            {"numero_jornada": 3, "posicion": 1},
        ]
        assert compute_lider_desde_jornada(history) == 1

    def test_s_rn_06_never_at_1(self):
        """S-RN-06: player always at posicion >= 2 → None."""
        history = [
            {"numero_jornada": i + 1, "posicion": i + 2}
            for i in range(5)
        ]
        assert compute_lider_desde_jornada(history) is None
