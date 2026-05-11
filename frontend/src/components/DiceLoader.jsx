import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const SLOW_THRESHOLD_MS = 3000
const FADE_OUT_MS = 400

/**
 * Loader de cold start. Detecta cuando el backend tarda más de 3s en
 * responder y muestra un overlay full-screen con un dado 3D rodando.
 *
 * Estados:
 *   idle    → request en vuelo, todavía dentro del threshold (no se renderiza)
 *   visible → pasaron los 3s, mostramos el loader
 *   hiding  → el backend respondió, animamos fade-out durante FADE_OUT_MS
 *   gone    → desmontado, no se renderiza
 *
 * Se monta una sola vez al inicio de la sesión. Si la primera request es
 * rápida (server caliente), el componente nunca se ve.
 */
export default function DiceLoader() {
  const [phase, setPhase] = useState('idle')

  useEffect(() => {
    let cancelled = false
    let showTimer
    let hideTimer

    showTimer = setTimeout(() => {
      if (!cancelled) setPhase('visible')
    }, SLOW_THRESHOLD_MS)

    fetch(`${API_URL}/health`)
      .then(() => finish())
      .catch(() => finish())

    function finish() {
      if (cancelled) return
      clearTimeout(showTimer)
      setPhase((current) => {
        if (current === 'visible') {
          hideTimer = setTimeout(() => {
            if (!cancelled) setPhase('gone')
          }, FADE_OUT_MS)
          return 'hiding'
        }
        return 'gone'
      })
    }

    return () => {
      cancelled = true
      clearTimeout(showTimer)
      clearTimeout(hideTimer)
    }
  }, [])

  if (phase === 'idle' || phase === 'gone') return null

  return (
    <div className={`dice-loader ${phase === 'hiding' ? 'hiding' : ''}`} role="status" aria-live="polite">
      <div className="dice-loader-stage">
        <span className="eyebrow">
          <span className="dot" />
          Conectando · Liga de Dudo
        </span>

        <div className="dice-3d-platform" aria-hidden="true">
          <div className="dice-3d-cube">
            <div className="dice-face dice-face-front">
              <span className="dice-pip" />
            </div>
            <div className="dice-face dice-face-back">
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
            </div>
            <div className="dice-face dice-face-right">
              <span className="dice-pip" />
              <span className="dice-pip" />
            </div>
            <div className="dice-face dice-face-left">
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
            </div>
            <div className="dice-face dice-face-top">
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
            </div>
            <div className="dice-face dice-face-bot">
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
              <span className="dice-pip" />
            </div>
          </div>
        </div>

        <h2 className="dice-loader-title">
          Despertando<br />
          <span className="ital">la mesa.</span>
        </h2>
        <p className="dice-loader-sub">
          La base de datos descansa entre reuniones.
          Tarda unos segundos en arrancar — los dados ya están rodando.
        </p>

        <div className="dice-loader-progress">
          <span className="bar" aria-hidden="true" />
          <span>~10 segundos</span>
        </div>
      </div>
    </div>
  )
}
