<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChatLineRound, Star, Download, Headset } from '@element-plus/icons-vue'

export type PostItem = {
  id: number
  content: string
  media_url: string | null
  media_type: 'none' | 'image' | 'video' | 'audio'
  media_items?: { id: number; file_url: string; media_type: string }[]
  view_count: number
  like_count: number
  comment_count: number
  is_pinned: boolean
  created_at: string
}

const props = defineProps<{
  post: PostItem
}>()

const router = useRouter()

const createdAtText = computed(() => {
  const d = new Date(props.post.created_at)
  if (Number.isNaN(d.getTime())) return props.post.created_at
  return d.toLocaleString()
})

function goDetail() {
  router.push(`/posts/${props.post.id}`)
}

function getFileName(url: string): string {
  const parts = url.split('/')
  return parts[parts.length - 1] || '附件'
}
</script>

<template>
  <article class="post-card" @click="goDetail">
    <div class="post-meta">
      <div class="post-time">{{ createdAtText }}</div>
      <div class="post-stats">浏览 {{ post.view_count }}</div>
    </div>
    <el-tag v-if="post.is_pinned" size="small" type="warning" class="pin-badge">置顶</el-tag>

    <div v-if="post.content" class="post-content">{{ post.content }}</div>

    <div v-if="post.media_url" class="post-media">
      <img
        v-if="post.media_type === 'image'"
        :src="post.media_url"
        alt=""
        loading="lazy"
        style="aspect-ratio:16/9;object-fit:cover"
      />
      <video
        v-else-if="post.media_type === 'video'"
        :src="post.media_url"
        controls
        playsinline
        @click.stop
      ></video>
      <div v-else-if="post.media_type === 'audio'" class="audio-wrapper" @click.stop>
        <div class="audio-info">
          <el-icon :size="20"><Headset /></el-icon>
          <span class="audio-name">音频</span>
        </div>
        <audio class="audio-player" :src="post.media_url" controls preload="metadata"></audio>
      </div>
      <a v-else :href="post.media_url" target="_blank" rel="noreferrer" class="file-link" @click.stop>
        <el-icon :size="18"><Download /></el-icon>
        <span>{{ getFileName(post.media_url) }}</span>
      </a>
    </div>

    <div v-if="post.media_items?.length" class="post-media-grid">
      <div v-for="m in post.media_items" :key="m.id" class="media-cell" @click.stop>
        <img
          v-if="m.media_type === 'image'"
          :src="m.file_url"
          alt=""
          loading="lazy"
          style="aspect-ratio:16/9;object-fit:cover"
        />
        <video
          v-else-if="m.media_type === 'video'"
          :src="m.file_url"
          controls
          playsinline
        ></video>
        <div v-else-if="m.media_type === 'audio'" class="audio-wrapper">
          <div class="audio-info">
            <el-icon :size="20"><Headset /></el-icon>
            <span class="audio-name">音频</span>
          </div>
          <audio class="audio-player" :src="m.file_url" controls preload="metadata"></audio>
        </div>
        <a v-else :href="m.file_url" target="_blank" rel="noreferrer" class="file-link">
          <el-icon :size="18"><Download /></el-icon>
          <span>{{ getFileName(m.file_url) }}</span>
        </a>
      </div>
    </div>

    <div class="post-actions">
      <span class="stat-item">
        <el-icon :size="14"><Star /></el-icon>
        {{ post.like_count }}
      </span>
      <span class="stat-item">
        <el-icon :size="14"><ChatLineRound /></el-icon>
        {{ post.comment_count }}
      </span>
    </div>
  </article>
</template>

<style scoped>
.post-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: border-color .2s, box-shadow .25s, transform .25s;
  content-visibility: auto;
  contain-intrinsic-size: auto 180px;
}

.post-card:hover {
  border-color: var(--accent-border);
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
  will-change: transform;
}

.post-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: var(--text-3);
  font-size: 13px;
}

.pin-badge {
  margin-top: 8px;
}

.post-content {
  margin-top: 10px;
  white-space: pre-wrap;
  line-height: 1.65;
  color: var(--text-1);
}

.post-media {
  margin-top: 12px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border);
  background: #f5f6f8;
}

.post-media img,
.post-media video {
  display: block;
  width: 100%;
  height: auto;
}

.audio-wrapper {
  background: #f2f3f5;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.audio-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-2);
  font-size: 13px;
  font-weight: 500;
}

.audio-player {
  width: 100%;
  height: 40px;
  border-radius: 6px;
}

.file-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  background: var(--primary-light);
  color: var(--primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-sm);
}

.file-link:hover {
  opacity: .8;
}

.post-actions {
  display: flex;
  gap: 16px;
  margin-top: 10px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-3);
}

.post-media-grid {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}

.media-cell img,
.media-cell video {
  display: block;
  width: 100%;
  border-radius: var(--radius-sm);
  max-height: 400px;
  object-fit: cover;
}

.media-cell .audio-wrapper {
  margin-top: 0;
}
</style>
