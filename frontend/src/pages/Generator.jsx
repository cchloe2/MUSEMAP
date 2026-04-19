import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { playlistApi } from '../api/musemapApi'
import TrackCard from '../components/TrackCard'

const GENRES = [
  { label: 'Jazz',      color: 'coral'  },
  { label: 'Soul',      color: 'purple' },
  { label: 'Hip-Hop',   color: 'blue'   },
  { label: 'Electronic',color: 'teal'   },
  { label: 'Rock',      color: 'amber'  },
  { label: 'R&B',       color: 'pink'   },
  { label: 'Indie',     color: 'purple' },
  { label: 'Classical', color: 'blue'   },
  { label: 'Funk',      color: 'coral'  },
  { label: 'Pop',       color: 'pink'   },
  { label: 'Blues',     color: 'teal'   },
  { label: 'Reggae',    color: 'amber'  },
]

const MOODS = [
  { key: 'relax',     label: 'Relax',     emoji: '🌙' },
  { key: 'hype',      label: 'Hype',      emoji: '⚡' },
  { key: 'focus',     label: 'Focus',     emoji: '🎯' },
  { key: 'happy',     label: 'Happy',     emoji: '☀️' },
  { key: 'melancholy',label: 'Melancholy',emoji: '🌧️' },
  { key: 'romantic',  label: 'Romantic',  emoji: '💫' },
]

