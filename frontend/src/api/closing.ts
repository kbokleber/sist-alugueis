import apiClient from './client'

export interface ClosingResponse {
  id: string
  property_id: string
  year_month: string
  total_revenue: number
  total_expenses: number
  net_result: number
  total_nights: number
  total_bookings: number
  depreciation_value: number
  cleaning_total: number
  platform_fee_total: number
  other_expenses: number
  status: 'DRAFT' | 'CLOSED' | 'CANCELLED'
  notes?: string
  closed_at?: string
  created_at: string
  updated_at?: string
}

export interface ClosingListResponse {
  data: ClosingResponse[]
  meta?: {
    total: number
    page: number
    per_page: number
    total_pages: number
  }
}

export const closingApi = {
  list: async (property_id?: string): Promise<ClosingListResponse> => {
    const response = await apiClient.get<ClosingListResponse>('/closing', {
      params: property_id ? { property_id } : undefined,
    })
    return response.data
  },

  generate: async (data: { property_id: string; year_month: string }): Promise<ClosingResponse> => {
    const response = await apiClient.post<{ data: ClosingResponse }>('/closing/generate', data)
    return response.data.data
  },

  get: async (property_id: string, year_month: string): Promise<ClosingResponse> => {
    const response = await apiClient.get<{ data: ClosingResponse }>(`/closing/${property_id}/${year_month}`)
    return response.data.data
  },

  close: async (property_id: string, year_month: string): Promise<ClosingResponse> => {
    const response = await apiClient.post<{ data: ClosingResponse }>(`/closing/${property_id}/${year_month}/close`)
    return response.data.data
  },

  reopen: async (property_id: string, year_month: string): Promise<ClosingResponse> => {
    const response = await apiClient.post<{ data: ClosingResponse }>(`/closing/${property_id}/${year_month}/reopen`)
    return response.data.data
  },

  exportCsv: async (property_id: string, year_month: string): Promise<void> => {
    const response = await apiClient.get(`/closing/${property_id}/${year_month}/export`, {
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `fechamento-${property_id}-${year_month}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  },
}
