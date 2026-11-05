import { useRef, useState } from 'react'
import { ScanFace, Upload, Loader2, UserX, WifiOff, AlertCircle, ImagePlus } from 'lucide-react'
import { recognizeFace, fetchStudent } from '../api'
import StudentCard from './StudentCard'

export default function FaceScan({ captures, selected, setSelected, addCapture }) {
  const [phase, setPhase] = useState('idle')   // idle | scanning | done | error
  const [res, setRes] = useState(null)
  const [dim, setDim] = useState(null)
  const file = useRef(null)

  function pick(c) { setSelected(c); setPhase('idle'); setRes(null) }
  function upload(e) {
    const f = e.target.files[0]
    if (f) pick({ id: crypto.randomUUID(), blob: f, url: URL.createObjectURL(f) })
    e.target.value = ''
  }

  async function identify() {
    setPhase('scanning'); setRes(null)
    const r = await recognizeFace(selected.blob)
    if (!r.ok) return fail(r.status === 'offline' ? 'offline' : r.status === 404 || r.status === 422 ? 'nomatch' : 'error', r)
    const adm = r.data.admission_number ?? r.data.admission_no
    const s = await fetchStudent(adm)
    if (!s.ok) return fail(s.status === 'offline' ? 'offline' : 'orphan', { adm })
    setRes({ ...r.data, student: s.data }); setPhase('done')
  }
  function fail(kind, extra) { setRes({ kind, ...extra }); setPhase('error') }

  const box = res?.bbox && dim ? {
    left: `${res.bbox[0] / dim.w * 100}%`, top: `${res.bbox[1] / dim.h * 100}%`,
    width: `${(res.bbox[2] - res.bbox[0]) / dim.w * 100}%`, height: `${(res.bbox[3] - res.bbox[1]) / dim.h * 100}%`
  } : null

  return (
    <div className="scan">
      <section className="viewer">
        <div className="screen square">
          {selected ? (
            <>
              <img src={selected.url} alt="Person to identify" onLoad={e => setDim({ w: e.target.naturalWidth, h: e.target.naturalHeight })} />
              {phase === 'scanning' && <i className="sweep" />}
              {phase === 'done' && box && <i className="facebox" style={box} />}
            </>
          ) : (
            <div className="nosig"><ImagePlus size={40} /><h3>No image selected</h3><p>Pick a frame captured from the drone, or upload a photo.</p></div>
          )}
          <i className="c tl" /><i className="c tr" /><i className="c bl" /><i className="c br" />
        </div>
        <div className="actions">
          <button className="btn big" disabled={!selected || phase === 'scanning'} onClick={identify}>
            {phase === 'scanning' ? <><Loader2 size={18} className="spin" />Scanning face</> : <><ScanFace size={18} />Identify person</>}
          </button>
          <button className="btn ghost" onClick={() => file.current.click()}><Upload size={16} />Upload photo</button>
          <input ref={file} type="file" accept="image/*" hidden onChange={upload} />
        </div>
        {captures.length > 0 && (
          <div className="strip">
            {captures.map(c => <button key={c.id} className={selected?.id === c.id ? 'on' : ''} onClick={() => pick(c)}><img src={c.url} alt="Captured frame" /></button>)}
          </div>
        )}
      </section>

      <section className="result">
        {phase === 'idle' && <Msg icon={ScanFace} title="Ready to scan" text="Select an image and choose Identify person. The backend will match the face and return the student's record." />}
        {phase === 'scanning' && <div className="card skeleton" aria-busy="true"><i /><i /><i /><i /></div>}
        {phase === 'done' && (
          <>
            <div className="match"><span>Match found</span><b>{Math.round((res.confidence ?? 0) * 100)}% confidence</b></div>
            <StudentCard data={res.student} />
          </>
        )}
        {phase === 'error' && res.kind === 'nomatch' && <Msg tone="warn" icon={UserX} title="No student matched" text={res.message || 'No registered face matches this image. Try a clearer, front-facing frame.'} />}
        {phase === 'error' && res.kind === 'orphan' && <Msg tone="warn" icon={UserX} title="Face matched, but no record found" text={`The backend matched admission number ${res.adm}, but that student has no record.`} />}
        {phase === 'error' && res.kind === 'offline' && <Msg tone="bad" icon={WifiOff} title="Backend unavailable" text="Could not reach the Flask server at 127.0.0.1:5000. Start it, make sure CORS is enabled, then try again." />}
        {phase === 'error' && res.kind === 'error' && <Msg tone="bad" icon={AlertCircle} title="Something went wrong" text={`The server returned status ${res.status}.`} />}
      </section>
    </div>
  )
}
function Msg({ icon: Icon, title, text, tone = '' }) {
  return <div className={`card msg ${tone}`} role="status"><Icon size={26} /><div><h3>{title}</h3><p>{text}</p></div></div>
}
