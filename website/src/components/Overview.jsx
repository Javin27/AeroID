import { Users, Activity, Server, History, CheckCircle2, XCircle } from 'lucide-react'
import StudentSearch from './StudentSearch'
export default function Overview({ system, activity, onResult }) {
  const { online, total } = system
  return (
    <>
      <div className="stats">
        <div className="card stat"><Users /><div><small>Registered students</small><strong>{total ?? '—'}</strong></div></div>
        <div className="card stat"><Activity /><div><small>Lookups this session</small><strong>{activity.length}</strong></div></div>
        <div className="card stat"><Server /><div><small>System status</small><strong className={online ? 'ok' : 'bad'}>{online ? 'Online' : 'Offline'}</strong></div></div>
      </div>
      <div className="grid2">
        <div><h3 className="h">Quick search</h3><StudentSearch compact onResult={onResult} /></div>
        <div>
          <h3 className="h">Recent identification activity</h3>
          <div className="card list">
            {activity.length === 0 && <p className="muted"><History size={16} /> No lookups yet. Search for a student to start the log.</p>}
            {activity.map(a => (
              <div className="row" key={a.id}>
                {a.found ? <CheckCircle2 className="ok" size={18} /> : <XCircle className="bad" size={18} />}
                <div><b>{a.found ? a.name : 'No match'}</b><small>Admission {a.admission}</small></div>
                <time>{new Date(a.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
