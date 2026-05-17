<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ChatLineRound, Delete, Download, Edit, Headset, Sort, Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { http } from '../api/http'
import { replyComment } from '../api/inbox'
import CommentBody from '../components/CommentBody.vue'
import { usePlayer } from '../composables/usePlayer'

type Post = {
  id: number
  content: string
  media_url: string | null
  media_type: 'none' | 'image' | 'video' | 'audio'
  media_items: { id: number; file_url: string; media_type: string }[]
  view_count: number
  like_count: number
  comment_count: number
  is_pinned: boolean
  created_at: string
  updated_at: string
}

type Comment = {
  id: number
  post: number
  parent: number | null
  nickname: string
  content: string
  admin_reply: string
  replied_at: string | null
  replies: Comment[]
  created_at: string
}

const route = useRoute()
const router = useRouter()
const isAuthed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const loading = ref(false)
const post = ref<Post | null>(null)
const comments = ref<Comment[]>([])

const editing = ref(false)
const editContent = ref('')
const editSaving = ref(false)
const editFiles = ref<File[]>([])
const editFileInput = ref<HTMLInputElement | null>(null)
const deleteMediaLoading = ref<number | null>(null)

const replyingId = ref<number | null>(null)
const replyText = ref('')
const replySaving = ref(false)

const commentNickname = ref('')
const commentText = ref('')
const commentSaving = ref(false)

const deleteCommentLoading = ref<number | null>(null)

const { pauseForMedia, resumeAfterMedia } = usePlayer()
const mediaPlaying = ref(false)

function onMediaPlay() {
  mediaPlaying.value = true
  pauseForMedia()
}

function onMediaPause() {
  mediaPlaying.value = false
  window.setTimeout(() => {
    if (!mediaPlaying.value) resumeAfterMedia()
  }, 500)
}

const rootComments = computed(() => comments.value.filter(c => c.parent === null))

function getAllCommentCount(): number {
  function countReplies(list: Comment[]): number {
    let total = list.length
    for (const c of list) {
      if (c.replies && c.replies.length) {
        total += countReplies(c.replies)
      }
    }
    return total
  }
  return countReplies(comments.value)
}

