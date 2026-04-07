const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function apiFetch(path) {
  const r = await fetch(`${API_URL}${path}`)
  if (r.status === 404) return null
  if (!r.ok) throw new Error(`Error ${r.status}`)
  return r.json()
}

export const getRanking = () => apiFetch('/temporadas/activa/ranking')
export const getReuniones = () => apiFetch('/temporadas/activa/reuniones')
export const getEstadisticas = () => apiFetch('/temporadas/activa/estadisticas')
export const getResultadosReunion = (id) => apiFetch(`/reuniones/${id}`)
