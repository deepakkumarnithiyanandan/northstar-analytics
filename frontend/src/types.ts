export type ViewName = 'dashboard' | 'upload' | 'assistant' | 'data'

export interface Dataset {
  id: number
  name: string
  row_count: number
  uploaded_at: string
}

export interface KPISet {
  total_revenue: number
  total_orders: number
  average_order_value: number
  total_customers: number
  revenue_growth: number | null
}

export interface ChartPoint {
  label: string
  value: number
}

export interface DashboardData {
  dataset: Dataset
  kpis: KPISet
  revenue_over_time: ChartPoint[]
  revenue_by_region: ChartPoint[]
  revenue_by_category: ChartPoint[]
  top_products: ChartPoint[]
  order_trend: ChartPoint[]
  insights: string[]
}

export interface SaleRecord {
  id: number
  order_id: string
  order_date: string
  customer_id: string
  product: string
  category: string
  region: string
  quantity: number
  unit_price: number
  revenue: number
}

export interface SalesPage {
  items: SaleRecord[]
  total: number
  limit: number
  offset: number
}

export interface Visualization {
  type: 'line' | 'bar' | 'pie' | 'table' | 'histogram'
  title: string
  data: ChartPoint[]
}

export interface AskResult {
  answer: string
  intent: string
  metrics: Record<string, unknown>
  visualization: Visualization
  query_id: number
}

export interface QueryFilters {
  start_date: string
  end_date: string
  region: string
  category: string
  product: string
}

export const EMPTY_FILTERS: QueryFilters = {
  start_date: '',
  end_date: '',
  region: '',
  category: '',
  product: '',
}