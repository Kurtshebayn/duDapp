import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Nav() {
  const { isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/ranking')
  }

  return (
    <nav>
      <NavLink to="/ranking" className="nav-brand">🎲 Liga de Dudo</NavLink>
      <div className="nav-links">
        <NavLink to="/ranking">Ranking</NavLink>
        <NavLink to="/reuniones">Reuniones</NavLink>
        <NavLink to="/estadisticas">Estadísticas</NavLink>
        {isAuthenticated ? (
          <>
            <NavLink to="/admin">Admin</NavLink>
            <button
              onClick={handleLogout}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '0.5rem 0.75rem',
                fontSize: 'inherit',
                borderRadius: 'var(--radius)',
              }}
            >
              Salir
            </button>
          </>
        ) : (
          <NavLink to="/login">Admin</NavLink>
        )}
      </div>
    </nav>
  )
}
