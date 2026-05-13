import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Ranking from '../Ranking'

// Mock the api module
vi.mock('../../services/api', () => ({
  getRankingNarrativo: vi.fn(),
  getReuniones: vi.fn(() => Promise.resolve([])),
  getTemporadaActiva: vi.fn(() => Promise.resolve({ nombre: 'Temporada Test', id: 1, estado: 'activa' })),
}))

// Base entry with narrative fields
function makeEntry(overrides = {}) {
  return {
    id_jugador: 1,
    nombre: 'Ana',
    foto_url: null,
    puntos: 15,
    asistencias: 1,
    posicion: 1,
    delta_posicion: 0,
    racha: 0,
    lider_desde_jornada: null,
    ...overrides,
  }
}

// Build a minimal ranking with 3+ entries so podium renders
function makeRanking(overrides = []) {
  const base = [
    makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1 }),
    makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
    makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
  ]
  // Apply overrides to first entry or add to array
  if (overrides.length > 0) {
    return overrides
  }
  return base
}

async function renderRanking(rankingData) {
  const { getRankingNarrativo } = await import('../../services/api')
  vi.mocked(getRankingNarrativo).mockResolvedValueOnce(rankingData)

  render(
    <MemoryRouter>
      <Ranking />
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument()
  })
}

describe('Ranking.jsx — API wiring', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('1. mounting calls getRankingNarrativo once; getRanking is NOT called (REQ-02)', async () => {
    const api = await import('../../services/api')
    vi.mocked(api.getRankingNarrativo).mockResolvedValueOnce(makeRanking())

    render(<MemoryRouter><Ranking /></MemoryRouter>)

    await waitFor(() => {
      expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument()
    })

    expect(api.getRankingNarrativo).toHaveBeenCalledOnce()
    // getRanking is not in the mock — it was removed from api.js (covered by api.test.js)
    expect('getRanking' in api).toBe(false)
  })
})

describe('Ranking.jsx — Delta badges', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('2. delta_posicion: 3 → "sube 3" badge present (REQ-04)', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, delta_posicion: 3 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.getByText('sube 3')).toBeInTheDocument()
  })

  it('3. delta_posicion: -2 → "cae 2" present (REQ-05)', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, delta_posicion: -2 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.getByText('cae 2')).toBeInTheDocument()
  })

  it('4. delta_posicion: 0 → no sube/cae badge (REQ-06)', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, delta_posicion: 0 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.queryByText(/^sube/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^cae/)).not.toBeInTheDocument()
  })
})

describe('Ranking.jsx — Racha badges', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('5. racha: 4 → "racha de 4" present (REQ-07)', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, racha: 4 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.getByText('racha de 4')).toBeInTheDocument()
  })

  it('6. racha: 0 → no racha badge (REQ-08)', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, racha: 0 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.queryByText(/^racha de/)).not.toBeInTheDocument()
  })
})

describe('Ranking.jsx — Líder badges', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('7. lider_desde_jornada: 3 → "líder desde J-3" present (REQ-09)', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, lider_desde_jornada: 3 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.getByText('líder desde J-3')).toBeInTheDocument()
  })

  it('8. lider_desde_jornada: null → no líder badge (REQ-10)', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, lider_desde_jornada: null }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.queryByText(/^líder desde/)).not.toBeInTheDocument()
  })
})

describe('Ranking.jsx — Badge cap (table) and podium (no cap)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('9. Table cap: all 3 active → 2 badges in table, delta suppressed (REQ-11, EC-02)', async () => {
    // Rank 4+ goes to rest table (not podium)
    // We need 4 players so rank-4 goes to table
    const data = [
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 20, asistencias: 2 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 19, asistencias: 2 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 18, asistencias: 2 }),
      makeEntry({ id_jugador: 4, nombre: 'Diana', puntos: 17, asistencias: 2, delta_posicion: 1, racha: 3, lider_desde_jornada: 2 }),
    ]
    await renderRanking(data)
    // In the table row for Diana (rank 4): 2 badges, no sube
    expect(screen.getByText('líder desde J-2')).toBeInTheDocument()
    expect(screen.getByText('racha de 3')).toBeInTheDocument()
    expect(screen.queryByText('sube 1')).not.toBeInTheDocument()
  })

  it('10. Podium no-cap: rank-1 entry all 3 active → 3 badges (REQ-12, EC-02)', async () => {
    const data = [
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 20, asistencias: 2, delta_posicion: 1, racha: 5, lider_desde_jornada: 1 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 19, asistencias: 2 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 18, asistencias: 2 }),
    ]
    await renderRanking(data)
    // Podium card for Ana has all 3
    expect(screen.getByText('líder desde J-1')).toBeInTheDocument()
    expect(screen.getByText('racha de 5')).toBeInTheDocument()
    expect(screen.getByText('sube 1')).toBeInTheDocument()
  })
})

describe('Ranking.jsx — assignRanks pipeline and tonal classes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('11. assignRanks in pipeline: podium renders gold/silver/bronze (REQ-15)', async () => {
    const data = makeRanking()
    await renderRanking(data)
    // Podium renders for 3+ players — check medals present
    expect(screen.getByText('I')).toBeInTheDocument()
    expect(screen.getByText('II')).toBeInTheDocument()
    expect(screen.getByText('III')).toBeInTheDocument()
  })

  it('12. EC-01: lider:1, racha:0, delta:0 → only "líder desde J-1" badge', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, lider_desde_jornada: 1, racha: 0, delta_posicion: 0 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.getByText('líder desde J-1')).toBeInTheDocument()
    expect(screen.queryByText(/^racha de/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^sube/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^cae/)).not.toBeInTheDocument()
  })

  it('13. EC-03: getRankingNarrativo returns [] → no error, no podium (EC-03)', async () => {
    await renderRanking([])
    // Empty ranking renders without error
    expect(screen.queryByText('I')).not.toBeInTheDocument()
    expect(screen.queryByText('II')).not.toBeInTheDocument()
  })

  it('14. EC-05: delta:0, racha:0, lider:2 → only "líder desde J-2"', async () => {
    const data = makeRanking([
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 15, asistencias: 1, delta_posicion: 0, racha: 0, lider_desde_jornada: 2 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 14, asistencias: 1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 13, asistencias: 1 }),
    ])
    await renderRanking(data)
    expect(screen.getByText('líder desde J-2')).toBeInTheDocument()
    expect(screen.queryByText(/^sube/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^cae/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^racha de/)).not.toBeInTheDocument()
  })

  it('15. Tonal class: "sube N" has narrative-pill--positive; "cae N" has narrative-pill--regression (REQ-16)', async () => {
    const data = [
      makeEntry({ id_jugador: 1, nombre: 'Ana', puntos: 20, asistencias: 2, delta_posicion: 2 }),
      makeEntry({ id_jugador: 2, nombre: 'Bruno', puntos: 19, asistencias: 2, delta_posicion: -1 }),
      makeEntry({ id_jugador: 3, nombre: 'Carlos', puntos: 18, asistencias: 2 }),
    ]
    await renderRanking(data)
    const subePill = screen.getByText('sube 2')
    const caePill = screen.getByText('cae 1')
    expect(subePill).toHaveClass('narrative-pill--positive')
    expect(subePill).not.toHaveClass('narrative-pill--regression')
    expect(caePill).toHaveClass('narrative-pill--regression')
    expect(caePill).not.toHaveClass('narrative-pill--positive')
  })
})
