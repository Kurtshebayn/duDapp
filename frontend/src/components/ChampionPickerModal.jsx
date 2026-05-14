import { useEffect, useState } from 'react'

/**
 * Modal for resolving a tiebreaker after closing a season.
 * Props:
 *   open: boolean
 *   tiedPlayers: Array<{ id_jugador: number, nombre: string }>
 *   onPick: (idJugador: number) => void
 *   onCancel: () => void
 *   loading: boolean
 *   error: string | null
 */
export default function ChampionPickerModal({ open, tiedPlayers, onPick, onCancel, loading, error }) {
  const [selectedId, setSelectedId] = useState(null)

  useEffect(() => {
    if (!open) setSelectedId(null)
  }, [open])

  if (!open) return null

  function handleConfirm() {
    if (selectedId === null || loading) return
    onPick(selectedId)
  }

  function handleCancel() {
    if (loading) return
    onCancel()
  }

  return (
    <div className="modal-backdrop" onClick={handleCancel}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3 className="modal-title">Empate al cierre — seleccioná el campeón</h3>
        <p style={{ marginBottom: '16px', color: 'var(--muted)' }}>
          Hay {tiedPlayers.length} jugadores empatados en 1° puesto. Elegí el campeón según el enfrentamiento directo.
        </p>

        <div style={{ marginBottom: '16px' }}>
          {tiedPlayers.map((p) => (
            <button
              key={p.id_jugador}
              type="button"
              className={`champion-picker-option${selectedId === p.id_jugador ? ' champion-picker-option--selected' : ''}`}
              data-id={p.id_jugador}
              aria-pressed={selectedId === p.id_jugador ? 'true' : 'false'}
              onClick={() => setSelectedId(p.id_jugador)}
              disabled={loading}
            >
              {p.nombre}
            </button>
          ))}
        </div>

        {error && (
          <div className="alert alert-error modal-alert">{error}</div>
        )}

        <div className="modal-actions">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleCancel}
            disabled={loading}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={handleConfirm}
            disabled={selectedId === null || loading}
          >
            {loading ? 'Guardando…' : 'Confirmar'}
          </button>
        </div>
      </div>
    </div>
  )
}
