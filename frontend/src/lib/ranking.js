/**
 * Helpers de ranking — competition ranking, podio, helpers de medalla.
 *
 * Convención: standard competition ranking ("1, 1, 3, 4").
 * Si dos jugadores empatan en puntos, comparten posición; el siguiente
 * salta el número que ocuparían los empatados. Patrón olímpico.
 */

const PLACE_CLASS_BY_RANK = { 1: 'gold', 2: 'silver', 3: 'bronze' }
const MEDAL_LABEL_BY_RANK = { 1: 'I', 2: 'II', 3: 'III' }

/**
 * Asigna `rank` a cada entrada del ranking según puntos descendentes.
 * Asume que el array YA viene ordenado por puntos desc desde el backend.
 *
 *   [{p:100}, {p:100}, {p:80}, {p:70}]
 *   → [{p:100, rank:1}, {p:100, rank:1}, {p:80, rank:3}, {p:70, rank:4}]
 */
export function assignRanks(ranking) {
  const result = []
  for (let i = 0; i < ranking.length; i++) {
    const sameAsPrev =
      i > 0 && ranking[i].puntos === ranking[i - 1].puntos
    const rank = sameAsPrev ? result[i - 1].rank : i + 1
    result.push({ ...ranking[i], rank })
  }
  return result
}

/**
 * Devuelve los jugadores que pertenecen al podio (rank ≤ 3).
 * Puede devolver más de 3 entradas si hay empate justo en la posición
 * de corte (ej: dos terceros → podium tiene 4 entries).
 */
export function getPodium(ranked) {
  return ranked.filter((e) => e.rank <= 3)
}

/**
 * ¿El podio merece el layout asimétrico (silver-gold↑-bronze)?
 * Solo si tiene exactamente 3 jugadores con ranks únicos 1, 2, 3.
 * Cualquier empate o cantidad distinta de 3 fuerza el layout simétrico.
 */
export function isPodiumAsymmetric(podium) {
  if (podium.length !== 3) return false
  const ranks = podium.map((e) => e.rank).sort()
  return ranks[0] === 1 && ranks[1] === 2 && ranks[2] === 3
}

/** Mapea rank → clase CSS (gold/silver/bronze). Defaults a bronze. */
export function placeClassForRank(rank) {
  return PLACE_CLASS_BY_RANK[rank] || 'bronze'
}

/** Mapea rank → numeral romano (I/II/III). Defaults a III. */
export function medalLabelForRank(rank) {
  return MEDAL_LABEL_BY_RANK[rank] || 'III'
}

/**
 * Devuelve cuántos jugadores comparten el primer puesto.
 * Útil para mostrar "Empate · N líderes" vs "Líder por X pts".
 */
export function countLeaders(ranked) {
  return ranked.filter((e) => e.rank === 1).length
}

/**
 * Diferencia en puntos entre el grupo líder y el siguiente grupo distinto.
 * Devuelve null si no hay siguiente grupo (todos empatados al tope).
 */
export function leaderGap(ranked) {
  if (ranked.length === 0) return null
  const leader = ranked[0]
  const next = ranked.find((e) => e.rank > leader.rank)
  return next ? leader.puntos - next.puntos : null
}
