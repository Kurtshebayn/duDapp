import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import {
  getTemporadaActiva,
  getResultadosReunion,
  registrarReunion,
  editarReunion,
} from '../../services/api'
import PosicionadorReunion from '../../components/PosicionadorReunion'

function hoy() {
  return new Date().toISOString().slice(0, 10)
}

export default function GestionReunion({ modo }) {
  const { token } = useAuth()
  const navigate = useNavigate()
  const { id: reunionId } = useParams()

  const [temporada, setTemporada] = useState(null)
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

  if (loading) return <p className="status">Cargando...</p>
  if (!temporada) return null

  return (
    <>
      <h1>{modo === 'crear' ? 'Registrar reunión' : 'Editar reunión'}</h1>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-group" style={{ maxWidth: 220 }}>
        <label className="form-label">Fecha</label>
        <input
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

      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <button
          className="btn btn-primary"
          onClick={handleGuardar}
          disabled={saving}
        >
          {saving ? 'Guardando...' : modo === 'crear' ? 'Confirmar reunión' : 'Guardar cambios'}
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/admin')}>
          Cancelar
        </button>
      </div>
    </>
  )
}
