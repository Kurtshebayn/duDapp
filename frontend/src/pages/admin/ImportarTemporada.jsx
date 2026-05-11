import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { importarTemporada } from '../../services/api'
import PageHeader from '../../components/PageHeader'

function hoy() {
  return new Date().toISOString().slice(0, 10)
}

function ErrorPanel({ error }) {
  if (!error) return null

  // Pydantic validation errors come as an array
  if (Array.isArray(error)) {
    return (
      <div className="alert alert-error">
        <p><strong>Error de validación:</strong></p>
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
      return <div className="alert alert-error">{error.message}</div>

    case 'jugadores_no_resueltos':
      return (
        <div className="alert alert-error">
          <p>Estos jugadores del CSV no existen en el catálogo. Creálos primero desde el dashboard:</p>
          <ul>
            {(error.nombres ?? []).map((n) => <li key={n}>{n}</li>)}
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
          Fila {error.fila}: dos jugadores tienen el mismo puntaje ({error.valor}). Revisá la planilla — en Dudo cada posición tiene un puntaje único.
        </div>
      )

    case 'reunion_todos_ausentes':
      return (
        <div className="alert alert-error">
          Fila {error.fila}: todos los jugadores tienen puntaje 0. Una reunión sin asistentes no es válida.
        </div>
      )

    case 'campeon_no_inscripto':
      return <div className="alert alert-error">{error.message}</div>

    case 'csv_header_duplicate':
      return (
        <div className="alert alert-error">
          El CSV tiene un encabezado duplicado: <strong>{error.nombre}</strong>. Cada columna debe tener un nombre único.
        </div>
      )

    case 'csv_encoding_invalid':
      return (
        <div className="alert alert-error">
          El archivo no pudo leerse como UTF-8. Guardá el CSV con codificación UTF-8 desde tu editor o Google Sheets.
        </div>
      )

    case 'csv_invalido':
      return (
        <div className="alert alert-error">
          El archivo no tiene una estructura CSV válida. Verificá que sea un archivo de texto con encabezados y filas de datos.
        </div>
      )

    case 'csv_sin_reuniones':
      return (
        <div className="alert alert-error">
          El CSV tiene encabezados pero ninguna fila de datos. Agregá al menos una reunión.
        </div>
      )

    case 'frontend':
      return <div className="alert alert-error">{error.message}</div>

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
  const navigate = useNavigate()

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
      const detail = err.body?.detail
      if (Array.isArray(detail)) {
        setError(detail)
      } else if (detail && typeof detail === 'object') {
        setError(detail)
      } else {
        setError({ code: 'unknown', message: err.message })
      }
    } finally {
      setSubmitting(false)
    }
  }

  // ── Success state ──────────────────────────────────────────────────
  if (resumen) {
    return (
      <section className="editorial-page admin-form-page">
        <Link to="/admin" className="back-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="m15 18-6-6 6-6" />
          </svg>
          Volver al panel
        </Link>

        <PageHeader
          eyebrow="Importación · Completada"
          title={<>Listo,<br /><span className="ital">importada.</span></>}
          description={`La temporada "${nombre}" se importó correctamente y quedó cerrada.`}
          meta={[
            { label: 'Jugadores', value: resumen.jugadores_inscriptos },
            { label: 'Reuniones', value: resumen.reuniones_creadas },
            { label: 'Posiciones', value: resumen.posiciones_creadas },
            { label: 'Invitados', value: resumen.invitados_inferidos },
          ]}
        />

        <div className="form-actions form-actions-spaced">
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => navigate('/admin')}
          >
            Volver al dashboard
          </button>
        </div>
      </section>
    )
  }

  // ── Form state ─────────────────────────────────────────────────────
  return (
    <section className="editorial-page admin-form-page">
      <Link to="/admin" className="back-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="m15 18-6-6 6-6" />
        </svg>
        Volver al panel
      </Link>

      <PageHeader
        eyebrow="Panel admin · Importar"
        title={<>Importar<br /><span className="ital">temporada histórica.</span></>}
        description="Subí un CSV exportado de Google Sheets para incorporar una temporada cerrada al histórico de la liga. No afecta a la temporada activa."
      />

      <div className="stitch" />

      <ErrorPanel error={error} />

      <form onSubmit={handleSubmit} className="admin-form">
        <div className="form-group">
          <label className="form-label" htmlFor="it-nombre">Nombre de la temporada *</label>
          <input
            id="it-nombre"
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

        <div className="form-group field-narrow">
          <label className="form-label" htmlFor="it-fecha">Fecha de inicio *</label>
          <input
            id="it-fecha"
            className="form-input"
            type="date"
            value={fechaInicio}
            onChange={(e) => setFechaInicio(e.target.value)}
            required
            disabled={submitting}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="it-campeon">Campeón (opcional)</label>
          <input
            id="it-campeon"
            className="form-input"
            type="text"
            value={campeonNombre}
            onChange={(e) => setCampeonNombre(e.target.value)}
            placeholder="Nombre exacto del campeón (debe estar en el CSV)"
            disabled={submitting}
          />
          <span className="form-help">
            Solo completar cuando el campeón no coincide con el jugador de mayor puntaje.
          </span>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="it-archivo">Archivo CSV *</label>
          <input
            id="it-archivo"
            type="file"
            accept=".csv,text/csv"
            className="form-file"
            onChange={(e) => setArchivo(e.target.files[0] ?? null)}
            disabled={submitting}
            required
          />
          <span className="form-help">
            Exportá desde Google Sheets: Archivo → Descargar → Valores separados por comas (.csv).
            Separador <code>;</code> preferido, <code>,</code> también aceptado.
          </span>
        </div>

        <div className="form-actions">
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? 'Importando…' : 'Importar temporada'}
          </button>
          <Link to="/admin" className="btn btn-secondary">
            Cancelar
          </Link>
        </div>
      </form>
    </section>
  )
}
