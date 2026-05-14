import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ChampionPickerModal from '../ChampionPickerModal'

const twoPlayers = [
  { id_jugador: 1, nombre: 'Ana' },
  { id_jugador: 2, nombre: 'Bruno' },
]

function renderModal(props = {}) {
  const defaults = {
    open: true,
    tiedPlayers: twoPlayers,
    onPick: vi.fn(),
    onCancel: vi.fn(),
    loading: false,
    error: null,
  }
  return render(<ChampionPickerModal {...defaults} {...props} />)
}

describe('ChampionPickerModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('1. open=false → renders nothing', () => {
    const { container } = renderModal({ open: false })
    expect(container.firstChild).toBeNull()
  })

  it('2. open=true with 2 tiedPlayers → renders 2 option buttons with player names', () => {
    renderModal()
    expect(screen.getByText('Ana')).toBeInTheDocument()
    expect(screen.getByText('Bruno')).toBeInTheDocument()
  })

  it('3. Confirm button disabled until a player is selected', () => {
    renderModal()
    const confirm = screen.getByRole('button', { name: /confirmar/i })
    expect(confirm).toBeDisabled()
  })

  it('4. Clicking a player marks it aria-pressed=true and enables Confirm', () => {
    renderModal()
    const anaBtn = screen.getByText('Ana').closest('button')
    fireEvent.click(anaBtn)
    expect(anaBtn).toHaveAttribute('aria-pressed', 'true')
    const confirm = screen.getByRole('button', { name: /confirmar/i })
    expect(confirm).not.toBeDisabled()
  })

  it('5. Clicking Confirm calls onPick(idJugador) with selected player id', () => {
    const onPick = vi.fn()
    renderModal({ onPick })
    const anaBtn = screen.getByText('Ana').closest('button')
    fireEvent.click(anaBtn)
    const confirm = screen.getByRole('button', { name: /confirmar/i })
    fireEvent.click(confirm)
    expect(onPick).toHaveBeenCalledOnce()
    expect(onPick).toHaveBeenCalledWith(1)
  })

  it('6. Clicking Cancel calls onCancel', () => {
    const onCancel = vi.fn()
    renderModal({ onCancel })
    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('7. loading=true → both Confirm and Cancel buttons disabled', () => {
    renderModal({ loading: true })
    // When loading, confirm button text changes to "Guardando…"
    const cancel = screen.getByRole('button', { name: /cancelar/i })
    const confirm = screen.getByRole('button', { name: /guardando/i })
    expect(confirm).toBeDisabled()
    expect(cancel).toBeDisabled()
  })

  it('8. error="some error" → renders error text inside .modal-alert; modal not closed', () => {
    renderModal({ error: 'some error' })
    const alert = document.querySelector('.modal-alert')
    expect(alert).not.toBeNull()
    expect(alert.textContent).toContain('some error')
    // modal is still present
    expect(screen.getByText('Ana')).toBeInTheDocument()
  })

  it('9. clicking backdrop calls onCancel; clicking inside modal card does NOT call onCancel', () => {
    const onCancel = vi.fn()
    renderModal({ onCancel })
    // Click the backdrop (modal-backdrop div itself)
    const backdrop = document.querySelector('.modal-backdrop')
    fireEvent.click(backdrop)
    expect(onCancel).toHaveBeenCalledOnce()

    onCancel.mockClear()

    // Click inside the modal card — stopPropagation should prevent onCancel
    const card = document.querySelector('.modal-card')
    fireEvent.click(card)
    expect(onCancel).not.toHaveBeenCalled()
  })
})
