import { useState, useEffect, useRef } from 'react'

const INVITADO = { id_jugador: null, nombre: 'Invitado', es_invitado: true }

/**
 * Props:
 *   jugadores:          [{id, nombre}]  — jugadores inscritos en la temporada
 *   posicionesIniciales: [{posicion, id_jugador, es_invitado}]  — para modo edición
 *   onChange:           (posiciones) => void  — array de {posicion, id_jugador, es_invitado}
 */
export default function PosicionadorReunion({ jugadores, posicionesIniciales = [], onChange }) {
  // slots: object  { slotIndex(0-based): {id_jugador, nombre, es_invitado} }
  const [slots, setSlots] = useState(() => {
    const map = {}
    posicionesIniciales.forEach((p) => {
      const nombre = p.es_invitado
        ? 'Invitado'
        : (jugadores.find((j) => j.id === p.id_jugador)?.nombre ?? '?')
      map[p.posicion - 1] = { id_jugador: p.id_jugador, nombre, es_invitado: p.es_invitado }
    })
    return map
  })

  const dragging = useRef(null) // { item, fromIndex: number | null }
  const [dragOverIndex, setDragOverIndex] = useState(null)

  const numSlots = jugadores.length + 3

  // Derived: IDs of regular players already placed
  const placedIds = new Set(
    Object.values(slots)
      .filter((v) => !v.es_invitado)
      .map((v) => v.id_jugador),
  )
  const disponibles = jugadores.filter((j) => !placedIds.has(j.id))

  // Notify parent whenever slots change
  useEffect(() => {
    const posiciones = Object.entries(slots)
      .filter(([, item]) => item != null)
      .map(([idx, item]) => ({
        posicion: parseInt(idx) + 1,
        id_jugador: item.id_jugador,
        es_invitado: item.es_invitado,
      }))
    onChange(posiciones)
  }, [slots]) // eslint-disable-line react-hooks/exhaustive-deps

  function startDrag(item, fromIndex = null) {
    dragging.current = { item, fromIndex }
  }

  function dropOnSlot(targetIndex) {
    if (!dragging.current) return
    const { item, fromIndex } = dragging.current

    setSlots((prev) => {
      const next = { ...prev }

      // Vaciar slot de origen (si viene de otro slot)
      if (fromIndex !== null) {
        delete next[fromIndex]
      }

      // Si el slot destino ya está ocupado y el origen era un slot, intercambiar
      if (next[targetIndex] != null && fromIndex !== null) {
        next[fromIndex] = next[targetIndex]
      }

      next[targetIndex] = item
      return next
    })

    dragging.current = null
    setDragOverIndex(null)
  }

  function removeFromSlot(idx) {
    setSlots((prev) => {
      const next = { ...prev }
      delete next[idx]
      return next
    })
  }

  return (
    <div className="posicionador">
      {/* Panel izquierdo: disponibles */}
      <div>
        <p className="section-title">Disponibles</p>
        <div className="disponibles-list">
          {disponibles.map((j) => (
            <div
              key={j.id}
              className="chip chip-player"
              draggable
              onDragStart={() => startDrag({ id_jugador: j.id, nombre: j.nombre, es_invitado: false })}
            >
              {j.nombre}
            </div>
          ))}
          <div
            className="chip chip-invitado"
            draggable
            onDragStart={() => startDrag({ ...INVITADO })}
            title="Arrastrar para añadir un invitado"
          >
            + Invitado
          </div>
        </div>
        {disponibles.length === 0 && (
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Todos posicionados
          </p>
        )}
      </div>

      {/* Panel derecho: slots de posición */}
      <div>
        <p className="section-title">Posiciones</p>
        <div className="slots-list">
          {Array.from({ length: numSlots }, (_, i) => {
            const item = slots[i]
            const isOver = dragOverIndex === i
            return (
              <div
                key={i}
                className={`slot${isOver ? ' drag-over' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOverIndex(i) }}
                onDragLeave={() => setDragOverIndex(null)}
                onDrop={() => dropOnSlot(i)}
              >
                <span className={`rank-num rank-${i + 1}`}>{i + 1}</span>
                {item ? (
                  <>
                    <span
                      className={`chip ${item.es_invitado ? 'chip-invitado-slot' : 'chip-player'}`}
                      style={{ flex: 1, cursor: 'grab' }}
                      draggable
                      onDragStart={() => startDrag(item, i)}
                    >
                      {item.nombre}
                    </span>
                    <button className="btn-remove" onClick={() => removeFromSlot(i)}>×</button>
                  </>
                ) : (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    Arrastrar aquí
                  </span>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
