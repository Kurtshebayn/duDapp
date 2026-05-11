import { useRef, useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { getJugadores, crearTemporada, subirFotoJugador } from '../../services/api'
import PlayerAvatar from '../../components/PlayerAvatar'
import PageHeader from '../../components/PageHeader'

const CAMERA_ICON = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
    <circle cx="12" cy="13" r="3" />
  </svg>
)

export default function CrearTemporada() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [uploadingId, setUploadingId] = useState(null)
  const [nombre, setNombre] = useState('')
  const [fechaInicio, setFechaInicio] = useState(() => new Date().toISOString().slice(0, 10))
  const [jugadoresExistentes, setJugadoresExistentes] = useState([])
  const [seleccionados, setSeleccionados] = useState(new Set())
  const [nuevosNombres, setNuevosNombres] = useState([])
  const [nuevoInput, setNuevoInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getJugadores().then((data) => setJugadoresExistentes(data ?? []))
  }, [])

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
      setJugadoresExistentes((prev) =>
        prev.map((j) => (j.id === jugadorId ? { ...j, foto_url: updated.foto_url } : j))
      )
    } catch {
      // silencioso
    } finally {
      setUploadingId(null)
    }
  }

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
    <section className="editorial-page admin-form-page">
      <Link to="/admin" className="back-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="m15 18-6-6 6-6" />
        </svg>
        Volver al panel
      </Link>

      <PageHeader
        eyebrow="Panel admin · Nueva temporada"
        title={<>Empezá una<br /><span className="ital">temporada.</span></>}
        description="Definí el nombre, la fecha de inicio y la lista de jugadores que van a competir. Podés sumar jugadores nuevos o reusar los del catálogo."
      />

      <div className="stitch" />

      {error && <div className="alert alert-error">{error}</div>}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden-file-input"
        onChange={handleFotoChange}
      />

      <form onSubmit={handleSubmit} className="admin-form">
        <div className="form-group">
          <label className="form-label" htmlFor="ct-nombre">Nombre de la temporada</label>
          <input
            id="ct-nombre"
            className="form-input"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ej: Liga 2026"
            required
            autoFocus
          />
        </div>

        <div className="form-group field-narrow">
          <label className="form-label" htmlFor="ct-fecha">Fecha de inicio</label>
          <input
            id="ct-fecha"
            className="form-input"
            type="date"
            value={fechaInicio}
            onChange={(e) => setFechaInicio(e.target.value)}
            required
          />
        </div>

        {jugadoresExistentes.length > 0 && (
          <div className="form-group">
            <div className="page-section-head">
              <h2 className="page-section-title">Jugadores del catálogo.</h2>
              <span className="eyebrow">
                <span className="dot" />
                {seleccionados.size} de {jugadoresExistentes.length} seleccionados
              </span>
            </div>
            <div className="checkbox-grid">
              {jugadoresExistentes.map((j) => (
                <div key={j.id} className="checkbox-item-wrap">
                  <label
                    className={`checkbox-item${seleccionados.has(j.id) ? ' selected' : ''}`}
                    onClick={() => toggleSeleccionado(j.id)}
                  >
                    <input type="checkbox" readOnly checked={seleccionados.has(j.id)} />
                    <PlayerAvatar nombre={j.nombre} fotoUrl={j.foto_url} size={22} />
                    {j.nombre}
                  </label>
                  <button
                    type="button"
                    className="btn-foto"
                    title="Cambiar foto"
                    aria-label="Cambiar foto"
                    disabled={uploadingId === j.id}
                    onClick={() => handleFotoClick(j.id)}
                  >
                    {uploadingId === j.id ? <span>…</span> : CAMERA_ICON}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="form-group">
          <div className="page-section-head">
            <h2 className="page-section-title">Jugadores nuevos.</h2>
            {nuevosNombres.length > 0 && (
              <span className="eyebrow">
                <span className="dot" />
                {nuevosNombres.length} para crear
              </span>
            )}
          </div>
          <div className="form-inline">
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
            <div className="chip-list">
              {nuevosNombres.map((n) => (
                <span key={n} className="chip chip-player">
                  {n}
                  <button
                    type="button"
                    className="btn-remove"
                    onClick={() => quitarNuevo(n)}
                    aria-label={`Quitar ${n}`}
                  >×</button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="form-actions">
          <button className="btn btn-primary" type="submit" disabled={loading || totalJugadores === 0}>
            {loading ? 'Creando…' : `Crear temporada (${totalJugadores} jugadores)`}
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/admin')}>
            Cancelar
          </button>
        </div>
      </form>
    </section>
  )
}
