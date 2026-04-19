import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../hooks/useAuth'
import { spotifyApi } from '../api/musemapApi'
import api from '../api/musemapApi'

const GENRE_OPTIONS = [
  'Jazz','Soul','Hip-Hop','Electronic','Rock',
  'R&B','Indie','Classical','Pop','Blues','Funk','Reggae'
]

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Cabinet+Grotesk:wght@400;500;700;800&family=Instrument+Sans:wght@400;500&display=swap');

  .studio-root {
    min-height: 100vh;
    background: #0a0a0f;
    color: #e8e6f0;
    font-family: 'Instrument Sans', sans-serif;
    padding: 2rem 2rem 4rem;
  }

  .studio-logo {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-weight: 800;
    font-size: 1.5rem;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #c084fc, #818cf8, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .studio-section-label {
    font-size: 10px;
    font-weight: 500;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: #52505f;
    margin-bottom: 12px;
    display: block;
  }

  /* ── Playlist cards ── */
  .pl-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
    margin-bottom: 2rem;
  }

  .pl-card {
    position: relative;
    border-radius: 14px;
    overflow: hidden;
    cursor: pointer;
    border: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.03);
    transition: transform 0.2s cubic-bezier(.34,1.56,.64,1), border-color 0.2s, box-shadow 0.2s;
    aspect-ratio: 1 / 1.1;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 12px;
  }

  .pl-card:hover {
    transform: translateY(-4px) scale(1.02);
    border-color: rgba(192,132,252,0.35);
    box-shadow: 0 12px 32px rgba(129,140,248,0.15), 0 0 0 1px rgba(192,132,252,0.2);
  }

  .pl-card.selected {
    border-color: rgba(192,132,252,0.6);
    background: rgba(129,140,248,0.08);
    box-shadow: 0 0 0 1px rgba(192,132,252,0.4), 0 8px 24px rgba(129,140,248,0.2);
  }

  .pl-card .cover-bg {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    opacity: 0.35;
    transition: opacity 0.2s;
  }

  .pl-card:hover .cover-bg,
  .pl-card.selected .cover-bg {
    opacity: 0.55;
  }

  .pl-card .cover-fallback {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    opacity: 0.15;
    transition: opacity 0.2s;
  }

  .pl-card:hover .cover-fallback {
    opacity: 0.3;
  }

  .pl-card .pl-info {
    position: relative;
    z-index: 1;
  }

  .pl-card .pl-name {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-weight: 700;
    font-size: 13px;
    color: #f0eeff;
    line-height: 1.3;
    margin-bottom: 3px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .pl-card .pl-count {
    font-size: 11px;
    color: #7c7a8a;
  }

  .pl-card .check-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: linear-gradient(135deg, #c084fc, #818cf8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    z-index: 2;
    opacity: 0;
    transform: scale(0.6);
    transition: opacity 0.15s, transform 0.2s cubic-bezier(.34,1.56,.64,1);
  }

  .pl-card.selected .check-badge {
    opacity: 1;
    transform: scale(1);
  }

  /* ── Filter chips ── */
  .filter-chip {
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    color: #7c7a8a;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }

  .filter-chip:hover { border-color: rgba(192,132,252,0.3); color: #c4b5fd; }

  .filter-chip.active {
    background: rgba(192,132,252,0.12);
    border-color: rgba(192,132,252,0.5);
    color: #c084fc;
  }

  /* ── Inputs ── */
  .studio-input {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 8px 12px;
    color: #e8e6f0;
    font-size: 13px;
    font-family: 'Instrument Sans', sans-serif;
    outline: none;
    width: 110px;
    transition: border-color 0.15s;
  }

  .studio-input:focus { border-color: rgba(192,132,252,0.5); }
  .studio-input::placeholder { color: #3d3b4a; }

  /* ── Boutons ── */
  .btn-apply {
    padding: 9px 22px;
    border-radius: 999px;
    border: none;
    background: linear-gradient(135deg, #c084fc, #818cf8);
    color: white;
    font-family: 'Cabinet Grotesk', sans-serif;
    font-weight: 700;
    font-size: 13px;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
  }

  .btn-apply:hover { opacity: 0.88; transform: translateY(-1px); }
  .btn-apply:disabled { background: #2a2836; color: #52505f; cursor: default; transform: none; }

  .btn-export {
    padding: 9px 20px;
    border-radius: 10px;
    border: 1px solid rgba(56,189,248,0.4);
    background: rgba(56,189,248,0.08);
    color: #38bdf8;
    font-family: 'Cabinet Grotesk', sans-serif;
    font-weight: 700;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-export:hover { background: rgba(56,189,248,0.14); border-color: rgba(56,189,248,0.6); }

  /* ── Table ── */
  .studio-table-wrap {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1.5rem;
  }

  .studio-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }

  .studio-table th {
    padding: 11px 14px;
    text-align: left;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #52505f;
    background: rgba(255,255,255,0.02);
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }

  .studio-table td {
    padding: 11px 14px;
    font-size: 13px;
    color: #b8b5c8;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: background 0.1s;
  }

  .studio-table tr:last-child td { border-bottom: none; }

  .studio-table tbody tr:hover td {
    background: rgba(255,255,255,0.025);
    color: #e8e6f0;
  }

  .track-link { color: #c084fc; text-decoration: none; }
  .track-link:hover { color: #e9d5ff; }

  /* ── Pop badge ── */
  .pop-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 500;
  }

  /* ── Modal ── */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
    padding: 1rem;
  }

  .modal-box {
    background: #13111f;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 1.75rem;
    width: 100%;
    max-width: 380px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.6);
  }

  .modal-title {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-weight: 800;
    font-size: 18px;
    color: #f0eeff;
    margin-bottom: 4px;
  }

  .modal-sub { font-size: 13px; color: #52505f; margin-bottom: 1.5rem; }

  .export-opt {
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 8px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.15s;
    text-align: left;
    width: 100%;
  }

  .export-opt:hover { transform: translateY(-1px); }

  .export-opt .opt-title {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 3px;
  }

  .export-opt .opt-desc { font-size: 12px; }

  .opt-spotify {
    background: rgba(29,158,117,0.1);
    border-color: rgba(29,158,117,0.35);
  }
  .opt-spotify:hover { background: rgba(29,158,117,0.18); border-color: rgba(29,158,117,0.6); }
  .opt-spotify .opt-title { color: #34d399; }
  .opt-spotify .opt-desc  { color: #059669; }

  .opt-csv {
    background: rgba(56,189,248,0.08);
    border-color: rgba(56,189,248,0.3);
  }
  .opt-csv:hover { background: rgba(56,189,248,0.14); border-color: rgba(56,189,248,0.55); }
  .opt-csv .opt-title { color: #38bdf8; }
  .opt-csv .opt-desc  { color: #0369a1; }

  .btn-cancel {
    width: 100%;
    margin-top: 10px;
    padding: 10px;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.06);
    background: transparent;
    color: #52505f;
    font-size: 13px;
    cursor: pointer;
    transition: color 0.15s;
  }
  .btn-cancel:hover { color: #b8b5c8; }

  /* ── Error / success banners ── */
  .banner-error   { background: rgba(220,38,38,0.1);  border: 1px solid rgba(220,38,38,0.25);  color: #fca5a5; border-radius: 10px; padding: 10px 14px; font-size: 13px; margin-bottom: 1rem; }
  .banner-success { background: rgba(29,158,117,0.1); border: 1px solid rgba(29,158,117,0.25); color: #6ee7b7; border-radius: 10px; padding: 10px 14px; font-size: 13px; margin-bottom: 1rem; }

  /* ── Divider ── */
  .divider { height: 1px; background: rgba(255,255,255,0.05); margin: 1.75rem 0; border: none; }

  /* ── Stats row ── */
  .stats-row {
    display: flex;
    gap: 16px;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    align-items: center;
  }

  .stat-chip {
    font-size: 12px;
    color: #52505f;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 999px;
    padding: 4px 12px;
  }

  .stat-chip span { color: #c084fc; font-weight: 500; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
`

export default function Studio() {
  const { user } = useAuth()

  const [playlists,     setPlaylists]     = useState([])
  const [selectedPids,  setSelectedPids]  = useState([])
  const [tracks,        setTracks]        = useState([])
  const [stats,         setStats]         = useState(null)
  const [loading,       setLoading]       = useState(false)
  const [showModal,     setShowModal]     = useState(false)
  const [exporting,     setExporting]     = useState(false)
  const [exportUrl,     setExportUrl]     = useState('')
  const [error,         setError]         = useState('')

  const [filterGenres,  setFilterGenres]  = useState([])
  const [yearMin,       setYearMin]       = useState('')
  const [yearMax,       setYearMax]       = useState('')
  const [popMin,        setPopMin]        = useState('')

  useEffect(() => {
    spotifyApi.getPlaylists(50)
      .then(r => setPlaylists(r.data))
      .catch(() => setError('Impossible de charger les playlists. Reconnecte-toi.'))
  }, [])

  const togglePid = id =>
    setSelectedPids(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id])

  const toggleGenre = g =>
    setFilterGenres(p => p.includes(g) ? p.filter(x => x !== g) : [...p, g])

  const handleFilter = async () => {
    if (!selectedPids.length) { setError('Sélectionne au moins une playlist.'); return }
    setError(''); setLoading(true); setTracks([]); setStats(null); setExportUrl('')
    try {
      const { data } = await api.post('/studio/filter', {
        playlist_ids:   selectedPids,
        genres:         filterGenres,
        year_min:       yearMin ? parseInt(yearMin) : null,
        year_max:       yearMax ? parseInt(yearMax) : null,
        popularity_min: popMin  ? parseInt(popMin)  : null,
      })
      setTracks(data.tracks || [])
      setStats(data.stats)
    } catch(e) {
      setError(e.response?.data?.detail || 'Erreur lors du filtrage.')
    } finally { setLoading(false) }
  }

  const handleExportSpotify = async () => {
    setExporting(true); setError('')
    const name = `MuseMap · ${new Date().toLocaleDateString('fr-FR')}`
    try {
      const { data } = await api.post('/studio/export/spotify', {
        track_ids:     tracks.map(t => t.spotify_id),
        playlist_name: name,
        public:        false,
      })
      setExportUrl(data.playlist_url)
      setShowModal(false)
    } catch(e) {
      setError(e.response?.data?.detail || 'Export Spotify échoué.')
    } finally { setExporting(false) }
  }

  const handleExportCsv = () => {
    const header = ['Titre','Artiste','Album','Année','Popularité','ISRC','URL Spotify']
    const rows   = tracks.map(t => [
      `"${(t.name   || '').replace(/"/g, '""')}"`,
      `"${(t.artist || '').replace(/"/g, '""')}"`,
      `"${(t.album  || '').replace(/"/g, '""')}"`,
      t.release_year || '',
      t.popularity   || '',
      t.isrc         || '',
      t.spotify_url  || '',
    ])
    const csv  = [header, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = 'musemap_export.csv'; a.click()
    URL.revokeObjectURL(url)
    setShowModal(false)
  }

  const popColor = (p) => {
    if (!p) return { bg:'rgba(255,255,255,0.05)', color:'#52505f' }
    if (p > 70) return { bg:'rgba(29,158,117,0.15)', color:'#34d399' }
    if (p > 40) return { bg:'rgba(186,117,23,0.15)', color:'#fbbf24' }
    return { bg:'rgba(217,70,48,0.15)', color:'#fb7185' }
  }

  return (
    <>
      <style>{css}</style>
      <div className="studio-root">

        {/* ── Header ── */}
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'2.5rem' }}>
          <div>
            <div className="studio-logo">MuseMap</div>
            <p style={{ fontSize:'12px', color:'#3d3b4a', marginTop:'2px', fontWeight:500, letterSpacing:'.06em' }}>
              STUDIO
            </p>
          </div>
          {user && (
            <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
              <div style={{ width:'32px', height:'32px', borderRadius:'50%', background:'linear-gradient(135deg,#c084fc,#818cf8)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'13px', fontWeight:700, color:'white' }}>
                {(user.display_name || 'U')[0].toUpperCase()}
              </div>
              <span style={{ fontSize:'13px', color:'#7c7a8a' }}>{user.display_name}</span>
            </div>
          )}
        </div>

        {/* ── Playlists grid ── */}
        <span className="studio-section-label">
          Playlists · {selectedPids.length > 0 ? `${selectedPids.length} sélectionnées` : 'Clique pour sélectionner'}
        </span>

        {playlists.length === 0 && !error && (
          <div style={{ display:'flex', gap:'10px', marginBottom:'2rem' }}>
            {[1,2,3,4,5,6].map(i => (
              <div key={i} style={{ flex:'0 0 160px', aspectRatio:'1/1.1', borderRadius:'14px', background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.05)', animation:'pulse 1.5s ease-in-out infinite', animationDelay:`${i*0.1}s` }} />
            ))}
          </div>
        )}

        <div className="pl-grid">
          {playlists.map(p => {
            const sel = selectedPids.includes(p.spotify_id)
            return (
              <div
                key={p.spotify_id}
                className={`pl-card${sel ? ' selected' : ''}`}
                onClick={() => togglePid(p.spotify_id)}
              >
                {p.image_url
                  ? <div className="cover-bg" style={{ backgroundImage:`url(${p.image_url})` }} />
                  : <div className="cover-fallback">♪</div>
                }
                <div className="check-badge">✓</div>
                <div className="pl-info">
                  <p className="pl-name">{p.name}</p>
                  <p className="pl-count">{p.track_count} tracks</p>
                </div>
              </div>
            )
          })}
        </div>

        <hr className="divider" />

        {/* ── Filtres ── */}
        <span className="studio-section-label">Filtres</span>

        <div style={{ display:'flex', flexWrap:'wrap', gap:'8px', marginBottom:'1.25rem' }}>
          {GENRE_OPTIONS.map(g => (
            <button key={g}
              className={`filter-chip${filterGenres.includes(g) ? ' active' : ''}`}
              onClick={() => toggleGenre(g)}>
              {g}
            </button>
          ))}
        </div>

        <div style={{ display:'flex', gap:'12px', flexWrap:'wrap', alignItems:'flex-end', marginBottom:'2rem' }}>
          {[
            { label:'Année min', val:yearMin,  set:setYearMin,  ph:'2010' },
            { label:'Année max', val:yearMax,  set:setYearMax,  ph:'2024' },
            { label:'Pop. min',  val:popMin,   set:setPopMin,   ph:'50'   },
          ].map(({ label, val, set, ph }) => (
            <div key={label} style={{ display:'flex', flexDirection:'column', gap:'5px' }}>
              <label style={{ fontSize:'10px', color:'#3d3b4a', letterSpacing:'.08em', textTransform:'uppercase' }}>
                {label}
              </label>
              <input
                type="number"
                className="studio-input"
                placeholder={ph}
                value={val}
                onChange={e => set(e.target.value)}
              />
            </div>
          ))}
          <button className="btn-apply" onClick={handleFilter} disabled={loading}>
            {loading ? 'Analyse...' : 'Appliquer →'}
          </button>
        </div>

        {/* ── Banners ── */}
        {error      && <p className="banner-error">{error}</p>}
        {exportUrl  && (
          <a href={exportUrl} target="_blank" rel="noreferrer" className="banner-success" style={{ display:'block', textDecoration:'none' }}>
            ✓ Playlist créée — Ouvrir sur Spotify ↗
          </a>
        )}

        {/* ── Résultats ── */}
        {tracks.length > 0 && (
          <>
            <div className="stats-row">
              <p className="stat-chip"><span>{stats?.total_after_filter}</span> tracks</p>
              <p className="stat-chip"><span>{stats?.playlists_merged}</span> playlists fusionnées</p>
              {stats?.total_before_filter > stats?.total_after_filter && (
                <p className="stat-chip"><span>{stats.total_before_filter - stats.total_after_filter}</span> filtrés</p>
              )}
              <button className="btn-export" style={{ marginLeft:'auto' }} onClick={() => setShowModal(true)}>
                Exporter →
              </button>
            </div>

            <div className="studio-table-wrap">
              <table className="studio-table">
                <thead>
                  <tr>
                    <th style={{ width:'28%' }}>Titre</th>
                    <th style={{ width:'22%' }}>Artiste</th>
                    <th style={{ width:'22%' }}>Album</th>
                    <th style={{ width:'10%' }}>Année</th>
                    <th style={{ width:'10%' }}>Pop.</th>
                    <th style={{ width:'8%'  }}>ISRC</th>
                  </tr>
                </thead>
                <tbody>
                  {tracks.map((t, i) => {
                    const { bg, color } = popColor(t.popularity)
                    return (
                      <tr key={t.spotify_id || i}>
                        <td>
                          {t.spotify_url
                            ? <a href={t.spotify_url} target="_blank" rel="noreferrer" className="track-link">{t.name}</a>
                            : t.name
                          }
                        </td>
                        <td>{t.artist}</td>
                        <td style={{ color:'#52505f' }}>{t.album || '—'}</td>
                        <td style={{ color:'#52505f' }}>{t.release_year || '—'}</td>
                        <td>
                          <span className="pop-badge" style={{ background:bg, color }}>
                            {t.popularity ?? '—'}
                          </span>
                        </td>
                        <td style={{ color:'#3d3b4a', fontSize:'11px', letterSpacing:'.03em' }}>
                          {t.isrc ? t.isrc.slice(0,8)+'…' : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {/* ── Modal export ── */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <p className="modal-title">Exporter la sélection</p>
            <p className="modal-sub">{tracks.length} tracks · Choisis le format de sortie</p>

            <button className="export-opt opt-spotify" onClick={handleExportSpotify} disabled={exporting}>
              <p className="opt-title">{exporting ? 'Sauvegarde en cours...' : 'Sauvegarder sur Spotify'}</p>
              <p className="opt-desc">Playlist privée · {tracks.length} tracks · public: false</p>
            </button>

            <button className="export-opt opt-csv" onClick={handleExportCsv}>
              <p className="opt-title">Exporter en CSV</p>
              <p className="opt-desc">Titre, Artiste, Album, ISRC — universel</p>
            </button>

            <button className="btn-cancel" onClick={() => setShowModal(false)}>Annuler</button>
          </div>
        </div>
      )}
    </>
  )
}
