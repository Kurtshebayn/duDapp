import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getResultadosReunion } from '../services/api'

function formatFecha(iso) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

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

  if (loading) return <p className="status">Cargando...</p>
  if (error === 'not_found') return <p className="status">Reunión no encontrada.</p>
  if (error) return <p className="status">Error al cargar los datos.</p>
  if (!data) return null

  return (
    <>
      <Link to="/reuniones" className="back-link">← Reuniones</Link>
      <h1>Jornada {data.numero_jornada} · {formatFecha(data.fecha)}</h1>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Jugador</th>
              <th>Puntos</th>
            </tr>
          </thead>
          <tbody>
            {data.posiciones.map((p) => (
              <tr key={`${p.posicion}-${p.nombre}`}>
                <td>
                  <span className={`rank-num rank-${p.posicion}`}>
                    {MEDAL[p.posicion] ?? p.posicion}
                  </span>
                </td>
                <td>
                  {p.nombre}
                  {p.es_invitado && <span className="badge-invitado">invitado</span>}
                </td>
                <td>{p.puntos}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
