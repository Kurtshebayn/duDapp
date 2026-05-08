import { useState, useEffect } from 'react'
import { getHistoricoResumen, getHeadToHead } from '../services/api'
import PlayerAvatar from '../components/PlayerAvatar'

// ── Sub-tab definitions (C11) ─────────────────────────────────────────────────

const TABS = [
  { id: 'panorama', label: 'Panorama' },
  { id: 'rachas', label: 'Rachas' },
  { id: 'asistencia', label: 'Asistencia' },
  { id: 'h2h', label: 'Head-to-Head' },
]

// ── Sub-components (inline — Design 3.2) ─────────────────────────────────────

function PanoramaSection({ data }) {
  return (
    <div>
      {/* M3 — Campeones */}
      <p className="section-title">Campeones</p>
      {data.campeones.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin campeones registrados.</p>
      ) : (
        <div className="table-wrap" style={{ marginBottom: '2rem' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                <th>Campeonatos</th>
              </tr>
            </thead>
            <tbody>
              {data.campeones.map((e, i) => (
                <tr key={e.id_jugador}>
                  <td><span className={`rank-num rank-${i + 1}`}>{i + 1}</span></td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                      {e.nombre}
                    </span>
                  </td>
                  <td><strong>{e.campeonatos}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* M1 — Puntos totales */}
      <p className="section-title">Puntos totales históricos</p>
      {data.puntos_totales.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin datos.</p>
      ) : (
        <div className="table-wrap" style={{ marginBottom: '2rem' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                <th>Puntos</th>
              </tr>
            </thead>
            <tbody>
              {data.puntos_totales.map((e, i) => (
                <tr key={e.id_jugador}>
                  <td><span className={`rank-num rank-${i + 1}`}>{i + 1}</span></td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                      {e.nombre}
                    </span>
                  </td>
                  <td><strong>{e.puntos}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* M7 — Promedios */}
      <p className="section-title">Promedios</p>
      {data.promedios.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin datos.</p>
      ) : (
        <div className="table-wrap" style={{ marginBottom: '2rem' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                <th>Promedio</th>
                <th>Puntos</th>
                <th>Asist.</th>
              </tr>
            </thead>
            <tbody>
              {data.promedios.map((e, i) => (
                <tr key={e.id_jugador}>
                  <td><span className={`rank-num rank-${i + 1}`}>{i + 1}</span></td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                      {e.nombre}
                    </span>
                  </td>
                  <td><strong>{e.promedio}</strong></td>
                  <td>{e.puntos}</td>
                  <td>{e.asistencias}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function RachaCard({ item, tipo }) {
  const label =
    tipo === 'victorias' ? 'victorias consecutivas'
    : tipo === 'inasistencia' ? 'inasistencias consecutivas'
    : 'asistencias consecutivas'

  return (
    <div className="highlight-card" style={{ marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
        <PlayerAvatar nombre={item.nombre} fotoUrl={item.foto_url} size={36} />
        <span style={{ fontWeight: 700 }}>{item.nombre}</span>
        <span style={{ marginLeft: 'auto', color: 'var(--accent-light)', fontWeight: 700 }}>
          {item.longitud} {label}
        </span>
      </div>
      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
        Desde {item.temporada_inicio.nombre} jornada {item.jornada_inicio}
        {' '}hasta {item.temporada_fin.nombre} jornada {item.jornada_fin}
      </div>
    </div>
  )
}

function RachasSection({ data }) {
  return (
    <div>
      {/* M2 — Victorias */}
      <p className="section-title">Victorias históricas</p>
      {data.victorias.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin datos.</p>
      ) : (
        <div className="table-wrap" style={{ marginBottom: '2rem' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                <th>Victorias</th>
              </tr>
            </thead>
            <tbody>
              {data.victorias.map((e, i) => (
                <tr key={e.id_jugador}>
                  <td><span className={`rank-num rank-${i + 1}`}>{i + 1}</span></td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                      {e.nombre}
                    </span>
                  </td>
                  <td><strong>{e.victorias}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* M5 — Racha victorias */}
      <p className="section-title">Mayor racha de victorias</p>
      {data.racha_victorias.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin rachas registradas.</p>
      ) : (
        <div style={{ marginBottom: '2rem' }}>
          {data.racha_victorias.map(item => (
            <RachaCard key={item.id_jugador} item={item} tipo="victorias" />
          ))}
        </div>
      )}

      {/* M9 — Podios */}
      <p className="section-title">Podios históricos</p>
      {data.podios.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin datos.</p>
      ) : (
        <div className="table-wrap" style={{ marginBottom: '2rem' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                <th style={{ color: 'var(--gold)' }}>Oro</th>
                <th style={{ color: 'var(--silver)' }}>Plata</th>
                <th style={{ color: 'var(--bronze)' }}>Bronce</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {data.podios.map((e, i) => (
                <tr key={e.id_jugador}>
                  <td><span className={`rank-num rank-${i + 1}`}>{i + 1}</span></td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                      {e.nombre}
                    </span>
                  </td>
                  <td style={{ color: 'var(--gold)' }}>{e.oro}</td>
                  <td style={{ color: 'var(--silver)' }}>{e.plata}</td>
                  <td style={{ color: 'var(--bronze)' }}>{e.bronce}</td>
                  <td><strong>{e.total}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function AsistenciaSection({ data }) {
  // M4: single sorted-desc list; show top 5 as "más asistentes"
  const TOP_N = 5
  const masAsistentes = data.asistencias.slice(0, TOP_N)

  return (
    <div>
      {/* M4 — Más asistentes (top 5) */}
      <p className="section-title">Más asistencias</p>
      {masAsistentes.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin datos.</p>
      ) : (
        <div className="table-wrap" style={{ marginBottom: '2rem' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                <th>Asistencias</th>
              </tr>
            </thead>
            <tbody>
              {masAsistentes.map((e, i) => (
                <tr key={e.id_jugador}>
                  <td><span className={`rank-num rank-${i + 1}`}>{i + 1}</span></td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                      {e.nombre}
                    </span>
                  </td>
                  <td>{e.asistencias}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* M6 — Racha asistencia perfecta (top 5) */}
      <p className="section-title">Mayor racha de asistencia perfecta</p>
      {data.racha_asistencia.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin rachas registradas.</p>
      ) : (
        <div style={{ marginBottom: '2rem' }}>
          {data.racha_asistencia.map(item => (
            <RachaCard key={item.id_jugador} item={item} tipo="asistencia" />
          ))}
        </div>
      )}

      {/* M10 — Mayor racha de inasistencias (top 5) */}
      <p className="section-title">Mayor racha de inasistencias</p>
      <p className="status" style={{ padding: '0.25rem 0 0.75rem', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
        Solo jugadores con al menos 1 asistencia en cada temporada cerrada.
      </p>
      {data.racha_inasistencia.length === 0 ? (
        <p className="status" style={{ padding: '1rem 0' }}>Sin rachas registradas.</p>
      ) : (
        <div style={{ marginBottom: '2rem' }}>
          {data.racha_inasistencia.map(item => (
            <RachaCard key={item.id_jugador} item={item} tipo="inasistencia" />
          ))}
        </div>
      )}
    </div>
  )
}

function H2HSection({ resumen, h2hCache, loadingH2h, errorH2h, selectedJugadorId, onSelect }) {
  // Dropdown built from puntos_totales list, alphabetically sorted (C13)
  const jugadoresOrdenados = [...resumen.puntos_totales].sort((a, b) =>
    a.nombre.localeCompare(b.nombre)
  )

  const h2hData = selectedJugadorId != null ? h2hCache[selectedJugadorId] : null

  return (
    <div>
      <div className="form-group">
        <label className="form-label" htmlFor="h2h-select">Jugador</label>
        <select
          id="h2h-select"
          className="form-input"
          value={selectedJugadorId ?? ''}
          onChange={e => onSelect(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">Seleccioná un jugador...</option>
          {jugadoresOrdenados.map(j => (
            <option key={j.id_jugador} value={j.id_jugador}>{j.nombre}</option>
          ))}
        </select>
      </div>

      {selectedJugadorId == null && (
        <p className="status" style={{ padding: '1rem 0' }}>
          Seleccioná un jugador para ver sus enfrentamientos.
        </p>
      )}

      {selectedJugadorId != null && loadingH2h && (
        <p className="status" style={{ padding: '1rem 0' }}>Cargando...</p>
      )}

      {selectedJugadorId != null && errorH2h && !loadingH2h && (
        <p className="status" style={{ padding: '1rem 0' }}>Error al cargar los enfrentamientos.</p>
      )}

      {h2hData && !loadingH2h && !errorH2h && (
        <>
          {h2hData.rivales.length === 0 ? (
            <p className="status" style={{ padding: '1rem 0' }}>
              {h2hData.nombre} no tiene reuniones compartidas con otros jugadores.
            </p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Rival</th>
                    <th>Victorias</th>
                    <th>Derrotas</th>
                    <th>Reuniones</th>
                  </tr>
                </thead>
                <tbody>
                  {h2hData.rivales.map(r => (
                    <tr key={r.rival_id}>
                      <td>
                        <span className="player-name-cell">
                          <PlayerAvatar nombre={r.rival_nombre} fotoUrl={r.rival_foto_url} />
                          {r.rival_nombre}
                        </span>
                      </td>
                      <td style={{ color: 'var(--accent-light)' }}><strong>{r.victorias}</strong></td>
                      <td style={{ color: 'var(--text-muted)' }}>{r.derrotas}</td>
                      <td>{r.reuniones_compartidas}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Historico() {
  const [activeTab, setActiveTab] = useState('panorama')
  const [resumen, setResumen] = useState(null)
  const [loadingResumen, setLoadingResumen] = useState(true)
  const [errorResumen, setErrorResumen] = useState(null)
  const [selectedJugadorId, setSelectedJugadorId] = useState(null)
  const [h2hCache, setH2hCache] = useState({})
  const [loadingH2h, setLoadingH2h] = useState(false)
  const [errorH2h, setErrorH2h] = useState(null)

  useEffect(() => {
    getHistoricoResumen()
      .then(data => {
        setResumen(data)
        setLoadingResumen(false)
      })
      .catch(err => {
        setErrorResumen(err)
        setLoadingResumen(false)
      })
  }, [])

  function handleSelectJugador(id) {
    setSelectedJugadorId(id)
    setErrorH2h(null)

    if (id == null) return

    // Cache hit — no fetch needed
    if (h2hCache[id] !== undefined) return

    // Fetch and cache
    setLoadingH2h(true)
    getHeadToHead(id)
      .then(data => {
        if (data === null) {
          // apiFetch returns null on 404
          setErrorH2h(new Error('Jugador no encontrado'))
        } else {
          setH2hCache(prev => ({ ...prev, [id]: data }))
        }
        setLoadingH2h(false)
      })
      .catch(err => {
        setErrorH2h(err)
        setLoadingH2h(false)
      })
  }

  if (loadingResumen) return <p className="status">Cargando...</p>
  if (errorResumen) return <p className="status">Error al cargar el histórico.</p>
  if (!resumen) return <p className="status">Error al cargar el histórico.</p>

  // Empty state: all 9 arrays empty
  const isEmpty = (
    resumen.puntos_totales.length === 0 &&
    resumen.victorias.length === 0 &&
    resumen.campeones.length === 0 &&
    resumen.asistencias.length === 0 &&
    resumen.racha_victorias.length === 0 &&
    resumen.racha_asistencia.length === 0 &&
    resumen.promedios.length === 0 &&
    resumen.podios.length === 0 &&
    resumen.racha_inasistencia.length === 0
  )

  if (isEmpty) {
    return (
      <>
        <h1>Histórico de la liga</h1>
        <p className="status">Aún no hay temporadas cerradas en la liga.</p>
      </>
    )
  }

  return (
    <>
      <h1>Histórico de la liga</h1>

      <div className="subtabs" style={{ marginBottom: '1.5rem' }}>
        {TABS.map(t => (
          <button
            key={t.id}
            className={`subtab${activeTab === t.id ? ' active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'panorama' && <PanoramaSection data={resumen} />}
      {activeTab === 'rachas' && <RachasSection data={resumen} />}
      {activeTab === 'asistencia' && <AsistenciaSection data={resumen} />}
      {activeTab === 'h2h' && (
        <H2HSection
          resumen={resumen}
          h2hCache={h2hCache}
          loadingH2h={loadingH2h}
          errorH2h={errorH2h}
          selectedJugadorId={selectedJugadorId}
          onSelect={handleSelectJugador}
        />
      )}
    </>
  )
}
