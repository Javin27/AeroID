import { useState } from 'react'
import { Search, Loader2, UserX, WifiOff, AlertCircle, ScanSearch } from 'lucide-react'
import { fetchStudent, pick } from '../api'
import StudentCard from './StudentCard'

export default function StudentSearch({ onResult, compact }) {
  const [q, setQ] = useState('')
  const [state, setState] = useState({ type: 'idle' })

  async function submit(e) {
    e.preventDefault()
    const adm = q.trim()
    if (!adm) return setState({ type: 'empty' })
    setState({ type: 'loading' })
    const r = await fetchStudent(adm)
    if (r.ok) {
      setState({ type: 'success', data: r.data })
      onResult?.({ admission: adm, name: pick(r.data, 'name'), found: true })
    } else {
      setState({ type: r.status === 404 ? 'notfound' : r.status === 'offline' ? 'offline' : 'error', code: r.status, adm })
      onResult?.({ admission: adm, name: null, found: false })
    }
  }

  return (
    <section>
      <form className="searchbar" onSubmit={submit}>
        <Search size={18} />
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Enter admission number" aria-label="Admission number" />
        <button className="btn" disabled={state.type === 'loading'}>
          {state.type === 'loading' ? <Loader2 size={16} className="spin" /> : 'Find student'}
        </button>
      </form>
      {!compact && state.type === 'idle' && <Msg icon={ScanSearch} title="Look up a student" text="Enter an admission number to see their record." />}
      {state.type === 'empty' && <Msg tone="warn" icon={AlertCircle} title="Enter an admission number" text="The search box is empty." />}
      {state.type === 'loading' && <div className="card skeleton" aria-busy="true"><i /><i /><i /><i /></div>}
      {state.type === 'notfound' && <Msg tone="warn" icon={UserX} title="Student not found" text={`No student has admission number “${state.adm}”. Check the number and try again.`} />}
      {state.type === 'offline' && <Msg tone="bad" icon={WifiOff} title="Backend unavailable" text="Could not reach the Flask server at 127.0.0.1:5000. Start it, make sure CORS is enabled, then search again." />}
      {state.type === 'error' && <Msg tone="bad" icon={AlertCircle} title="Something went wrong" text={`The server returned status ${state.code}.`} />}
      {state.type === 'success' && <StudentCard data={state.data} />}
    </section>
  )
}
function Msg({ icon: Icon, title, text, tone = '' }) {
  return <div className={`card msg ${tone}`} role="status"><Icon size={26} /><div><h3>{title}</h3><p>{text}</p></div></div>
}
