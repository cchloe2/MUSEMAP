const COLORS = ['coral','purple','teal','pink','amber','blue']

export default function TrackCard({ track, index }) {
  const color = COLORS[index % COLORS.length]
  return (
    <div style={{
      display:'flex', alignItems:'center', gap:'12px',
      background:'var(--surface)', border:'0.5px solid var(--border)',
      borderRadius:'var(--radius-md)', padding:'12px 14px',
      marginBottom:'8px', transition:'transform 0.1s',
    }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateX(4px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'translateX(0)'}
    >
      {track.image_url ? (
        <img src={track.image_url} alt="" style={{ width:'44px', height:'44px', borderRadius:'6px', objectFit:'cover', flexShrink:0 }} />
      ) : (
        <div style={{ width:'44px', height:'44px', borderRadius:'6px', flexShrink:0, background:`var(--${color}-bg)`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:'20px' }}>
          🎵
        </div>
      )}
      <div style={{ flex:1, minWidth:0 }}>
        <p style={{ fontSize:'14px', fontWeight:500, color:'var(--text)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>
          {track.name}
        </p>
        <p style={{ fontSize:'12px', color:'var(--text-muted)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>
          {track.artist}
        </p>
      </div>
      {track.popularity != null && (
        <span style={{ fontSize:'11px', fontWeight:500, padding:'3px 8px', borderRadius:'999px', background:`var(--${color}-bg)`, color:`var(--${color})`, flexShrink:0 }}>
          {track.popularity}
        </span>
      )}
      {track.spotify_url && (
        <a href={track.spotify_url} target="_blank" rel="noreferrer" style={{ color:'var(--text-hint)', fontSize:'16px', flexShrink:0 }}>↗</a>
      )}
    </div>
  )
}
