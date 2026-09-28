import { BarChart3, Database, LayoutDashboard, MessageSquareText, Upload, type LucideIcon } from 'lucide-react'
import type { ViewName } from '../types'

const navigation: { id: ViewName; label: string; icon: LucideIcon }[] = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'assistant', label: 'Ask Northstar', icon: MessageSquareText },
  { id: 'data', label: 'Data explorer', icon: Database },
  { id: 'upload', label: 'Import data', icon: Upload },
]

export function Sidebar({ active, onChange }: { active: ViewName; onChange: (view: ViewName) => void }) {
  return (
    <aside className="sidebar">
      <div className="brand-lockup">
        <div className="brand-mark"><BarChart3 size={19} strokeWidth={2.3} /></div>
        <div><strong>northstar</strong><span>ANALYTICS STUDIO</span></div>
      </div>
      <div className="workspace-label">WORKSPACE</div>
      <nav className="side-nav" aria-label="Main navigation">
        {navigation.map(({ id, label, icon: Icon }) => (
          <button className={`nav-item ${active === id ? 'active' : ''}`} key={id} onClick={() => onChange(id)}>
            <Icon size={18} strokeWidth={1.9} /><span>{label}</span>
            {id === 'assistant' && <span className="nav-spark">AI</span>}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="sidebar-rule" />
        <div className="profile-chip"><div className="profile-avatar">NS</div><div><strong>Analyst workspace</strong><span>Local environment</span></div></div>
      </div>
    </aside>
  )
}