<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChatLineRound, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { http } from '../api/http'

type Post = {
  id: number
  content: string
  media_url: string | null
  media_type: 'none' | 'image' | 'video'
  view_count: number
  like_count: number
  comment_count: number
  created_at: string
}

type Comment = {
  id: number
  post: number
  nickname: string
  content: string
  admin_reply: string
  replied_at: string | null
  created_at: string
}

const props = defineProps<{
  post: Post
}>()

const postState = ref<Post>({ ...props.post })

watch(
  () => props.post,
  (next) => {
    postState.value = { ...next }
  },
)

const createdAtText = computed(() => {
  const d = new Date(postState.value.created_at)
  if (Number.isNaN(d.getTime())) return postState.value.created_at
  return d.toLocaleString()
})

const drawerOpen = ref(false)
const commentsLoading = ref(false)
const comments = ref<Comment[]>([])
const nickname = ref('')
const commentText = ref('')

async function openComments() {
  drawerOpen.value = true
}

async function loadComments() {
  commentsLoading.value = true
  try {
    await http.post(`/api/posts/${postState.value.id}/view/`)
    const { data } = await http.get<Comment[]>(
      `/api/posts/${postState.value.id}/comments/`,
    )
    comments.value = data
    const postRes = await http.get<Post>(`/api/posts/${postState.value.id}/`)
    postState.value.view_count = postRes.data.view_count
    postState.value.comment_count = postRes.data.comment_count
  } catch (e) {
    ElMessage.error('加载评论失败')
  } finally {
    commentsLoading.value = false
  }
}

watch(drawerOpen, (open) => {
  if (open) void loadComments()
})

async function like() {
  try {
    const { data } = await http.post<{ like_count: number }>(
      `/api/posts/${postState.value.id}/like/`,
    )
    postState.value.like_count = data.like_count
  } catch (e) {
    ElMessage.error('点赞失败')
  }
}

async function submitComment() {
  const content = commentText.value.trim()
  if (!content) return

  try {
    await http.post(`/api/posts/${postState.value.id}/comments/`, {
      nickname: nickname.value.trim(),
      content,
    })
    commentText.value = ''
    await loadComments()
  } catch (e) {
    ElMessage.error('发表评论失败')
  }
}
</script>

<template>
  <article class="post-card">
    <div class="post-meta">
      <div class="post-time">{{ createdAtText }}</div>
      <div class="post-stats">浏览 {{ postState.view_count }}</div>
    </div>

    <div v-if="postState.content" class="post-content">{{ postState.content }}</div>

    <div v-if="postState.media_url" class="post-media">
      <img
        v-if="postState.media_type === 'image'"
        :src="postState.media_url"
        alt=""
        loading="lazy"
      />
      <video
        v-else-if="postState.media_type === 'video'"
        :src="postState.media_url"
        controls
        playsinline
      ></video>
      <a v-else :href="postState.media_url" target="_blank" rel="noreferrer">
        查看附件
      </a>
    </div>

    <div class="post-actions">
      <el-button :icon="Star" text @click="like">点赞 {{ postState.like_count }}</el-button>
      <el-button :icon="ChatLineRound" text @click="openComments">
        评论 {{ postState.comment_count }}
      </el-button>
    </div>

    <el-drawer v-model="drawerOpen" title="评论" size="420px">
      <div class="comment-box">
        <el-input v-model="nickname" placeholder="留下一个让ta知道你的昵称！" maxlength="32" />
        <el-input
          v-model="commentText"
          type="textarea"
          :rows="3"
          placeholder="写下你的想法…"
          maxlength="500"
          show-word-limit
        />
        <el-button type="primary" @click="submitComment">发布</el-button>
      </div>

      <el-divider />

      <el-skeleton v-if="commentsLoading" :rows="6" animated />
      <div v-else class="comment-list">
        <div v-for="c in comments" :key="c.id" class="comment-item">
          <div class="comment-head">
            <div class="comment-name">{{ c.nickname || '匿名' }}</div>
            <div class="comment-time">{{ new Date(c.created_at).toLocaleString() }}</div>
          </div>
          <div class="comment-content">{{ c.content }}</div>
          <div v-if="c.admin_reply" class="admin-reply">
            <div class="admin-reply-title">管理员回复</div>
            <div class="admin-reply-content">{{ c.admin_reply }}</div>
          </div>
        </div>
      </div>
    </el-drawer>
  </article>
</template>

<style scoped>
.post-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow-1);
}

.post-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  color: var(--text-3);
  font-size: 13px;
}

.post-content {
  margin-top: 10px;
  white-space: pre-wrap;
  line-height: 1.65;
  color: var(--text-1);
}

.post-media {
  margin-top: 12px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: #000;
}

.post-media img,
.post-media video {
  display: block;
  width: 100%;
  height: auto;
}

.post-actions {
  display: flex;
  gap: 12px;
  margin-top: 10px;
}

.comment-box {
  display: grid;
  gap: 10px;
}

.comment-list {
  display: grid;
  gap: 12px;
}

.comment-item {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px;
  background: var(--card-bg);
}

.comment-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-3);
  font-size: 12px;
}

.comment-name {
  color: var(--text-2);
  font-weight: 600;
}

.comment-content {
  margin-top: 6px;
  white-space: pre-wrap;
  line-height: 1.6;
  color: var(--text-1);
}

.admin-reply {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px dashed var(--border);
}

.admin-reply-title {
  font-size: 12px;
  color: var(--text-3);
}

.admin-reply-content {
  margin-top: 4px;
  color: var(--text-1);
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
