import { useState, useEffect } from 'react'
import { getRanking } from '../services/api'
import PlayerAvatar from '../components/PlayerAvatar'

const MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

export default function Ranking() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getRanking()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="status">Cargando...</p>
  if (error) return <p className="status">Error al cargar los datos.</p>
  if (!data) return <p className="status">No hay temporada activa.</p>
  if (data.length === 0) return <p className="status">Aún no hay reuniones registradas.</p>

  return (
    <>
      <h1>Tabla de posiciones</h1>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Jugador</th>
              <th>Puntos</th>
              <th>Asistencias</th>
            </tr>
          </thead>
          <tbody>
            {data.map((entry, i) => {
              const pos = i + 1
              return (
                <tr key={entry.id_jugador}>
                  <td>
                    <span className={`rank-num rank-${pos}`}>
                      {MEDAL[pos] ?? pos}
                    </span>
                  </td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={entry.nombre} fotoUrl={entry.foto_url} />
                      {entry.nombre}
                    </span>
                  </td>
                  <td><strong>{entry.puntos}</strong></td>
                  <td>{entry.asistencias}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </>
  )
}
