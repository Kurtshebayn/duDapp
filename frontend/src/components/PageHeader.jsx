/**
 * Cabecera editorial de página. Reutilizable en cualquier vista del sistema
 * de diseño (Posiciones, Reuniones, Histórico, Dashboard, etc.).
 *
 * Layout:
 *   ┌────────────────────────────────────────┐
 *   │  EYEBROW                               │
 *   │  TITLE EDITORIAL           META  META  │
 *   │  description               META  META  │
 *   └────────────────────────────────────────┘
 *
 * Si `meta` no se pasa o está vacío, la columna derecha desaparece y el
 * texto ocupa todo el ancho.
 *
 * Props:
 *   - eyebrow: string (chip uppercase con punto cuero al lado)
 *   - title: ReactNode — usar JSX para incluir <br/> o <span className="ital">
 *   - description: string (párrafo bajo el título)
 *   - meta: Array<{ label, value, unit? }> | null
 *
 * Ejemplo:
 *   <PageHeader
 *     eyebrow="Temporada 2026 · En curso"
 *     title={<>Tabla de<br/><span className="ital">posiciones.</span></>}
 *     description="Quince puntos al primero..."
 *     meta={[
 *       { label: 'Jornadas jugadas', value: 14 },
 *       { label: 'Última jornada', value: 29, unit: 'abr' },
 *     ]}
 *   />
 */
export default function PageHeader({ eyebrow, title, description, meta }) {
  const hasMeta = Array.isArray(meta) && meta.length > 0

  return (
    <header className={`page-header ${hasMeta ? 'has-meta' : ''}`}>
      <div>
        {eyebrow && (
          <span className="eyebrow">
            <span className="dot" />
            {eyebrow}
          </span>
        )}
        {title && <h1 className="display page-header-title">{title}</h1>}
        {description && <p className="page-header-sub">{description}</p>}
      </div>

      {hasMeta && (
        <aside className="page-header-meta">
          {meta.map((cell, i) => (
            <div className="cell" key={i}>
              <div className="label">{cell.label}</div>
              <div className="value num">
                {cell.value}
                {cell.unit && <span className="unit">{cell.unit}</span>}
              </div>
            </div>
          ))}
        </aside>
      )}
    </header>
  )
}
