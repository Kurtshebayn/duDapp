/**
 * Helpers de fechas para todo el frontend.
 *
 * Regla de oro: cuando el backend devuelve fechas como strings sin timezone
 * (ej: "2026-04-29"), `new Date(str)` las parsea como UTC midnight, lo que
 * causa corrimiento de un día en zonas horarias al oeste de UTC. Estas
 * funciones evitan el bug parseando como hora LOCAL.
 */

/**
 * Parsea un string de fecha del backend a Date local.
 * Soporta:
 *   "2026-04-29"
 *   "2026-04-29T00:00:00"
 *   "2026-04-29T03:00:00-03:00"
 *   "2026-04-29T00:00:00Z"
 *
 * Devuelve null si el string es vacío o malformado.
 */
export function parseLocalDate(str) {
  if (!str) return null
  const m = String(str).match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) {
    return new Date(+m[1], +m[2] - 1, +m[3])
  }
  const d = new Date(str)
  return isNaN(d.getTime()) ? null : d
}

/**
 * Formato corto editorial: { day: 5, month: "may" }
 *
 * Devuelve un objeto en lugar de un string para que el caller pueda
 * renderizar el día y mes con tipografías diferentes (mono vs sans).
 */
export function formatShortDate(date) {
  if (!date) return null
  const day = date.getDate()
  const month = new Intl.DateTimeFormat('es', { month: 'short' })
    .format(date)
    .replace('.', '')
    .toLowerCase()
  return { day, month }
}

/**
 * Formato largo: "29 de abril de 2026"
 * Útil para detalles de reunión, headers de jornada específica.
 */
export function formatLongDate(date) {
  if (!date) return null
  return new Intl.DateTimeFormat('es', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

/**
 * Formato día + mes largo: "29 de abril"
 * Útil para listas dentro de una temporada activa donde el año es implícito.
 */
export function formatDayMonth(date) {
  if (!date) return null
  return new Intl.DateTimeFormat('es', {
    day: 'numeric',
    month: 'long',
  }).format(date)
}

/**
 * Compara dos fechas y devuelve la más reciente.
 * Útil para encontrar la última jornada en una lista de reuniones.
 */
export function maxDate(dates) {
  return dates.reduce((max, d) => {
    if (!d) return max
    return !max || d > max ? d : max
  }, null)
}

/**
 * Convierte un entero (1-3999) a numeral romano.
 * Útil para fechas con vibe diploma / sello editorial.
 * Devuelve string vacío si el input es inválido.
 */
export function toRoman(num) {
  const n = Number(num)
  if (!Number.isInteger(n) || n < 1 || n > 3999) return ''
  const map = [
    [1000, 'M'], [900, 'CM'], [500, 'D'], [400, 'CD'],
    [100, 'C'], [90, 'XC'], [50, 'L'], [40, 'XL'],
    [10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I'],
  ]
  let result = ''
  let rest = n
  for (const [val, sym] of map) {
    while (rest >= val) {
      result += sym
      rest -= val
    }
  }
  return result
}
