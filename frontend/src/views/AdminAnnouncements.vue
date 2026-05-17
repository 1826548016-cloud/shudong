<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { http } from '../api/http'
import type { SiteAnnouncement } from '../api/announcement'

const router = useRouter()

const authed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const list = ref<SiteAnnouncement[]>([])
const loading = ref(false)
const saving = ref(false)

const createForm = reactive({
  title: '',
  content: '',
  is_active: true,
  files: [] as File[],
})

const fileInput = ref<HTMLInputElement | null>(null)

function handleCreateFileSelect(e: Event) {
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

const editOpen = ref(false)
const editSaving = ref(false)
const editForm = reactive({
  id: 0,
  title: '',
  content: '',
  is_active: true,
  replaceFiles: [] as File[],
})

const editFileInput = ref<HTMLInputElement | null>(null)

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

function mediaCount(item: SiteAnnouncement): string {
  const n = item.media_items?.length ?? 0
  if (n === 0) return ''
  return ` · ${n}个附件`
}

async function loadList() {
  loading.value = true
  try {
    const { data } = await http.get<SiteAnnouncement[]>('/api/admin/announcements/')
    list.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function doCreate() {
  if (!createForm.title.trim() || !createForm.content.trim()) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  saving.value = true
  try {
    const formData = new FormData()
    formData.append('title', createForm.title)
    formData.append('content', createForm.content)
    formData.append('is_active', String(createForm.is_active))
    for (const f of createForm.files) {
      formData.append('files', f)
    }
    await http.post('/api/admin/announcements/', formData)
    createForm.title = ''
    createForm.content = ''
    createForm.is_active = true
    createForm.files = []
    ElMessage.success('公告已发布')
    await loadList()
  } catch (e) {
    ElMessage.error('发布失败')
  } finally {
    saving.value = false
  }
}

function openEdit(item: SiteAnnouncement) {
  editForm.id = item.id
  editForm.title = item.title
  editForm.content = item.content
  editForm.is_active = item.is_active
  editForm.replaceFiles = []
  editOpen.value = true
}

async function doUpdate() {
  if (!editForm.title.trim() || !editForm.content.trim()) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  editSaving.value = true
  try {
    const formData = new FormData()
    formData.append('title', editForm.title)
    formData.append('content', editForm.content)
    formData.append('is_active', String(editForm.is_active))
    if (editForm.replaceFiles.length > 0) {
      for (const f of editForm.replaceFiles) {
        formData.append('files', f)
      }
    }
    await http.patch(`/api/admin/announcements/${editForm.id}/`, formData)
    ElMessage.success('已保存')
    editOpen.value = false
    editForm.replaceFiles = []
    await loadList()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    editSaving.value = false
  }
}

async function doDelete(id: number) {
  try {
    await http.delete(`/api/admin/announcements/${id}/delete/`)
    ElMessage.success('已删除')
    await loadList()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString()
}

onMounted(async () => {
  if (!authed.value) {
    await router.push('/admin/login')
    return
  }
  await loadList()
})
</script>

<template>
  <section class="page">
    <div class="card">
      <div class="title">发布公告</div>
      <div class="form-row">
        <el-input v-model="createForm.title" placeholder="公告标题" maxlength="128" />
      </div>
      <div class="form-row">
        <el-input v-model="createForm.content" type="textarea" :rows="3" placeholder="公告内容（支持图片、视频、文件）" maxlength="2000" />
      </div>
      <div class="form-row">
        <div class="file-section">
          <input
            ref="fileInput"
            type="file"
            multiple
            accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.zip"
            style="display:none"
            @change="handleCreateFileSelect"
          />
          <el-button size="small" :icon="Plus" @click="fileInput?.click()">添加附件</el-button>
          <span v-if="createForm.files.length === 0" class="hint">支持图片、视频、音频、文档</span>
        </div>
        <div v-if="createForm.files.length" class="file-tags">
          <el-tag
            v-for="(f, i) in createForm.files"
            :key="i"
            closable
            size="small"
            @close="removeCreateFile(i)"
          >
            {{ f.name }}
          </el-tag>
        </div>
      </div>
      <div class="form-row form-actions">
        <el-switch v-model="createForm.is_active" active-text="立即启用" />
        <el-button type="primary" :icon="Plus" :loading="saving" @click="doCreate">发布公告</el-button>
      </div>
    </div>

    <div class="card">
      <div class="title">已有公告 ({{ list.length }})</div>
      <el-skeleton v-if="loading" :rows="6" animated />
      <div v-else-if="list.length === 0" class="empty">暂无公告</div>
      <div v-else class="list">
        <div v-for="item in list" :key="item.id" class="list-item" :class="{ inactive: !item.is_active }">
          <div class="item-left">
            <div class="item-title">
              <el-tag :type="item.is_active ? 'success' : 'info'" size="small" effect="plain">
                {{ item.is_active ? '启用' : '停用' }}
              </el-tag>
              {{ item.title }}
              <span class="item-media-hint">{{ mediaCount(item) }}</span>
            </div>
            <div class="item-content">{{ item.content }}</div>
            <div class="item-time">{{ formatTime(item.created_at) }}</div>
          </div>
          <div class="item-actions">
            <el-button text :icon="Edit" @click="openEdit(item)">编辑</el-button>
            <el-button text type="danger" :icon="Delete" @click="doDelete(item.id)">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="editOpen" title="编辑公告" width="540px">
      <div class="form-row">
        <el-input v-model="editForm.title" placeholder="公告标题" maxlength="128" />
      </div>
      <div class="form-row">
        <el-input v-model="editForm.content" type="textarea" :rows="4" placeholder="公告内容" maxlength="2000" />
      </div>
      <div class="form-row">
        <div class="file-section">
          <input
            ref="editFileInput"
            type="file"
            multiple
            accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.zip"
            style="display:none"
            @change="handleEditFileSelect"
          />
          <el-button size="small" @click="editFileInput?.click()">替换附件</el-button>
          <span class="hint">选择新文件会替换旧附件</span>
        </div>
        <div v-if="editForm.replaceFiles.length" class="file-tags">
          <el-tag
            v-for="(f, i) in editForm.replaceFiles"
            :key="i"
            closable
            size="small"
            @close="removeEditFile(i)"
          >
            {{ f.name }}
          </el-tag>
        </div>
      </div>
      <div class="form-row">
        <el-switch v-model="editForm.is_active" active-text="启用" />
      </div>
      <template #footer>
        <el-button @click="editOpen = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="doUpdate">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.page {
  max-width: 760px;
  margin: 0 auto;
}

.card {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
  color: var(--text-1);
}

.form-row {
  margin-bottom: 12px;
}

.file-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hint {
  font-size: 12px;
  color: var(--text-3);
}

.file-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.empty {
  text-align: center;
  padding: 32px 0;
  color: var(--text-3);
  font-size: 14px;
}

.list {
  display: grid;
  gap: 12px;
}

.list-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 14px;
  border: 1px solid var(--border, #eee);
  border-radius: 8px;
  transition: border-color 0.2s;
}

.list-item:hover {
  border-color: var(--el-color-primary);
}

.list-item.inactive {
  opacity: 0.55;
}

.item-left {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-media-hint {
  font-size: 12px;
  color: var(--text-3);
  font-weight: 400;
}

.item-content {
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.item-time {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 6px;
}

.item-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 12px;
}
</style>
