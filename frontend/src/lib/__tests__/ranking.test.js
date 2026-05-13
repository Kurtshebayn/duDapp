import { describe, it, expect } from 'vitest'
import fixtures from '../../../../backend/tests/fixtures/competition_ranking.json'
import { assignRanks } from '../ranking'

describe('assignRanks — bit-exact contract con backend fixtures', () => {
  fixtures.forEach((scenario) => {
    it(scenario.name, () => {
      const result = assignRanks(scenario.input)
      expect(result.length).toBe(scenario.expected.length)
      scenario.expected.forEach((expectedEntry, i) => {
        expect(result[i].rank).toBe(expectedEntry.posicion)
      })
    })
  })
})
