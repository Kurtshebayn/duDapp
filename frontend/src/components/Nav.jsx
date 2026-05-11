import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import DiceIcon from './DiceIcon'
import UserPill from './UserPill'

/**
 * Header de la app. Renderiza un grid de 3 columnas:
 *   [spacer · nav pill centrada · user-pill (solo si hay sesión)]
 *
 * En mobile el spacer colapsa, la nav se centra y la user-pill se reduce
 * a solo el avatar. Por debajo de 420px desaparece el texto "Liga de Dudo"
 * para que las 3 tabs siempre quepan.
 */
export default function Nav() {
  const { isAuthenticated } = useAuth()

  return (
    <header className="app-header">
      <div className="app-header-spacer" aria-hidden="true" />

      <nav className="nav-pill" aria-label="Navegación principal">
        <NavLink to="/ranking" className="brand" end>
          <DiceIcon size={26} className="brand-dice" />
          <span className="brand-name">Liga de Dudo</span>
        </NavLink>
        <NavLink to="/ranking" className="tab" end>Posiciones</NavLink>
        <NavLink to="/reuniones" className="tab">Reuniones</NavLink>
        <NavLink to="/historico" className="tab">Histórico</NavLink>
      </nav>

      {isAuthenticated ? (
        <UserPill />
      ) : (
        <NavLink to="/login" className="admin-link-pill">Admin</NavLink>
      )}
    </header>
  )
}
