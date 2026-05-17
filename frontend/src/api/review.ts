import { http } from './http'

export type ContentReview = {
  id: number
  review_type: 'comment' | 'message'
  source_id: number
  nickname: string
  content: string
  ai_reason: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}

export async function fetchReviews() {
  const { data } = await http.get<ContentReview[]>('/api/admin/reviews/')
  return data
}

export async function fetchReviewCount() {
  const { data } = await http.get<{ count: number }>('/api/admin/reviews/count/')
  return data.count
}

export async function approveReview(id: number) {
  const { data } = await http.post(`/api/admin/reviews/${id}/approve/`)
  return data
}

export async function rejectReview(id: number) {
  const { data } = await http.post(`/api/admin/reviews/${id}/reject/`)
  return data
}
