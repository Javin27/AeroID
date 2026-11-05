import { useEffect, useState } from 'react'
import { Radar, ScanFace } from 'lucide-react'
import { fetchSystem } from './api'
import { Logo } from './components/Logo'
import DroneVision from './components/DroneVision'
import FaceScan from './components/FaceScan'

export default function App() {
  const [tab, setTab] = useState('vision')
  const [online, setOnline] = useState(false)
  const [captures, setCaptures] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    const check = () => fetchSystem().then(s => setOnline(s.online))
    check()
    const t = setInterval(check, 10000)
    return () => clearInterval(t)
  }, [])

  const addCapture = blob => {
    const c = { id: crypto.randomUUID(), blob, url: URL.createObjectURL(blob), at: Date.now() }
    setCaptures(l => [c, ...l].slice(0, 12))
    return c
  }
  const scan = c => { setSelected(c); setTab('scan') }

  return (
    <div className="shell">
      <header className="bar">
        <Logo />
        <div className="tabs" role="tablist">
          <button role="tab" aria-selected={tab === 'vision'} onClick={() => setTab('vision')}><Radar size={17} />Drone vision</button>
          <button role="tab" aria-selected={tab === 'scan'} onClick={() => setTab('scan')}><ScanFace size={17} />Face scan</button>
        </div>
        <span className={online ? 'chip on' : 'chip off'}><i className="dot" />{online ? 'Backend connected' : 'Backend offline'}</span>
      </header>
      <main>
        {tab === 'vision'
          ? <DroneVision captures={captures} onCapture={addCapture} onScan={scan} />
          : <FaceScan captures={captures} selected={selected} setSelected={setSelected} addCapture={addCapture} />}
      </main>
    </div>
  )
}
