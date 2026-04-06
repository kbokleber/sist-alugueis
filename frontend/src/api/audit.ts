import apiClient from './client'

export interface AuditLog {
  id: string
  user_id: string | null
  action: string
  entity_type: string
  entity_id: string
  old_values: Record<string, unknown> | null
  new_values: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
  user?: {
    id: string
    email: string
    full_name: string
  }
}

export interface AuditLogFilters {
  entity_type?: string
  entity_id?: string
  user_id?: string
  start_date?: string
  end_date?: string
}

export const auditApi = {
  list: async (params?: {
    entity_type?: string
    entity_id?: string
    page?: number
    per_page?: number
  }): Promise<{ data: AuditLog[]; meta: { total: number; page: number; per_page: number; total_pages: number } }> => {
    const response = await apiClient.get<{ data: AuditLog[]; meta: { total: number; page: number; per_page: number; total_pages: number } }>('/audit', { params })
    return response.data
  },

  getEntityHistory: async (entityType: string, entityId: string): Promise<AuditLog[]> => {
    const response = await apiClient.get<{ data: AuditLog[] }>(`/audit/${entityType}/${entityId}`)
    return response.data.data
  },
}
