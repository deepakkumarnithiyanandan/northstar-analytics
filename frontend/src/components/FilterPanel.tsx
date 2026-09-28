import { RotateCcw, SlidersHorizontal } from 'lucide-react'
import type { QueryFilters } from '../types'

interface FilterPanelProps {
  filters: QueryFilters
  options: { regions: string[]; categories: string[]; products: string[] }
  onChange: (filters: QueryFilters) => void
}

export function FilterPanel({ filters, options, onChange }: FilterPanelProps) {
  const update = (key: keyof QueryFilters, value: string) => onChange({ ...filters, [key]: value })
  return (
    <section className="filter-panel" aria-label="Dashboard filters">
      <div className="filter-title"><SlidersHorizontal size={16} /><span>FILTERS</span></div>
      <label className="filter-control"><span>From</span><input aria-label="Start date" type="date" value={filters.start_date} onChange={(event) => update('start_date', event.target.value)} /></label>
      <label className="filter-control"><span>To</span><input aria-label="End date" type="date" value={filters.end_date} onChange={(event) => update('end_date', event.target.value)} /></label>
      {(['region', 'category', 'product'] as const).map((key) => (
        <label className="filter-control" key={key}><span>{key[0].toUpperCase() + key.slice(1)}</span><select value={filters[key]} onChange={(event) => update(key, event.target.value)}><option value="">All {key === 'category' ? 'categories' : `${key}s`}</option>{options[key === 'region' ? 'regions' : key === 'category' ? 'categories' : 'products'].map((value) => <option key={value}>{value}</option>)}</select></label>
      ))}
      <button className="icon-button filter-reset" title="Clear filters" aria-label="Clear filters" onClick={() => onChange({ start_date: '', end_date: '', region: '', category: '', product: '' })}><RotateCcw size={15} /></button>
    </section>
  )
}