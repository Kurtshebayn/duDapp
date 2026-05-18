import { describe, it, expect } from 'vitest'
import { toRoman } from '../dates'

describe('toRoman — entero a numeral romano', () => {
  it('convierte unidades básicas', () => {
    expect(toRoman(1)).toBe('I')
    expect(toRoman(4)).toBe('IV')
    expect(toRoman(5)).toBe('V')
    expect(toRoman(9)).toBe('IX')
  })

  it('convierte decenas y centenas con notación sustractiva', () => {
    expect(toRoman(40)).toBe('XL')
    expect(toRoman(90)).toBe('XC')
    expect(toRoman(400)).toBe('CD')
    expect(toRoman(900)).toBe('CM')
  })

  it('convierte años modernos del proyecto', () => {
    expect(toRoman(2026)).toBe('MMXXVI')
    expect(toRoman(2025)).toBe('MMXXV')
    expect(toRoman(2000)).toBe('MM')
    expect(toRoman(1999)).toBe('MCMXCIX')
  })

  it('devuelve string vacío para inputs inválidos', () => {
    expect(toRoman(0)).toBe('')
    expect(toRoman(-1)).toBe('')
    expect(toRoman(4000)).toBe('')
    expect(toRoman(1.5)).toBe('')
    expect(toRoman(null)).toBe('')
    expect(toRoman(undefined)).toBe('')
    expect(toRoman('foo')).toBe('')
  })

  it('acepta strings numéricos coercibles', () => {
    expect(toRoman('2026')).toBe('MMXXVI')
  })
})
