export interface InventoryCategory {
  id: string
  property_id: string
  name: string
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at?: string | null
}

export interface InventoryItem {
  id: string
  property_id: string
  category_id: string
  category_name?: string | null
  name: string
  quantity_expected: number
  color?: string | null
  serial_number?: string | null
  brand?: string | null
  model?: string | null
  image_url?: string | null
  notes?: string | null
  is_consumable?: boolean
  is_active: boolean
  created_at: string
  updated_at?: string | null
}

export type ChecklistType = 'checkin' | 'checkout'
export type ChecklistStatus = 'draft' | 'completed'
export type ChecklistItemCondition = 'ok' | 'missing' | 'damaged' | 'other'

export interface ChecklistItem {
  id: string
  checklist_id: string
  inventory_item_id?: string | null
  item_name: string
  category_name: string
  quantity_expected: number
  quantity_found?: number | null
  condition: ChecklistItemCondition
  incident_notes?: string | null
  incident_image_url?: string | null
  is_consumable?: boolean
  sort_order: number
}

export interface StayChecklist {
  id: string
  property_id: string
  rental_revenue_id: string
  checklist_type: ChecklistType
  status: ChecklistStatus
  performed_by_user_id?: string | null
  performed_by_name?: string | null
  performed_at?: string | null
  general_notes?: string | null
  has_incidents: boolean
  created_at: string
  updated_at?: string | null
  items: ChecklistItem[]
}

export interface ChecklistSummary {
  id: string
  property_id: string
  rental_revenue_id: string
  checklist_type: ChecklistType
  status: ChecklistStatus
  has_incidents: boolean
  performed_by_name?: string | null
  performed_at?: string | null
}
