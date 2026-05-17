<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

import { http } from '../api/http'
import { fetchProfilePublic } from '../api/profile'
import { fetchAnnouncements, type SiteAnnouncement } from '../api/announcement'
import PostCard from '../components/PostCard.vue'

type Post = {
  id: number
  content: string
  media_url: string | null
  media_type: 'none' | 'image' | 'video'
  media_items?: { id: number; file_url: string; media_type: string }[]
  view_count: number
  like_count: number
  comment_count: number
  is_pinned: boolean
  created_at: string
}

const loading = ref(false)
const posts = ref<Post[]>([])
const announcements = ref<SiteAnnouncement[]>([])
const siteNickname = ref('树洞主人')
const siteUpdatedAt = ref('')
const postTotal = ref(0)
const searchQuery = ref('')

const filteredPosts = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return posts.value
  return posts.value.filter((p) => p.content.toLowerCase().includes(q))
})

function timeAgo(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 2592000) return `${Math.floor(diff / 86400)} 天前`
  const d = new Date(iso)
  return d.toLocaleString()
}

async function loadPosts() {
  loading.value = true
  try {
    const { data } = await http.get<Post[]>('/api/posts/')
    posts.value = data
    postTotal.value = data.length
    if (data.length > 0) {
      siteUpdatedAt.value = data.reduce((max, p) =>
        p.created_at > max ? p.created_at : max, data[0].created_at)
    }
  } catch (e) {
    ElMessage.error('加载动态失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProfilePublic()
    .then((p) => {
      siteNickname.value = p.nickname || '树洞主人'
    })
    .catch(() => {})
  fetchAnnouncements()
    .then((list) => {
      announcements.value = list
    })
    .catch(() => {})
  void loadPosts()
})
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div class="page-title">什么时候才能大雪深埋呢？</div>
      <div class="page-subtitle">这里是 {{ siteNickname }} 的树洞 · 无需繁杂登录，随便看看，想说就说</div>
      <div class="page-stats">
        <span class="stats-item">{{ postTotal }} 条动态</span>
        <span v-if="siteUpdatedAt" class="stats-item">最近更新：{{ timeAgo(siteUpdatedAt) }}</span>
      </div>
    </div>

    <div v-if="announcements.length" class="announcements">
        <div v-for="item in announcements" :key="item.id" class="announce-card">
          <div class="announce-header">
            <span class="announce-icon">📢</span>
            <span class="announce-title">{{ item.title }}</span>
          </div>
          <div class="announce-body">{{ item.content }}</div>
          <div v-if="item.media_items && item.media_items.length" class="announce-media">
            <div v-for="m in item.media_items" :key="m.id" class="announce-media-item">
              <el-image
                v-if="m.media_type === 'image'"
                :src="m.file_url"
                :preview-src-list="[m.file_url]"
                fit="cover"
                lazy
                class="announce-img"
                style="aspect-ratio:16/9"
              />
              <video
                v-else-if="m.media_type === 'video'"
                :src="m.file_url"
                controls
                class="announce-video"
              />
              <a
                v-else
                :href="m.file_url"
                target="_blank"
                class="announce-file-link"
              >
                📎 查看附件
              </a>
            </div>
          </div>
        </div>
      </div>

      <el-skeleton v-if="loading" :rows="10" animated />
      <div v-else class="feed">
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索动态内容..."
            :prefix-icon="Search"
            clearable
            size="default"
          />
        </div>
        <PostCard v-for="p in filteredPosts" :key="p.id" :post="p" v-memo="[p.id, p.like_count, p.comment_count, p.view_count, p.is_pinned]" />
        <div v-if="filteredPosts.length === 0 && searchQuery" class="empty">没有匹配的动态</div>
        <div v-else-if="posts.length === 0" class="empty">还没有动态</div>
    </div>
  </section>
</template>

<style scoped>
.page {
  min-height: 100vh;
}

.page-head {
  margin: 0 0 24px;
  padding: 32px 0 0;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-1);
  letter-spacing: -.02em;
  line-height: 1.4;
}

.page-subtitle {
  margin-top: 6px;
  font-size: 14px;
  color: var(--text-3);
}

.page-stats {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stats-item {
  font-size: 12px;
  color: var(--text-2);
  background: var(--primary-light);
  color: var(--primary);
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.announcements {
  margin-bottom: 20px;
  display: grid;
  gap: 10px;
}

.announce-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  box-shadow: var(--shadow-sm);
}

.announce-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.announce-icon {
  font-size: 18px;
}

.announce-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-1);
}

.announce-body {
  font-size: 14px;
  color: var(--text-2);
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-all;
}

.announce-media {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}

.announce-media-item {
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.announce-img {
  width: 100%;
  max-height: 300px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.announce-video {
  width: 100%;
  max-height: 300px;
  border-radius: var(--radius-sm);
  background: #000;
}

.announce-file-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--primary-light);
  border-radius: 6px;
  color: var(--primary);
  font-size: 13px;
  text-decoration: none;
  font-weight: 500;
}

.announce-file-link:hover {
  opacity: .8;
}

.feed {
  display: grid;
  gap: 12px;
}

.search-bar {
  margin-bottom: 4px;
}

.empty {
  text-align: center;
  padding: 48px 0;
  color: var(--text-3);
  font-size: 14px;
}
</style>
