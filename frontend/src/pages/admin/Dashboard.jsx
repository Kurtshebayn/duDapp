import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { getTemporadaActiva, getReuniones, cerrarTemporada } from '../../services/api'

function formatFecha(iso) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function Dashboard() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [temporada, setTemporada] = useState(undefined) // undefined = loading, null = no activa
  const [reuniones, setReuniones] = useState([])
  const [cerrando, setCerrando] = useState(false)
  const [error, setError] = useState(null)

  const cargar = useCallback(async () => {
    const [t, r] = await Promise.all([
      getTemporadaActiva().catch(() => null),
      getReuniones().catch(() => []),
    ])
    setTemporada(t)
    setReuniones(r ?? [])
  }, [])

  useEffect(() => { cargar() }, [cargar])

  async function handleCerrar() {
    if (!confirm(`¿Cerrar la temporada "${temporada.nombre}"? Esta acción es irreversible.`)) return
    setCerrando(true)
    setError(null)
    try {
      await cerrarTemporada(token, temporada.id)
      await cargar()
    } catch (err) {
      setError(err.message)
    } finally {
      setCerrando(false)
    }
  }

  function copiarLink() {
    navigator.clipboard.writeText(`${window.location.origin}/ranking`)
    alert('Link copiado al portapapeles.')
  }

  if (temporada === undefined) return <p className="status">Cargando...</p>

  // ── Sin temporada activa ──────────────────────────────────────────────────
  if (!temporada) {
    return (
      <div className="empty-state">
        <div className="empty-state-title">No hay temporada activa</div>
        <div className="empty-state-sub">Creá una nueva temporada para empezar a registrar reuniones.</div>
        <Link to="/admin/temporada/nueva" className="btn btn-primary">
          + Nueva temporada
        </Link>
      </div>
    )
  }

  // ── Temporada activa ──────────────────────────────────────────────────────
  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="season-card">
        <div className="season-card-header">
          <div>
            <div className="season-name">{temporada.nombre}</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              {temporada.total_reuniones} reunión{temporada.total_reuniones !== 1 ? 'es' : ''} ·{' '}
              {temporada.jugadores.length} jugadores
            </div>
          </div>
          <div className="season-actions">
            <button className="btn btn-secondary btn-sm" onClick={copiarLink}>
              Compartir link
            </button>
            <button
              className="btn btn-danger btn-sm"
              onClick={handleCerrar}
              disabled={cerrando}
            >
              {cerrando ? 'Cerrando...' : 'Cerrar temporada'}
            </button>
          </div>
        </div>
        <Link
          to="/admin/reuniones/nueva"
          className="btn btn-primary btn-sm"
        >
          + Registrar reunión
        </Link>
      </div>

      <h1>Reuniones</h1>

      {reuniones.length === 0 ? (
        <p style={{ color: 'var(--text-muted)' }}>Aún no hay reuniones registradas.</p>
      ) : (
        <div className="list">
          {[...reuniones].reverse().map((r) => (
            <div key={r.id} className="list-item" style={{ cursor: 'default' }}>
              <div className="list-item-left">
                <span className="jornada-badge">Jornada {r.numero_jornada}</span>
                <span className="list-item-date">{formatFecha(r.fecha)}</span>
              </div>
              <Link
                to={`/admin/reuniones/${r.id}/editar`}
                className="btn btn-secondary btn-sm"
                onClick={(e) => e.stopPropagation()}
              >
                Editar
              </Link>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
