import apiClient from './client'
import type {
  ChecklistItemCondition,
  ChecklistSummary,
  ChecklistType,
  InventoryCategory,
  InventoryItem,
  StayChecklist,
} from '@/types/inventory.types'

export interface InventoryCategoryPayload {
  name: string
  sort_order?: number
}

export interface InventoryItemPayload {
  category_id: string
  name: string
  quantity_expected: number
  color?: string | null
  serial_number?: string | null
  brand?: string | null
  model?: string | null
  image_url?: string | null
  notes?: string | null
  is_consumable?: boolean
}

export interface ChecklistItemUpdatePayload {
  id: string
  quantity_found?: number | null
  condition?: ChecklistItemCondition
  incident_notes?: string | null
  incident_image_url?: string | null
}

export const inventoryCategoriesApi = {
  list: async (
    propertyId: string,
    includeInactive = false
  ): Promise<InventoryCategory[]> => {
    const response = await apiClient.get<{ data: InventoryCategory[] }>(
      `/properties/${propertyId}/inventory-categories`,
      { params: { include_inactive: includeInactive } }
    )
    return response.data.data
  },

  create: async (
    propertyId: string,
    data: InventoryCategoryPayload
  ): Promise<InventoryCategory> => {
    const response = await apiClient.post<{ data: InventoryCategory }>(
      `/properties/${propertyId}/inventory-categories`,
      data
    )
    return response.data.data
  },

  update: async (
    id: string,
    data: Partial<InventoryCategoryPayload> & { is_active?: boolean }
  ): Promise<InventoryCategory> => {
    const response = await apiClient.put<{ data: InventoryCategory }>(
      `/inventory-categories/${id}`,
      data
    )
    return response.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/inventory-categories/${id}`)
  },
}

export const inventoryItemsApi = {
  list: async (
    propertyId: string,
    params?: { category_id?: string; q?: string; include_inactive?: boolean }
  ): Promise<InventoryItem[]> => {
    const response = await apiClient.get<{ data: InventoryItem[] }>(
      `/properties/${propertyId}/inventory-items`,
      { params }
    )
    return response.data.data
  },

  create: async (propertyId: string, data: InventoryItemPayload): Promise<InventoryItem> => {
    const response = await apiClient.post<{ data: InventoryItem }>(
      `/properties/${propertyId}/inventory-items`,
      data
    )
    return response.data.data
  },

  update: async (
    id: string,
    data: Partial<InventoryItemPayload> & { is_active?: boolean }
  ): Promise<InventoryItem> => {
    const response = await apiClient.put<{ data: InventoryItem }>(`/inventory-items/${id}`, data)
    return response.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/inventory-items/${id}`)
  },
}

export const checklistsApi = {
  list: async (params?: {
    property_id?: string
    has_incidents?: boolean
  }): Promise<ChecklistSummary[]> => {
    const response = await apiClient.get<{ data: ChecklistSummary[] }>('/checklists', { params })
    return response.data.data
  },

  listForRevenue: async (revenueId: string): Promise<StayChecklist[]> => {
    const response = await apiClient.get<{ data: StayChecklist[] }>(
      `/revenues/${revenueId}/checklists`
    )
    return response.data.data
  },

  create: async (revenueId: string, checklistType: ChecklistType): Promise<StayChecklist> => {
    const response = await apiClient.post<{ data: StayChecklist }>(
      `/revenues/${revenueId}/checklists`,
      { checklist_type: checklistType }
    )
    return response.data.data
  },

  get: async (id: string): Promise<StayChecklist> => {
    const response = await apiClient.get<{ data: StayChecklist }>(`/checklists/${id}`)
    return response.data.data
  },

  updateItems: async (
    id: string,
    data: { items: ChecklistItemUpdatePayload[]; general_notes?: string | null }
  ): Promise<StayChecklist> => {
    const response = await apiClient.put<{ data: StayChecklist }>(`/checklists/${id}/items`, data)
    return response.data.data
  },

  complete: async (id: string): Promise<StayChecklist> => {
    const response = await apiClient.post<{ data: StayChecklist }>(`/checklists/${id}/complete`)
    return response.data.data
  },

  reopen: async (id: string): Promise<StayChecklist> => {
    const response = await apiClient.post<{ data: StayChecklist }>(`/checklists/${id}/reopen`)
    return response.data.data
  },
}
