import { LayoutDashboard, Search, ScanFace, Plane } from 'lucide-react'
const items = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'search', label: 'Student lookup', icon: Search },
  { id: 'live', label: 'Live detection', icon: ScanFace }
]
export function Logo() {
  return <div className="logo"><span className="logo-mark"><Plane size={18} /></span><span>Aero<b>ID</b></span></div>
}
export default function Sidebar({ page, setPage, online }) {
  return (
    <aside className="sidebar">
      <Logo />
      <nav>
        {items.map(({ id, label, icon: Icon }) => (
          <button key={id} className={page === id ? 'nav active' : 'nav'} onClick={() => setPage(id)}>
            <Icon size={18} /><span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="side-status"><i className={online ? 'dot on' : 'dot off'} />{online ? 'Backend connected' : 'Backend offline'}</div>
    </aside>
  )
}
