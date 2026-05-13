import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Reuniones from '../Reuniones'

// MemoryRouter REQUIRED — Reuniones renders <Link to={...}>
vi.mock('../../services/api', () => ({
  getReuniones: vi.fn(),
  getTemporadaActiva: vi.fn(() => Promise.resolve({ nombre: 'Temporada Test', id: 1, estado: 'activa' })),
}))

function makeReunion(overrides = {}) {
  return {
    id: 1,
    numero_jornada: 1,
    fecha: '2026-05-01',
    ganador: null,
    ...overrides,
  }
}

describe('Reuniones.jsx — Winner avatar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('1. ganador present → PlayerAvatar accessible name present (REQ-13)', async () => {
    const { getReuniones } = await import('../../services/api')
    vi.mocked(getReuniones).mockResolvedValueOnce([
      makeReunion({
        id: 1,
        numero_jornada: 1,
        ganador: { id_jugador: 5, nombre: 'Sebastián', foto_url: null },
      }),
    ])

    render(
      <MemoryRouter>
        <Reuniones />
      </MemoryRouter>
    )

    // Wait for loading to finish
    await screen.findByText(/Todas las jornadas/)

    // PlayerAvatar renders initial span when no fotoUrl — text "S" or the span is accessible by name
    // When foto_url is null, PlayerAvatar renders a span with the initial
    const playerArea = document.querySelector('.row-ganador')
    expect(playerArea).not.toBeNull()
    // The component should render PlayerAvatar (span with "S" initial)
    const { container } = { container: document.body }
    const initial = container.querySelector('.row-ganador span[aria-hidden="true"]')
    expect(initial).not.toBeNull()
  })

  it('2. ganador null → no avatar; winner cell container IS present (REQ-14)', async () => {
    const { getReuniones } = await import('../../services/api')
    vi.mocked(getReuniones).mockResolvedValueOnce([
      makeReunion({ id: 1, numero_jornada: 1, ganador: null }),
    ])

    render(
      <MemoryRouter>
        <Reuniones />
      </MemoryRouter>
    )

    await screen.findByText(/Todas las jornadas/)

    // Winner cell exists (preserves grid column)
    const ganadorCell = document.querySelector('.row-ganador')
    expect(ganadorCell).not.toBeNull()
    // No avatar image or initial
    const img = ganadorCell?.querySelector('img')
    const initial = ganadorCell?.querySelector('span[aria-hidden="true"]')
    expect(img).toBeNull()
    expect(initial).toBeNull()
  })

  it('3. Mixed rows: all 3 rows rendered; winner cell in every row (EC-04)', async () => {
    const { getReuniones } = await import('../../services/api')
    vi.mocked(getReuniones).mockResolvedValueOnce([
      makeReunion({ id: 1, numero_jornada: 1, ganador: { id_jugador: 5, nombre: 'Sebastián', foto_url: null } }),
      makeReunion({ id: 2, numero_jornada: 2, ganador: null }),
      makeReunion({ id: 3, numero_jornada: 3, ganador: { id_jugador: 2, nombre: 'Ana', foto_url: null } }),
    ])

    render(
      <MemoryRouter>
        <Reuniones />
      </MemoryRouter>
    )

    await screen.findByText(/Todas las jornadas/)

    // All 3 rows should be rendered
    const rows = document.querySelectorAll('.board-reuniones .row')
    expect(rows).toHaveLength(3)

    // Each row must have a .row-ganador cell
    const ganadorCells = document.querySelectorAll('.row-ganador')
    expect(ganadorCells).toHaveLength(3)
  })
})
