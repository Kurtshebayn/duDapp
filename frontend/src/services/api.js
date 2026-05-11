const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function apiFetch(path, options = {}) {
  const r = await fetch(`${API_URL}${path}`, options)
  if (r.status === 404) return null
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    // Derive a readable string for backward-compatible err.message:
    // - If detail is a plain string, use it directly
    // - If detail is a dict with a message field, use that
    // - If detail is something else (Pydantic array, etc.), fall back to generic
    const detail = body.detail
    let message
    if (typeof detail === 'string') {
      message = detail
    } else if (detail && typeof detail === 'object' && !Array.isArray(detail) && detail.message) {
      message = detail.message
    } else if (detail && typeof detail === 'object' && !Array.isArray(detail) && detail.code) {
      message = detail.code
    } else {
      message = `Error ${r.status}`
    }
    const err = new Error(message)
    err.body = body       // full parsed body for structured error rendering
    err.status = r.status
    throw err
  }
  return r.json()
}

function authHeaders(token) {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
}

// ── Public ────────────────────────────────────────────────────────────────────

export const getRanking = () => apiFetch('/temporadas/activa/ranking')
export const getReuniones = () => apiFetch('/temporadas/activa/reuniones')
export const getResultadosReunion = (id) => apiFetch(`/reuniones/${id}`)
export const getTemporadaActiva = () => apiFetch('/temporadas/activa')
export const getJugadores = () => apiFetch('/jugadores')
export const getHistoricoResumen = () => apiFetch('/historico/resumen')
export const getHeadToHead = (jugadorId) => apiFetch(`/historico/head-to-head/${jugadorId}`)

// ── Admin ─────────────────────────────────────────────────────────────────────

export function login(identificador, password) {
  return apiFetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identificador, password }),
  })
}

export function crearTemporada(token, nombre, fechaInicio, jugadores) {
  return apiFetch('/temporadas', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ nombre, fecha_inicio: fechaInicio, jugadores }),
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

export function subirFotoJugador(token, id, file) {
  const form = new FormData()
  form.append('foto', file)
  return apiFetch(`/jugadores/${id}/foto`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
}

export function crearJugador(token, nombre) {
  return apiFetch('/jugadores', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ nombre }),
  })
}

export function inscribirJugadorEnActiva(token, idJugador) {
  return apiFetch('/temporadas/activa/inscripciones', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ id_jugador: idJugador }),
  })
}

export function importarTemporada(token, formData) {
  // Do NOT set Content-Type — the browser sets multipart/form-data with boundary automatically
  return apiFetch('/temporadas/import', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })
}