async function load() {
  const id = Number(route.params.id)
  if (!id) return

  loading.value = true
  try {
    const postRes = await http.get<Post>(`/api/posts/${id}/`)
    post.value = postRes.data
    await loadComments()
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

async function loadComments() {
  if (!post.value) return
  try {
    const { data } = await http.get<Comment[]>(`/api/posts/${post.value.id}/comments/`)
    comments.value = data
    const postRes = await http.get<Post>(`/api/posts/${post.value.id}/`)
    post.value.view_count = postRes.data.view_count
    post.value.comment_count = postRes.data.comment_count
    post.value.like_count = postRes.data.like_count
  } catch (e) {
    ElMessage.error('加载评论失败')
  }
}

async function like() {
  if (!post.value) return
  try {
    const { data } = await http.post<{ like_count: number }>(
      `/api/posts/${post.value.id}/like/`,
    )
    post.value.like_count = data.like_count
  } catch (e) {
    ElMessage.error('点赞失败')
  }
}

async function submitComment() {
  if (!post.value) return
  const content = commentText.value.trim()
  if (!content) return
  commentSaving.value = true
  try {
    await http.post(`/api/posts/${post.value.id}/comments/`, {
      nickname: commentNickname.value.trim(),
      content,
    })
    commentText.value = ''
    await loadComments()
  } catch (e) {
    ElMessage.error('发表评论失败')
  } finally {
    commentSaving.value = false
  }
}

function startReply(c: Comment) {
  replyingId.value = c.id
  replyText.value = ''
}

async function submitReplyTo() {
  if (!post.value || !replyingId.value) return
  const content = replyText.value.trim()
  if (!content) return
  replySaving.value = true
  try {
    await http.post(`/api/posts/${post.value.id}/comments/`, {
      nickname: commentNickname.value.trim() || undefined,
      content,
      parent: replyingId.value,
    })
    replyText.value = ''
    replyingId.value = null
    await loadComments()
  } catch (e) {
    ElMessage.error('回复失败')
  } finally {
    replySaving.value = false
  }
}

async function submitAdminReply() {
  if (!replyingId.value) return
  replySaving.value = true
  try {
    await replyComment(replyingId.value, replyText.value.trim())
    ElMessage.success('已回复')
    window.dispatchEvent(new Event('treehole-unread-refresh'))
    replyingId.value = null
    replyText.value = ''
    await loadComments()
  } catch (e) {
    ElMessage.error('回复失败')
  } finally {
    replySaving.value = false
  }
}

function goBack() {
  window.history.back()
}

async function togglePin() {
  if (!post.value) return
  try {
    const { data } = await http.post<{ is_pinned: boolean }>(`/api/posts/${post.value.id}/pin/`)
    post.value.is_pinned = data.is_pinned
    ElMessage.success(data.is_pinned ? '已置顶' : '已取消置顶')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function startEdit() {
  if (!post.value) return
  editContent.value = post.value.content
  editFiles.value = []
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  editContent.value = ''
  editFiles.value = []
}

function handleEditFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  for (const f of input.files) {
    editFiles.value.push(f)
  }
  input.value = ''
}

function removeEditFile(index: number) {
  editFiles.value.splice(index, 1)
}

async function deletePostMedia(mediaId: number) {
  if (!post.value) return
  deleteMediaLoading.value = mediaId
  try {
    await http.delete(`/api/posts/${post.value.id}/media/${mediaId}/`)
    if (post.value.media_items) {
      post.value.media_items = post.value.media_items.filter(m => m.id !== mediaId)
    }
    ElMessage.success('已删除文件')
  } catch (e) {
    ElMessage.error('删除文件失败')
  } finally {
    deleteMediaLoading.value = null
  }
}

async function saveEdit() {
  if (!post.value) return
  editSaving.value = true
  try {
    const formData = new FormData()
    formData.append('content', editContent.value.trim())
    if (editFiles.value.length > 0) {
      for (const f of editFiles.value) {
        formData.append('files', f)
      }
    }
    const { data } = await http.patch<Post>(`/api/posts/${post.value.id}/`, formData)
    post.value = data
    editing.value = false
    editFiles.value = []
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    editSaving.value = false
  }
}

async function deletePost() {
  if (!post.value) return
  try {
    await ElMessageBox.confirm('确定要删除这条动态吗？删除后不可恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await http.delete(`/api/posts/${post.value.id}/`)
    ElMessage.success('已删除')
    await router.push('/')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function deleteComment(id: number) {
  deleteCommentLoading.value = id
  try {
    await http.delete(`/api/comments/${id}/`)
    ElMessage.success('评论已删除')
    await loadComments()
  } catch (e) {
    ElMessage.error('删除评论失败')
  } finally {
    deleteCommentLoading.value = null
  }
}

function getFileName(url: string): string {
  const parts = url.split('/')
  return parts[parts.length - 1] || '附件'
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <div class="bg-overlay"></div>
    <div class="page-content">

    <el-button text :icon="ArrowLeft" class="back-btn" @click="goBack">返回</el-button>

    <el-skeleton v-if="loading" :rows="10" animated />
    <template v-else>
      <div v-if="post" class="post-card">
        <div class="post-meta">
          <div class="time">{{ new Date(post.created_at).toLocaleString() }}</div>
          <div class="stats">
            浏览 {{ post.view_count }} · 点赞 {{ post.like_count }} · 评论 {{ getAllCommentCount() }}
          </div>
        </div>
        <el-tag v-if="post.is_pinned" size="small" type="warning" class="pin-badge">置顶</el-tag>

        <div v-if="post.content" class="content">{{ post.content }}</div>

        <div v-if="post.media_url" class="media">
          <img v-if="post.media_type === 'image'" :src="post.media_url" alt="" loading="lazy" style="aspect-ratio:16/9;object-fit:cover" />
          <video v-else-if="post.media_type === 'video'" :src="post.media_url" controls playsinline @play="onMediaPlay" @pause="onMediaPause"></video>
          <div v-else-if="post.media_type === 'audio'" class="audio-wrapper">
            <div class="audio-info">
              <el-icon :size="24"><Headset /></el-icon>
              <span class="audio-name">音频</span>
            </div>
            <audio class="audio-player" :src="post.media_url" controls preload="metadata" @play="onMediaPlay" @pause="onMediaPause"></audio>
          </div>
          <a v-else :href="post.media_url" target="_blank" rel="noreferrer" class="file-link">
            <el-icon :size="20"><Download /></el-icon>
            <span>{{ getFileName(post.media_url) }}</span>
          </a>
        </div>

        <div v-if="post.media_items?.length" class="media-grid">
          <div v-for="m in post.media_items" :key="m.id" class="media-cell">
            <img v-if="m.media_type === 'image'" :src="m.file_url" alt="" loading="lazy" style="aspect-ratio:16/9;object-fit:cover" />
            <video v-else-if="m.media_type === 'video'" :src="m.file_url" controls playsinline @play="onMediaPlay" @pause="onMediaPause"></video>
            <div v-else-if="m.media_type === 'audio'" class="audio-wrapper">
              <div class="audio-info">
                <el-icon :size="24"><Headset /></el-icon>
                <span class="audio-name">音频</span>
              </div>
              <audio class="audio-player" :src="m.file_url" controls preload="metadata" @play="onMediaPlay" @pause="onMediaPause"></audio>
            </div>
            <a v-else :href="m.file_url" target="_blank" rel="noreferrer" class="file-link">
              <el-icon :size="20"><Download /></el-icon>
              <span>{{ getFileName(m.file_url) }}</span>
            </a>
          </div>
        </div>

        <div class="post-actions">
          <el-button :icon="Star" text @click="like">点赞 {{ post.like_count }}</el-button>
          <el-button :icon="ChatLineRound" text>评论 {{ post.comment_count }}</el-button>
        </div>

        <div v-if="isAuthed" class="admin-bar">
          <el-button :icon="Edit" text size="small" @click="startEdit">编辑</el-button>
          <el-button :icon="Sort" text size="small" :type="post.is_pinned ? 'warning' : ''" @click="togglePin">
            {{ post.is_pinned ? '取消置顶' : '置顶' }}
          </el-button>
          <el-button :icon="Delete" text size="small" type="danger" @click="deletePost">删除</el-button>
        </div>

        <div v-if="editing" class="edit-area">
          <el-input
            v-model="editContent"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
          />
          <div v-if="post.media_items?.length" class="edit-media-list">
            <div v-for="m in post.media_items" :key="m.id" class="edit-media-row">
              <span class="edit-media-name">{{ getFileName(m.file_url) }}</span>
              <el-button
                :icon="Delete"
                size="small"
                type="danger"
                circle
                :loading="deleteMediaLoading === m.id"
                @click="deletePostMedia(m.id)"
              />
            </div>
          </div>
          <div class="edit-file-row">
            <input
              ref="editFileInput"
              type="file"
              multiple
              accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar,.7z,.txt"
              style="display:none"
              @change="handleEditFileSelect"
            />
            <el-button size="small" @click="editFileInput!.click()">+ 添加文件</el-button>
            <el-tag
              v-for="(f, i) in editFiles"
              :key="i"
              size="small"
              closable
              @close="removeEditFile(i)"
            >
              {{ f.name }}
            </el-tag>
          </div>
          <div class="edit-actions">
            <el-button @click="cancelEdit">取消</el-button>
            <el-button type="primary" :loading="editSaving" @click="saveEdit">保存</el-button>
          </div>
        </div>
      </div>

      <div class="comment-section">
        <div class="comment-write">
          <el-input v-model="commentNickname" placeholder="昵称（选填）" maxlength="32" />
          <el-input
            v-model="commentText"
            type="textarea"
            :rows="3"
            placeholder="写下你的想法…"
            maxlength="500"
            show-word-limit
          />
          <el-button type="primary" :loading="commentSaving" @click="submitComment">发布评论</el-button>
        </div>

        <div class="title">评论（{{ getAllCommentCount() }}）</div>
        <div class="comment-list">
          <div v-for="c in rootComments" :key="c.id" :id="`comment-${c.id}`" class="comment-item">
            <CommentBody
              :comment="c"
              :replying-id="replyingId"
              :reply-text="replyText"
              :reply-saving="replySaving"
              :is-authed="isAuthed"
              :comment-nickname="commentNickname"
              :deleting-id="deleteCommentLoading"
              @start-reply="startReply"
              @update:reply-text="replyText = $event"
              @submit-reply-to="submitReplyTo"
              @submit-admin-reply="submitAdminReply"
              @cancel-reply="replyingId = null"
              @delete-comment="deleteComment"
            />
            <div v-for="r in c.replies" :key="r.id" :id="`comment-${r.id}`" class="comment-reply">
              <CommentBody
                :comment="r"
                :replying-id="replyingId"
                :reply-text="replyText"
                :reply-saving="replySaving"
                :is-authed="isAuthed"
                :comment-nickname="commentNickname"
                :is-nested="true"
                :deleting-id="deleteCommentLoading"
                @start-reply="startReply"
                @update:reply-text="replyText = $event"
                @submit-reply-to="submitReplyTo"
                @submit-admin-reply="submitAdminReply"
                @cancel-reply="replyingId = null"
                @delete-comment="deleteComment"
              />
              <div v-for="rr in r.replies" :key="rr.id" :id="`comment-${rr.id}`" class="comment-reply-nested">
                <CommentBody
                  :comment="rr"
                  :replying-id="replyingId"
                  :reply-text="replyText"
                  :reply-saving="replySaving"
                  :is-authed="isAuthed"
                  :comment-nickname="commentNickname"
                  :is-nested="true"
                  :deleting-id="deleteCommentLoading"
                  @start-reply="startReply"
                  @update:reply-text="replyText = $event"
                  @submit-reply-to="submitReplyTo"
                  @submit-admin-reply="submitAdminReply"
                  @cancel-reply="replyingId = null"
                  @delete-comment="deleteComment"
                />
              </div>
            </div>
          </div>
          <div v-if="rootComments.length === 0" class="empty">暂无评论，来说点什么吧</div>
        </div>
      </div>
    </template>
    </div>
  </section>
</template>

<style scoped>
.page {
  position: relative;
  min-height: 100vh;
}

.bg-image {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  pointer-events: none;
}

.bg-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1;
  background: rgba(0, 0, 0, 0.08);
  pointer-events: none;
}

.page-content {
  position: relative;
  z-index: 2;
  max-width: 720px;
  margin: 0 auto;
}

.back-btn {
  margin-bottom: 10px;
  color: #fff;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.post-card {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
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

.content {
  margin-top: 14px;
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--text-1);
  font-size: 15px;
}

.media {
  margin-top: 14px;
  border-radius: 12px;
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

.audio-wrapper {
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-radius: 12px;
}

.audio-info {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-2);
  font-size: 15px;
  font-weight: 500;
}

.audio-player {
  width: 100%;
  height: 44px;
  border-radius: 8px;
}

.file-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--primary);
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: background 0.3s, box-shadow 0.3s;
}

.file-link:hover {
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.media-grid {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.media-cell img,
.media-cell video {
  display: block;
  width: 100%;
  border-radius: 12px;
  max-height: 500px;
  object-fit: cover;
}

.media-cell .audio-wrapper {
  margin-top: 0;
}

.post-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}

.admin-bar {
  display: flex;
  gap: 4px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.edit-area {
  margin-top: 14px;
  display: grid;
  gap: 10px;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.edit-media-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.edit-media-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 10px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.edit-media-name {
  font-size: 13px;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-file-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.comment-section {
  margin-top: 20px;
}

.comment-write {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius);
  padding: 16px;
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
}

.title {
  font-size: 16px;
  font-weight: 900;
  color: #fff;
  margin-bottom: 10px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.comment-list {
  display: grid;
  gap: 12px;
}

.comment-item {
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 12px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.3s, transform 0.3s;
}

.comment-item:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
}

.comment-reply {
  margin: 8px 0 0 20px;
  padding: 12px 14px;
  border-left: 2px solid rgba(0, 0, 0, 0.08);
  border-radius: 0 10px 10px 0;
  background: rgba(255, 255, 255, 0.45);
}

.comment-reply-nested {
  margin: 6px 0 0 20px;
  padding: 10px 12px;
  border-left: 2px solid rgba(0, 0, 0, 0.05);
  border-radius: 0 8px 8px 0;
  background: rgba(255, 255, 255, 0.3);
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
