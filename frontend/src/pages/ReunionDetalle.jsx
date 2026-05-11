import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getResultadosReunion } from '../services/api'
import PlayerAvatar from '../components/PlayerAvatar'
import PageHeader from '../components/PageHeader'
import { parseLocalDate } from '../lib/dates'

/**
 * Detalle de una jornada — todos los puestos con puntos.
 *
 * Posiciones 1-3 reciben tinte metálico (oro/peltre/cobre) en el número.
 * Invitados muestran badge sutil junto al apodo.
 */
export default function ReunionDetalle() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getResultadosReunion(id)
      .then((d) => {
        if (!d) setError('not_found')
        else setData(d)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <p className="status">Cargando…</p>
  if (error === 'not_found') return <p className="status">Reunión no encontrada.</p>
  if (error) return <p className="status">Error al cargar los datos.</p>
  if (!data) return null

  const fecha = parseLocalDate(data.fecha)
  const day = fecha ? fecha.getDate() : null
  const monthName = fecha
    ? new Intl.DateTimeFormat('es', { month: 'long' }).format(fecha)
    : null
  const year = fecha ? fecha.getFullYear() : null

  return (
    <section className="editorial-page reunion-detalle-page">
      <Link to="/reuniones" className="back-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="m15 18-6-6 6-6" />
        </svg>
        Volver a reuniones
      </Link>

      <PageHeader
        eyebrow={`Jornada ${data.numero_jornada}${year ? ` · ${year}` : ''}`}
        title={
          fecha ? (
            <>
              {day} de<br />
              <span className="ital">{monthName}.</span>
            </>
          ) : (
            <>Sin <span className="ital">fecha.</span></>
          )
        }
        description={`${data.posiciones.length} ${data.posiciones.length === 1 ? 'jugador' : 'jugadores'} en la mesa.`}
      />

      <div className="stitch" />

      <div className="page-section-head">
        <h2 className="page-section-title">Resultados.</h2>
        <span className="eyebrow">
          <span className="dot" />
          Por puesto · puntos
        </span>
      </div>

      <div className="board board-reunion-detalle" role="table" aria-label="Resultados de la jornada">
        <div className="row head" role="row">
          <div role="columnheader">#</div>
          <div role="columnheader">Jugador</div>
          <div role="columnheader" className="num-cell">Puntos</div>
        </div>

        {data.posiciones.map((p) => (
          <div className="row" key={`${p.posicion}-${p.nombre}`} role="row">
            <div className={`pos num ${p.posicion <= 3 ? `pos-${p.posicion}` : ''}`}>
              {String(p.posicion).padStart(2, '0')}
            </div>
            <div className="name">
              <PlayerAvatar nombre={p.nombre} fotoUrl={p.foto_url} size={36} />
              <div className="name-text">
                <span className="apodo">
                  {p.nombre}
                  {p.es_invitado && <span className="invitado-tag">invitado</span>}
                </span>
              </div>
            </div>
            <div className="num-cell points">{p.puntos}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
