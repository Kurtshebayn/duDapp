import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

/**
 * Pill de identidad arriba a la derecha.
 * Solo se renderiza cuando hay sesión activa (chequea isAuthenticated arriba).
 *
 * Usa <details>/<summary> nativo para el dropdown — cero JS para abrir/cerrar.
 * El único listener es para cerrar al hacer click fuera.
 */
export default function UserPill() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const detailsRef = useRef(null)

  // Cerrar al click fuera
  useEffect(() => {
    function handleClickOutside(e) {
      const el = detailsRef.current
      if (el && el.open && !el.contains(e.target)) {
        el.open = false
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function close() {
    if (detailsRef.current) detailsRef.current.open = false
  }

  function go(path) {
    return (e) => {
      e.preventDefault()
      close()
      navigate(path)
    }
  }

  function handleLogout() {
    close()
    logout()
    navigate('/ranking')
  }

  const displayName = user?.displayName || 'Admin'
  const initial = user?.initial || 'A'

  return (
    <details className="user-pill" ref={detailsRef}>
      <summary aria-label="Menú de administrador">
        <span className="avatar" aria-hidden="true">{initial}</span>
        <span className="user-name">{displayName}</span>
        <svg className="chev" viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="m6 9 6 6 6-6"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </summary>

      <div className="user-menu" role="menu">
        <div className="user-menu-head">
          <div className="who">{displayName}</div>
          <div className="role">Administrador</div>
        </div>

        <a href="/admin" onClick={go('/admin')} role="menuitem">
          <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="3" y="3" width="7" height="9" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5"/>
            <rect x="14" y="3" width="7" height="5" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5"/>
            <rect x="14" y="12" width="7" height="9" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5"/>
            <rect x="3" y="16" width="7" height="5" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5"/>
          </svg>
          Panel admin
        </a>

        <a href="/admin/reuniones/nueva" onClick={go('/admin/reuniones/nueva')} role="menuitem">
          <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
          </svg>
          Registrar reunión
        </a>

        <hr />

        <button type="button" className="danger" onClick={handleLogout} role="menuitem">
          <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="m16 17 5-5-5-5M21 12H9" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Cerrar sesión
        </button>
      </div>
    </details>
  )
}
