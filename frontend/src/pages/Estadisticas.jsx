import { useState, useEffect } from 'react'
import { getEstadisticas } from '../services/api'
import PlayerAvatar from '../components/PlayerAvatar'

const PODIO = ['🥇', '🥈', '🥉']

export default function Estadisticas() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getEstadisticas()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="status">Cargando...</p>
  if (error) return <p className="status">Error al cargar los datos.</p>
  if (!data) return <p className="status">No hay temporada activa.</p>
  if (data.ranking.length === 0) return <p className="status">Aún no hay reuniones registradas.</p>

  const { top3, mejor_promedio, mas_inasistencias, ranking } = data

  return (
    <>
      <h1>Estadísticas</h1>

      {top3.length > 0 && (
        <>
          <p className="section-title">Top 3</p>
          <div className="top3">
            {top3.map((e, i) => (
              <div key={e.id_jugador} className="top3-card">
                <div className="top3-pos">{PODIO[i]}</div>
                <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} size={48} />
                <div className="top3-nombre">{e.nombre}</div>
                <div className="top3-puntos">{e.puntos} pts · {e.asistencias} asist.</div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="highlight-cards">
        {mejor_promedio && (
          <div className="highlight-card">
            <div className="card-label">Mejor promedio</div>
            <div className="name">{mejor_promedio.nombre}</div>
            <div className="stat">{mejor_promedio.promedio} pts/jornada</div>
          </div>
        )}
        {mas_inasistencias && (
          <div className="highlight-card">
            <div className="card-label">Más inasistencias</div>
            <div className="name">{mas_inasistencias.nombre}</div>
            <div className="stat">{mas_inasistencias.inasistencias} ausencias</div>
          </div>
        )}
      </div>

      <p className="section-title">Todos los jugadores</p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Jugador</th>
              <th>Puntos</th>
              <th>Asist.</th>
              <th>Promedio</th>
              <th>Inas.</th>
            </tr>
          </thead>
          <tbody>
            {ranking.map((e, i) => (
              <tr key={e.id_jugador}>
                <td><span className={`rank-num rank-${i + 1}`}>{i + 1}</span></td>
                <td>
                  <span className="player-name-cell">
                    <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                    {e.nombre}
                  </span>
                </td>
                <td><strong>{e.puntos}</strong></td>
                <td>{e.asistencias}</td>
                <td>{e.promedio}</td>
                <td>{e.inasistencias}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
