const COLORS = [
  ['#3b1f6e', '#a07de0'],
  ['#1f3b6e', '#7da0e0'],
  ['#1f6e3b', '#7de0a0'],
  ['#6e3b1f', '#e0a07d'],
  ['#6e1f5a', '#e07dd4'],
  ['#1f5a6e', '#7dd4e0'],
]

function colorForName(name) {
  const code = name.charCodeAt(0) || 0
  return COLORS[code % COLORS.length]
}

export default function PlayerAvatar({ nombre, fotoUrl, size = 28 }) {
  const style = { width: size, height: size, borderRadius: '50%', flexShrink: 0 }

  if (fotoUrl) {
    return (
      <img
        src={fotoUrl}
        alt={nombre}
        style={{ ...style, objectFit: 'cover' }}
      />
    )
  }

  const [bg, color] = colorForName(nombre ?? '?')
  return (
    <span
      style={{
        ...style,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: bg,
        color,
        fontWeight: 700,
        fontSize: Math.round(size * 0.45),
        userSelect: 'none',
      }}
    >
      {(nombre ?? '?')[0].toUpperCase()}
    </span>
  )
}
