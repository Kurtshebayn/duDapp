/**
 * NarrativeBadges — renders narrative pills for a ranking entry.
 *
 * Priority order: líder > racha > delta.
 * variant='table': max 2 badges (cap by priority).
 * variant='podium': all applicable badges (no cap).
 *
 * Returns null when no badges apply (no empty div in DOM).
 */
export default function NarrativeBadges({ entry, variant }) {
  const badges = []

  // Build in priority order: líder > racha > delta
  if (entry.lider_desde_jornada != null) {
    badges.push({
      key: 'leader',
      tone: 'leader',
      text: `líder desde J-${entry.lider_desde_jornada}`,
    })
  }
  if (entry.racha > 0) {
    badges.push({
      key: 'racha',
      tone: 'racha',
      text: `racha de ${entry.racha}`,
    })
  }
  if (entry.delta_posicion > 0) {
    badges.push({
      key: 'delta',
      tone: 'positive',
      text: `sube ${entry.delta_posicion}`,
    })
  } else if (entry.delta_posicion < 0) {
    badges.push({
      key: 'delta',
      tone: 'regression',
      text: `cae ${Math.abs(entry.delta_posicion)}`,
    })
  }

  if (badges.length === 0) return null

  const visible = variant === 'table' ? badges.slice(0, 2) : badges

  return (
    <div className="narrative-strip">
      {visible.map((b) => (
        <span key={b.key} className={`narrative-pill narrative-pill--${b.tone}`}>
          {b.text}
        </span>
      ))}
    </div>
  )
}
