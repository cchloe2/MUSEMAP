import { useState, useEffect } from 'react'
import { spotifyApi } from '../api/musemapApi'

export function useAuth() {
  const [user, setUser]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    spotifyApi.getMe()
      .then(r => setUser(r.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login  = () => { window.location.href = 'http://127.0.0.1:8000/auth/login' }
  const logout = () => {
    fetch('http://127.0.0.1:8000/auth/logout')
    sessionStorage.removeItem('musemap_token')
    setUser(null)
  }

  return { user, loading, login, logout }
}
