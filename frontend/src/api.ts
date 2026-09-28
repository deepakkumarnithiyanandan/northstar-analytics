import type { AskResult, DashboardData, Dataset, QueryFilters, SalesPage } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, init)
  } catch {
    throw new ApiError('Could not reach the analytics API. Check that the backend is running.', 0)
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown } | null
    let message = `Request failed (${response.status}).`
    if (typeof body?.detail === 'string') message = body.detail
    if (Array.isArray(body?.detail)) {
      message = body.detail.map((issue: { msg?: string; loc?: (string | number)[] }) => `${issue.loc?.slice(1).join('.') ?? 'Request'}: ${issue.msg ?? 'is invalid'}`).join(' ')
    } else if (body?.detail && typeof body.detail === 'object') {
      const detail = body.detail as { message?: string; errors?: string[] }
      message = [detail.message, ...(detail.errors ?? [])].filter(Boolean).join(' ')
    }
    throw new ApiError(message, response.status)
  }
  return response.json() as Promise<T>
}

export function queryString(datasetId: number | null, filters?: QueryFilters) {
  const params = new URLSearchParams()
  if (datasetId) params.set('dataset_id', String(datasetId))
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value)
    })
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

export const getDatasets = () => request<Dataset[]>('/api/datasets')
export const getHealth = () => request<{ status: string }>('/api/health')
export const getDashboard = (datasetId: number | null, filters: QueryFilters) =>
  request<DashboardData>(`/api/dashboard${queryString(datasetId, filters)}`)
export const getSales = (datasetId: number | null, filters: QueryFilters, offset: number) => {
  const params = new URLSearchParams(queryString(datasetId, filters).replace(/^\?/, ''))
  params.set('limit', '50')
  params.set('offset', String(offset))
  return request<SalesPage>(`/api/sales?${params.toString()}`)
}
export const getOptions = (kind: 'regions' | 'categories' | 'products', datasetId: number | null) =>
  request<{ items: string[] }>(`/api/${kind}${queryString(datasetId)}`)
export const loadDemo = () => request<Dataset>('/api/demo', { method: 'POST' })

export async function uploadCsv(file: File) {
  const body = new FormData()
  body.append('file', file)
  return request<{ dataset: Dataset; warnings: string[] }>('/api/upload', { method: 'POST', body })
}

export function askQuestion(question: string, datasetId: number | null) {
  return request<AskResult>(`/api/ask${queryString(datasetId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
}