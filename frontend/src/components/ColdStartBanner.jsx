import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const SLOW_THRESHOLD_MS = 3000

export default function ColdStartBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    let timer
    let cancelled = false

    timer = setTimeout(() => {
      if (!cancelled) setVisible(true)
    }, SLOW_THRESHOLD_MS)

    fetch(`${API_URL}/health`)
      .then(() => {
        clearTimeout(timer)
        if (!cancelled) setVisible(false)
      })
      .catch(() => {
        clearTimeout(timer)
        if (!cancelled) setVisible(false)
      })

    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [])

  if (!visible) return null

  return (
    <div className="cold-start-banner">
      <span className="cold-start-spinner" />
      El servidor está despertando, puede tardar hasta 30 segundos...
    </div>
  )
}
