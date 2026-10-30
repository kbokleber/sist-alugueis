export interface Revenue {
  id: string
  user_id: string
  property_id: string
  property_name?: string
  year_month: string
  date: string
  checkin_date: string | null
  checkout_date: string | null
  guest_name: string
  listing_name: string | null
  listing_source: string | null
  nights: number
  gross_amount: number
  cleaning_fee: number
  platform_fee: number
  net_amount: number
  pending_amount: number | null
  external_id: string | null
  notes: string | null
  checkin_checklist_status?: 'draft' | 'completed' | null
  checkout_checklist_status?: 'draft' | 'completed' | null
  checkin_checklist_id?: string | null
  checkout_checklist_id?: string | null
  checkin_has_incidents?: boolean
  checkout_has_incidents?: boolean
  checkin_performed_by_name?: string | null
  checkout_performed_by_name?: string | null
  created_at: string
  updated_at: string | null
}

export interface CreateRevenueRequest {
  property_id: string
  year_month: string
  date: string
  checkin_date?: string
  checkout_date?: string
  guest_name: string
  listing_name?: string
  listing_source?: string
  nights: number
  gross_amount?: number
  cleaning_fee?: number
  platform_fee?: number
  net_amount: number
  pending_amount?: number
  external_id?: string
  notes?: string
}
