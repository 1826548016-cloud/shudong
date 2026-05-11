<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, type UploadFile } from 'element-plus'

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
  updated_at: string
}

const router = useRouter()

const authed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const createForm = reactive<{
  content: string
  media_type: 'none' | 'image' | 'video'
  file: File | null
}>({
  content: '',
  media_type: 'none',
  file: null,
})

const posts = ref<Post[]>([])
const loading = ref(false)
const saving = ref(false)

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

function onFileChange(uploadFile: UploadFile) {
  createForm.file = (uploadFile.raw as File) ?? null
}

function onFileRemove() {
  createForm.file = null
}

async function createPost() {
  const content = createForm.content.trim()
  if (!content && !createForm.file) return

  saving.value = true
  try {
    const formData = new FormData()
    formData.append('content', content)
    formData.append('media_type', createForm.media_type)
    if (createForm.file) formData.append('media', createForm.file)

    await http.post('/api/posts/', formData)
    createForm.content = ''
    createForm.media_type = 'none'
    createForm.file = null
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

const editOpen = ref(false)
const editSaving = ref(false)
const editForm = reactive<{
  id: number | null
  content: string
  media_type: 'none' | 'image' | 'video'
  file: File | null
}>({
  id: null,
  content: '',
  media_type: 'none',
  file: null,
})

function openEdit(p: Post) {
  editForm.id = p.id
  editForm.content = p.content
  editForm.media_type = p.media_type
  editForm.file = null
  editOpen.value = true
}

function onEditFileChange(uploadFile: UploadFile) {
  editForm.file = (uploadFile.raw as File) ?? null
}

function onEditFileRemove() {
  editForm.file = null
}

async function saveEdit() {
  if (!editForm.id) return
  editSaving.value = true
  try {
    const formData = new FormData()
    formData.append('content', editForm.content.trim())
    formData.append('media_type', editForm.media_type)
    if (editForm.file) formData.append('media', editForm.file)
    await http.patch(`/api/posts/${editForm.id}/`, formData)
    ElMessage.success('已保存')
    editOpen.value = false
    await loadPosts()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    editSaving.value = false
  }
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
        <el-select v-model="createForm.media_type" placeholder="媒体类型">
          <el-option label="无" value="none" />
          <el-option label="图片" value="image" />
          <el-option label="视频" value="video" />
        </el-select>
        <el-upload
          :auto-upload="false"
          :limit="1"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
        >
          <el-button>选择文件</el-button>
        </el-upload>
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
          <div class="post-id">#{{ p.id }}</div>
          <div class="post-text">{{ p.content || '（无文字）' }}</div>
        </div>
        <div class="post-actions">
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
        <div class="row">
          <el-select v-model="editForm.media_type" placeholder="媒体类型">
            <el-option label="无" value="none" />
            <el-option label="图片" value="image" />
            <el-option label="视频" value="video" />
          </el-select>
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="onEditFileChange"
            :on-remove="onEditFileRemove"
          >
            <el-button>替换文件</el-button>
          </el-upload>
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
  align-items: center;
  gap: 10px;
  margin-top: 10px;
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

.post-actions {
  display: flex;
  gap: 8px;
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
</style>
