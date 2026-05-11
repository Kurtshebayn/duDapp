import { createContext, useContext, useMemo, useState } from 'react'

const AuthContext = createContext(null)

/**
 * Decodifica el payload de un JWT sin validar firma (es responsabilidad del
 * backend). Devuelve null si el token está malformado.
 */
function parseJwt(token) {
  if (!token) return null
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(decodeURIComponent(escape(json)))
  } catch {
    return null
  }
}

/**
 * Deriva info de usuario desde el token. Defensivo: si el JWT no expone
 * name/email cae a "Admin" / "A".
 */
function deriveUser(token) {
  const claims = parseJwt(token)
  if (!claims) return null

  const email = claims.email || claims.sub || ''
  const handle = email.includes('@') ? email.split('@')[0] : email
  const displayName = claims.name || handle || 'Admin'
  const initial = (displayName[0] || 'A').toUpperCase()

  return { email, displayName, initial, claims }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))

  const user = useMemo(() => deriveUser(token), [token])

  function login(newToken) {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  function logout() {
    localStorage.removeItem('token')
    setToken(null)
  }

  const value = {
    token,
    user,
    login,
    logout,
    isAuthenticated: !!token,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
