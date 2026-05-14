import { useRef, useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import {
  getTemporadaActiva,
  getReuniones,
  cerrarTemporada,
  designarCampeon,
  getJugadores,
  subirFotoJugador,
  crearJugador,
  inscribirJugadorEnActiva,
} from '../../services/api'
import PlayerAvatar from '../../components/PlayerAvatar'
import PageHeader from '../../components/PageHeader'
import ChampionPickerModal from '../../components/ChampionPickerModal'
import { parseLocalDate, formatDayMonth } from '../../lib/dates'

export default function Dashboard() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [temporada, setTemporada] = useState(undefined)
  const [reuniones, setReuniones] = useState([])
  const [jugadores, setJugadores] = useState([])
  const [cerrando, setCerrando] = useState(false)
  const [error, setError] = useState(null)
  const [uploadingId, setUploadingId] = useState(null)
  const [linkCopied, setLinkCopied] = useState(false)

  const [showNuevoJugador, setShowNuevoJugador] = useState(false)
  const [nuevoNombre, setNuevoNombre] = useState('')
  const [creandoJugador, setCreandoJugador] = useState(false)
  const [errorModal, setErrorModal] = useState(null)

  const [tieModalOpen, setTieModalOpen] = useState(false)
  const [tiedPlayers, setTiedPlayers] = useState([])
  const [closingTemporadaId, setClosingTemporadaId] = useState(null)
  const [designandoCampeon, setDesignandoCampeon] = useState(false)
  const [errorTiebreaker, setErrorTiebreaker] = useState(null)

  const [agregandoId, setAgregandoId] = useState(null)

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
      const response = await cerrarTemporada(token, temporada.id)
      if (response?.tie_detected === true) {
        setTiedPlayers(response.tied_players ?? [])
        setClosingTemporadaId(temporada.id)
        setErrorTiebreaker(null)
        setTieModalOpen(true)
        // Do NOT call cargar() yet — wait for admin to resolve or cancel
      } else {
        await cargar()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setCerrando(false)
    }
  }

  async function handleDesignarCampeon(idJugador) {
    if (!closingTemporadaId) return
    setDesignandoCampeon(true)
    setErrorTiebreaker(null)
    try {
      await designarCampeon(token, closingTemporadaId, idJugador)
      setTieModalOpen(false)
      setTiedPlayers([])
      setClosingTemporadaId(null)
      await cargar()
    } catch (err) {
      setErrorTiebreaker(err.message)
    } finally {
      setDesignandoCampeon(false)
    }
  }

  function handleCancelarTiebreaker() {
    if (designandoCampeon) return
    setTieModalOpen(false)
    setTiedPlayers([])
    setClosingTemporadaId(null)
    setErrorTiebreaker(null)
    cargar()
  }

  async function copiarLink() {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/ranking`)
      setLinkCopied(true)
      setTimeout(() => setLinkCopied(false), 2000)
    } catch {
      // silencioso
    }
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

  function abrirModalNuevoJugador() {
    setNuevoNombre('')
    setErrorModal(null)
    setShowNuevoJugador(true)
  }

  function cerrarModalNuevoJugador() {
    if (creandoJugador) return
    setShowNuevoJugador(false)
    setNuevoNombre('')
    setErrorModal(null)
  }

  async function handleCrearJugador(e) {
    e.preventDefault()
    const nombre = nuevoNombre.trim()
    if (!nombre) {
      setErrorModal('El nombre es obligatorio')
      return
    }
    setCreandoJugador(true)
    setErrorModal(null)
    try {
      await crearJugador(token, nombre)
      setShowNuevoJugador(false)
      setNuevoNombre('')
      await cargar()
    } catch (err) {
      setErrorModal(err.message)
    } finally {
      setCreandoJugador(false)
    }
  }

  async function handleAgregarATemporada(jugadorId) {
    setAgregandoId(jugadorId)
    setError(null)
    try {
      const result = await inscribirJugadorEnActiva(token, jugadorId)
      if (!result) throw new Error('No se pudo inscribir el jugador (404).')
      await cargar()
    } catch (err) {
      setError(err.message)
    } finally {
      setAgregandoId(null)
    }
  }

  if (temporada === undefined) return <p className="status">Cargando…</p>

  const inscritosIds = new Set((temporada?.jugadores ?? []).map((j) => j.id))
  const ordenadas = [...reuniones].sort(
    (a, b) => (b.numero_jornada || 0) - (a.numero_jornada || 0)
  )

  return (
    <section className="editorial-page admin-dashboard">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden-file-input"
        onChange={handleFotoChange}
      />

      <PageHeader
        eyebrow="Panel admin"
        title={<>Tu <span className="ital">mesa.</span></>}
        description={
          temporada
            ? `${temporada.nombre} en curso. Registrá reuniones, gestioná jugadores, cerrá la temporada cuando llegue el momento.`
            : 'Sin temporada activa. Empezá una nueva para comenzar a registrar jornadas.'
        }
      />

      <div className="dashboard-toolbar">
        <Link to="/admin/importar-temporada" className="btn btn-secondary btn-sm">
          Importar temporada histórica
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="stitch" />

      {/* ── Temporada activa o empty state ─────────────────────────── */}
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
                <div className="season-meta">
                  {temporada.total_reuniones} reunión{temporada.total_reuniones !== 1 ? 'es' : ''} ·{' '}
                  {temporada.jugadores.length} jugadores
                </div>
              </div>
              <div className="season-actions">
                <button className="btn btn-secondary btn-sm" onClick={copiarLink}>
                  {linkCopied ? 'Link copiado' : 'Compartir link'}
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={handleCerrar}
                  disabled={cerrando}
                >
                  {cerrando ? 'Cerrando…' : 'Cerrar temporada'}
                </button>
              </div>
            </div>
            <div className="season-card-actions">
              <Link to="/admin/reuniones/nueva" className="btn btn-primary btn-sm">
                + Registrar reunión
              </Link>
            </div>
          </div>

          <div className="page-section-head">
            <h2 className="page-section-title">Reuniones.</h2>
            <span className="eyebrow">
              <span className="dot" />
              {reuniones.length} {reuniones.length === 1 ? 'jornada' : 'jornadas'}
            </span>
          </div>

          {reuniones.length === 0 ? (
            <p className="status historico-empty">Aún no hay reuniones registradas.</p>
          ) : (
            <div className="board board-reuniones board-admin" role="table">
              {ordenadas.map((r) => (
                <div key={r.id} className="row" role="row">
                  <div className="pos num">{String(r.numero_jornada).padStart(2, '0')}</div>
                  <div className="row-fecha">
                    {formatDayMonth(parseLocalDate(r.fecha)) || 'Sin fecha'}
                  </div>
                  <Link
                    to={`/admin/reuniones/${r.id}/editar`}
                    className="btn btn-secondary btn-sm row-edit"
                  >
                    Editar
                  </Link>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      <div className="stitch" />

      {/* ── Catálogo de jugadores ──────────────────────────────────── */}
      <div className="page-section-head">
        <h2 className="page-section-title">Jugadores.</h2>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={abrirModalNuevoJugador}
        >
          + Nuevo jugador
        </button>
      </div>

      {jugadores.length === 0 ? (
        <p className="status historico-empty">Aún no hay jugadores en el catálogo.</p>
      ) : (
        <div className="jugadores-grid">
          {jugadores.map((j) => {
            const yaInscrito = inscritosIds.has(j.id)
            return (
              <div key={j.id} className="jugador-card">
                <PlayerAvatar nombre={j.nombre} fotoUrl={j.foto_url} size={48} />
                <span className="jugador-card-nombre">{j.nombre}</span>
                {temporada && !yaInscrito && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm jugador-card-add"
                    title="Agregar a la temporada activa"
                    disabled={agregandoId === j.id}
                    onClick={() => handleAgregarATemporada(j.id)}
                  >
                    {agregandoId === j.id ? '…' : '+ Temporada'}
                  </button>
                )}
                <button
                  type="button"
                  className="btn-foto"
                  title="Cambiar foto"
                  disabled={uploadingId === j.id}
                  onClick={() => handleFotoClick(j.id)}
                  aria-label="Cambiar foto"
                >
                  {uploadingId === j.id ? (
                    <span>…</span>
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
                      <circle cx="12" cy="13" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* ── Modal Desempate Campeón ────────────────────────────────── */}
      <ChampionPickerModal
        open={tieModalOpen}
        tiedPlayers={tiedPlayers}
        onPick={handleDesignarCampeon}
        onCancel={handleCancelarTiebreaker}
        loading={designandoCampeon}
        error={errorTiebreaker}
      />

      {/* ── Modal Nuevo Jugador ────────────────────────────────────── */}
      {showNuevoJugador && (
        <div className="modal-backdrop" onClick={cerrarModalNuevoJugador}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">Nuevo jugador</h3>
            <form onSubmit={handleCrearJugador}>
              <div className="form-group">
                <label className="form-label" htmlFor="nuevo-jugador-nombre">Nombre</label>
                <input
                  id="nuevo-jugador-nombre"
                  className="form-input"
                  type="text"
                  placeholder="ej: Bahamo"
                  value={nuevoNombre}
                  onChange={(e) => setNuevoNombre(e.target.value)}
                  autoFocus
                  disabled={creandoJugador}
                />
              </div>
              {errorModal && (
                <div className="alert alert-error modal-alert">{errorModal}</div>
              )}
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={cerrarModalNuevoJugador}
                  disabled={creandoJugador}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn btn-primary btn-sm"
                  disabled={creandoJugador || !nuevoNombre.trim()}
                >
                  {creandoJugador ? 'Creando…' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}
