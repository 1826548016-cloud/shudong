import { http } from './http'

export type MessageItem = {
  id: number
  nickname: string
  content: string
  created_at: string
}

export async function fetchMessages(): Promise<MessageItem[]> {
  const { data } = await http.get<MessageItem[]>('/api/messages/')
  return data
}

export async function createMessage(nickname: string, content: string): Promise<MessageItem> {
  const { data } = await http.post<MessageItem>('/api/messages/', { nickname, content })
  return data
}

export async function deleteMessage(id: number): Promise<void> {
  await http.delete(`/api/messages/${id}/`)
}
