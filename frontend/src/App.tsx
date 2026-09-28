import { useEffect, useState } from 'react'
import { ArrowRight, ArrowUpRight, CircleDollarSign, Database, Menu, PackageCheck, ShoppingBag, Users } from 'lucide-react'
import { ApiError, getDashboard, getDatasets, getHealth, getOptions, getSales, loadDemo } from './api'
import { AIChat } from './components/AIChat'
import { AIInsightCard } from './components/AIInsightCard'
import { ChartCard } from './components/ChartCard'
import { DataTable } from './components/DataTable'
import { FilterPanel } from './components/FilterPanel'
import { KpiCard } from './components/KpiCard'
import { Sidebar } from './components/Sidebar'
import { UploadArea } from './components/UploadArea'
import { EMPTY_FILTERS, type DashboardData, type Dataset, type QueryFilters, type SaleRecord, type ViewName } from './types'

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const titles: Record<ViewName, { eyebrow: string; title: string }> = {
  dashboard: { eyebrow: 'BUSINESS OVERVIEW', title: 'Your sales, in focus.' },
  upload: { eyebrow: 'DATA MANAGEMENT', title: 'Bring your data in.' },
  assistant: { eyebrow: 'NATURAL LANGUAGE ANALYTICS', title: 'Ask better questions.' },
  data: { eyebrow: 'DATA EXPLORER', title: 'Every row, accounted for.' },
}

