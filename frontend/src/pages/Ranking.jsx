import { useState, useEffect } from 'react'
import { getRankingNarrativo, getReuniones, getTemporadaActiva } from '../services/api'
import PlayerAvatar from '../components/PlayerAvatar'
import NarrativeBadges from '../components/NarrativeBadges'
import PageHeader from '../components/PageHeader'
import { parseLocalDate, formatShortDate, maxDate } from '../lib/dates'
import {
  assignRanks,
  getPodium,
  isPodiumAsymmetric,
  placeClassForRank,
  medalLabelForRank,
  countLeaders,
  leaderGap,
} from '../lib/ranking'

/**
 * Página unificada Posiciones + Estadísticas.
 *
 * Aplica standard competition ranking (1, 1, 3, 4) — empates comparten
 * posición y la siguiente salta. Podio se muestra asimétrico solo cuando
 * los 3 ranks son únicos; con empates pasa a layout simétrico.
 */
export default function Ranking() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    Promise.all([
      getRankingNarrativo(),
      getReuniones(),
      getTemporadaActiva(),
    ])
      .then(([ranking, reuniones, temporada]) => {
        setData({ ranking, reuniones, temporada })
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="status">Cargando…</p>
  if (error) return <p className="status">Error al cargar los datos.</p>
  if (!data || !data.ranking) return <p className="status">No hay temporada activa.</p>

  // Filtra jugadores con 0 asistencias y 0 puntos (regla de negocio)
  const filtered = (data.ranking || []).filter(
    (e) => (e.asistencias || 0) > 0 || (e.puntos || 0) > 0
  )

  if (filtered.length === 0) {
    return <p className="status">Aún no hay reuniones registradas.</p>
  }

  // Asigna competition rank: 1, 1, 3, 4...
  const ranking = assignRanks(filtered)

  const reuniones = data.reuniones || []
  const temporada = data.temporada || {}

  // Solo mostramos podio cuando hay 3+ jugadores con puntos
  const hasPodium = ranking.length >= 3
  const podium = hasPodium ? getPodium(ranking) : []
  const asymmetric = isPodiumAsymmetric(podium)
  const rest = hasPodium
    ? ranking.filter((e) => e.rank > 3)
    : ranking

  const leaders = countLeaders(ranking)
  const gap = leaderGap(ranking)

  const ultimaFecha = formatShortDate(
    maxDate(reuniones.map((r) => parseLocalDate(r.fecha)))
  )

  function formatPromedio(e) {
    if (!e || !e.asistencias) return '—'
    return (e.puntos / e.asistencias).toFixed(1)
  }

  async function handleCopyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback silencioso si clipboard API no está disponible
    }
  }

  // ── Meta cell para "Líder por" / "Empate al tope" ──────────────────
  let leaderCell
  if (leaders > 1) {
    leaderCell = { label: 'Empate al tope', value: leaders, unit: 'líderes' }
  } else if (gap !== null) {
    leaderCell = { label: 'Líder por', value: gap, unit: 'pts' }
  } else {
    leaderCell = { label: 'Líder', value: ranking[0]?.nombre || '—', unit: null }
  }

  return (
    <section className="ranking-page editorial-page">
      <PageHeader
        eyebrow={temporada.nombre ? `${temporada.nombre} · En curso` : 'Temporada activa'}
        title={
          <>
            Tabla de<br />
            <span className="ital">posiciones.</span>
          </>
        }
        description="Quince puntos al primero, catorce al segundo, así hacia abajo. Los invitados toman lugar en la mesa pero no en la tabla. Los ausentes no suman."
        meta={[
          { label: 'Jornadas jugadas', value: reuniones.length },
          { label: 'Jugadores', value: ranking.length },
          {
            label: 'Última jornada',
            value: ultimaFecha ? ultimaFecha.day : '—',
            unit: ultimaFecha ? ultimaFecha.month : null,
          },
          leaderCell,
        ]}
      />

      <div className="stitch" />

      {/* ── Podio (solo si hay 3+ jugadores con puntos) ──────────── */}
      {hasPodium && (
        <>
          <div className="page-section-head">
            <h2 className="page-section-title">El podio.</h2>
            <span className="eyebrow">
              <span className="dot" />
              {asymmetric ? 'Top 3 · Promedios' : 'Empate · Top con promedios'}
            </span>
          </div>

          <div className={`podium ${asymmetric ? '' : 'symmetric'}`}>
            {podium.map((e) => {
              const placeClass = placeClassForRank(e.rank)
              const isFirst = e.rank === 1
              return (
                <article
                  key={e.id_jugador}
                  className={`podium-card ${placeClass}`}
                >
                  <div className="podium-inner">
                    <span className="podium-head">
                      <PlayerAvatar
                        nombre={e.nombre}
                        fotoUrl={e.foto_url}
                        size={isFirst ? 68 : 60}
                      />
                      <span className={`medal-badge ${placeClass}`}>
                        {medalLabelForRank(e.rank)}
                      </span>
                    </span>
                    <div className="player-name">{e.nombre}</div>
                    <div className="player-meta">{e.asistencias} asistencias</div>
                    <NarrativeBadges entry={e} variant="podium" />
                    <div className="stat-row">
                      <div className="stat">
                        <div className="k">Puntos</div>
                        <div className="v">{e.puntos}</div>
                      </div>
                      <div className="stat">
                        <div className="k">Promedio</div>
                        <div className="v">{formatPromedio(e)}</div>
                      </div>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        </>
      )}

      {/* ── Tabla completa ───────────────────────────────────────── */}
      {rest.length > 0 && (
        <>
          {hasPodium && <div className="stitch" />}

          <div className="page-section-head">
            <h2 className="page-section-title">
              {hasPodium ? 'Tabla completa.' : 'Posiciones.'}
            </h2>
            <span className="eyebrow">
              <span className="dot" />
              {ranking.length} {ranking.length === 1 ? 'jugador' : 'jugadores'}
            </span>
          </div>

          <div className="board" role="table" aria-label="Tabla de posiciones">
            <div className="row head" role="row">
              <div role="columnheader">#</div>
              <div role="columnheader">Jugador</div>
              <div role="columnheader" className="num-cell">Puntos</div>
              <div role="columnheader" className="num-cell col-asis">Asis.</div>
              <div role="columnheader" className="num-cell">Promedio</div>
            </div>

            {rest.map((e) => (
              <div className="row" key={e.id_jugador} role="row">
                <div className="pos num">{String(e.rank).padStart(2, '0')}</div>
                <div className="name">
                  <PlayerAvatar nombre={e.nombre} fotoUrl={e.foto_url} size={36} />
                  <div className="name-text">
                    <span className="apodo">{e.nombre}</span>
                    <NarrativeBadges entry={e} variant="table" />
                    <small>{e.asistencias} asistencias</small>
                  </div>
                </div>
                <div className="num-cell points">{e.puntos}</div>
                <div className="num-cell dim col-asis">{e.asistencias}</div>
                <div className="num-cell dim">{formatPromedio(e)}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── Compartir ────────────────────────────────────────────── */}
      <section className="share">
        <div>
          <h3>Comparte la mesa.</h3>
          <p>Cualquiera con el link puede consultar la tabla. Sin login.</p>
        </div>
        <button type="button" className="share-cta" onClick={handleCopyLink}>
          {copied ? 'Link copiado' : 'Copiar link público'}
          <span className="icon-pill" aria-hidden="true">
            {copied ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 1 0-7.07-7.07l-1 1" />
                <path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 1 0 7.07 7.07l1-1" />
              </svg>
            )}
          </span>
        </button>
      </section>
    </section>
  )
}
