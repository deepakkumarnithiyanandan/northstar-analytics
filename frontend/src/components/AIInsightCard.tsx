import { Sparkles } from 'lucide-react'

export function AIInsightCard({ insights }: { insights: string[] }) {
  return (
    <section className="insight-card">
      <div className="insight-title"><span><Sparkles size={17} /></span><div><strong>AI Insights</strong><small>Patterns detected in this dataset</small></div><span className="generated-tag">GENERATED</span></div>
      {!insights.length ? <p className="insight-empty">Add more dates or records to surface useful patterns.</p> : <ul>{insights.map((insight) => <li key={insight}>{insight}</li>)}</ul>}
      <span className="insight-footnote">Computed from the filtered sales data</span>
    </section>
  )
}