import { useRef, useState } from 'react'
import { AlertCircle, CheckCircle2, FileUp, LoaderCircle } from 'lucide-react'
import { ApiError, uploadCsv } from '../api'
import type { Dataset } from '../types'

export function UploadArea({ onUploaded }: { onUploaded: (dataset: Dataset) => void }) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [success, setSuccess] = useState(false)

  async function submit(file?: File) {
    if (!file) return
    setMessage('')
    setSuccess(false)
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setMessage('That file is not a CSV. Choose a .csv file to continue.')
      return
    }
    setBusy(true)
    try {
      const result = await uploadCsv(file)
      setSuccess(true)
      setMessage(`${result.dataset.name} is ready with ${result.dataset.row_count.toLocaleString()} rows.`)
      onUploaded(result.dataset)
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : 'Upload failed. Try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="upload-wrap">
      <button className={`drop-zone ${dragging ? 'dragging' : ''}`} onClick={() => fileInput.current?.click()} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); void submit(event.dataTransfer.files[0]) }} disabled={busy}>
        <span className="upload-icon">{busy ? <LoaderCircle className="spin" size={23} /> : <FileUp size={23} />}</span>
        <strong>{busy ? 'Validating and importing…' : 'Drop your sales CSV here'}</strong>
        <span>or choose a file from your computer</span>
        <span className="upload-meta">CSV · UTF-8 · up to 10 MB</span>
      </button>
      <input ref={fileInput} className="visually-hidden" type="file" accept=".csv,text/csv" onChange={(event) => void submit(event.target.files?.[0])} />
      {message && <div className={`upload-message ${success ? 'success' : 'error'}`} role="status">{success ? <CheckCircle2 size={17} /> : <AlertCircle size={17} />}{message}</div>}
      <div className="required-fields"><strong>Required columns</strong><code>order_id, order_date, customer_id, product, category, region, quantity, unit_price</code><span>Revenue is calculated from quantity × unit price when omitted.</span></div>
    </div>
  )
}