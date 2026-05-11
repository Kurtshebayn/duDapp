"""
Smoke test for Phase A — posicion_snapshot table.
RED: fails before model + migration are applied (table does not exist).
GREEN: passes once the SQLAlchemy model is imported and Base.metadata
       includes posicion_snapshot (conftest uses Base.metadata.create_all).
"""
import pytest
from sqlalchemy import inspect


def test_posicion_snapshot_table_exists(db):
    """Table posicion_snapshot must exist after Base.metadata.create_all."""
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    assert "posicion_snapshot" in tables


def test_posicion_snapshot_has_expected_columns(db):
    """
    Columns: id, id_temporada, id_reunion, id_jugador, posicion,
             puntos_acumulados.
    """
    inspector = inspect(db.bind)
    columns = {c["name"] for c in inspector.get_columns("posicion_snapshot")}
    expected = {
        "id",
        "id_temporada",
        "id_reunion",
        "id_jugador",
        "posicion",
        "puntos_acumulados",
    }
    assert expected.issubset(columns)


def test_posicion_snapshot_unique_constraint_exists(db):
    """
    Unique constraint uq_snapshot_reunion_jugador on (id_reunion, id_jugador)
    must be present.
    """
    inspector = inspect(db.bind)
    unique_constraints = inspector.get_unique_constraints("posicion_snapshot")
    constraint_column_sets = [
        frozenset(uc["column_names"]) for uc in unique_constraints
    ]
    assert frozenset(["id_reunion", "id_jugador"]) in constraint_column_sets


def test_posicion_snapshot_composite_index_exists(db):
    """
    Composite index ix_snapshot_temporada_jugador_reunion on
    (id_temporada, id_jugador, id_reunion) must be present.
    """
    inspector = inspect(db.bind)
    indexes = inspector.get_indexes("posicion_snapshot")
    index_names = {idx["name"] for idx in indexes}
    assert "ix_snapshot_temporada_jugador_reunion" in index_names
