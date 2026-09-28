import { FormEvent, useState } from 'react'
import { ArrowUp, Bot, LoaderCircle, Sparkles } from 'lucide-react'
import { ApiError, askQuestion } from '../api'
import type { AskResult } from '../types'
import { RecommendedChart } from './ChartCard'

const suggestions = ['Top 5 products by revenue', 'Show monthly revenue', 'Which region leads revenue?']

export function AIChat({ datasetId }: { datasetId: number | null }) {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState<AskResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!question.trim() || busy) return
    setBusy(true)
    setError('')
    try {
      setResult(await askQuestion(question.trim(), datasetId))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Could not answer that question. Try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="assistant-layout">
      <section className="assistant-intro"><div className="assistant-glyph"><Sparkles size={20} /></div><span className="eyebrow">NORTHSTAR INTELLIGENCE</span><h2>Ask a question.<br /><em>Find the signal.</em></h2><p>Explore this dataset in plain language. Answers are grounded in your sales data and paired with a recommended chart.</p></section>
      <div className="assistant-workspace">
        <div className="chat-prompt"><Bot size={17} /><span>What would you like to know?</span><span className="secure-label">DATA-BOUNDED</span></div>
        <form className="question-form" onSubmit={(event) => void submit(event)}><input aria-label="Ask a question about your data" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="e.g. Which region had the highest revenue?" maxLength={1000} /><button aria-label="Send question" disabled={busy || !question.trim()}>{busy ? <LoaderCircle className="spin" size={18} /> : <ArrowUp size={18} />}</button></form>
        <div className="suggestions">{suggestions.map((suggestion) => <button key={suggestion} onClick={() => setQuestion(suggestion)}>{suggestion}</button>)}</div>
        {error && <div className="inline-error" role="alert">{error}</div>}
        {result && <div className="answer-panel" aria-live="polite"><div className="answer-header"><span className="answer-dot" /><span>ANALYSIS</span><span className="answer-intent">{result.intent.replaceAll('_', ' ')}</span></div><p className="answer-text">{result.answer}</p><RecommendedChart visualization={result.visualization} /></div>}
      </div>
    </div>
  )
}