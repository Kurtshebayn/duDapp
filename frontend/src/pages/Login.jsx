import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { login as apiLogin } from '../services/api'
import DiceIcon from '../components/DiceIcon'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [identificador, setIdentificador] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await apiLogin(identificador, password)
      login(data.access_token)
      navigate('/admin')
    } catch (err) {
      setError('Credenciales incorrectas.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="editorial-page login-page">
      <Link to="/ranking" className="back-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="m15 18-6-6 6-6" />
        </svg>
        Volver a posiciones
      </Link>

      <div className="login-card">
        <DiceIcon size={56} className="login-dice" />

        <span className="eyebrow login-eyebrow">
          <span className="dot" />
          Admin · Liga de Dudo
        </span>

        <h1 className="display login-title">
          Acceso al<br />
          <span className="ital">panel.</span>
        </h1>

        <p className="login-sub">
          Ingresá con tus credenciales para registrar reuniones y administrar la liga.
        </p>

        {error && <div className="alert alert-error login-alert">{error}</div>}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label className="form-label" htmlFor="login-id">Nombre o email</label>
            <input
              id="login-id"
              className="form-input"
              type="text"
              value={identificador}
              onChange={(e) => setIdentificador(e.target.value)}
              placeholder="admin@dudo.com"
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="login-pwd">Contraseña</label>
            <input
              id="login-pwd"
              className="form-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            className="btn btn-primary login-submit"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Ingresando…' : 'Ingresar'}
          </button>
        </form>
      </div>
    </section>
  )
}
