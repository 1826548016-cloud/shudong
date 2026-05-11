<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

import { http } from '../api/http'
import { replyComment } from '../api/inbox'

type Post = {
  id: number
  content: string
  media_url: string | null
  media_type: 'none' | 'image' | 'video'
  view_count: number
  like_count: number
  comment_count: number
  created_at: string
  updated_at: string
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

const route = useRoute()
const isAuthed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const loading = ref(false)
const post = ref<Post | null>(null)
const comments = ref<Comment[]>([])

const replyingId = ref<number | null>(null)
const replyText = ref('')
const replySaving = ref(false)

async function load() {
  const id = Number(route.params.id)
  if (!id) return

  loading.value = true
  try {
    const postRes = await http.get<Post>(`/api/posts/${id}/`)
    post.value = postRes.data
    const { data } = await http.get<Comment[]>(`/api/posts/${id}/comments/`)
    comments.value = data
    await nextTick()
    const target = route.query.comment ? Number(route.query.comment) : null
    if (target) {
      const el = document.getElementById(`comment-${target}`)
      if (el) {
        el.scrollIntoView({ block: 'center' })
        el.classList.add('flash')
        window.setTimeout(() => el.classList.remove('flash'), 1200)
      }
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function startReply(c: Comment) {
  replyingId.value = c.id
  replyText.value = ''
}

async function submitReply() {
  if (!replyingId.value) return
  replySaving.value = true
  try {
    await replyComment(replyingId.value, replyText.value.trim())
    ElMessage.success('已回复')
    window.dispatchEvent(new Event('treehole-unread-refresh'))
    replyingId.value = null
    replyText.value = ''
    await load()
  } catch (e) {
    ElMessage.error('回复失败')
  } finally {
    replySaving.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <el-skeleton v-if="loading" :rows="10" animated />
    <template v-else>
      <div v-if="post" class="post-card">
        <div class="post-meta">
          <div class="time">{{ new Date(post.created_at).toLocaleString() }}</div>
          <div class="stats">
            浏览 {{ post.view_count }} · 点赞 {{ post.like_count }} · 评论 {{ post.comment_count }}
          </div>
        </div>
        <div v-if="post.content" class="content">{{ post.content }}</div>
        <div v-if="post.media_url" class="media">
          <img v-if="post.media_type === 'image'" :src="post.media_url" alt="" />
          <video v-else-if="post.media_type === 'video'" :src="post.media_url" controls></video>
          <a v-else :href="post.media_url" target="_blank" rel="noreferrer">查看附件</a>
        </div>
      </div>

      <div class="title">评论</div>
      <div class="comment-list">
        <div v-for="c in comments" :key="c.id" :id="`comment-${c.id}`" class="comment-item">
          <div class="comment-head">
            <div class="name">{{ c.nickname || '匿名' }}</div>
            <div class="time">{{ new Date(c.created_at).toLocaleString() }}</div>
          </div>
          <div class="comment-content">{{ c.content }}</div>

          <div v-if="c.admin_reply" class="reply-box">
            <div class="reply-title">管理员回复</div>
            <div class="reply-content">{{ c.admin_reply }}</div>
          </div>

          <div v-if="isAuthed" class="admin-actions">
            <el-button text @click="startReply(c)">回复</el-button>
          </div>

          <div v-if="isAuthed && replyingId === c.id" class="reply-editor">
            <el-input
              v-model="replyText"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              placeholder="写下管理员回复…"
            />
            <div class="row">
              <el-button @click="replyingId = null">取消</el-button>
              <el-button type="primary" :loading="replySaving" @click="submitReply">提交</el-button>
            </div>
          </div>
        </div>
        <div v-if="comments.length === 0" class="empty">暂无评论</div>
      </div>
    </template>
  </section>
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

.content {
  margin-top: 10px;
  white-space: pre-wrap;
  line-height: 1.65;
  color: var(--text-1);
}

.media {
  margin-top: 12px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: #000;
}

.media img,
.media video {
  display: block;
  width: 100%;
  height: auto;
}

.title {
  margin: 14px 0 10px;
  font-size: 16px;
  font-weight: 900;
  color: var(--text-1);
}

.comment-list {
  display: grid;
  gap: 12px;
}

.comment-item {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
  background: var(--card-bg);
}

.comment-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-3);
  font-size: 12px;
}

.comment-content {
  margin-top: 6px;
  white-space: pre-wrap;
  line-height: 1.6;
  color: var(--text-1);
}

.reply-box {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px dashed var(--border);
}

.reply-title {
  font-size: 12px;
  color: var(--text-3);
}

.reply-content {
  margin-top: 4px;
  color: var(--text-1);
  white-space: pre-wrap;
  line-height: 1.6;
}

.admin-actions {
  margin-top: 8px;
}

.reply-editor {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}

.row {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.empty {
  text-align: center;
  padding: 30px 0;
  color: var(--text-3);
  font-size: 14px;
}

.flash {
  outline: 2px solid rgba(22, 100, 255, 0.35);
  outline-offset: 2px;
  border-radius: 12px;
}
</style>
