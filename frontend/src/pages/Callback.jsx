import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Callback() {
  const navigate = useNavigate()

  useEffect(() => {
    // Le token est dans l'URL si le back le retourne en param
    // Sinon le cookie httponly est déjà setté automatiquement
    const params = new URLSearchParams(window.location.search)
    const token  = params.get('access_token')
    if (token) sessionStorage.setItem('musemap_token', token)
    navigate('/generate', { replace: true })
  }, [navigate])

  return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100vh' }}>
      <p style={{ fontFamily:'var(--font-display)', fontSize:'1.2rem' }}>
        Connexion en cours...
      </p>
    </div>
  )
}
