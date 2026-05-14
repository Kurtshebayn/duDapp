import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import NarrativeBadges from '../NarrativeBadges'

// Helper to render NarrativeBadges with given props
function renderBadges(entry, variant = 'podium') {
  return render(<NarrativeBadges entry={entry} variant={variant} />)
}

describe('NarrativeBadges — variant="podium"', () => {
  it('1. delta_posicion: 3 → badge text "sube 3" present', () => {
    renderBadges({ delta_posicion: 3, racha: 0, lider_desde_jornada: null })
    expect(screen.getByText('sube 3')).toBeInTheDocument()
  })

  it('2. delta_posicion: -2 → badge text "cae 2" present; "cae -2" NOT present', () => {
    renderBadges({ delta_posicion: -2, racha: 0, lider_desde_jornada: null })
    expect(screen.getByText('cae 2')).toBeInTheDocument()
    expect(screen.queryByText('cae -2')).not.toBeInTheDocument()
  })

  it('3. delta_posicion: 0 → no sube/cae badge', () => {
    renderBadges({ delta_posicion: 0, racha: 0, lider_desde_jornada: null })
    expect(screen.queryByText(/^sube/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^cae/)).not.toBeInTheDocument()
  })

  it('4. racha: 4 → badge text "racha de 4" present', () => {
    renderBadges({ delta_posicion: 0, racha: 4, lider_desde_jornada: null })
    expect(screen.getByText('racha de 4')).toBeInTheDocument()
  })

  it('5. racha: 0 → no racha badge', () => {
    renderBadges({ delta_posicion: 0, racha: 0, lider_desde_jornada: null })
    expect(screen.queryByText(/^racha de/)).not.toBeInTheDocument()
  })

  it('5b. racha: 1 → no racha badge (a single improvement is not a streak)', () => {
    renderBadges({ delta_posicion: 0, racha: 1, lider_desde_jornada: null })
    expect(screen.queryByText(/^racha de/)).not.toBeInTheDocument()
  })

  it('6. lider_desde_jornada: 3 → badge text "líder desde J-3" present', () => {
    renderBadges({ delta_posicion: 0, racha: 0, lider_desde_jornada: 3 })
    expect(screen.getByText('líder desde J-3')).toBeInTheDocument()
  })

  it('7. lider_desde_jornada: null → no líder badge', () => {
    renderBadges({ delta_posicion: 0, racha: 0, lider_desde_jornada: null })
    expect(screen.queryByText(/^líder desde/)).not.toBeInTheDocument()
  })

  it('8. all 3 active (lider:1, racha:5, delta:2) podium → 3 badges present', () => {
    const { container } = renderBadges({ delta_posicion: 2, racha: 5, lider_desde_jornada: 1 })
    const pills = container.querySelectorAll('.narrative-pill')
    expect(pills).toHaveLength(3)
    expect(screen.getByText('líder desde J-1')).toBeInTheDocument()
    expect(screen.getByText('racha de 5')).toBeInTheDocument()
    expect(screen.getByText('sube 2')).toBeInTheDocument()
  })

  it('9. none active (delta:0, racha:0, lider:null) → 0 badges, component returns null', () => {
    const { container } = renderBadges({ delta_posicion: 0, racha: 0, lider_desde_jornada: null })
    expect(container.firstChild).toBeNull()
  })

  it('10. "sube N" element has class narrative-pill--positive, NOT narrative-pill--regression', () => {
    renderBadges({ delta_posicion: 2, racha: 0, lider_desde_jornada: null })
    const pill = screen.getByText('sube 2')
    expect(pill).toHaveClass('narrative-pill--positive')
    expect(pill).not.toHaveClass('narrative-pill--regression')
  })

  it('11. "cae N" element has class narrative-pill--regression, NOT narrative-pill--positive', () => {
    renderBadges({ delta_posicion: -3, racha: 0, lider_desde_jornada: null })
    const pill = screen.getByText('cae 3')
    expect(pill).toHaveClass('narrative-pill--regression')
    expect(pill).not.toHaveClass('narrative-pill--positive')
  })

  it('12. EC-01: lider:1, racha:0, delta:0 → only "líder desde J-1" badge', () => {
    const { container } = renderBadges({ delta_posicion: 0, racha: 0, lider_desde_jornada: 1 })
    const pills = container.querySelectorAll('.narrative-pill')
    expect(pills).toHaveLength(1)
    expect(screen.getByText('líder desde J-1')).toBeInTheDocument()
  })

  it('13. EC-05: delta:0, racha:0, lider:2 → only "líder desde J-2" badge', () => {
    const { container } = renderBadges({ delta_posicion: 0, racha: 0, lider_desde_jornada: 2 })
    const pills = container.querySelectorAll('.narrative-pill')
    expect(pills).toHaveLength(1)
    expect(screen.getByText('líder desde J-2')).toBeInTheDocument()
  })
})

describe('NarrativeBadges — variant="table" (badge cap)', () => {
  it('14. Table: lider:2, racha:3, delta:1 → exactly 2 badges: líder + racha; sube 1 NOT present', () => {
    const { container } = render(
      <NarrativeBadges
        entry={{ delta_posicion: 1, racha: 3, lider_desde_jornada: 2 }}
        variant="table"
      />
    )
    const pills = container.querySelectorAll('.narrative-pill')
    expect(pills).toHaveLength(2)
    expect(screen.getByText('líder desde J-2')).toBeInTheDocument()
    expect(screen.getByText('racha de 3')).toBeInTheDocument()
    expect(screen.queryByText('sube 1')).not.toBeInTheDocument()
  })

  it('15. Table: lider:null, racha:2, delta:-1 → exactly 2 badges: racha + cae', () => {
    const { container } = render(
      <NarrativeBadges
        entry={{ delta_posicion: -1, racha: 2, lider_desde_jornada: null }}
        variant="table"
      />
    )
    const pills = container.querySelectorAll('.narrative-pill')
    expect(pills).toHaveLength(2)
    expect(screen.getByText('racha de 2')).toBeInTheDocument()
    expect(screen.getByText('cae 1')).toBeInTheDocument()
  })

  it('16. Table: lider:null, racha:0, delta:2 → exactly 1 badge: sube 2', () => {
    const { container } = render(
      <NarrativeBadges
        entry={{ delta_posicion: 2, racha: 0, lider_desde_jornada: null }}
        variant="table"
      />
    )
    const pills = container.querySelectorAll('.narrative-pill')
    expect(pills).toHaveLength(1)
    expect(screen.getByText('sube 2')).toBeInTheDocument()
  })
})
