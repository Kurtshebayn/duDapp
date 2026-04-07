const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function apiFetch(path, options = {}) {
  const r = await fetch(`${API_URL}${path}`, options)
  if (r.status === 404) return null
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    throw new Error(body.detail || `Error ${r.status}`)
  }
  return r.json()
}

function authHeaders(token) {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
}

// ── Public ────────────────────────────────────────────────────────────────────

export const getRanking = () => apiFetch('/temporadas/activa/ranking')
export const getReuniones = () => apiFetch('/temporadas/activa/reuniones')
export const getEstadisticas = () => apiFetch('/temporadas/activa/estadisticas')
export const getResultadosReunion = (id) => apiFetch(`/reuniones/${id}`)
export const getTemporadaActiva = () => apiFetch('/temporadas/activa')
export const getJugadores = () => apiFetch('/jugadores')

// ── Admin ─────────────────────────────────────────────────────────────────────

export function login(email, password) {
  return apiFetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export function crearTemporada(token, nombre, jugadores) {
  return apiFetch('/temporadas', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ nombre, jugadores }),
  })
}

export function registrarReunion(token, temporadaId, fecha, posiciones) {
  return apiFetch(`/temporadas/${temporadaId}/reuniones`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ fecha, posiciones }),
  })
}

export function editarReunion(token, reunionId, fecha, posiciones) {
  return apiFetch(`/reuniones/${reunionId}`, {
    method: 'PUT',
    headers: authHeaders(token),
    body: JSON.stringify({ fecha, posiciones }),
  })
}

export function cerrarTemporada(token, temporadaId) {
  return apiFetch(`/temporadas/${temporadaId}/cerrar`, {
    method: 'POST',
    headers: authHeaders(token),
  })
}
