# Reseteo de contraseña del admin

El sistema tiene un único usuario administrador. Si se pierde acceso, hay dos formas de recuperarlo.

---

## Opción A — Vía variables de entorno en Render (recomendada)

El backend lee `ADMIN_PASSWORD` al iniciar. Si está definida, crea o actualiza el admin automáticamente.

1. Ir a **Render → duDapp-backend → Environment**
2. Agregar o actualizar las variables:
   - `ADMIN_PASSWORD` = nueva contraseña
   - `ADMIN_EMAIL` = email del admin (si se quiere cambiar; default: `admin@dudo.com`)
   - `ADMIN_NOMBRE` = nombre del admin (si se quiere cambiar; default: `Admin`)
3. Hacer **Manual Deploy → Deploy latest commit** (o cualquier redeploy)
4. Al arrancar, el backend actualiza el hash de la contraseña automáticamente
5. Verificar en los logs del deploy que aparece:
   ```
   [setup_admin] Contrasena actualizada para admin@dudo.com
   ```
6. Una vez confirmado el acceso, se puede dejar la variable o removerla (el admin ya quedó guardado en la DB)

---

## Opción B — Script local apuntando a la DB de producción

Útil si no se tiene acceso a Render o se prefiere no hacer un redeploy.

**Requisitos:** Python instalado, acceso al `DATABASE_URL` de producción.

```bash
cd backend

# Setear variables (usar los valores reales)
export DATABASE_URL="postgresql://user:pass@host/dbname"
export ADMIN_EMAIL="admin@dudo.com"
export ADMIN_PASSWORD="nueva_contraseña_segura"
export ADMIN_NOMBRE="Admin"

python scripts/crear_admin.py
```

Si el admin ya existe, actualiza la contraseña. Si no existe, lo crea.

---

## Verificar que funciona

Después del reseteo, intentar login en la app:
- URL: `/login`
- Identificador: email del admin o nombre (según cómo se configuró)
- Contraseña: la nueva contraseña

Si el login falla, revisar los logs del backend para descartar errores de conexión a la DB.
