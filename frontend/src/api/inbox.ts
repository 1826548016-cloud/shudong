import { http } from './http'

export type UnreadCount = {
  count: number
}

export type UnreadComment = {
  id: number
  post: number
  post_content: string
  nickname: string
  content: string
  admin_reply: string
  replied_at: string | null
  is_unread: boolean
  created_at: string
}

export async function fetchUnreadCount() {
  const { data } = await http.get<UnreadCount>('/api/admin/comments/unread/count/')
  return data
}

export async function fetchUnreadComments() {
  const { data } = await http.get<UnreadComment[]>('/api/admin/comments/unread/')
  return data
}

export async function replyComment(commentId: number, adminReply: string) {
  const { data } = await http.post(`/api/admin/comments/${commentId}/reply/`, {
    admin_reply: adminReply,
  })
  return data
}

export async function markCommentRead(commentId: number) {
  const { data } = await http.post(`/api/admin/comments/${commentId}/read/`)
  return data
}
