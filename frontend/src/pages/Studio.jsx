import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { spotifyApi } from '../api/musemapApi'
import api from '../api/musemapApi'

const GENRE_OPTIONS = ['Jazz','Soul','Hip-Hop','Electronic','Rock','R&B','Indie','Classical','Pop','Blues']

export default function Studio() {
  const { user } = useAuth()

  const [playlists,       setPlaylists]       = useState([])
  const [selectedPids,    setSelectedPids]    = useState([])
  const [tracks,          setTracks]          = useState([])
  const [stats,           setStats]           = useState(null)
  const [loading,         setLoading]         = useState(false)
  const [showModal,       setShowModal]       = useState(false)
  const [exporting,       setExporting]       = useState(false)
  const [exportSuccess,   setExportSuccess]   = useState('')
  const [error,           setError]           = useState('')

  // Filtres
  const [filterGenres,    setFilterGenres]    = useState([])
  const [filterYearMin,   setFilterYearMin]   = useState('')
  const [filterYearMax,   setFilterYearMax]   = useState('')
  const [filterPopMin,    setFilterPopMin]    = useState('')

  useEffect(() => {
    spotifyApi.getPlaylists(50)
      .then(r => setPlaylists(r.data))
      .catch(() => setError('Impossible de charger les playlists.'))
  }, [])

  const togglePlaylist = (id) =>
    setSelectedPids(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id])

  const toggleGenre = (g) =>
    setFilterGenres(p => p.includes(g) ? p.filter(x => x !== g) : [...p, g])

  const handleFilter = async () => {
    if (!selectedPids.length) { setError('Sélectionne au moins une playlist.'); return }
    setError(''); setLoading(true); setTracks([]); setStats(null)
    try {
      const { data } = await api.post('/studio/filter', {
        playlist_ids:   selectedPids,
        genres:         filterGenres,
        year_min:       filterYearMin ? parseInt(filterYearMin) : null,
        year_max:       filterYearMax ? parseInt(filterYearMax) : null,
        popularity_min: filterPopMin  ? parseInt(filterPopMin)  : null,
      })
      setTracks(data.tracks || [])
      setStats(data.stats)
    } catch(e) {
      setError(e.response?.data?.detail || 'Erreur lors du filtrage.')
    } finally { setLoading(false) }
  }

  // ── Export Spotify ──
  const handleExportSpotify = async () => {
    setExporting(true); setError('')
    const name = `MuseMap Studio · ${new Date().toLocaleDateString('fr-FR')}`
    try {
      const { data } = await api.post('/studio/export/spotify', {
        track_ids: tracks.map(t => t.spotify_id),
        playlist_name: name,
        public: false,
      })
      setExportSuccess(data.playlist_url)
      setShowModal(false)
    } catch(e) {
      setError(e.response?.data?.detail || 'Export Spotify échoué.')
    } finally { setExporting(false) }
  }

  // ── Export CSV — côté client, zéro dépendance ──
  const handleExportCsv = () => {
    const header = ['Titre','Artiste','Album','Année','Popularité','ISRC','URL Spotify']
    const rows = tracks.map(t => [
      `"${(t.name   || '').replace(/"/g,'""')}"`,
      `"${(t.artist || '').replace(/"/g,'""')}"`,
      `"${(t.album  || '').replace(/"/g,'""')}"`,
      t.release_year || '',
      t.popularity   || '',
      t.isrc         || '',
      t.spotify_url  || '',
    ])
    const csv = [header, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = 'musemap_export.csv'; a.click()
    URL.revokeObjectURL(url)
    setShowModal(false)
  }

  // ── Styles inline réutilisables ──
  const card = {
    background:'var(--surface)', border:'0.5px solid var(--border)',
    borderRadius:'var(--radius-md)', padding:'12px',
  }
  const label = {
    fontSize:'11px', fontWeight:500, letterSpacing:'.08em',
    textTransform:'uppercase', color:'var(--text-hint)', marginBottom:'8px',
    display:'block',
  }

  return (
    <div style={{ maxWidth:'800px', margin:'0 auto', padding:'2rem 1.5rem', fontFamily:'var(--font-body)' }}>

      {/* ── Header ── */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'2rem' }}>
        <h1 style={{ fontFamily:'var(--font-display)', fontWeight:800, fontSize:'1.8rem', background:'var(--gradient)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}>
          MuseMap Studio
        </h1>
        {user && <span style={{ fontSize:'13px', color:'var(--text-muted)' }}>{user.display_name}</span>}
      </div>

      {/* ── Sélection playlists ── */}
      <span style={label}>Tes playlists</span>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(150px,1fr))', gap:'8px', marginBottom:'1.5rem' }}>
        {playlists.map(p => {
          const sel = selectedPids.includes(p.spotify_id)
          return (
            <button key={p.spotify_id} onClick={() => togglePlaylist(p.spotify_id)} style={{
              ...card,
              border: sel ? '1.5px solid var(--purple)' : '0.5px solid var(--border)',
              background: sel ? 'var(--purple-bg)' : 'var(--surface)',
              textAlign:'left', cursor:'pointer', transition:'all .15s',
            }}>
              <p style={{ fontSize:'13px', fontWeight:500, color: sel ? 'var(--purple)' : 'var(--text)', marginBottom:'2px', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>
                {p.name}
              </p>
              <p style={{ fontSize:'11px', color:'var(--text-hint)' }}>{p.track_count} tracks</p>
            </button>
          )
        })}
      </div>

      {/* ── Filtres ── */}
      <span style={label}>Filtres</span>
      <div style={{ display:'flex', flexWrap:'wrap', gap:'8px', marginBottom:'1rem' }}>
        {GENRE_OPTIONS.map(g => {
          const on = filterGenres.includes(g)
          return (
            <button key={g} onClick={() => toggleGenre(g)} style={{
              padding:'6px 14px', borderRadius:'999px', fontSize:'12px',
              border: on ? '1.5px solid var(--coral)' : '1.5px solid var(--border)',
              background: on ? 'var(--coral-bg)' : 'transparent',
              color: on ? 'var(--coral)' : 'var(--text-muted)',
              cursor:'pointer', transition:'all .15s',
            }}>
              {g}
            </button>
          )
        })}
      </div>
      <div style={{ display:'flex', gap:'12px', flexWrap:'wrap', marginBottom:'1.5rem', alignItems:'center' }}>
        {[
          { label:'Année min', value:filterYearMin, set:setFilterYearMin, ph:'2010' },
          { label:'Année max', value:filterYearMax, set:setFilterYearMax, ph:'2024' },
          { label:'Popularité min', value:filterPopMin, set:setFilterPopMin, ph:'50' },
        ].map(({ label:l, value, set, ph }) => (
          <div key={l} style={{ display:'flex', flexDirection:'column', gap:'4px' }}>
            <label style={{ fontSize:'11px', color:'var(--text-hint)' }}>{l}</label>
            <input
              type="number" placeholder={ph} value={value}
              onChange={e => set(e.target.value)}
              style={{ width:'100px', padding:'7px 10px', borderRadius:'var(--radius-sm)', border:'1.5px solid var(--border)', fontSize:'13px', background:'var(--surface)', color:'var(--text)' }}
            />
          </div>
        ))}
        <button onClick={handleFilter} disabled={loading} style={{
          marginTop:'18px', padding:'9px 24px', borderRadius:'999px', border:'none',
          background: loading ? '#ccc' : 'var(--gradient)', color:'white',
          fontFamily:'var(--font-display)', fontWeight:700, fontSize:'13px', cursor:'pointer',
        }}>
          {loading ? 'Filtrage...' : 'Appliquer →'}
        </button>
      </div>

      {/* ── Erreur ── */}
      {error && <p style={{ fontSize:'13px', color:'#A32D2D', background:'#FCEBEB', padding:'10px 14px', borderRadius:'var(--radius-sm)', marginBottom:'1rem' }}>{error}</p>}

      {/* ── Résultats ── */}
      {tracks.length > 0 && (
        <>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1rem' }}>
            <p style={{ fontSize:'13px', color:'var(--text-muted)' }}>
              {stats?.total_after_filter} tracks · {stats?.playlists_merged} playlists fusionnées
            </p>
            <button onClick={() => setShowModal(true)} style={{
              padding:'9px 20px', borderRadius:'var(--radius-md)',
              border:'1.5px solid var(--teal)', background:'var(--teal-bg)',
              color:'var(--teal)', fontFamily:'var(--font-display)', fontWeight:700, fontSize:'13px', cursor:'pointer',
            }}>
              Exporter →
            </button>
          </div>

          {/* ── Tableau ── */}
          <div style={{ border:'0.5px solid var(--border)', borderRadius:'var(--radius-md)', overflow:'auto', marginBottom:'1rem' }}>
            <table style={{ width:'100%', borderCollapse:'collapse', tableLayout:'fixed' }}>
              <thead>
                <tr style={{ background:'rgba(0,0,0,0.03)' }}>
                  {['Titre','Artiste','Album','Année','Pop.'].map((h,i) => (
                    <th key={h} style={{ padding:'10px 12px', textAlign:'left', fontSize:'11px', fontWeight:500, letterSpacing:'.06em', textTransform:'uppercase', color:'var(--text-hint)', borderBottom:'0.5px solid var(--border)', width: i===0?'28%':i===1?'22%':i===2?'22%':'14%' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tracks.map((t, i) => (
                  <tr key={t.spotify_id} style={{ background: i%2===0 ? 'transparent' : 'rgba(0,0,0,0.015)' }}>
                    <td style={{ padding:'10px 12px', fontSize:'13px', color:'var(--text)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>
                      <a href={t.spotify_url} target="_blank" rel="noreferrer" style={{ color:'var(--purple)', textDecoration:'none' }}>
                        {t.name}
                      </a>
                    </td>
                    <td style={{ padding:'10px 12px', fontSize:'13px', color:'var(--text-muted)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{t.artist}</td>
                    <td style={{ padding:'10px 12px', fontSize:'13px', color:'var(--text-muted)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{t.album || '—'}</td>
                    <td style={{ padding:'10px 12px', fontSize:'13px', color:'var(--text-muted)' }}>{t.release_year || '—'}</td>
                    <td style={{ padding:'10px 12px' }}>
                      <span style={{
                        fontSize:'11px', fontWeight:500, padding:'2px 8px', borderRadius:'999px',
                        background: (t.popularity||0)>70 ? 'var(--teal-bg)' : (t.popularity||0)>40 ? 'var(--amber-bg)' : 'var(--coral-bg)',
                        color:      (t.popularity||0)>70 ? 'var(--teal)'    : (t.popularity||0)>40 ? 'var(--amber)'    : 'var(--coral)',
                      }}>
                        {t.popularity ?? '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ── Lien Spotify post-export ── */}
          {exportSuccess && (
            <a href={exportSuccess} target="_blank" rel="noreferrer" style={{
              display:'block', textAlign:'center', padding:'12px',
              borderRadius:'var(--radius-md)', border:'1.5px solid var(--teal)',
              background:'var(--teal-bg)', color:'var(--teal)',
              fontFamily:'var(--font-display)', fontWeight:700, fontSize:'14px', marginBottom:'1rem',
            }}>
              Ouvrir sur Spotify ↗
            </a>
          )}
        </>
      )}

      {/* ── Modale export ── */}
      {showModal && (
        <div style={{ position:'absolute', inset:0, background:'rgba(0,0,0,0.4)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:100, borderRadius:'var(--radius-lg)' }}
          onClick={() => setShowModal(false)}>
          <div onClick={e => e.stopPropagation()} style={{
            background:'var(--surface)', borderRadius:'var(--radius-lg)',
            padding:'1.5rem', width:'100%', maxWidth:'360px',
            border:'0.5px solid var(--border)', margin:'1rem',
          }}>
            <p style={{ fontFamily:'var(--font-display)', fontWeight:700, fontSize:'16px', marginBottom:'4px', color:'var(--text)' }}>
              Exporter la sélection
            </p>
            <p style={{ fontSize:'13px', color:'var(--text-muted)', marginBottom:'1.25rem' }}>
              {tracks.length} tracks · Choisis le format
            </p>

            {/* Option 1 — Spotify */}
            <button onClick={handleExportSpotify} disabled={exporting} style={{
              width:'100%', padding:'14px', marginBottom:'8px',
              borderRadius:'var(--radius-md)', border:'1.5px solid var(--teal)',
              background:'var(--teal-bg)', cursor:'pointer', textAlign:'left',
              opacity: exporting ? 0.6 : 1,
            }}>
              <p style={{ fontSize:'14px', fontWeight:500, color:'var(--teal)', marginBottom:'2px' }}>
                {exporting ? 'Sauvegarde...' : 'Sauvegarder sur Spotify'}
              </p>
              <p style={{ fontSize:'12px', color:'var(--teal)' }}>Playlist privée · {tracks.length} tracks</p>
            </button>

            {/* Option 2 — CSV */}
            <button onClick={handleExportCsv} style={{
              width:'100%', padding:'14px',
              borderRadius:'var(--radius-md)', border:'1.5px solid var(--blue)',
              background:'var(--blue-bg)', cursor:'pointer', textAlign:'left',
            }}>
              <p style={{ fontSize:'14px', fontWeight:500, color:'var(--blue)', marginBottom:'2px' }}>Exporter en CSV</p>
              <p style={{ fontSize:'12px', color:'var(--blue)' }}>Titre, Artiste, Album, ISRC · Universel</p>
            </button>

            <button onClick={() => setShowModal(false)} style={{
              width:'100%', marginTop:'12px', padding:'10px',
              borderRadius:'var(--radius-md)', border:'1.5px solid var(--border)',
              background:'transparent', color:'var(--text-muted)', cursor:'pointer', fontSize:'13px',
            }}>
              Annuler
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
