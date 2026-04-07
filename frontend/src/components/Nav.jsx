import { NavLink } from 'react-router-dom'

export default function Nav() {
  return (
    <nav>
      <NavLink to="/ranking" className="nav-brand">🎲 Liga de Dudo</NavLink>
      <div className="nav-links">
        <NavLink to="/ranking">Ranking</NavLink>
        <NavLink to="/reuniones">Reuniones</NavLink>
        <NavLink to="/estadisticas">Estadísticas</NavLink>
      </div>
    </nav>
  )
}
