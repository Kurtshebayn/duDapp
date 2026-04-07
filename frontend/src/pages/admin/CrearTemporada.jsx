import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { getJugadores, crearTemporada } from '../../services/api'

export default function CrearTemporada() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [nombre, setNombre] = useState('')
  const [fechaInicio, setFechaInicio] = useState(() => new Date().toISOString().slice(0, 10))
  const [jugadoresExistentes, setJugadoresExistentes] = useState([])
  const [seleccionados, setSeleccionados] = useState(new Set())
  const [nuevosNombres, setNuevosNombres] = useState([]) // nombres de jugadores nuevos
  const [nuevoInput, setNuevoInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getJugadores().then((data) => setJugadoresExistentes(data ?? []))
  }, [])

  function toggleSeleccionado(id) {
    setSeleccionados((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function agregarNuevo() {
    const nombre = nuevoInput.trim()
    if (!nombre || nuevosNombres.includes(nombre)) return
    setNuevosNombres((prev) => [...prev, nombre])
    setNuevoInput('')
  }

  function quitarNuevo(nombre) {
    setNuevosNombres((prev) => prev.filter((n) => n !== nombre))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (seleccionados.size + nuevosNombres.length === 0) {
      setError('Agregá al menos un jugador.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const jugadores = [
        ...[...seleccionados].map((id) => ({ id })),
        ...nuevosNombres.map((n) => ({ nombre: n })),
      ]
      await crearTemporada(token, nombre, fechaInicio, jugadores)
      navigate('/admin')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const totalJugadores = seleccionados.size + nuevosNombres.length

  return (
    <>
      <h1>Nueva temporada</h1>
      {error && <div className="alert alert-error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Nombre de la temporada</label>
          <input
            className="form-input"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ej: Liga 2025"
            required
            autoFocus
          />
        </div>

        <div className="form-group" style={{ maxWidth: 220 }}>
          <label className="form-label">Fecha de inicio</label>
          <input
            className="form-input"
            type="date"
            value={fechaInicio}
            onChange={(e) => setFechaInicio(e.target.value)}
            required
          />
        </div>

        {jugadoresExistentes.length > 0 && (
          <div className="form-group">
            <label className="form-label">Jugadores existentes</label>
            <div className="checkbox-grid">
              {jugadoresExistentes.map((j) => (
                <label
                  key={j.id}
                  className={`checkbox-item${seleccionados.has(j.id) ? ' selected' : ''}`}
                  onClick={() => toggleSeleccionado(j.id)}
                >
                  <input type="checkbox" readOnly checked={seleccionados.has(j.id)} />
                  {j.nombre}
                </label>
              ))}
            </div>
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Jugadores nuevos</label>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <input
              className="form-input"
              value={nuevoInput}
              onChange={(e) => setNuevoInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), agregarNuevo())}
              placeholder="Nombre del jugador"
            />
            <button type="button" className="btn btn-secondary" onClick={agregarNuevo}>
              Agregar
            </button>
          </div>
          {nuevosNombres.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {nuevosNombres.map((n) => (
                <span key={n} className="chip chip-player">
                  {n}
                  <button
                    type="button"
                    className="btn-remove"
                    style={{ marginLeft: '0.4rem' }}
                    onClick={() => quitarNuevo(n)}
                  >×</button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button className="btn btn-primary" type="submit" disabled={loading || totalJugadores === 0}>
            {loading ? 'Creando...' : `Crear temporada (${totalJugadores} jugadores)`}
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/admin')}>
            Cancelar
          </button>
        </div>
      </form>
    </>
  )
}
