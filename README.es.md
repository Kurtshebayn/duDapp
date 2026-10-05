<div align="center">

# 🎲 duDapp

### Una plataforma web para gestionar una liga amistosa de **Dudo** (juego de dados) — temporadas, posiciones, estadísticas y narrativas.

[English](README.md) · `Español`

![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)

![Tests](https://img.shields.io/badge/tests-450%2B%20passing-brightgreen)
![Metodología](https://img.shields.io/badge/hecho%20con-TDD%20%2B%20SDD-blueviolet)
![Estado](https://img.shields.io/badge/estado-en%20producción-success)

</div>

---

> **¿Qué es el Dudo?** Un juego de dados sudamericano (primo del *Liar's Dice* / *Perudo*). Un grupo de amigos se junta cada semana, juega, y alguien tiene que llevar el puntaje. duDapp es ese alguien — convertido en un producto de verdad.

<div align="center">
  <img src="docs/screenshots/standings.png" alt="Tabla de posiciones de duDapp" width="600">
</div>

## El problema

Una liga semanal de Dudo entre amigos vivía en planillas de Google Drive y notebooks de Colab desperdigadas. Difícil de actualizar, difícil de leer, imposible de disfrutar. El admin peleaba con el Excel; los jugadores no tenían una forma clara de ver cómo iban.

**duDapp** lo resuelve: el administrador registra cada reunión semanal, y cualquier persona — sin crear cuenta — abre un link público para ver la tabla de posiciones en vivo, los resultados por jornada y las estadísticas de la temporada.

## Por qué es más que un CRUD

Lo interesante no son las pantallas — son las **reglas del dominio**. Esta app modela un juego real con fidelidad:

| Regla | Detalle |
|-------|---------|
| 🏆 **Puntaje por posición** | El 1° siempre recibe 15 pts, el 2° 14… posición *N* = `15 − (N−1)`, sin importar cuántos asistan |
| 👤 **Invitados** | Ocupan una posición y consumen puntos, pero **nunca** aparecen en la tabla de la temporada |
| 🚫 **Ausentes** | Reciben 0; el promedio se calcula solo sobre asistencias reales |
| 🔒 **Temporadas inmutables** | Una vez cerrada, una temporada no se puede editar — nunca |
| ⚖️ **Desempate** | Los empates al cierre se resuelven por enfrentamiento directo, con un flujo de admin para coronar al campeón |
| ➕ **Incorporaciones a mitad de temporada** | El jugador tardío computa como ausente (0 pts) en las jornadas previas; su promedio refleja solo sus asistencias reales |

Todo esto vive en **lógica de negocio pura y testeable** — no enterrada en los handlers HTTP.

## Stack y arquitectura

| Capa | Tecnología |
|------|-----------|
| **Backend** | FastAPI (Python), SQLAlchemy, migraciones Alembic |
| **Frontend** | React SPA, Vite, React Router |
| **Base de datos** | PostgreSQL en Neon (serverless) |
| **Auth** | JWT propia (PyJWT), un solo admin |
| **Testing** | pytest (backend) + Vitest / React Testing Library (frontend) |

El backend sigue un diseño en capas limpio — el que mantiene la lógica honesta:

```
Request HTTP
   │
   ▼
routers/      ← reciben requests, devuelven responses (finos)
   │
   ▼
services/     ← lógica de negocio pura (sin API, sin DB — 100% testeable)
   │
   ▼
models/ + schemas/   ← tablas SQLAlchemy (PostgreSQL/Neon) + validación Pydantic
```

**Metodología:** **TDD** pragmático (tests antes de la implementación, enfocados en reglas de negocio — no en getters/setters triviales) y **SDD** (toda feature nace de una especificación en `/docs`).

## El camino recorrido

El proyecto creció en fases deliberadas — cada una un cimiento, no una carrera hacia el demo:

| Fase | Qué se construyó |
|------|------------------|
| **1 · Cimientos** | Proyecto FastAPI, modelos SQLAlchemy, migraciones Alembic, auth JWT, DB conectada, CORS resuelto |
| **2 · Lógica de negocio** | Motor de puntaje, crear/editar temporada, registrar/editar reunión, cerrar temporada — todo con TDD |
| **3 · Datos públicos** | Endpoints de lectura para espectadores: posiciones (con reglas de visibilidad), resultados por jornada, estadísticas |
| **4 · Frontend base** | React SPA con vistas públicas: posiciones con medallas, resultados con badge de invitado, estadísticas |
| **5 · Frontend admin** | Vistas protegidas: login JWT, dashboard, crear temporada, registrar/editar reunión con drag & drop, compartir link |
| **6 · Pulido y lanzamiento** | Deploy a producción (Render + Vercel + Neon), rediseño editorial *cream/leather* completo en 9 páginas |
| **7 · Post-launch** | Ranking narrativo, sello del campeón, histórico cross-temporadas, import CSV, hardening de seguridad OWASP |

## Features destacadas

- **📈 Ranking narrativo** — snapshots de posición por jornada alimentan pills como *"sube N"*, *"cae N"*, *"racha de N"*, *"líder desde la jornada N"*.
- **👑 Sello del campeón** — cuando no hay temporada activa, la última cerrada muestra su ranking final dentro de un sello dorado ornamentado (laureles, itálica serif, año en números romanos).
- **🗂️ Histórico cross-temporadas** — estadísticas públicas agregadas que cruzan todas las temporadas.
- **📥 Import CSV** — un endpoint de admin que cargó 5 temporadas históricas previas al sistema.

## Lecciones aprendidas (las de verdad)

Operar en producción enseña cosas que localhost nunca enseñará. Dos que quedaron grabadas:

- **🔐 Los JWT se estaban firmando con un secret de fallback público en producción.** `JWT_SECRET` nunca se había seteado en Render, así que la app caía silenciosamente a un default. Detectado durante una auditoría OWASP Top 10 → se rotó el secret y se agregó un chequeo **fail-fast** para que la app se niegue a arrancar sin un secret real. (Shipeado como parte de la fase de hardening, junto a rate-limiting en login, validación de uploads y apagar `/docs` en prod.)
- **🚀 Render no corre las migraciones por ti.** Los deploys shipeaban código adelantado al schema hasta que el start command se actualizó para correr `alembic upgrade head` en cada deploy.

No son notas al pie — son la diferencia entre "funciona en mi máquina" y "corre en producción".

## Deployment

```
   Navegador
      │
      ▼
  React SPA  ──►  API FastAPI  ──►  PostgreSQL
  (Vercel)        (Render)          (Neon)
```

- **Frontend → Vercel** (con rewrites para el ruteo client-side)
- **Backend → Render** (corre `alembic upgrade head` en cada deploy)
- **Base de datos → Neon** (PostgreSQL serverless)

En producción desde **abril de 2026**.

## Correr en local

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

**Variables de entorno requeridas** (nunca commiteadas — usa un `.env` local):

| Variable | Para qué |
|----------|----------|
| `DATABASE_URL` | String de conexión a PostgreSQL |
| `JWT_SECRET` | Secret para firmar tokens (la app **no arranca** sin él) |
| `CORS_ORIGINS` | Orígenes permitidos del frontend |

Corre las suites de tests con:

```bash
cd backend && pytest          # backend
cd frontend && npm test       # frontend
```

---

<div align="center">

Hecho como un camino de aprendizaje — de una planilla a un producto en producción. 🎲

</div>
