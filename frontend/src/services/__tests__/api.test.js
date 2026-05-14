import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('api — designarCampeon', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          id: 5,
          nombre: 'Liga 2024',
          fecha_inicio: '2024-01-01',
          estado: 'cerrada',
          campeon_id: 7,
          tie_detected: false,
        }),
      })
    ))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('calls fetch with POST /temporadas/5/campeon and body {id_jugador: 7}', async () => {
    const { designarCampeon } = await import('../api.js')
    await designarCampeon('tok', 5, 7)
    expect(vi.mocked(fetch)).toHaveBeenCalledOnce()
    const [url, opts] = vi.mocked(fetch).mock.calls[0]
    expect(url).toMatch(/\/temporadas\/5\/campeon$/)
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toEqual({ id_jugador: 7 })
  })

  it('includes Authorization: Bearer <token> header', async () => {
    const { designarCampeon } = await import('../api.js')
    await designarCampeon('my-token', 5, 7)
    const [, opts] = vi.mocked(fetch).mock.calls[0]
    expect(opts.headers['Authorization']).toBe('Bearer my-token')
  })

  it('returns parsed JSON on success', async () => {
    const { designarCampeon } = await import('../api.js')
    const result = await designarCampeon('tok', 5, 7)
    expect(result).toMatchObject({ id: 5, campeon_id: 7, tie_detected: false })
  })
})

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
