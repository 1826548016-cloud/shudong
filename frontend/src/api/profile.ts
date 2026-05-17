import { http } from './http'

export type ProfilePublic = {
  nickname: string
  bio: string
  wechat_id: string
  douyin_url: string
  email: string
  avatar_url: string | null
}

export type ProfileAdmin = {
  nickname: string
  avatar_url: string | null
  bio: string
  wechat_id: string
  douyin_url: string
  phone_num: string
  email: string
  updated_at: string
}

export async function fetchProfilePublic() {
  const { data } = await http.get<ProfilePublic>('/api/profile/')
  return data
}

export async function fetchProfileAdmin() {
  const { data } = await http.get<ProfileAdmin>('/api/admin/profile/')
  return data
}
