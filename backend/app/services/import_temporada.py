"""Import orchestrator service for bulk-import-temporadas.

Implements REQ-IMP-03 through REQ-IMP-26 (validation + persistence).
Validation order (NFR-IMP-03):
  1. Pydantic form validation (FastAPI level — handled by router)
  2. _check_nombre_no_duplicado
  3. _parsear_csv
  4. _validar_headers
  5. _resolver_jugadores
  6. _validar_puntajes
  7. _validar_reuniones_no_vacias
  8. _validar_campeon
  9. _persistir_temporada (with dry pre-pass for duplicate-score detection)
"""
import csv
import io
from dataclasses import dataclass
from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inscripcion import Inscripcion
from app.models.jugador import Jugador
from app.models.posicion import Posicion
from app.models.reunion import Reunion
from app.models.temporada import EstadoTemporada, Temporada
from app.services.reconstruir_posiciones import (
    PosicionReconstruida,
    reconstruir_posiciones_de_reunion,
)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ParsedCsv:
    headers: list  # list[str] — trimmed, original case preserved
    filas: list    # list[list[str]] — raw cell strings, BEFORE int parsing


@dataclass
class ResumenImportData:
    jugadores_inscriptos: int
    reuniones_creadas: int
    posiciones_creadas: int
    invitados_inferidos: int


@dataclass
class ImportResult:
    temporada: Temporada
    resumen: ResumenImportData


# ---------------------------------------------------------------------------
# Step 2: duplicate season name check
# ---------------------------------------------------------------------------

def _check_nombre_no_duplicado(db: Session, nombre: str) -> None:
    """Raise HTTPException 409 if a Temporada with this exact nombre already exists."""
    existing = db.query(Temporada).filter(Temporada.nombre == nombre).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "temporada_duplicada",
                "message": f"Ya existe una temporada con nombre '{nombre}'",
            },
        )


# ---------------------------------------------------------------------------
# Step 3: CSV parsing
# ---------------------------------------------------------------------------

def _parsear_csv(archivo_bytes: bytes) -> ParsedCsv:
    """Decode UTF-8 (strip BOM), detect separator, parse into headers + raw cells.

    Raises HTTPException 422:
    - csv_encoding_invalid  — bytes not decodeable as UTF-8
    - csv_invalido          — empty or no parseable structure (no header)
    - csv_sin_reuniones     — header found but zero data rows
    """
    # Decode UTF-8 with BOM stripping (utf-8-sig handles the BOM transparently)
    try:
        text = archivo_bytes.decode("utf-8-sig")
    except (UnicodeDecodeError, ValueError):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "csv_encoding_invalid",
                "message": "El archivo no es UTF-8 válido. Exportá el CSV con codificación UTF-8.",
            },
        )

    # Auto-detect separator: `;` default, `,` fallback when first line has no `;`
    lines = text.splitlines()
    # Filter blank lines for separator detection
    non_blank = [line for line in lines if line.strip()]

    if not non_blank:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "csv_invalido",
                "message": "El archivo está vacío o no tiene una estructura válida.",
            },
        )

    first_line = non_blank[0]
    sep = ";" if ";" in first_line else ","

    # Parse with csv.reader
    reader = csv.reader(io.StringIO(text), delimiter=sep)
    all_rows = list(reader)

    # Strip blank rows (rows where all cells are empty strings or row is empty)
    all_rows = [row for row in all_rows if any(cell.strip() for cell in row)]

    if not all_rows:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "csv_invalido",
                "message": "El archivo no contiene filas con datos.",
            },
        )

    # First non-empty row is the header
    raw_headers = all_rows[0]
    headers = [h.strip() for h in raw_headers]

    # At least one header name required
    if not any(h for h in headers):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "csv_invalido",
                "message": "La fila de encabezados no contiene nombres de jugadores.",
            },
        )

    data_rows = all_rows[1:]

    if not data_rows:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "csv_sin_reuniones",
                "message": "El CSV tiene encabezados pero no contiene filas de datos (reuniones).",
            },
        )

    return ParsedCsv(headers=headers, filas=data_rows)


# ---------------------------------------------------------------------------
# Step 4: header duplicate validation
# ---------------------------------------------------------------------------

def _validar_headers(headers: list) -> None:
    """Trim + case-insensitive duplicate check.

    Raises HTTPException 422 csv_header_duplicate on first duplicate found.
    """
    seen = set()
    for h in headers:
        normalized = h.strip().lower()
        if normalized in seen:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "csv_header_duplicate",
                    "message": f"El encabezado '{h.strip()}' aparece más de una vez (ignorando mayúsculas).",
                    "nombre": h.strip(),
                },
            )
        seen.add(normalized)


# ---------------------------------------------------------------------------
# Step 5: player name resolution
# ---------------------------------------------------------------------------

