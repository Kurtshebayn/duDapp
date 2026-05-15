import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Ranking from '../Ranking'

// Mock the api module — 4 endpoints (4th added for vista-ultima-temporada-cerrada)
vi.mock('../../services/api', () => ({
  getRankingNarrativo: vi.fn(),
  getReuniones: vi.fn(() => Promise.resolve([])),
  getTemporadaActiva: vi.fn(() => Promise.resolve({ nombre: 'Temporada Test', id: 1, estado: 'activa' })),
  getUltimaCerradaRankingNarrativo: vi.fn(() => Promise.resolve(null)),
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

// Helper for live-mode renders: sets up all 4 mocks
// getUltimaCerradaRankingNarrativo defaults to null (no closed season) → live mode
async function renderRanking(rankingData) {
  const api = await import('../../services/api')
  vi.mocked(api.getRankingNarrativo).mockResolvedValueOnce(rankingData)
  // getTemporadaActiva already defaults to active season via vi.mock above
  // getUltimaCerradaRankingNarrativo already defaults to null via vi.mock above

  render(
    <MemoryRouter>
      <Ranking />
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument()
  })
}

// Helper for closed-mode renders
async function renderRankingClosed({ ultimaCerrada }) {
  const api = await import('../../services/api')
  vi.mocked(api.getRankingNarrativo).mockResolvedValueOnce(null)
  vi.mocked(api.getTemporadaActiva).mockResolvedValueOnce(null)
  vi.mocked(api.getUltimaCerradaRankingNarrativo).mockResolvedValueOnce(ultimaCerrada)

  render(
    <MemoryRouter>
      <Ranking />
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument()
  })
}

// Helper for empty-mode renders
async function renderRankingEmpty() {
  const api = await import('../../services/api')
  vi.mocked(api.getRankingNarrativo).mockResolvedValueOnce(null)
  vi.mocked(api.getTemporadaActiva).mockResolvedValueOnce(null)
  vi.mocked(api.getUltimaCerradaRankingNarrativo).mockResolvedValueOnce(null)

  render(
    <MemoryRouter>
      <Ranking />
    </MemoryRouter>
  )

  await waitFor(() => {
    expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument()
  })
}

// Minimal closed-mode payload factory
function makeUltimaCerrada(overrides = {}) {
  return {
    temporada_id: 99,
    temporada_nombre: 'Copa Invierno',
    fecha_cierre: '2026-05-10',
    campeon: {
      id: 1,
      nombre: 'Ana',
      foto_url: null,
      puntos: 90,
      asistencias: 6,
      promedio: 15.0,
    },
    ranking: [
      { id_jugador: 1, nombre: 'Ana',    foto_url: null, puntos: 90, asistencias: 6, promedio: 15.0, posicion: 1, racha: 3 },
      { id_jugador: 2, nombre: 'Bruno',  foto_url: null, puntos: 84, asistencias: 6, promedio: 14.0, posicion: 2, racha: 0 },
      { id_jugador: 3, nombre: 'Carlos', foto_url: null, puntos: 78, asistencias: 6, promedio: 13.0, posicion: 3, racha: 0 },
    ],
    ...overrides,
  }
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

// ─────────────────────────────────────────────────────────────────────────────
// Closed mode tests (REQ-4, REQ-5, REQ-6)
// ─────────────────────────────────────────────────────────────────────────────

describe('Ranking.jsx — Closed mode (no active season, closed season exists)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('16. closed mode: renders CAMPEÓN label and champion name', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada() })
    expect(screen.getByText('CAMPEÓN')).toBeInTheDocument()
    expect(screen.getAllByText('Ana').length).toBeGreaterThan(0)
  })

  it('17. closed mode: renders TEMPORADA CERRADA badge', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada() })
    // The .closed-badge eyebrow renders "Temporada cerrada" (case-insensitive match)
    // Multiple elements may contain the text — at least one must exist
    expect(screen.getAllByText(/Temporada cerrada/i).length).toBeGreaterThan(0)
  })

  it('18. closed mode: renders champion stats (puntos, asistencias, promedio)', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada() })
    // champion-stats section has Puntos/Asistencias/Promedio labels + values
    const heroSection = document.querySelector('.champion-hero')
    expect(heroSection).not.toBeNull()
    expect(heroSection.textContent).toContain('90')
    expect(heroSection.textContent).toContain('15.0')
  })

  it('19. closed mode: fecha_cierre present → subline includes "Cerrada el"', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada({ fecha_cierre: '2026-05-10' }) })
    expect(screen.getByText(/Cerrada el/)).toBeInTheDocument()
  })

  it('20. closed mode: fecha_cierre null → subline does NOT include "Cerrada el"', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada({ fecha_cierre: null }) })
    expect(screen.queryByText(/Cerrada el/)).not.toBeInTheDocument()
    // Temporada name still visible
    expect(screen.getByText(/Copa Invierno/)).toBeInTheDocument()
  })

  it('21. closed mode: campeon null (empate) → no CAMPEÓN label, tie-note rendered', async () => {
    await renderRankingClosed({
      ultimaCerrada: makeUltimaCerrada({ campeon: null }),
    })
    expect(screen.queryByText('CAMPEÓN')).not.toBeInTheDocument()
    expect(screen.getByText(/empate/i)).toBeInTheDocument()
  })

  it('22. closed mode: ranking table renders all players', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada() })
    expect(screen.getAllByText('Bruno').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Carlos').length).toBeGreaterThan(0)
  })

  it('23. closed mode: racha pill visible for champion (racha >= 2)', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada() })
    // Ana has racha: 3 in makeUltimaCerrada
    expect(screen.getAllByText('racha de 3').length).toBeGreaterThan(0)
  })

  it('24. closed mode: no delta pills (sube/cae) in table — closed entries lack those fields', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada() })
    expect(screen.queryByText(/^sube/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^cae/)).not.toBeInTheDocument()
  })

  it('25. closed mode: no líder desde pills — closed entries lack that field', async () => {
    await renderRankingClosed({ ultimaCerrada: makeUltimaCerrada() })
    expect(screen.queryByText(/^líder desde/)).not.toBeInTheDocument()
  })

  it('26. live mode regression: with active season, closed mode hero NOT rendered', async () => {
    const api = await import('../../services/api')
    vi.mocked(api.getRankingNarrativo).mockResolvedValueOnce(makeRanking())
    // getTemporadaActiva defaults to active (from vi.mock top)
    // getUltimaCerradaRankingNarrativo defaults to null (from vi.mock top)
    render(<MemoryRouter><Ranking /></MemoryRouter>)
    await waitFor(() => expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument())
    expect(screen.queryByText('CAMPEÓN')).not.toBeInTheDocument()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Empty mode tests (REQ-4)
// ─────────────────────────────────────────────────────────────────────────────

describe('Ranking.jsx — Empty mode (no active, no closed seasons)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('27. empty mode: renders "Todavía no hay temporadas registradas" copy', async () => {
    await renderRankingEmpty()
    expect(screen.getByText(/Todavía no hay temporadas registradas/)).toBeInTheDocument()
  })

  it('28. empty mode: no CAMPEÓN label, no table visible', async () => {
    await renderRankingEmpty()
    expect(screen.queryByText('CAMPEÓN')).not.toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })
})
