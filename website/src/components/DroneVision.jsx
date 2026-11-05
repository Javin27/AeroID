import { useEffect, useRef, useState } from 'react'
import { Camera, PlugZap, Webcam, ScanFace, ImageOff } from 'lucide-react'

export default function DroneVision({ captures, onCapture, onScan }) {
  const [url, setUrl] = useState(() => localStorage.getItem('aeroid.stream') || '')
  const [src, setSrc] = useState('')            // active stream URL
  const [mode, setMode] = useState('stream')    // 'stream' | 'webcam'
  const [err, setErr] = useState('')
  const [live, setLive] = useState(false)
  const media = useRef(null)

  useEffect(() => {
    if (mode !== 'webcam') return
    let stream
    navigator.mediaDevices?.getUserMedia({ video: true })
      .then(s => { stream = s; media.current.srcObject = s; setLive(true); setErr('') })
      .catch(() => setErr('Webcam access was blocked.'))
    return () => { stream?.getTracks().forEach(t => t.stop()); setLive(false) }
  }, [mode])

  function connect(e) {
    e.preventDefault()
    setErr(''); setLive(false)
    localStorage.setItem('aeroid.stream', url)
    setSrc(url.trim())
  }

  async function capture() {
    const el = media.current
    const w = el.videoWidth || el.naturalWidth, h = el.videoHeight || el.naturalHeight
    if (!w) return setErr('No frame to capture yet.')
    try {
      const c = document.createElement('canvas'); c.width = w; c.height = h
      c.getContext('2d').drawImage(el, 0, 0)
      const blob = await new Promise(r => c.toBlob(r, 'image/jpeg', 0.92))
      onCapture(blob); setErr('')
    } catch { setErr('The stream blocks frame capture. Enable CORS on the stream server, or upload an image in Face scan.') }
  }

  return (
    <div className="vision">
      <section className="viewer">
        <div className="hud">
          <span className={live ? 'rec on' : 'rec'}><i className="dot" />{live ? 'Live' : 'No signal'}</span>
          <div className="seg">
            <button className={mode === 'stream' ? 'on' : ''} onClick={() => setMode('stream')}><PlugZap size={14} />Drone</button>
            <button className={mode === 'webcam' ? 'on' : ''} onClick={() => setMode('webcam')}><Webcam size={14} />Webcam test</button>
          </div>
        </div>
        <div className="screen">
          {mode === 'webcam' && <video ref={media} autoPlay muted playsInline />}
          {mode === 'stream' && src && <img ref={media} src={src} crossOrigin="anonymous" alt="Drone feed"
            onLoad={() => { setLive(true); setErr('') }} onError={() => { setLive(false); setErr('Could not load the stream. Check the URL and that the drone is on.') }} />}
          {!live && <div className="nosig"><Camera size={40} /><h3>No video yet</h3><p>Enter your drone's stream URL below, or switch to Webcam test.</p></div>}
          <i className="c tl" /><i className="c tr" /><i className="c bl" /><i className="c br" />
        </div>
        {mode === 'stream' && (
          <form className="urlbar" onSubmit={connect}>
            <input value={url} onChange={e => setUrl(e.target.value)} placeholder="Stream URL, e.g. http://192.168.4.1:81/stream" aria-label="Stream URL" />
            <button className="btn">Connect</button>
          </form>
        )}
        {err && <p className="err">{err}</p>}
        <button className="btn big" onClick={capture} disabled={!live}><Camera size={18} />Capture frame</button>
      </section>

      <aside className="panel">
        <h3>Captured frames</h3>
        {captures.length === 0 && <p className="empty"><ImageOff size={18} />Captured frames appear here.</p>}
        <div className="thumbs">
          {captures.map(c => (
            <figure key={c.id}>
              <img src={c.url} alt="Captured frame" />
              <button className="btn sm" onClick={() => onScan(c)}><ScanFace size={14} />Scan</button>
            </figure>
          ))}
        </div>
      </aside>
    </div>
  )
}