def _resolver_jugadores(headers: list, db: Session) -> dict:
    """Map each header to a Jugador via case-insensitive trimmed exact match.

    Returns {header_str: Jugador}. Collects ALL unresolved names before raising.
    Does NOT auto-create Jugador records.

    Raises HTTPException 422 jugadores_no_resueltos with full list.
    """
    # Load all jugadores from DB (small table, fetch once)
    all_jugadores = db.query(Jugador).all()
    jugador_map = {j.nombre.strip().lower(): j for j in all_jugadores}

    result = {}
    unresolved = []

    for header in headers:
        key = header.strip().lower()
        jugador = jugador_map.get(key)
        if jugador is None:
            unresolved.append(header.strip())
        else:
            result[header] = jugador

    if unresolved:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "jugadores_no_resueltos",
                "message": f"Los siguientes jugadores no existen en el catálogo: {', '.join(unresolved)}",
                "nombres": unresolved,
            },
        )

    return result


# ---------------------------------------------------------------------------
# Step 6: score validation
# ---------------------------------------------------------------------------

def _validar_puntajes(parsed: ParsedCsv) -> list:
    """Convert raw cell strings to ints in [0, 15]. Collects ALL invalid cells.

    Returns list[list[int]] (the int matrix).
    Raises HTTPException 422 puntaje_invalido with errores list.
    """
    errores = []
    matrix = []

    for row_idx, fila in enumerate(parsed.filas, start=1):
        int_row = []
        for col_idx, cell in enumerate(fila):
            cell_str = cell.strip()
            valid = True
            try:
                value = int(cell_str)
                if value < 0 or value > 15:
                    valid = False
            except (ValueError, TypeError):
                valid = False

            if not valid:
                header = parsed.headers[col_idx] if col_idx < len(parsed.headers) else f"col{col_idx+1}"
                errores.append({
                    "fila": row_idx,
                    "columna": header,
                    "valor": cell_str,
                })
                int_row.append(0)  # placeholder so matrix is consistent
            else:
                int_row.append(int(cell_str))

        matrix.append(int_row)

    if errores:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "puntaje_invalido",
                "message": f"Se encontraron {len(errores)} celdas con puntajes inválidos.",
                "errores": errores,
            },
        )

    return matrix


# ---------------------------------------------------------------------------
# Step 7: all-absent meeting validation
# ---------------------------------------------------------------------------

def _validar_reuniones_no_vacias(matriz: list) -> None:
    """Raise HTTPException 422 reunion_todos_ausentes if any row has all zeros."""
    for row_idx, fila in enumerate(matriz, start=1):
        if all(v == 0 for v in fila):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "reunion_todos_ausentes",
                    "message": f"La fila {row_idx} tiene todos los puntajes en 0. Una reunión sin asistentes no es válida.",
                    "fila": row_idx,
                },
            )


# ---------------------------------------------------------------------------
# Step 8: champion validation
# ---------------------------------------------------------------------------

def _validar_campeon(
    campeon_nombre: Optional[str],
    jugadores_resueltos: dict,
) -> Optional[Jugador]:
    """Match campeon_nombre case-insensitively against jugadores_resueltos keys.

    Returns the Jugador if found, None if campeon_nombre is None.
    Raises HTTPException 422 campeon_no_inscripto on mismatch.
    """
    if campeon_nombre is None:
        return None

    normalized = campeon_nombre.strip().lower()
    for header, jugador in jugadores_resueltos.items():
        if header.strip().lower() == normalized:
            return jugador

    raise HTTPException(
        status_code=422,
        detail={
            "code": "campeon_no_inscripto",
            "message": f"El campeón '{campeon_nombre.strip()}' no está en los jugadores inscriptos del CSV.",
        },
    )


# ---------------------------------------------------------------------------
# Step 9: persistence (with dry pre-pass for duplicate-score detection)
# ---------------------------------------------------------------------------

def _fila_a_scores(fila: list, headers: list) -> dict:
    """Convert an int row + headers into a {player_name: score} dict."""
    return {headers[i]: fila[i] for i in range(len(headers))}


