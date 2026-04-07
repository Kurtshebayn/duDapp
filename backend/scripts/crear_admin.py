"""
Crea o actualiza el usuario administrador en la base de datos.

Uso:
    cd backend
    python scripts/crear_admin.py

Variables de entorno requeridas:
    DATABASE_URL  — conexión a PostgreSQL (o SQLite para desarrollo)
    ADMIN_EMAIL   — email del admin (default: admin@dudo.com)
    ADMIN_PASSWORD — contraseña del admin (requerida si es la primera vez)
    ADMIN_NOMBRE  — nombre del admin (default: Admin)
"""

import os
import sys

import bcrypt

# Asegura que el módulo app sea encontrado desde backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, SessionLocal, engine
from app.models.usuario import Usuario  # noqa: F401 — registra el modelo


def main() -> None:
    email = os.getenv("ADMIN_EMAIL", "admin@dudo.com")
    nombre = os.getenv("ADMIN_NOMBRE", "Admin")
    password = os.getenv("ADMIN_PASSWORD", "")

    if not password:
        print("ERROR: Definí la variable de entorno ADMIN_PASSWORD antes de correr este script.")
        sys.exit(1)

    # Crea las tablas si no existen (útil en desarrollo)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        usuario = db.query(Usuario).filter(Usuario.email == email).first()

        if usuario:
            usuario.password_hash = password_hash
            usuario.nombre = nombre
            db.commit()
            print(f"OK: Contrasena actualizada para {email}")
        else:
            db.add(Usuario(email=email, nombre=nombre, password_hash=password_hash))
            db.commit()
            print(f"OK: Admin creado: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
