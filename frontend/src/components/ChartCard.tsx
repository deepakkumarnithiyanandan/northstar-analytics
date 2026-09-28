import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ChartPoint, Visualization } from '../types'

const COLORS = ['#1f6f59', '#e5a640', '#4675a8', '#d56b52', '#8067a3', '#8da447']
const money = (value: number) => `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`

function AxisTick({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) {
  return <text x={x} y={y} dy={4} fill="#82908a" fontSize={11} textAnchor="middle">{payload?.value}</text>
}

export function ChartCard({ title, eyebrow, data, kind = 'line', height = 260, valueFormat = 'currency' }: {
  title: string; eyebrow?: string; data: ChartPoint[]; kind?: 'line' | 'bar' | 'pie'; height?: number; valueFormat?: 'currency' | 'number'
}) {
  const formatValue = (value: number) => valueFormat === 'number' ? Number(value).toLocaleString() : money(Number(value))
  const formatAxis = (value: number) => valueFormat === 'number' ? String(value) : `${Math.round(Number(value) / 1000)}k`
  return (
    <section className="chart-card">
      <div className="chart-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div><span className="chart-period">All activity</span></div>
      {!data.length ? <div className="chart-empty">No data for these filters.</div> : (
        <div className="chart-body" style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            {kind === 'pie' ? (
              <PieChart><Pie data={data} dataKey="value" nameKey="label" innerRadius={62} outerRadius={94} paddingAngle={3} stroke="none">{data.map((item, index) => <Cell key={item.label} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip formatter={(value) => formatValue(Number(value))} /></PieChart>
            ) : kind === 'bar' ? (
              <BarChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}><CartesianGrid vertical={false} stroke="#e9ede8" /><XAxis dataKey="label" tick={<AxisTick />} axisLine={false} tickLine={false} interval={0} /><YAxis tickFormatter={formatAxis} tick={{ fill: '#82908a', fontSize: 11 }} axisLine={false} tickLine={false} width={42} /><Tooltip formatter={(value) => formatValue(Number(value))} cursor={{ fill: '#f1f4f0' }} /><Bar dataKey="value" fill="#1f6f59" radius={[4, 4, 0, 0]} maxBarSize={42} /></BarChart>
            ) : (
              <LineChart data={data} margin={{ top: 12, right: 8, bottom: 0, left: 0 }}><CartesianGrid vertical={false} stroke="#e9ede8" /><XAxis dataKey="label" tick={<AxisTick />} axisLine={false} tickLine={false} /><YAxis tickFormatter={formatAxis} tick={{ fill: '#82908a', fontSize: 11 }} axisLine={false} tickLine={false} width={42} /><Tooltip formatter={(value) => formatValue(Number(value))} /><Line type="monotone" dataKey="value" stroke="#1f6f59" strokeWidth={3} dot={{ r: 3, fill: '#fff', strokeWidth: 2 }} activeDot={{ r: 5 }} /></LineChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
      {kind === 'pie' && data.length > 0 && <div className="chart-legend">{data.map((item, index) => <span key={item.label}><i style={{ background: COLORS[index % COLORS.length] }} />{item.label}</span>)}</div>}
    </section>
  )
}

export function RecommendedChart({ visualization }: { visualization: Visualization }) {
  if (visualization.type === 'table' || visualization.type === 'histogram') {
    return <section className="recommended-table"><h3>{visualization.title}</h3>{visualization.data.map((row) => <div key={row.label}><span>{row.label}</span><strong>{money(row.value)}</strong></div>)}</section>
  }
  return <ChartCard title={visualization.title} eyebrow="RECOMMENDED VISUALIZATION" data={visualization.data} kind={visualization.type === 'pie' ? 'pie' : visualization.type === 'bar' ? 'bar' : 'line'} height={230} />
}