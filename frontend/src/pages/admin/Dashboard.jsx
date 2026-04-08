import { useRef, useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import {
  getTemporadaActiva,
  getReuniones,
  cerrarTemporada,
  getJugadores,
  subirFotoJugador,
} from '../../services/api'
import PlayerAvatar from '../../components/PlayerAvatar'

function formatFecha(iso) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function Dashboard() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [temporada, setTemporada] = useState(undefined) // undefined = loading
  const [reuniones, setReuniones] = useState([])
  const [jugadores, setJugadores] = useState([])
  const [cerrando, setCerrando] = useState(false)
  const [error, setError] = useState(null)
  const [uploadingId, setUploadingId] = useState(null)

  const cargar = useCallback(async () => {
    const [t, r, j] = await Promise.all([
      getTemporadaActiva().catch(() => null),
      getReuniones().catch(() => []),
      getJugadores().catch(() => []),
    ])
    setTemporada(t)
    setReuniones(r ?? [])
    setJugadores(j ?? [])
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

  function handleFotoClick(jugadorId) {
    fileInputRef.current.dataset.jugadorId = jugadorId
    fileInputRef.current.click()
  }

  async function handleFotoChange(e) {
    const file = e.target.files[0]
    if (!file) return
    const jugadorId = Number(fileInputRef.current.dataset.jugadorId)
    e.target.value = ''
    setUploadingId(jugadorId)
    try {
      const updated = await subirFotoJugador(token, jugadorId, file)
      setJugadores((prev) =>
        prev.map((j) => (j.id === jugadorId ? { ...j, foto_url: updated.foto_url } : j))
      )
    } catch {
      // silencioso — el avatar no cambia
    } finally {
      setUploadingId(null)
    }
  }

  if (temporada === undefined) return <p className="status">Cargando...</p>

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleFotoChange}
      />

      {error && <div className="alert alert-error">{error}</div>}

      {/* ── Temporada ──────────────────────────────────────────────── */}
      {!temporada ? (
        <div className="empty-state">
          <div className="empty-state-title">No hay temporada activa</div>
          <div className="empty-state-sub">
            Creá una nueva temporada para empezar a registrar reuniones.
          </div>
          <Link to="/admin/temporada/nueva" className="btn btn-primary">
            + Nueva temporada
          </Link>
        </div>
      ) : (
        <>
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
            <Link to="/admin/reuniones/nueva" className="btn btn-primary btn-sm">
              + Registrar reunión
            </Link>
          </div>

          <h1>Reuniones</h1>

          {reuniones.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
              Aún no hay reuniones registradas.
            </p>
          ) : (
            <div className="list" style={{ marginBottom: '2.5rem' }}>
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
      )}

      {/* ── Jugadores ──────────────────────────────────────────────── */}
      {jugadores.length > 0 && (
        <>
          <h1>Jugadores</h1>
          <div className="jugadores-grid">
            {jugadores.map((j) => (
              <div key={j.id} className="jugador-card">
                <PlayerAvatar nombre={j.nombre} fotoUrl={j.foto_url} size={48} />
                <span className="jugador-card-nombre">{j.nombre}</span>
                <button
                  type="button"
                  className="btn-foto"
                  title="Cambiar foto"
                  disabled={uploadingId === j.id}
                  onClick={() => handleFotoClick(j.id)}
                >
                  {uploadingId === j.id ? '…' : '📷'}
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  )
}
