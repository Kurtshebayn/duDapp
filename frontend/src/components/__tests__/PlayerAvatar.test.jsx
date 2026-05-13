import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import PlayerAvatar from '../PlayerAvatar.jsx'

describe('PlayerAvatar', () => {
  it('renderiza una <img> con alt cuando hay fotoUrl', () => {
    render(<PlayerAvatar nombre="Juan" fotoUrl="https://example.com/juan.jpg" />)
    const img = screen.getByAltText('Juan')
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('src', 'https://example.com/juan.jpg')
  })

  it('renderiza la inicial en mayúscula cuando no hay fotoUrl', () => {
    const { container } = render(<PlayerAvatar nombre="sebastián" />)
    const span = container.querySelector('span[aria-hidden="true"]')
    expect(span).not.toBeNull()
    expect(span?.textContent).toBe('S')
  })

  it('renderiza "?" cuando no hay nombre ni fotoUrl', () => {
    const { container } = render(<PlayerAvatar />)
    const span = container.querySelector('span[aria-hidden="true"]')
    expect(span?.textContent).toBe('?')
  })
})
