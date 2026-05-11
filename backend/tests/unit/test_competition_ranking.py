"""
Unit tests for assign_competition_ranks() — Phase B.
Strict TDD: this file was written BEFORE the implementation.

Uses shared fixture backend/tests/fixtures/competition_ranking.json,
which is the contract shared with the future JS parity test.

Algorithm:
  Walk list already sorted by puntos desc.
  If i == 0 or entry[i].puntos != entry[i-1].puntos → posicion = i + 1
  Else → same posicion as entry[i-1].
  (Standard competition ranking / Olympic ranking: 1, 1, 3, 4)

Bit-exact port of frontend/src/lib/ranking.js:assignRanks().
"""

import json
from pathlib import Path

import pytest

from app.services.ranking import assign_competition_ranks

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "competition_ranking.json"


def load_fixtures():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _expected_map(expected: list[dict]) -> dict[int, int]:
    """Build {id_jugador: posicion} from expected list."""
    return {e["id_jugador"]: e["posicion"] for e in expected}


# ---------------------------------------------------------------------------
# Parametrized over all fixture cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "case",
    load_fixtures(),
    ids=[c["name"] for c in load_fixtures()],
)
def test_assign_competition_ranks_fixture(case):
    """All fixture cases must produce the expected posicion per id_jugador."""
    result = assign_competition_ranks(case["input"])

    if not case["expected"]:
        assert result == []
        return

    expected = _expected_map(case["expected"])
    assert len(result) == len(case["input"]), (
        f"Case '{case['name']}': output length {len(result)} "
        f"!= input length {len(case['input'])}"
    )
    for entry in result:
        pid = entry["id_jugador"]
        assert pid in expected, f"id_jugador {pid} not in expected map"
        assert entry["posicion"] == expected[pid], (
            f"Case '{case['name']}': id_jugador={pid} "
            f"got posicion={entry['posicion']}, "
            f"expected={expected[pid]}"
        )


# ---------------------------------------------------------------------------
# Explicit edge case tests (belt-and-suspenders beyond the fixture)
# ---------------------------------------------------------------------------


def test_empty_input_returns_empty_list():
    assert assign_competition_ranks([]) == []


def test_single_entry_gets_posicion_1():
    result = assign_competition_ranks(
        [{"id_jugador": 1, "nombre": "Ana", "puntos": 15, "asistencias": 1}]
    )
    assert len(result) == 1
    assert result[0]["posicion"] == 1


def test_all_tied_all_get_posicion_1():
    entries = [
        {"id_jugador": i, "nombre": f"J{i}", "puntos": 42, "asistencias": 1}
        for i in range(1, 6)
    ]
    result = assign_competition_ranks(entries)
    assert all(e["posicion"] == 1 for e in result)


def test_no_ties_sequential_posiciones():
    entries = [
        {"id_jugador": 1, "nombre": "Ana",    "puntos": 15, "asistencias": 1},
        {"id_jugador": 2, "nombre": "Bruno",  "puntos": 14, "asistencias": 1},
        {"id_jugador": 3, "nombre": "Carlos", "puntos": 13, "asistencias": 1},
    ]
    result = assign_competition_ranks(entries)
    assert [e["posicion"] for e in result] == [1, 2, 3]


def test_partial_tie_skips_rank():
    """100, 100, 80, 70 → posiciones 1, 1, 3, 4 (not 1, 1, 2, 3)."""
    entries = [
        {"id_jugador": 1, "nombre": "A", "puntos": 100, "asistencias": 1},
        {"id_jugador": 2, "nombre": "B", "puntos": 100, "asistencias": 1},
        {"id_jugador": 3, "nombre": "C", "puntos": 80,  "asistencias": 1},
        {"id_jugador": 4, "nombre": "D", "puntos": 70,  "asistencias": 1},
    ]
    result = assign_competition_ranks(entries)
    assert [e["posicion"] for e in result] == [1, 1, 3, 4]


def test_does_not_mutate_input():
    """assign_competition_ranks must not modify the input list or its dicts."""
    entries = [
        {"id_jugador": 1, "nombre": "Ana", "puntos": 10, "asistencias": 1},
        {"id_jugador": 2, "nombre": "Bob", "puntos": 8,  "asistencias": 1},
    ]
    original_keys_0 = set(entries[0].keys())
    assign_competition_ranks(entries)
    # Input dicts must not have gained "posicion"
    assert set(entries[0].keys()) == original_keys_0
    assert "posicion" not in entries[0]


def test_output_preserves_all_original_fields():
    """Each output entry must carry all original fields plus posicion."""
    entries = [
        {"id_jugador": 1, "nombre": "Ana", "puntos": 15, "asistencias": 2}
    ]
    result = assign_competition_ranks(entries)
    assert result[0]["id_jugador"] == 1
    assert result[0]["nombre"] == "Ana"
    assert result[0]["puntos"] == 15
    assert result[0]["asistencias"] == 2
    assert result[0]["posicion"] == 1
