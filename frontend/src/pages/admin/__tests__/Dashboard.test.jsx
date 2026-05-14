import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// Mock AuthContext so Dashboard gets a token without needing real auth
vi.mock('../../../auth/AuthContext', () => ({
  useAuth: () => ({ token: 'fake-token', logout: vi.fn() }),
}))

// Mock all api functions used by Dashboard
vi.mock('../../../services/api', () => ({
  getTemporadaActiva: vi.fn(),
  getReuniones: vi.fn(),
  getJugadores: vi.fn(),
  cerrarTemporada: vi.fn(),
  designarCampeon: vi.fn(),
  subirFotoJugador: vi.fn(),
  crearJugador: vi.fn(),
  inscribirJugadorEnActiva: vi.fn(),
}))

// Mock ChampionPickerModal to keep tests focused on Dashboard logic
// We spy on its props to verify wiring without rendering the full modal UI
vi.mock('../../../components/ChampionPickerModal', () => ({
  default: ({ open, tiedPlayers, onPick, onCancel, loading, error }) => {
    if (!open) return null
    return (
      <div data-testid="champion-picker-modal">
        {tiedPlayers.map((p) => (
          <button
            key={p.id_jugador}
            data-testid={`pick-${p.id_jugador}`}
            onClick={() => onPick(p.id_jugador)}
          >
            {p.nombre}
          </button>
        ))}
        <button data-testid="modal-cancel" onClick={onCancel}>Cancelar</button>
        {error && <div data-testid="modal-error">{error}</div>}
        {loading && <span data-testid="modal-loading">loading</span>}
      </div>
    )
  },
}))

const temporadaActiva = {
  id: 1,
  nombre: 'Liga 2024',
  estado: 'activa',
  total_reuniones: 0,
  jugadores: [],
  campeon_id: null,
  tie_detected: false,
}

async function renderDashboard() {
  const { getTemporadaActiva, getReuniones, getJugadores } = await import('../../../services/api')
  vi.mocked(getTemporadaActiva).mockResolvedValue(temporadaActiva)
  vi.mocked(getReuniones).mockResolvedValue([])
  vi.mocked(getJugadores).mockResolvedValue([])

  const Dashboard = (await import('../Dashboard')).default
  render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  )

  // Wait for the component to finish loading
  await waitFor(() => {
    expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument()
  })
}

