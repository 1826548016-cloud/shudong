import { http } from './http'

export type MusicItem = {
  id: number
  title: string
  artist: string
  file: string
  file_url: string
  duration: number
  created_at: string
}

export async function fetchMusicList(): Promise<MusicItem[]> {
  const { data } = await http.get<MusicItem[]>('/api/music/')
  return data
}

export async function uploadMusic(formData: FormData): Promise<MusicItem> {
  const { data } = await http.post<MusicItem>('/api/music/', formData)
  return data
}

export async function deleteMusic(id: number): Promise<void> {
  await http.delete(`/api/music/${id}/`)
}
