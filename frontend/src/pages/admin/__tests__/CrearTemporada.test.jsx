import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../../../auth/AuthContext', () => ({
  useAuth: () => ({ token: 'fake-token' }),
}))

vi.mock('../../../services/api', () => ({
  getJugadores: vi.fn(),
  crearTemporada: vi.fn(),
  subirFotoJugador: vi.fn(),
}))

async function renderAndFillForm() {
  const api = await import('../../../services/api')
  vi.mocked(api.getJugadores).mockResolvedValue([])
  vi.mocked(api.crearTemporada).mockResolvedValue({ id: 1 })

  const CrearTemporada = (await import('../CrearTemporada')).default
  render(
    <MemoryRouter>
      <CrearTemporada />
    </MemoryRouter>
  )
  await waitFor(() => expect(api.getJugadores).toHaveBeenCalled())

  fireEvent.change(screen.getByLabelText('Nombre de la temporada'), {
    target: { value: 'Liga 2027' },
  })
  fireEvent.change(screen.getByPlaceholderText('Nombre del jugador'), {
    target: { value: 'Ana' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Agregar' }))
  return api
}

function submit() {
  fireEvent.click(screen.getByRole('button', { name: /Crear temporada/ }))
}

describe('CrearTemporada — scoring mode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('defaults to fixed 15-point scoring and sends fijo_15', async () => {
    const api = await renderAndFillForm()

    expect(screen.getByRole('radio', { name: /Fijo \(15 puntos\)/ })).toBeChecked()

    submit()

    await waitFor(() => expect(api.crearTemporada).toHaveBeenCalledOnce())
    const args = vi.mocked(api.crearTemporada).mock.calls[0]
    expect(args[4]).toBe('fijo_15')
  })

  it('sends por_asistentes when "Según asistentes" is selected', async () => {
    const api = await renderAndFillForm()

    fireEvent.click(screen.getByRole('radio', { name: /Según asistentes/ }))
    submit()

    await waitFor(() => expect(api.crearTemporada).toHaveBeenCalledOnce())
    const args = vi.mocked(api.crearTemporada).mock.calls[0]
    expect(args[4]).toBe('por_asistentes')
  })
})
