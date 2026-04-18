import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  withCredentials: true,   // envoie les cookies httponly automatiquement
})

// ── Intercepteur : ajoute le token Bearer si présent en mémoire ──
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('musemap_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const spotifyApi = {
  getMe:       ()           => api.get('/spotify/me'),
  getPlaylists: (limit=20)  => api.get(`/spotify/playlists?limit=${limit}`),
}

export const playlistApi = {
  generate: (body)                    => api.post('/playlist/generate', body),
  save:     (body, name='MuseMap Playlist') =>
    api.post(`/playlist/save?playlist_name=${encodeURIComponent(name)}`, body),
}

export default api
