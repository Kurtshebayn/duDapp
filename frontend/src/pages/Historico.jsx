import { useState, useEffect } from 'react'
import { getHistoricoResumen, getHeadToHead } from '../services/api'
import PlayerAvatar from '../components/PlayerAvatar'
import PageHeader from '../components/PageHeader'

// ── Sub-tab definitions ──────────────────────────────────────────────────────

const TABS = [
  { id: 'panorama', label: 'Panorama' },
  { id: 'rachas', label: 'Rachas' },
  { id: 'asistencia', label: 'Asistencia' },
  { id: 'h2h', label: 'Head-to-Head' },
]

// ── Sub-components ───────────────────────────────────────────────────────────

function PanoramaSection({ data }) {
  return (
    <div>
      <RankedTable
        title="Campeones"
        emptyMsg="Sin campeones registrados."
        rows={data.campeones}
        columns={[{ key: 'campeonatos', label: 'Campeonatos', strong: true }]}
      />

      <RankedTable
        title="Puntos totales históricos"
        emptyMsg="Sin datos."
        rows={data.puntos_totales}
        columns={[{ key: 'puntos', label: 'Puntos', strong: true }]}
      />

      <RankedTable
        title="Promedios"
        emptyMsg="Sin datos."
        rows={data.promedios}
        columns={[
          { key: 'promedio', label: 'Promedio', strong: true },
          { key: 'puntos', label: 'Puntos' },
          { key: 'asistencias', label: 'Asist.' },
        ]}
      />
    </div>
  )
}

