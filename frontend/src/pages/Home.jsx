import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { useEffect } from 'react'

export default function Home() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && user) navigate('/generate')
  }, [user, loading, navigate])

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg)', padding: '2rem', textAlign: 'center'
    }}>
      <h1 style={{
        fontFamily: 'var(--font-display)', fontWeight: 800,
        fontSize: 'clamp(3rem, 8vw, 6rem)', lineHeight: 1.05,
        background: 'var(--gradient)',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        marginBottom: '1rem'
      }}>
        MuseMap
      </h1>

      <p style={{
        fontSize: '1.1rem', color: 'var(--text-muted)',
        maxWidth: '400px', lineHeight: 1.7, marginBottom: '2.5rem'
      }}>
        Turn your mood into the perfect playlist.<br/>
        Describe your moment, we find the music.
      </p>

      <button onClick={login} style={{
        padding: '14px 36px',
        borderRadius: 'var(--radius-pill)',
        border: 'none',
        background: 'var(--gradient)',
        color: 'white',
        fontFamily: 'var(--font-display)',
        fontWeight: 700, fontSize: '1rem',
        letterSpacing: '0.03em',
        transition: 'opacity 0.15s, transform 0.1s',
      }}
        onMouseEnter={e => e.target.style.opacity = '0.88'}
        onMouseLeave={e => e.target.style.opacity = '1'}
      >
        Connect with Spotify →
      </button>

      <p style={{ marginTop: '1rem', fontSize: '12px', color: 'var(--text-hint)' }}>
        Requires a Spotify Premium account
      </p>
    </div>
  )
}