describe('Dashboard — handleCerrar tie-detection branching', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()
    // Mock window.confirm to always return true (admin confirms)
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('1. handleCerrar with tie_detected:false → modal NOT in DOM; cargar() re-fetches', async () => {
    const api = await import('../../../services/api')
    vi.mocked(api.getTemporadaActiva).mockResolvedValue(temporadaActiva)
    vi.mocked(api.getReuniones).mockResolvedValue([])
    vi.mocked(api.getJugadores).mockResolvedValue([])
    vi.mocked(api.cerrarTemporada).mockResolvedValueOnce({
      id: 1,
      nombre: 'Liga 2024',
      estado: 'cerrada',
      campeon_id: 7,
      tie_detected: false,
    })

    const Dashboard = (await import('../Dashboard')).default
    render(<MemoryRouter><Dashboard /></MemoryRouter>)
    await waitFor(() => expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument())

    // Click Cerrar temporada
    await act(async () => {
      fireEvent.click(screen.getByText('Cerrar temporada'))
    })

    // Modal should NOT be in DOM
    expect(screen.queryByTestId('champion-picker-modal')).not.toBeInTheDocument()
    // cargar() re-fetches (getTemporadaActiva called twice: initial + post-cerrar)
    expect(vi.mocked(api.getTemporadaActiva).mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('2. handleCerrar with tie_detected:true → modal opens with tied players listed', async () => {
    const api = await import('../../../services/api')
    vi.mocked(api.getTemporadaActiva).mockResolvedValue(temporadaActiva)
    vi.mocked(api.getReuniones).mockResolvedValue([])
    vi.mocked(api.getJugadores).mockResolvedValue([])
    vi.mocked(api.cerrarTemporada).mockResolvedValueOnce({
      id: 1,
      nombre: 'Liga 2024',
      estado: 'cerrada',
      campeon_id: null,
      tie_detected: true,
      tied_players: [
        { id_jugador: 1, nombre: 'Ana' },
        { id_jugador: 2, nombre: 'Bruno' },
      ],
    })

    const Dashboard = (await import('../Dashboard')).default
    render(<MemoryRouter><Dashboard /></MemoryRouter>)
    await waitFor(() => expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument())

    await act(async () => {
      fireEvent.click(screen.getByText('Cerrar temporada'))
    })

    // Modal opens
    expect(screen.getByTestId('champion-picker-modal')).toBeInTheDocument()
    expect(screen.getByText('Ana')).toBeInTheDocument()
    expect(screen.getByText('Bruno')).toBeInTheDocument()
  })

  it('3. Confirming modal calls designarCampeon with correct ids, then closes modal and reloads', async () => {
    const api = await import('../../../services/api')
    vi.mocked(api.getTemporadaActiva).mockResolvedValue(temporadaActiva)
    vi.mocked(api.getReuniones).mockResolvedValue([])
    vi.mocked(api.getJugadores).mockResolvedValue([])
    vi.mocked(api.cerrarTemporada).mockResolvedValueOnce({
      id: 1,
      tie_detected: true,
      tied_players: [{ id_jugador: 1, nombre: 'Ana' }, { id_jugador: 2, nombre: 'Bruno' }],
    })
    vi.mocked(api.designarCampeon).mockResolvedValueOnce({
      id: 1,
      campeon_id: 1,
      tie_detected: false,
    })

    const Dashboard = (await import('../Dashboard')).default
    render(<MemoryRouter><Dashboard /></MemoryRouter>)
    await waitFor(() => expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument())

    // Open modal
    await act(async () => {
      fireEvent.click(screen.getByText('Cerrar temporada'))
    })
    expect(screen.getByTestId('champion-picker-modal')).toBeInTheDocument()

    // Pick Ana (id_jugador: 1)
    await act(async () => {
      fireEvent.click(screen.getByTestId('pick-1'))
    })

    // designarCampeon called with temporadaId=1, jugadorId=1
    expect(vi.mocked(api.designarCampeon)).toHaveBeenCalledWith('fake-token', 1, 1)

    // Modal closes after success
    await waitFor(() => {
      expect(screen.queryByTestId('champion-picker-modal')).not.toBeInTheDocument()
    })
  })

  it('4. Cancelling modal does NOT call designarCampeon', async () => {
    const api = await import('../../../services/api')
    vi.mocked(api.getTemporadaActiva).mockResolvedValue(temporadaActiva)
    vi.mocked(api.getReuniones).mockResolvedValue([])
    vi.mocked(api.getJugadores).mockResolvedValue([])
    vi.mocked(api.cerrarTemporada).mockResolvedValueOnce({
      id: 1,
      tie_detected: true,
      tied_players: [{ id_jugador: 1, nombre: 'Ana' }, { id_jugador: 2, nombre: 'Bruno' }],
    })

    const Dashboard = (await import('../Dashboard')).default
    render(<MemoryRouter><Dashboard /></MemoryRouter>)
    await waitFor(() => expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument())

    // Open modal
    await act(async () => {
      fireEvent.click(screen.getByText('Cerrar temporada'))
    })

    // Cancel the modal
    await act(async () => {
      fireEvent.click(screen.getByTestId('modal-cancel'))
    })

    expect(vi.mocked(api.designarCampeon)).not.toHaveBeenCalled()

    // Modal closed
    await waitFor(() => {
      expect(screen.queryByTestId('champion-picker-modal')).not.toBeInTheDocument()
    })
  })

  it('5. designarCampeon rejects with error → modal stays open; error message rendered', async () => {
    const api = await import('../../../services/api')
    vi.mocked(api.getTemporadaActiva).mockResolvedValue(temporadaActiva)
    vi.mocked(api.getReuniones).mockResolvedValue([])
    vi.mocked(api.getJugadores).mockResolvedValue([])
    vi.mocked(api.cerrarTemporada).mockResolvedValueOnce({
      id: 1,
      tie_detected: true,
      tied_players: [{ id_jugador: 1, nombre: 'Ana' }, { id_jugador: 2, nombre: 'Bruno' }],
    })
    vi.mocked(api.designarCampeon).mockRejectedValueOnce(new Error('Error 422'))

    const Dashboard = (await import('../Dashboard')).default
    render(<MemoryRouter><Dashboard /></MemoryRouter>)
    await waitFor(() => expect(screen.queryByText(/Cargando/)).not.toBeInTheDocument())

    // Open modal
    await act(async () => {
      fireEvent.click(screen.getByText('Cerrar temporada'))
    })

    // Pick Ana to trigger designarCampeon
    await act(async () => {
      fireEvent.click(screen.getByTestId('pick-1'))
    })

    // Modal stays open; error rendered
    await waitFor(() => {
      expect(screen.getByTestId('champion-picker-modal')).toBeInTheDocument()
      expect(screen.getByTestId('modal-error')).toHaveTextContent('Error 422')
    })
  })
})
