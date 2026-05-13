import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('api — getRankingNarrativo', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve([
          {
            id_jugador: 1,
            nombre: 'Ana',
            foto_url: null,
            puntos: 100,
            asistencias: 7,
            posicion: 1,
            delta_posicion: 2,
            racha: 3,
            lider_desde_jornada: 1,
          },
        ]),
      })
    ))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls fetch with path ending in /temporadas/activa/ranking-narrativo', async () => {
    const { getRankingNarrativo } = await import('../api.js')
    await getRankingNarrativo()
    expect(vi.mocked(fetch)).toHaveBeenCalledOnce()
    const [url] = vi.mocked(fetch).mock.calls[0]
    expect(url).toMatch(/\/temporadas\/activa\/ranking-narrativo$/)
  })

  it('returns the parsed JSON array with all 9 fields on first element', async () => {
    const { getRankingNarrativo } = await import('../api.js')
    const result = await getRankingNarrativo()
    expect(Array.isArray(result)).toBe(true)
    const entry = result[0]
    expect(entry).toHaveProperty('id_jugador')
    expect(entry).toHaveProperty('nombre')
    expect(entry).toHaveProperty('foto_url')
    expect(entry).toHaveProperty('puntos')
    expect(entry).toHaveProperty('asistencias')
    expect(entry).toHaveProperty('posicion')
    expect(entry).toHaveProperty('delta_posicion')
    expect(entry).toHaveProperty('racha')
    expect(entry).toHaveProperty('lider_desde_jornada')
  })

  it('getRanking is not exported from api.js', async () => {
    const mod = await import('../api.js')
    expect(mod.getRanking).toBeUndefined()
  })
})
