"""
Genera un backup de la base de datos PostgreSQL usando pg_dump.

Uso:
    cd backend
    python scripts/backup_db.py

El archivo se guarda en backups/duDapp_YYYYMMDD_HHMMSS.dump

Variables de entorno requeridas:
    DATABASE_URL — conexión a PostgreSQL (postgresql://user:pass@host/dbname)

Requiere que pg_dump esté instalado en el sistema.
Correr desde una máquina local con DATABASE_URL apuntando a la DB de producción (Neon).
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("ERROR: Definí la variable de entorno DATABASE_URL.")
        sys.exit(1)

    parsed = urlparse(database_url)
    if parsed.scheme not in ("postgresql", "postgres"):
        print(f"ERROR: DATABASE_URL debe ser PostgreSQL, no '{parsed.scheme}'.")
        sys.exit(1)

    backup_dir = Path(__file__).parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = backup_dir / f"duDapp_{timestamp}.dump"

    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = parsed.password

    cmd = [
        "pg_dump",
        "--format=custom",
        "--no-acl",
        "--no-owner",
        f"--host={parsed.hostname}",
        f"--port={parsed.port or 5432}",
        f"--username={parsed.username}",
        f"--dbname={parsed.path.lstrip('/')}",
        f"--file={output_file}",
    ]

    print(f"Conectando a {parsed.hostname}:{parsed.port or 5432}/{parsed.path.lstrip('/')}...")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ERROR: pg_dump falló:\n{result.stderr}")
        sys.exit(1)

    size_kb = output_file.stat().st_size // 1024
    print(f"OK: Backup guardado en {output_file} ({size_kb} KB)")


if __name__ == "__main__":
    main()
