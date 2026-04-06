import apiClient from './client'

export interface DashboardOverview {
  year_month: string
  total_properties: number
  total_revenue: number
  total_expenses: number
  total_net_result: number
  total_nights: number
  total_bookings: number
  properties: Array<{
    id: string
    name: string
    total_revenue: number
    total_expenses: number
    net_result: number
  }>
}

export interface PropertyDashboard {
  property: { id: string; name: string; value: number }
  year_month: string
  property_monthly_value: number
  months_owned: number
  one_percent: number
  total_revenue: number
  total_nights: number
  total_bookings: number
  net_revenue: number
  cleaning_total: number
  platform_fee_total: number
  other_expenses: number
  total_expenses: number
  gross_result: number
  net_result: number
}

export const dashboardApi = {
  overview: async (year_month?: string): Promise<DashboardOverview> => {
    const response = await apiClient.get<{ data: DashboardOverview }>('/dashboard/overview', {
      params: year_month ? { year_month } : undefined,
    })
    return response.data.data
  },

  property: async (id: string, year_month?: string): Promise<PropertyDashboard> => {
    const response = await apiClient.get<{ data: PropertyDashboard }>(
      `/dashboard/property/${id}`,
      { params: year_month ? { year_month } : undefined }
    )
    return response.data.data
  },

  chartBar: async (property_id: string, months = 12): Promise<{
    labels: string[]
    datasets: Array<{ label: string; data: (number | null)[] }>
  }> => {
    const response = await apiClient.get('/dashboard/chart/bar', {
      params: { property_id, months },
    })
    return response.data.data
  },

  chartPie: async (property_id: string, year_month: string): Promise<{
    labels: string[]
    datasets: Array<{ data: number[]; backgroundColor: string[] }>
  }> => {
    const response = await apiClient.get('/dashboard/chart/pie', {
      params: { property_id, year_month },
    })
    return response.data.data
  },
}