def _persistir_temporada(
    db: Session,
    nombre: str,
    fecha_inicio: date,
    campeon: Optional[Jugador],
    usuario_id: int,
    jugadores_resueltos: dict,
    headers: list,
    matriz: list,
) -> ImportResult:
    """Single-transaction persistence following NFR-IMP-04.

    Step A (dry pre-pass): call reconstruir_posiciones_de_reunion for each row
    BEFORE any DB write to catch duplicate-score ValueError → HTTPException 422
    puntajes_duplicados. This satisfies both NFR-IMP-03 (validation order) and
    NFR-IMP-04 (atomicity; no partial writes).

    Step B (wet pass): use cached reconstruction results to write all records.
    One db.commit() at the end. Explicit db.rollback() on any exception.
    """
    # ----- Dry pre-pass -----
    cached_posiciones: list[list[PosicionReconstruida]] = []
    for row_idx, fila in enumerate(matriz, start=1):
        scores = _fila_a_scores(fila, headers)
        try:
            posiciones = reconstruir_posiciones_de_reunion(scores)
        except ValueError as e:
            # Translate ValueError (duplicate score) → HTTPException 422
            # Extract the duplicate score value if possible
            msg = str(e)
            valor = None
            if "duplicado" in msg.lower():
                # Try to parse the score from the message "Puntaje duplicado ... : N"
                try:
                    valor = int(msg.split(":")[-1].strip())
                except (ValueError, IndexError):
                    valor = None
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "puntajes_duplicados",
                    "message": f"Fila {row_idx}: {msg}",
                    "fila": row_idx,
                    "valor": valor,
                },
            )
        cached_posiciones.append(posiciones)

    # ----- Wet pass -----
    try:
        campeon_id = campeon.id if campeon is not None else None

        temporada = Temporada(
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            estado=EstadoTemporada.cerrada,
            id_usuario=usuario_id,
            campeon_id=campeon_id,
        )
        db.add(temporada)
        db.flush()  # get temporada.id

        # Inscripciones — one per header/player
        for header, jugador in jugadores_resueltos.items():
            inscripcion = Inscripcion(
                id_temporada=temporada.id,
                id_jugador=jugador.id,
            )
            db.add(inscripcion)

        posiciones_creadas = 0
        invitados_inferidos = 0

        for jornada_idx, (fila, posiciones_list) in enumerate(
            zip(matriz, cached_posiciones), start=1
        ):
            reunion = Reunion(
                id_temporada=temporada.id,
                numero_jornada=jornada_idx,
                fecha=None,
            )
            db.add(reunion)
            db.flush()  # get reunion.id

            for pos in posiciones_list:
                jugador_id = None
                if not pos.es_invitado and pos.nombre_jugador is not None:
                    jugador_id = jugadores_resueltos[pos.nombre_jugador].id

                posicion_row = Posicion(
                    id_reunion=reunion.id,
                    id_jugador=jugador_id,
                    es_invitado=pos.es_invitado,
                    posicion=pos.posicion,
                    puntos=pos.puntos,
                )
                db.add(posicion_row)
                posiciones_creadas += 1
                if pos.es_invitado:
                    invitados_inferidos += 1

        db.commit()
        db.refresh(temporada)

        return ImportResult(
            temporada=temporada,
            resumen=ResumenImportData(
                jugadores_inscriptos=len(jugadores_resueltos),
                reuniones_creadas=len(matriz),
                posiciones_creadas=posiciones_creadas,
                invitados_inferidos=invitados_inferidos,
            ),
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------------------------
# Public orchestrator
# ---------------------------------------------------------------------------

def importar_temporada(
    db: Session,
    nombre: str,
    fecha_inicio: date,
    archivo_bytes: bytes,
    campeon_nombre: Optional[str],
    usuario_id: int,
) -> ImportResult:
    """Orchestrate validation → reconstruction → atomic persistence.

    Validation order (NFR-IMP-03):
    1. (Pydantic) handled by FastAPI before this function is called
    2. _check_nombre_no_duplicado   → 409 temporada_duplicada
    3. _parsear_csv                 → 422 csv_encoding_invalid / csv_invalido / csv_sin_reuniones
    4. _validar_headers             → 422 csv_header_duplicate
    5. _resolver_jugadores          → 422 jugadores_no_resueltos
    6. _validar_puntajes            → 422 puntaje_invalido
    7. _validar_reuniones_no_vacias → 422 reunion_todos_ausentes
    8. _validar_campeon             → 422 campeon_no_inscripto
    9. _persistir_temporada         → dry pre-pass (puntajes_duplicados) + wet pass

    Raises HTTPException on any failure. db.commit() only on happy path.
    """
    # Step 2
    _check_nombre_no_duplicado(db, nombre)

    # Step 3
    parsed = _parsear_csv(archivo_bytes)

    # Step 4
    _validar_headers(parsed.headers)

    # Step 5
    jugadores_resueltos = _resolver_jugadores(parsed.headers, db)

    # Step 6
    matriz = _validar_puntajes(parsed)

    # Step 7
    _validar_reuniones_no_vacias(matriz)

    # Step 8
    campeon = _validar_campeon(campeon_nombre, jugadores_resueltos)

    # Step 9
    return _persistir_temporada(
        db=db,
        nombre=nombre,
        fecha_inicio=fecha_inicio,
        campeon=campeon,
        usuario_id=usuario_id,
        jugadores_resueltos=jugadores_resueltos,
        headers=parsed.headers,
        matriz=matriz,
    )
