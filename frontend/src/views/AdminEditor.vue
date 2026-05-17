<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Delete, Edit, Sort, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { http } from '../api/http'

type PostMedia = {
  id: number
  file_url: string
  media_type: 'image' | 'video' | 'audio' | 'file'
}

type Post = {
  id: number
  content: string
  media_url: string | null
  media_type: 'none' | 'image' | 'video' | 'audio'
  media_items: PostMedia[]
  view_count: number
  like_count: number
  comment_count: number
  is_pinned: boolean
  created_at: string
  updated_at: string
}

const router = useRouter()

const authed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const createForm = reactive<{
  content: string
  files: File[]
}>({
  content: '',
  files: [],
})

const posts = ref<Post[]>([])
const loading = ref(false)
const saving = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)
const editFileInput = ref<HTMLInputElement | null>(null)

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  for (const f of input.files) {
    if (!createForm.files.some(ex => ex.name === f.name && ex.size === f.size)) {
      createForm.files.push(f)
    }
  }
  input.value = ''
}

function removeCreateFile(index: number) {
  createForm.files.splice(index, 1)
}

async function loadPosts() {
  loading.value = true
  try {
    const { data } = await http.get<Post[]>('/api/posts/')
    posts.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function createPost() {
  const content = createForm.content.trim()
  if (!content && createForm.files.length === 0) return

  saving.value = true
  try {
    const formData = new FormData()
    formData.append('content', content)
    for (const f of createForm.files) {
      formData.append('files', f)
    }

    await http.post('/api/posts/', formData)
    createForm.content = ''
    createForm.files = []
    ElMessage.success('发布成功')
    await loadPosts()
  } catch (e) {
    ElMessage.error('发布失败（需要管理员账号）')
  } finally {
    saving.value = false
  }
}

async function deletePost(id: number) {
  try {
    await http.delete(`/api/posts/${id}/`)
    ElMessage.success('已删除')
    await loadPosts()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function togglePin(p: Post) {
  try {
    const { data } = await http.post<{ is_pinned: boolean }>(`/api/posts/${p.id}/pin/`)
    ElMessage.success(data.is_pinned ? '已置顶' : '已取消置顶')
    await loadPosts()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const editOpen = ref(false)
const editSaving = ref(false)
const editForm = reactive<{
  id: number | null
  content: string
  replaceFiles: File[]
}>({
  id: null,
  content: '',
  replaceFiles: [],
})
const editPost = ref<Post | null>(null)
const deleteMediaLoading = ref<number | null>(null)

function openEdit(p: Post) {
  editPost.value = p
  editForm.id = p.id
  editForm.content = p.content
  editForm.replaceFiles = []
  editOpen.value = true
}

function handleEditFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  for (const f of input.files) {
    editForm.replaceFiles.push(f)
  }
  input.value = ''
}

function removeEditFile(index: number) {
  editForm.replaceFiles.splice(index, 1)
}

async function deletePostMedia(mediaId: number) {
  if (!editForm.id) return
  deleteMediaLoading.value = mediaId
  try {
    await http.delete(`/api/posts/${editForm.id}/media/${mediaId}/`)
    if (editPost.value?.media_items) {
      editPost.value.media_items = editPost.value.media_items.filter(m => m.id !== mediaId)
    }
    ElMessage.success('已删除文件')
  } catch (e) {
    ElMessage.error('删除文件失败')
  } finally {
    deleteMediaLoading.value = null
  }
}

async function saveEdit() {
  if (!editForm.id) return
  editSaving.value = true
  try {
    const formData = new FormData()
    formData.append('content', editForm.content.trim())
    if (editForm.replaceFiles.length > 0) {
      for (const f of editForm.replaceFiles) {
        formData.append('files', f)
      }
    }
    await http.patch(`/api/posts/${editForm.id}/`, formData)
    ElMessage.success('已保存')
    editOpen.value = false
    editForm.replaceFiles = []
    await loadPosts()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    editSaving.value = false
  }
}

function typeIcon(mt: string): string {
  if (mt === 'image') return '🖼️'
  if (mt === 'video') return '🎬'
  if (mt === 'audio') return '🎵'
  return '📄'
}

function mediaCount(p: Post): string {
  const n = p.media_items?.length ?? (p.media_url ? 1 : 0)
  if (n === 0) return ''
  return ` (${n}个附件)`
}

onMounted(async () => {
  if (!authed.value) {
    await router.push('/admin/login')
    return
  }
  await loadPosts()
})
</script>

<template>
  <section class="page">
    <div class="editor-card">
      <div class="title">发布动态</div>
      <el-input
        v-model="createForm.content"
        type="textarea"
        :rows="4"
        maxlength="2000"
        show-word-limit
        placeholder="写点什么…"
      />

      <div class="row">
        <div class="file-bar">
          <input
            ref="fileInput"
            type="file"
            multiple
            accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar,.7z,.txt"
            style="display:none"
            @change="handleFileSelect"
          />
          <el-button :icon="Plus" @click="fileInput!.click()">
            添加文件
          </el-button>
          <div v-if="createForm.files.length" class="file-tags">
            <el-tag
              v-for="(f, i) in createForm.files"
              :key="i"
              closable
              size="small"
              @close="removeCreateFile(i)"
            >
              {{ typeIcon(f.type) }} {{ f.name }}
            </el-tag>
          </div>
        </div>
        <el-button type="primary" :loading="saving" @click="createPost">
          发布
        </el-button>
      </div>
    </div>

    <div class="list-head">
      <div class="title">内容管理</div>
      <el-button :loading="loading" @click="loadPosts">刷新</el-button>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />
    <div v-else class="post-list">
      <div v-for="p in posts" :key="p.id" class="post-row">
        <div class="post-main">
          <div class="post-id">#{{ p.id }}{{ mediaCount(p) }}</div>
          <div class="post-text">{{ p.content || '（无文字）' }}</div>
          <div v-if="p.media_items?.length" class="post-media-icons">
            <span v-for="m in p.media_items" :key="m.id" class="media-icon" :title="m.file_url">
              {{ typeIcon(m.media_type) }}
            </span>
          </div>
          <el-tag v-if="p.is_pinned" size="small" type="warning" class="pin-tag">置顶</el-tag>
        </div>
        <div class="post-actions">
          <el-button :icon="Sort" text :type="p.is_pinned ? 'warning' : ''" @click="togglePin(p)">
            {{ p.is_pinned ? '取消置顶' : '置顶' }}
          </el-button>
          <el-button :icon="Edit" text @click="openEdit(p)">编辑</el-button>
          <el-button :icon="Delete" text type="danger" @click="deletePost(p.id)">
            删除
          </el-button>
        </div>
      </div>
      <div v-if="posts.length === 0" class="empty">暂无内容</div>
    </div>

    <el-dialog v-model="editOpen" title="编辑动态" width="520px">
      <div class="dialog-body">
        <el-input
          v-model="editForm.content"
          type="textarea"
          :rows="4"
          maxlength="2000"
          show-word-limit
        />
        <div v-if="editPost?.media_items?.length" class="dialog-media-list">
          <div class="dialog-media-title">已有文件：</div>
          <div v-for="m in editPost!.media_items" :key="m.id" class="dialog-media-row">
            <span class="dialog-media-name">{{ m.file_url.split('/').pop() }}</span>
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
        <div class="row">
          <div class="file-bar">
            <input
              ref="editFileInput"
              type="file"
              multiple
              accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar,.7z,.txt"
              style="display:none"
              @change="handleEditFileSelect"
            />
            <el-button :icon="Plus" @click="editFileInput!.click()">
              替换/新增文件
            </el-button>
            <div v-if="editForm.replaceFiles.length" class="file-tags">
              <el-tag
                v-for="(f, i) in editForm.replaceFiles"
                :key="i"
                closable
                size="small"
                @close="removeEditFile(i)"
              >
                {{ typeIcon(f.type) }} {{ f.name }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="editOpen = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="saveEdit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.editor-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow-1);
}

.title {
  font-size: 16px;
  font-weight: 800;
  color: var(--text-1);
  margin-bottom: 10px;
}

.row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 10px;
  margin-top: 10px;
}

.file-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.file-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.list-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 16px 0 10px;
}

.post-list {
  display: grid;
  gap: 10px;
}

.post-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--card-bg);
}

.post-main {
  min-width: 0;
  flex: 1;
}

.pin-tag {
  margin-left: 4px;
  vertical-align: middle;
}

.post-id {
  font-size: 12px;
  color: var(--text-3);
}

.post-text {
  margin-top: 4px;
  color: var(--text-1);
  font-size: 14px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.post-media-icons {
  margin-top: 6px;
  display: flex;
  gap: 4px;
}

.media-icon {
  font-size: 14px;
  cursor: default;
}

.post-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.empty {
  text-align: center;
  padding: 30px 0;
  color: var(--text-3);
  font-size: 14px;
}

.dialog-body {
  display: grid;
  gap: 10px;
}

.dialog-media-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dialog-media-title {
  font-size: 12px;
  color: var(--text-3);
  font-weight: 500;
}

.dialog-media-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 10px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.dialog-media-name {
  font-size: 13px;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
