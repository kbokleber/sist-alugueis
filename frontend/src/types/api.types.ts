export interface ApiResponse<T> {
  data: T
  message?: string
  meta?: {
    page: number
    per_page: number
    total: number
    total_pages?: number
  }
}

export interface PaginatedRequest {
  page?: number
  per_page?: number
  sort?: string
}
