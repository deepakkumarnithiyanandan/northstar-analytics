import { ArrowDownRight, ArrowUpRight, CircleHelp, type LucideIcon } from 'lucide-react'

interface KpiCardProps {
  label: string
  value: string
  note: string
  icon: LucideIcon
  tone: string
  trend?: number | null
}

export function KpiCard({ label, value, note, icon: Icon, tone, trend }: KpiCardProps) {
  const positive = (trend ?? 0) >= 0
  return (
    <article className="kpi-card">
      <div className="kpi-topline"><span>{label}</span><span className={`kpi-icon ${tone}`}><Icon size={18} /></span></div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-note">
        {trend !== undefined && trend !== null ? <span className={`trend ${positive ? 'positive' : 'negative'}`}>{positive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}{Math.abs(trend).toFixed(1)}%</span> : <CircleHelp size={14} />}
        <span>{note}</span>
      </div>
    </article>
  )
}