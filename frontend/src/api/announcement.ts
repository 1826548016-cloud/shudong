import { http } from './http'

export type AnnouncementMediaItem = {
  id: number
  file_url: string
  media_type: 'image' | 'video' | 'audio' | 'file'
  created_at: string
}

export type SiteAnnouncement = {
  id: number
  title: string
  content: string
  is_active: boolean
  media_items: AnnouncementMediaItem[]
  created_at: string
  updated_at: string
}

export async function fetchAnnouncements() {
  const { data } = await http.get<SiteAnnouncement[]>('/api/announcements/')
  return data
}
