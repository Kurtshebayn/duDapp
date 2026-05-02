import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { importarTemporada } from '../../services/api'

function hoy() {
  return new Date().toISOString().slice(0, 10)
}

function ErrorPanel({ error }) {
  if (!error) return null

  // Pydantic validation errors come as an array under body.detail
  if (Array.isArray(error)) {
    return (
      <div className="alert alert-error">
        <p>Error de validación:</p>
        <ul>
          {error.map((e, i) => (
            <li key={i}>
              {e.loc ? `${e.loc.join(' → ')}: ` : ''}{e.msg}
            </li>
          ))}
        </ul>
      </div>
    )
  }

  switch (error.code) {
    case 'temporada_duplicada':
      return (
        <div className="alert alert-error">
          {error.message}
        </div>
      )

    case 'jugadores_no_resueltos':
      return (
        <div className="alert alert-error">
          <p>
            Estos jugadores del CSV no existen en el catálogo. Creálos primero desde el
            dashboard:
          </p>
          <ul>
            {(error.nombres ?? []).map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </div>
      )

    case 'puntaje_invalido':
      return (
        <div className="alert alert-error">
          <p>Hay celdas con puntajes inválidos (deben ser números entre 0 y 15):</p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fila</th>
                  <th>Columna (jugador)</th>
                  <th>Valor encontrado</th>
                </tr>
              </thead>
              <tbody>
                {(error.errores ?? []).map((e, i) => (
                  <tr key={i}>
                    <td>{e.fila}</td>
                    <td>{e.columna}</td>
                    <td><code>{e.valor}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )

    case 'puntajes_duplicados':
      return (
        <div className="alert alert-error">
          Fila {error.fila}: dos jugadores tienen el mismo puntaje ({error.valor}). Revisá
          la planilla — en Dudo cada posición tiene un puntaje único.
        </div>
      )

    case 'reunion_todos_ausentes':
      return (
        <div className="alert alert-error">
          Fila {error.fila}: todos los jugadores tienen puntaje 0. Una reunión sin
          asistentes no es válida.
        </div>
      )

    case 'campeon_no_inscripto':
      return (
        <div className="alert alert-error">
          {error.message}
        </div>
      )

    case 'csv_header_duplicate':
      return (
        <div className="alert alert-error">
          El CSV tiene un encabezado duplicado: <strong>{error.nombre}</strong>. Cada
          columna debe tener un nombre único.
        </div>
      )

    case 'csv_encoding_invalid':
      return (
        <div className="alert alert-error">
          El archivo no pudo leerse como UTF-8. Guardá el CSV con codificación UTF-8 desde
          tu editor o Google Sheets.
        </div>
      )

    case 'csv_invalido':
      return (
        <div className="alert alert-error">
          El archivo no tiene una estructura CSV válida. Verificá que sea un archivo de
          texto con encabezados y filas de datos.
        </div>
      )

    case 'csv_sin_reuniones':
      return (
        <div className="alert alert-error">
          El CSV tiene encabezados pero ninguna fila de datos. Agregá al menos una reunión.
        </div>
      )

    case 'frontend':
      return (
        <div className="alert alert-error">
          {error.message}
        </div>
      )

    default:
      return (
        <div className="alert alert-error">
          {error.message ?? 'Ocurrió un error inesperado. Revisá los datos e intentá de nuevo.'}
        </div>
      )
  }
}

export default function ImportarTemporada() {
  const { token } = useAuth()

  const [nombre, setNombre] = useState('')
  const [fechaInicio, setFechaInicio] = useState(hoy())
  const [campeonNombre, setCampeonNombre] = useState('')
  const [archivo, setArchivo] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [resumen, setResumen] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!archivo) {
      setError({ code: 'frontend', message: 'Seleccioná un archivo CSV antes de importar.' })
      return
    }
    setSubmitting(true)
    setError(null)
    setResumen(null)
    try {
      const form = new FormData()
      form.append('nombre', nombre)
      form.append('fecha_inicio', fechaInicio)
      form.append('archivo', archivo)
      if (campeonNombre.trim()) {
        form.append('campeon_nombre', campeonNombre.trim())
      }
      const data = await importarTemporada(token, form)
      setResumen(data.resumen_import)
    } catch (err) {
      // err.body is the full parsed JSON body (set by the patched apiFetch)
      const detail = err.body?.detail
      if (Array.isArray(detail)) {
        // Pydantic validation error array
        setError(detail)
      } else if (detail && typeof detail === 'object') {
        // Our structured dict error: { code, message, ... }
        setError(detail)
      } else {
        // Fallback: plain string or no body
        setError({ code: 'unknown', message: err.message })
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (resumen) {
    return (
      <>
        <h1>Importación completada</h1>
        <div className="season-card">
          <div className="season-card-header">
            <div className="season-name">Resumen de importación</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Jugadores inscriptos</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{resumen.jugadores_inscriptos}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Reuniones creadas</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{resumen.reuniones_creadas}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Posiciones creadas</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{resumen.posiciones_creadas}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Invitados inferidos</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{resumen.invitados_inferidos}</div>
            </div>
          </div>
        </div>
        <div style={{ marginTop: '1.5rem' }}>
          <Link to="/admin" className="btn btn-primary">
            Volver al dashboard
          </Link>
        </div>
      </>
    )
  }

  return (
    <>
      <h1>Importar temporada histórica</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
        Importá una temporada cerrada desde un archivo CSV exportado de Google Sheets.
        La temporada se creará con estado <strong>cerrada</strong> y no afectará a la
        temporada activa actual.
      </p>

      <ErrorPanel error={error} />

      <form onSubmit={handleSubmit} style={{ maxWidth: 480 }}>
        <div className="form-group">
          <label className="form-label">Nombre de la temporada *</label>
          <input
            className="form-input"
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ej: Liga 2022"
            required
            disabled={submitting}
            autoFocus
          />
        </div>

        <div className="form-group">
          <label className="form-label">Fecha de inicio *</label>
          <input
            className="form-input"
            type="date"
            value={fechaInicio}
            onChange={(e) => setFechaInicio(e.target.value)}
            required
            disabled={submitting}
            style={{ maxWidth: 220 }}
          />
        </div>

        <div className="form-group">
          <label className="form-label">
            Campeón (opcional)
          </label>
          <input
            className="form-input"
            type="text"
            value={campeonNombre}
            onChange={(e) => setCampeonNombre(e.target.value)}
            placeholder="Nombre exacto del campeón (debe estar en el CSV)"
            disabled={submitting}
          />
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Solo completar cuando el campeón no coincide con el jugador de mayor puntaje.
          </span>
        </div>

        <div className="form-group">
          <label className="form-label">Archivo CSV *</label>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setArchivo(e.target.files[0] ?? null)}
            disabled={submitting}
            required
          />
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.25rem' }}>
            Exportá desde Google Sheets: Archivo → Descargar → Valores separados por comas (.csv).
            Separador <code>;</code> preferido, <code>,</code> también aceptado.
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginTop: '1rem' }}>
          <button
            className="btn btn-primary"
            type="submit"
            disabled={submitting}
          >
            {submitting ? 'Importando...' : 'Importar temporada'}
          </button>
          <Link to="/admin" className="btn btn-secondary">
            Cancelar
          </Link>
        </div>
      </form>
    </>
  )
}
