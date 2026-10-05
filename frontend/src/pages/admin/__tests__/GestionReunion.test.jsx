import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import GestionReunion from '../GestionReunion'
import { getTemporadaActiva } from '../../../services/api'

vi.mock('../../../auth/AuthContext', () => ({
  useAuth: () => ({ token: 'fake-token' }),
}))

vi.mock('../../../services/api', () => ({
  getTemporadaActiva: vi.fn(),
  getResultadosReunion: vi.fn(),
  registrarReunion: vi.fn(),
  editarReunion: vi.fn(),
}))

// Keep the drag & drop board out of these copy-focused tests.
vi.mock('../../../components/PosicionadorReunion', () => ({
  default: () => <div data-testid="posicionador" />,
}))

function temporada(extra = {}) {
  return { id: 1, nombre: 'Liga 2027', estado: 'activa', jugadores: [], ...extra }
}

function renderCrear() {
  return render(
    <MemoryRouter>
      <GestionReunion modo="crear" />
    </MemoryRouter>,
  )
}

describe('GestionReunion — scoring hint', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('explains fixed 15-point scoring for fijo_15 seasons', async () => {
    vi.mocked(getTemporadaActiva).mockResolvedValue(temporada({ modo_puntaje: 'fijo_15' }))
    renderCrear()
    expect(await screen.findByText(/15 al primero, 14 al segundo/)).toBeInTheDocument()
    expect(screen.queryByText(/el último registrado recibe 1 punto/)).not.toBeInTheDocument()
  })

  it('falls back to fijo_15 copy when the season has no modo_puntaje', async () => {
    vi.mocked(getTemporadaActiva).mockResolvedValue(temporada())
    renderCrear()
    expect(await screen.findByText(/15 al primero, 14 al segundo/)).toBeInTheDocument()
  })

  it('explains attendance-based scoring for por_asistentes seasons', async () => {
    vi.mocked(getTemporadaActiva).mockResolvedValue(temporada({ modo_puntaje: 'por_asistentes' }))
    renderCrear()
    expect(await screen.findByText(/el último registrado recibe 1 punto/)).toBeInTheDocument()
    expect(screen.queryByText(/15 al primero/)).not.toBeInTheDocument()
  })
})