export default function App() {
  const [view, setView] = useState<ViewName>('dashboard')
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [datasetId, setDatasetId] = useState<number | null>(null)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [filters, setFilters] = useState<QueryFilters>(EMPTY_FILTERS)
  const [options, setOptions] = useState({ regions: [] as string[], categories: [] as string[], products: [] as string[] })
  const [sales, setSales] = useState<SaleRecord[]>([])
  const [salesTotal, setSalesTotal] = useState(0)
  const [salesOffset, setSalesOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [apiOnline, setApiOnline] = useState<boolean | null>(null)

  useEffect(() => {
    void getHealth().then(() => setApiOnline(true)).catch(() => setApiOnline(false))
    void getDatasets().then((items) => {
      setDatasets(items)
      if (items.length) setDatasetId((current) => current ?? items[0].id)
    }).catch((requestError: unknown) => setError(requestError instanceof ApiError ? requestError.message : 'Could not connect to the API.'))
  }, [])

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    void getDashboard(datasetId, filters).then((data) => {
      if (!active) return
      setDashboard(data)
      setDatasetId((current) => current ?? data.dataset.id)
    }).catch((requestError: unknown) => {
      if (!active) return
      if (requestError instanceof ApiError && requestError.status === 404) setDashboard(null)
      else setError(requestError instanceof ApiError ? requestError.message : 'Could not load the dashboard.')
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [datasetId, filters])

  useEffect(() => {
    if (!datasetId) return
    let active = true
    void Promise.all([getOptions('regions', datasetId), getOptions('categories', datasetId), getOptions('products', datasetId)])
      .then(([regions, categories, products]) => {
        if (active) setOptions({ regions: regions.items, categories: categories.items, products: products.items })
      }).catch(() => { if (active) setOptions({ regions: [], categories: [], products: [] }) })
    return () => { active = false }
  }, [datasetId])

  useEffect(() => {
    if (view !== 'data' || !dashboard) return
    void getSales(datasetId, filters, salesOffset).then((page) => {
      setSales(page.items)
      setSalesTotal(page.total)
    }).catch((requestError: unknown) => setError(requestError instanceof ApiError ? requestError.message : 'Could not load sales rows.'))
  }, [view, datasetId, filters, salesOffset, dashboard])

  async function chooseDemo() {
    setBusy(true)
    setError('')
    try {
      const dataset = await loadDemo()
      setDatasets((current) => [dataset, ...current])
      setDatasetId(dataset.id)
      setFilters(EMPTY_FILTERS)
      setView('dashboard')
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Could not load the sample dataset.')
    } finally {
      setBusy(false)
    }
  }

  function onUploaded(dataset: Dataset) {
    setDatasets((current) => [dataset, ...current])
    setDatasetId(dataset.id)
    setFilters(EMPTY_FILTERS)
    setView('dashboard')
  }

  function changeView(next: ViewName) {
    setView(next)
    setSidebarOpen(false)
    setSalesOffset(0)
  }

  const title = titles[view]
  const selectedDataset = datasets.find((item) => item.id === datasetId) ?? dashboard?.dataset

  return (
    <div className={`app-shell ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <Sidebar active={view} onChange={changeView} />
      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="Toggle navigation" onClick={() => setSidebarOpen(!sidebarOpen)}><Menu size={19} /></button>
          <div className="breadcrumb"><span>Workspace</span><span className="crumb-slash">/</span><strong>{title.eyebrow.toLowerCase().replaceAll(' ', ' ')}</strong></div>
          <div className="topbar-actions">
            <label className="dataset-select"><Database size={15} /><select aria-label="Select dataset" value={datasetId ?? ''} onChange={(event) => setDatasetId(Number(event.target.value) || null)}><option value="">No dataset</option>{datasets.map((dataset) => <option value={dataset.id} key={dataset.id}>{dataset.name}</option>)}</select></label>
            <div className={`status-indicator ${apiOnline === false ? 'offline' : ''}`}><span />{apiOnline === null ? 'Connecting' : apiOnline ? 'API connected' : 'API offline'}</div>
          </div>
        </header>
        {sidebarOpen && <button className="mobile-backdrop" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
        <div className="page-content">
          <div className="page-heading"><div><span className="eyebrow">{title.eyebrow}</span><h1>{title.title}</h1></div>
            {view === 'dashboard' && dashboard && <button className="button button-dark" onClick={() => changeView('assistant')}><span>Ask your data</span><ArrowUpRight size={16} /></button>}
          </div>
          {error && <div className="page-error" role="alert">{error}</div>}
          {view === 'dashboard' && <DashboardView loading={loading} dashboard={dashboard} options={options} filters={filters} setFilters={setFilters} onUpload={() => changeView('upload')} onDemo={() => void chooseDemo()} busy={busy} />}
          {view === 'upload' && <section className="upload-page"><div className="section-intro"><div className="section-icon"><PackageCheck size={19} /></div><div><h2>Import a sales dataset</h2><p>Upload a CSV to build a clean, filterable analytics workspace.</p></div></div><UploadArea onUploaded={onUploaded} /><div className="import-divider"><span>OR START EXPLORING</span></div><button className="sample-button" onClick={() => void chooseDemo()} disabled={busy}><span className="sample-icon"><Database size={17} /></span><span><strong>{busy ? 'Preparing sample dataset…' : 'Load the sample sales dataset'}</strong><small>1,200 realistic orders across products, regions and months</small></span><ArrowRight size={17} /></button></section>}
          {view === 'assistant' && (dashboard ? <AIChat key={datasetId} datasetId={datasetId} /> : <EmptyState onUpload={() => changeView('upload')} onDemo={() => void chooseDemo()} busy={busy} />)}
          {view === 'data' && <section className="data-page"><div className="data-toolbar"><div><h2>Sales records</h2><p>{dashboard ? `${salesTotal.toLocaleString()} rows in ${selectedDataset?.name ?? 'this dataset'}` : 'Load a dataset to inspect individual records.'}</p></div>{dashboard && <button className="button button-light" onClick={() => changeView('upload')}>Import another CSV <ArrowUpRight size={15} /></button>}</div>{dashboard ? <><FilterPanel filters={filters} options={options} onChange={(next) => { setFilters(next); setSalesOffset(0) }} /><DataTable rows={sales} total={salesTotal} offset={salesOffset} onPage={setSalesOffset} /></> : <EmptyState onUpload={() => changeView('upload')} onDemo={() => void chooseDemo()} busy={busy} />}</section>}
        </div>
      </main>
    </div>
  )
}

function DashboardView({ loading, dashboard, options, filters, setFilters, onUpload, onDemo, busy }: {
  loading: boolean; dashboard: DashboardData | null; options: { regions: string[]; categories: string[]; products: string[] }
  filters: QueryFilters; setFilters: (filters: QueryFilters) => void; onUpload: () => void; onDemo: () => void; busy: boolean
}) {
  if (loading && !dashboard) return <div className="loading-state"><span className="loader" />Loading your workspace…</div>
  if (!dashboard) return <EmptyState onUpload={onUpload} onDemo={onDemo} busy={busy} />
  const kpis = dashboard.kpis
  return <>
    <div className="dataset-summary"><span className="dataset-dot" /><span>Viewing</span><strong>{dashboard.dataset.name}</strong><span className="summary-separator">·</span><span>{dashboard.dataset.row_count.toLocaleString()} sales rows</span><span className="summary-date">Updated {new Date(dashboard.dataset.uploaded_at).toLocaleDateString()}</span></div>
    <FilterPanel filters={filters} options={options} onChange={setFilters} />
    {loading && <div className="refresh-line"><span />Refreshing filtered metrics</div>}
    <div className="kpi-grid">
      <KpiCard label="Total revenue" value={currency.format(kpis.total_revenue)} note="in selected period" icon={CircleDollarSign} tone="tone-green" />
      <KpiCard label="Total orders" value={kpis.total_orders.toLocaleString()} note="distinct order IDs" icon={ShoppingBag} tone="tone-gold" />
      <KpiCard label="Average order value" value={currency.format(kpis.average_order_value)} note="revenue per order" icon={ArrowUpRight} tone="tone-blue" />
      <KpiCard label="Customers" value={kpis.total_customers.toLocaleString()} note="unique customers" icon={Users} tone="tone-coral" />
    </div>
    <div className="dashboard-grid">
      <div className="chart-main"><ChartCard title="Revenue over time" eyebrow="PERFORMANCE" data={dashboard.revenue_over_time} /><div className="chart-pair"><ChartCard title="Revenue by region" eyebrow="GEOGRAPHY" data={dashboard.revenue_by_region} kind="bar" height={230} /><ChartCard title="Revenue mix" eyebrow="CATEGORY" data={dashboard.revenue_by_category} kind="pie" height={230} /></div></div>
      <div className="insight-column"><KpiCard label="Revenue growth" value={kpis.revenue_growth === null ? '—' : `${kpis.revenue_growth >= 0 ? '+' : ''}${kpis.revenue_growth.toFixed(1)}%`} note="latest month vs. prior" icon={ArrowUpRight} tone="tone-green" trend={kpis.revenue_growth} /><AIInsightCard insights={dashboard.insights} /><ChartCard title="Order trend" eyebrow="VOLUME" data={dashboard.order_trend} height={185} valueFormat="number" /></div>
    </div>
    <section className="top-products"><div className="section-heading"><div><span className="eyebrow">PRODUCT PERFORMANCE</span><h2>Top products</h2></div><span>Ranked by revenue</span></div>{dashboard.top_products.slice(0, 5).map((item, index) => <div className="product-row" key={item.label}><span className="product-rank">{String(index + 1).padStart(2, '0')}</span><span className="product-name">{item.label}</span><div className="product-track"><span style={{ width: `${Math.max(6, item.value / (dashboard.top_products[0]?.value || 1) * 100)}%` }} /></div><strong>{currency.format(item.value)}</strong></div>)}</section>
  </>
}

function EmptyState({ onUpload, onDemo, busy }: { onUpload: () => void; onDemo: () => void; busy: boolean }) {
  return <section className="empty-state"><div className="empty-orbit"><div className="empty-core"><Database size={24} /></div><span className="orbit orbit-one" /><span className="orbit orbit-two" /></div><span className="eyebrow">A CLEARER VIEW STARTS HERE</span><h2>Your next decision<br />starts with data.</h2><p>Upload a sales CSV or explore the bundled sample workspace to see Northstar in action.</p><div className="empty-actions"><button className="button button-dark" onClick={onUpload}><span>Import a dataset</span><ArrowRight size={16} /></button><button className="button button-light" onClick={onDemo} disabled={busy}>{busy ? 'Loading…' : 'Explore sample data'}</button></div></section>
}