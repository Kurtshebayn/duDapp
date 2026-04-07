import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getReuniones } from '../services/api'

function formatFecha(iso) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function Reuniones() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getReuniones()
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
      <h1>Reuniones</h1>
      <div className="list">
        {[...data].reverse().map((r) => (
          <Link key={r.id} to={`/reuniones/${r.id}`} className="list-item">
            <div className="list-item-left">
              <span className="jornada-badge">Jornada {r.numero_jornada}</span>
              <span className="list-item-date">{formatFecha(r.fecha)}</span>
            </div>
            <span className="arrow">›</span>
          </Link>
        ))}
      </div>
    </>
  )
}
