import { useState, useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import {
  getTemporadaActiva,
  getResultadosReunion,
  registrarReunion,
  editarReunion,
} from '../../services/api'
import PosicionadorReunion from '../../components/PosicionadorReunion'
import PageHeader from '../../components/PageHeader'
import { parseLocalDate, formatDayMonth } from '../../lib/dates'

function hoy() {
  return new Date().toISOString().slice(0, 10)
}

export default function GestionReunion({ modo }) {
  const { token } = useAuth()
  const navigate = useNavigate()
  const { id: reunionId } = useParams()

  const [temporada, setTemporada] = useState(null)
  const [reunionMeta, setReunionMeta] = useState(null) // numero_jornada al editar
  const [fecha, setFecha] = useState(hoy())
  const [posiciones, setPosiciones] = useState([])
  const [posicionesIniciales, setPosicionesIniciales] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function init() {
      try {
        const t = await getTemporadaActiva()
        if (!t) { navigate('/admin'); return }
        setTemporada(t)

        if (modo === 'editar') {
          const reunion = await getResultadosReunion(reunionId)
          if (!reunion) { navigate('/admin'); return }
          setFecha(reunion.fecha ?? hoy())
          setReunionMeta({ numero_jornada: reunion.numero_jornada })
          const iniciales = reunion.posiciones.map((p) => ({
            posicion: p.posicion,
            id_jugador: p.id_jugador,
            es_invitado: p.es_invitado,
          }))
          setPosicionesIniciales(iniciales)
          setPosiciones(iniciales)
        }
      } catch {
        setError('Error al cargar datos.')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleGuardar() {
    if (posiciones.length === 0) {
      setError('Registrá al menos una posición.')
      return
    }
    setError(null)
    setSaving(true)
    try {
      if (modo === 'crear') {
        await registrarReunion(token, temporada.id, fecha, posiciones)
      } else {
        await editarReunion(token, reunionId, fecha, posiciones)
      }
      navigate('/admin')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="status">Cargando…</p>
  if (!temporada) return null

  const isEdit = modo === 'editar'
  const fechaParsed = parseLocalDate(fecha)
  const fechaLabel = fechaParsed ? formatDayMonth(fechaParsed) : null

  return (
    <section className="editorial-page admin-form-page">
      <Link to="/admin" className="back-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="m15 18-6-6 6-6" />
        </svg>
        Volver al panel
      </Link>

      <PageHeader
        eyebrow={
          isEdit && reunionMeta
            ? `Editar · Jornada ${reunionMeta.numero_jornada}`
            : `Panel admin · ${temporada.nombre}`
        }
        title={
          isEdit
            ? <>Editar la<br /><span className="ital">jornada.</span></>
            : <>Nueva<br /><span className="ital">jornada.</span></>
        }
        description={
          isEdit
            ? 'Reordená posiciones, cambiá fecha o sumá invitados. Los puntos se recalculan automáticamente al guardar.'
            : 'Asigná posiciones arrastrando jugadores. Los puntos se calculan según el puesto: 15 al primero, 14 al segundo, así hacia abajo.'
        }
      />

      <div className="stitch" />

      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-group field-narrow">
        <label className="form-label" htmlFor="gr-fecha">
          Fecha {fechaLabel && <span className="form-label-hint">· {fechaLabel}</span>}
        </label>
        <input
          id="gr-fecha"
          className="form-input"
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
          required
        />
      </div>

      <PosicionadorReunion
        jugadores={temporada.jugadores}
        posicionesIniciales={posicionesIniciales}
        onChange={setPosiciones}
      />

      <div className="form-actions">
        <button
          className="btn btn-primary"
          onClick={handleGuardar}
          disabled={saving}
        >
          {saving ? 'Guardando…' : isEdit ? 'Guardar cambios' : 'Confirmar reunión'}
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/admin')}>
          Cancelar
        </button>
      </div>
    </section>
  )
}
