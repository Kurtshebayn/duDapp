/**
 * Avatar circular de jugador.
 * - Si hay fotoUrl, renderiza la imagen.
 * - Si no, renderiza un círculo con la inicial sobre un gradiente cuero.
 *
 * El gradiente varía levemente según el nombre para dar identidad visual
 * a jugadores sin foto, sin romper la paleta cream/leather.
 */

const WARM_PAIRS = [
  // [background gradient (de → a), color de texto]
  ['#6b4423', '#a87a52', '#f5efe0'],   // saddle leather → light leather, texto hueso
  ['#3e2614', '#7a5436', '#ead8b3'],   // espresso → mid leather, texto bone
  ['#8b5a2b', '#c98860', '#fbf7ee'],   // copper → light copper, texto marfil
  ['#5c3d1f', '#9a7148', '#f5f1e7'],   // dark leather → tan, texto marfil
  ['#7d6020', '#c9a14b', '#1f1611'],   // dark gold → gold, texto tinta (contraste)
  ['#5e5852', '#9a9388', '#1f1611'],   // dark pewter → pewter, texto tinta
]

function colorPairFor(name) {
  const code = (name || '?').charCodeAt(0) || 0
  return WARM_PAIRS[code % WARM_PAIRS.length]
}

export default function PlayerAvatar({ nombre, fotoUrl, size = 28 }) {
  const baseStyle = {
    width: size,
    height: size,
    borderRadius: '50%',
    flexShrink: 0,
  }

  if (fotoUrl) {
    return (
      <img
        src={fotoUrl}
        alt={nombre}
        style={{ ...baseStyle, objectFit: 'cover', display: 'block' }}
      />
    )
  }

  const [from, to, color] = colorPairFor(nombre)
  return (
    <span
      aria-hidden="true"
      style={{
        ...baseStyle,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, ${from}, ${to})`,
        color,
        fontFamily: '"Instrument Serif", "Newsreader", Georgia, serif',
        fontSize: Math.round(size * 0.5),
        userSelect: 'none',
        boxShadow:
          'inset 0 1px 0 rgba(255, 255, 255, 0.18), inset 0 -1px 2px rgba(0, 0, 0, 0.18)',
      }}
    >
      {(nombre ?? '?')[0].toUpperCase()}
    </span>
  )
}
