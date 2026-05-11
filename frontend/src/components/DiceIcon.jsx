/**
 * Dado isométrico 3-caras — marca de la Liga de Dudo.
 * Muestra el "as" (1) en la cara superior, 3 a la izquierda, 2 a la derecha.
 *
 * Reutilizable: nav, loader de cold start, futuras decoraciones.
 */
export default function DiceIcon({ size = 26, className = '', ariaLabel }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 26 26"
      className={className}
      role={ariaLabel ? 'img' : 'presentation'}
      aria-label={ariaLabel}
      aria-hidden={ariaLabel ? undefined : 'true'}
    >
      {/* Right face (más oscuro: en sombra) */}
      <polygon
        points="24,7.5 13,14 13,25 24,18.5"
        fill="#7a5436"
        stroke="#3e2614"
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
      {/* Left face (cuero medio) */}
      <polygon
        points="2,7.5 13,14 13,25 2,18.5"
        fill="#b58f60"
        stroke="#3e2614"
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
      {/* Top face (hueso, más claro) */}
      <polygon
        points="13,1 24,7.5 13,14 2,7.5"
        fill="#ead8b3"
        stroke="#3e2614"
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
      {/* Top pip — el "as" wild de Dudo */}
      <circle cx="13" cy="7.5" r="1.3" fill="#1f1611" />
      {/* Left face: 3 pips diagonales */}
      <circle cx="9.2" cy="12.6" r="0.95" fill="#1f1611" />
      <circle cx="7" cy="16" r="0.95" fill="#1f1611" />
      <circle cx="4.8" cy="19.4" r="0.95" fill="#1f1611" />
      {/* Right face: 2 pips diagonales */}
      <circle cx="17" cy="12.6" r="0.95" fill="#1f1611" />
      <circle cx="20" cy="19" r="0.95" fill="#1f1611" />
    </svg>
  )
}