export default function Generator() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [selectedGenres, setSelectedGenres] = useState([])
  const [selectedMood,   setSelectedMood]   = useState('')
  const [prompt,         setPrompt]         = useState('')
  const [trackCount,     setTrackCount]     = useState(20)

  const [tracks,         setTracks]         = useState([])
  const [interpretation, setInterpretation] = useState(null)
  const [loading,        setLoading]        = useState(false)
  const [saving,         setSaving]         = useState(false)
  const [error,          setError]          = useState('')
  const [savedUrl,       setSavedUrl]       = useState('')

  const toggleGenre = (label) => {
    setSelectedGenres(prev =>
      prev.includes(label) ? prev.filter(g => g !== label) : [...prev, label]
    )
  }

  const handleGenerate = async () => {
    if (!selectedGenres.length && !prompt.trim()) {
      setError('Sélectionne au moins un genre ou décris ton moment.')
      return
    }
    setError(''); setTracks([]); setSavedUrl(''); setLoading(true)
    try {
      const { data } = await playlistApi.generate({
        prompt:      prompt || 'good music',
        genres:      selectedGenres.map(g => g.toLowerCase()),
        mood:        selectedMood,
        track_count: trackCount,
      })
      setTracks(data.tracks || [])
      setInterpretation(data.interpretation)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erreur lors de la génération.')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true); setError('')
    const name = prompt.trim()
      ? `MuseMap · ${prompt.slice(0, 30)}`
      : `MuseMap · ${selectedGenres.join(', ')}`
    try {
      const { data } = await playlistApi.save({
        prompt:      prompt || 'good music',
        genres:      selectedGenres.map(g => g.toLowerCase()),
        mood:        selectedMood,
        track_count: trackCount,
      }, name)
      setSavedUrl(data.playlist_url)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erreur lors de la sauvegarde.')
    } finally {
      setSaving(false)
    }
  }

  if (!user) {
    return (
      <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100vh' }}>
        <button onClick={() => navigate('/')} style={{
          padding:'12px 28px', borderRadius:'var(--radius-pill)',
          border:'none', background:'var(--gradient)', color:'white',
          fontFamily:'var(--font-display)', fontWeight:700
        }}>
          Se connecter
        </button>
      </div>
    )
  }

  return (
    <div style={{ maxWidth:'680px', margin:'0 auto', padding:'2rem 1.5rem' }}>

      {/* ── Header ── */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'2rem' }}>
        <h1 style={{
          fontFamily:'var(--font-display)', fontWeight:800, fontSize:'1.8rem',
          background:'var(--gradient)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent'
        }}>MuseMap</h1>
        <div style={{ display:'flex', alignItems:'center', gap:'12px' }}>
          <span style={{ fontSize:'13px', color:'var(--text-muted)' }}>
            {user.display_name}
          </span>
          <button onClick={() => navigate('/studio')} style={{
            padding:'6px 14px', borderRadius:'var(--radius-pill)',
            border:'1px solid var(--border)', background:'transparent',
            fontSize:'12px', color:'var(--text-muted)'
          }}>
            Studio
          </button>
          <button onClick={logout} style={{
            padding:'6px 14px', borderRadius:'var(--radius-pill)',
            border:'1px solid var(--border)', background:'transparent',
            fontSize:'12px', color:'var(--text-muted)'
          }}>
            Logout
          </button>
        </div>
      </div>

      {/* ── Genres ── */}
      <p style={{ fontSize:'11px', fontWeight:500, letterSpacing:'0.08em', textTransform:'uppercase', color:'var(--text-hint)', marginBottom:'0.6rem' }}>
        Genres
      </p>
      <div style={{ display:'flex', flexWrap:'wrap', gap:'8px', marginBottom:'1.5rem' }}>
        {GENRES.map(({ label, color }) => {
          const active = selectedGenres.includes(label)
          return (
            <button key={label} onClick={() => toggleGenre(label)} style={{
              padding:'7px 16px', borderRadius:'var(--radius-pill)',
              border: active ? `1.5px solid var(--${color})` : '1.5px solid var(--border)',
              background: active ? `var(--${color}-bg)` : 'transparent',
              color: active ? `var(--${color})` : 'var(--text-muted)',
              fontSize:'13px', fontWeight: active ? 500 : 400,
              transition:'all 0.15s',
            }}>
              {label}
            </button>
          )
        })}
      </div>

      {/* ── Mood ── */}
      <p style={{ fontSize:'11px', fontWeight:500, letterSpacing:'0.08em', textTransform:'uppercase', color:'var(--text-hint)', marginBottom:'0.6rem' }}>
        Mood
      </p>
      <div style={{ display:'flex', gap:'8px', flexWrap:'wrap', marginBottom:'1.5rem' }}>
        {MOODS.map(({ key, label, emoji }) => (
          <button key={key} onClick={() => setSelectedMood(key === selectedMood ? '' : key)} style={{
            display:'flex', flexDirection:'column', alignItems:'center', gap:'4px',
            padding:'10px 18px', borderRadius:'var(--radius-md)',
            border: selectedMood === key ? `1.5px solid var(--purple)` : '1.5px solid var(--border)',
            background: selectedMood === key ? 'var(--purple-bg)' : 'transparent',
            color: selectedMood === key ? 'var(--purple)' : 'var(--text-muted)',
            fontSize:'12px', minWidth:'70px', transition:'all 0.15s',
          }}>
            <span style={{ fontSize:'20px' }}>{emoji}</span>
            {label}
          </button>
        ))}
      </div>

      {/* ── Prompt ── */}
      <p style={{ fontSize:'11px', fontWeight:500, letterSpacing:'0.08em', textTransform:'uppercase', color:'var(--text-hint)', marginBottom:'0.6rem' }}>
        Décris ton moment
      </p>
      <textarea
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        placeholder="Ex : Soirée cosy à Paris sous la pluie, un verre de vin, lumières tamisées..."
        rows={3}
        style={{
          width:'100%', padding:'14px 16px',
          borderRadius:'var(--radius-md)',
          border:'1.5px solid var(--border)',
          background:'var(--surface)', color:'var(--text)',
          fontSize:'14px', lineHeight:1.6, resize:'none', outline:'none',
          marginBottom:'0.75rem', transition:'border-color 0.15s',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--purple)'}
        onBlur={e  => e.target.style.borderColor = 'var(--border)'}
      />

      {/* ── Track count ── */}
      <div style={{ display:'flex', alignItems:'center', gap:'12px', marginBottom:'1.5rem' }}>
        <span style={{ fontSize:'13px', color:'var(--text-muted)', whiteSpace:'nowrap' }}>
          Nombre de titres
        </span>
        {[10, 15, 20, 30].map(n => (
          <button key={n} onClick={() => setTrackCount(n)} style={{
            padding:'5px 12px', borderRadius:'var(--radius-pill)',
            border: trackCount === n ? `1.5px solid var(--coral)` : '1.5px solid var(--border)',
            background: trackCount === n ? 'var(--coral-bg)' : 'transparent',
            color: trackCount === n ? 'var(--coral)' : 'var(--text-muted)',
            fontSize:'13px', transition:'all 0.15s',
          }}>
            {n}
          </button>
        ))}
      </div>

      {/* ── Error ── */}
      {error && (
        <p style={{ fontSize:'13px', color:'#A32D2D', background:'#FCEBEB', padding:'10px 14px', borderRadius:'var(--radius-sm)', marginBottom:'1rem' }}>
          {error}
        </p>
      )}

      {/* ── Generate button ── */}
      <button onClick={handleGenerate} disabled={loading} style={{
        width:'100%', padding:'14px',
        borderRadius:'var(--radius-md)', border:'none',
        background: loading ? '#ccc' : 'var(--gradient)',
        color:'white', fontFamily:'var(--font-display)',
        fontWeight:700, fontSize:'1rem', letterSpacing:'0.03em',
        transition:'opacity 0.15s, transform 0.1s',
        marginBottom:'2rem',
      }}>
        {loading ? 'Generating...' : 'Generate my playlist →'}
      </button>

      {/* ── Results ── */}
      {tracks.length > 0 && (
        <>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1rem' }}>
            <p style={{ fontSize:'11px', fontWeight:500, letterSpacing:'0.08em', textTransform:'uppercase', color:'var(--text-hint)' }}>
              {tracks.length} tracks · {interpretation?.energy || ''} energy
            </p>
            {interpretation?.provider_used && (
              <span style={{ fontSize:'11px', color:'var(--text-hint)' }}>
                via {interpretation.provider_used}
              </span>
            )}
          </div>

          {tracks.map((track, i) => (
            <TrackCard key={track.spotify_id || i} track={track} index={i} />
          ))}

          {/* ── Save button ── */}
          {savedUrl ? (
            <a href={savedUrl} target="_blank" rel="noreferrer" style={{
              display:'block', width:'100%', marginTop:'1.5rem', padding:'13px',
              borderRadius:'var(--radius-md)', border:'1.5px solid var(--teal)',
              background:'var(--teal-bg)', color:'var(--teal)',
              fontFamily:'var(--font-display)', fontWeight:700,
              fontSize:'0.95rem', textAlign:'center',
            }}>
              Open in Spotify ↗
            </a>
          ) : (
            <button onClick={handleSave} disabled={saving} style={{
              width:'100%', marginTop:'1.5rem', padding:'13px',
              borderRadius:'var(--radius-md)',
              border:`1.5px solid var(--teal)`,
              background:'var(--teal-bg)', color:'var(--teal)',
              fontFamily:'var(--font-display)', fontWeight:700,
              fontSize:'0.95rem', transition:'all 0.15s',
            }}>
              {saving ? 'Saving...' : 'Save to Spotify →'}
            </button>
          )}
        </>
      )}
    </div>
  )
}
