import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getReuniones, getTemporadaActiva } from '../services/api'
import PageHeader from '../components/PageHeader'
import { parseLocalDate, formatShortDate, formatDayMonth, maxDate } from '../lib/dates'

/**
 * Lista editorial de jornadas de la temporada activa.
 *
 * Cada fila es una jornada — número grande en serif italic + fecha en serif
 * + arrow al detalle. Mismo lenguaje del leaderboard pero scope distinto.
 */
export default function Reuniones() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([getReuniones(), getTemporadaActiva()])
      .then(([reuniones, temporada]) => {
        setData({ reuniones, temporada })
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="status">Cargando…</p>
  if (error) return <p className="status">Error al cargar los datos.</p>
  if (!data || !data.reuniones) return <p className="status">No hay temporada activa.</p>
  if (data.reuniones.length === 0) {
    return <p className="status">Aún no hay reuniones registradas.</p>
  }

  const reuniones = data.reuniones
  const temporada = data.temporada || {}

  // Más recientes primero (no asumo orden del backend)
  const ordenadas = [...reuniones].sort(
    (a, b) => (b.numero_jornada || 0) - (a.numero_jornada || 0)
  )

  const ultimaFecha = formatShortDate(
    maxDate(reuniones.map((r) => parseLocalDate(r.fecha)))
  )

  return (
    <section className="editorial-page reuniones-page">
      <PageHeader
        eyebrow={temporada.nombre ? `${temporada.nombre} · En curso` : 'Temporada activa'}
        title={
          <>
            Las<br />
            <span className="ital">jornadas.</span>
          </>
        }
        description="Cada reunión es una historia. Haz click en una jornada para ver quién jugó, quién ganó, y quién no se presentó."
        meta={[
          { label: 'Total', value: reuniones.length },
          {
            label: 'Última',
            value: ultimaFecha ? ultimaFecha.day : '—',
            unit: ultimaFecha ? ultimaFecha.month : null,
          },
        ]}
      />

      <div className="stitch" />

      <div className="page-section-head">
        <h2 className="page-section-title">Todas las jornadas.</h2>
        <span className="eyebrow">
          <span className="dot" />
          {reuniones.length} {reuniones.length === 1 ? 'reunión' : 'reuniones'}
        </span>
      </div>

      <div className="board board-reuniones" role="table" aria-label="Lista de jornadas">
        {ordenadas.map((r) => (
          <Link
            key={r.id}
            to={`/reuniones/${r.id}`}
            className="row"
            role="row"
          >
            <div className="pos num">{String(r.numero_jornada).padStart(2, '0')}</div>
            <div className="row-fecha">
              {formatDayMonth(parseLocalDate(r.fecha)) || 'Sin fecha'}
            </div>
            <div className="arrow" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 6l6 6-6 6" />
              </svg>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}