function RachasSection({ data }) {
  return (
    <div>
      <RankedTable
        title="Victorias históricas"
        emptyMsg="Sin datos."
        rows={data.victorias}
        columns={[{ key: 'victorias', label: 'Victorias', strong: true }]}
      />

      <h3 className="historico-subtitle">Mayor racha de victorias</h3>
      {data.racha_victorias.length === 0 ? (
        <p className="status historico-empty">Sin rachas registradas.</p>
      ) : (
        <div className="historico-racha-list">
          {data.racha_victorias.map(item => (
            <RachaCard key={item.id_jugador} item={item} tipo="victorias" />
          ))}
        </div>
      )}

      <h3 className="historico-subtitle">Podios históricos</h3>
      {data.podios.length === 0 ? (
        <p className="status historico-empty">Sin datos.</p>
      ) : (
        <div className="table-wrap historico-table">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                <th className="th-gold">Oro</th>
                <th className="th-silver">Plata</th>
                <th className="th-bronze">Bronce</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {data.podios.map((e, i) => (
                <tr key={e.id_jugador}>
                  <td>
                    <span className={`rank-num rank-${i + 1}`}>{i + 1}</span>
                  </td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                      {e.nombre}
                    </span>
                  </td>
                  <td className="td-gold">{e.oro}</td>
                  <td className="td-silver">{e.plata}</td>
                  <td className="td-bronze">{e.bronce}</td>
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
  const TOP_N = 5
  const masAsistentes = data.asistencias.slice(0, TOP_N)

  return (
    <div>
      <RankedTable
        title="Más asistencias"
        emptyMsg="Sin datos."
        rows={masAsistentes}
        columns={[{ key: 'asistencias', label: 'Asistencias' }]}
      />

      <h3 className="historico-subtitle">Mayor racha de asistencia perfecta</h3>
      {data.racha_asistencia.length === 0 ? (
        <p className="status historico-empty">Sin rachas registradas.</p>
      ) : (
        <div className="historico-racha-list">
          {data.racha_asistencia.map(item => (
            <RachaCard key={item.id_jugador} item={item} tipo="asistencia" />
          ))}
        </div>
      )}

      <h3 className="historico-subtitle">Mayor racha de inasistencias</h3>
      <p className="historico-note">
        Solo jugadores con al menos 1 asistencia en cada temporada cerrada.
      </p>
      {data.racha_inasistencia.length === 0 ? (
        <p className="status historico-empty">Sin rachas registradas.</p>
      ) : (
        <div className="historico-racha-list">
          {data.racha_inasistencia.map(item => (
            <RachaCard key={item.id_jugador} item={item} tipo="inasistencia" />
          ))}
        </div>
      )}
    </div>
  )
}

function H2HSection({ resumen, h2hCache, loadingH2h, errorH2h, selectedJugadorId, onSelect }) {
  const jugadoresOrdenados = [...resumen.puntos_totales].sort((a, b) =>
    a.nombre.localeCompare(b.nombre)
  )

  const h2hData = selectedJugadorId != null ? h2hCache[selectedJugadorId] : null

  return (
    <div>
      <div className="form-group historico-h2h-form">
        <label className="form-label" htmlFor="h2h-select">Elige un jugador</label>
        <select
          id="h2h-select"
          className="form-input"
          value={selectedJugadorId ?? ''}
          onChange={e => onSelect(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">Selecciona un jugador…</option>
          {jugadoresOrdenados.map(j => (
            <option key={j.id_jugador} value={j.id_jugador}>{j.nombre}</option>
          ))}
        </select>
      </div>

      {selectedJugadorId == null && (
        <p className="status historico-empty">
          Seleccioná un jugador para ver sus enfrentamientos.
        </p>
      )}

      {selectedJugadorId != null && loadingH2h && (
        <p className="status historico-empty">Cargando…</p>
      )}

      {selectedJugadorId != null && errorH2h && !loadingH2h && (
        <p className="status historico-empty">Error al cargar los enfrentamientos.</p>
      )}

      {h2hData && !loadingH2h && !errorH2h && (
        <>
          {h2hData.rivales.length === 0 ? (
            <p className="status historico-empty">
              {h2hData.nombre} no tiene reuniones compartidas con otros jugadores.
            </p>
          ) : (
            <div className="table-wrap historico-table">
              <table>
                <thead>
                  <tr>
                    <th>Rival</th>
                    <th>Reuniones</th>
                    <th>Mejor desempeño</th>
                    <th>Peor desempeño</th>
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
                      <td>{r.reuniones_compartidas}</td>
                      <td className="h2h-wins"><strong>{r.victorias}</strong></td>
                      <td className="h2h-losses">{r.derrotas}</td>
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

/**
 * Tabla compartida para los rankings históricos.
 * `columns` es array de { key, label, strong? } — strong hace el valor bold.
 */
function RankedTable({ title, emptyMsg, rows, columns }) {
  return (
    <div>
      <h3 className="historico-subtitle">{title}</h3>
      {rows.length === 0 ? (
        <p className="status historico-empty">{emptyMsg}</p>
      ) : (
        <div className="table-wrap historico-table">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                {columns.map(c => (
                  <th key={c.key}>{c.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((e, i) => (
                <tr key={e.id_jugador}>
                  <td>
                    <span className={`rank-num rank-${i + 1}`}>{i + 1}</span>
                  </td>
                  <td>
                    <span className="player-name-cell">
                      <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} />
                      {e.nombre}
                    </span>
                  </td>
                  {columns.map(c => (
                    <td key={c.key}>
                      {c.strong ? <strong>{e[c.key]}</strong> : e[c.key]}
                    </td>
                  ))}
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
    <div className="racha-card">
      <div className="racha-card-head">
        <PlayerAvatar nombre={item.nombre} fotoUrl={item.foto_url} size={40} />
        <span className="racha-card-name">{item.nombre}</span>
        <span className="racha-card-count">
          <span className="num">{item.longitud}</span> {label}
        </span>
      </div>
      <div className="racha-card-range">
        Desde {item.temporada_inicio.nombre} jornada {item.jornada_inicio}
        {' '}hasta {item.temporada_fin.nombre} jornada {item.jornada_fin}
      </div>
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

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
    if (h2hCache[id] !== undefined) return

    setLoadingH2h(true)
    getHeadToHead(id)
      .then(data => {
        if (data === null) {
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

  if (loadingResumen) return <p className="status">Cargando…</p>
  if (errorResumen || !resumen) return <p className="status">Error al cargar el histórico.</p>

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
      <section className="editorial-page historico-page">
        <PageHeader
          eyebrow="Liga · Todas las temporadas"
          title={<>El <span className="ital">histórico.</span></>}
          description="Acá viven los récords, los campeones y las rachas. Por ahora la página espera la primera temporada cerrada."
        />
      </section>
    )
  }

  return (
    <section className="editorial-page historico-page">
      <PageHeader
        eyebrow="Liga · Todas las temporadas"
        title={<>El <span className="ital">histórico.</span></>}
        description="Récords acumulados a lo largo de todas las temporadas cerradas. Campeones, rachas, asistencia y enfrentamientos directos."
      />

      <div className="stitch" />

      <div className="historico-tabs" role="tablist">
        {TABS.map(t => (
          <button
            key={t.id}
            role="tab"
            aria-selected={activeTab === t.id}
            className={`historico-tab${activeTab === t.id ? ' active' : ''}`}
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
    </section>
  )
}
