<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete} from '@element-plus/icons-vue'

import { fetchMessages, createMessage, deleteMessage, type MessageItem } from '../api/message'
const list = ref<MessageItem[]>([])
const loading = ref(false)
const submitting = ref(false)

const nickname = ref('')
const content = ref('')

const isAuthed = computed(() => Boolean(localStorage.getItem('treehole_token')))

async function load() {
  loading.value = true
  try {
    list.value = await fetchMessages()
  } catch (e) {
    ElMessage.error('加载留言失败')
  } finally {
    loading.value = false
  }
}

async function submit() {
  const msg = content.value.trim()
  if (!msg) {
    ElMessage.warning('请写下留言内容')
    return
  }
  submitting.value = true
  try {
    await createMessage(nickname.value.trim() || '匿名', msg)
    content.value = ''
    ElMessage.success('留言成功')
    await load()
  } catch (e) {
    ElMessage.error('留言失败，请稍后再试')
  } finally {
    submitting.value = false
  }
}

async function remove(id: number) {
  try {
    await deleteMessage(id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="page-wrap">
    <div class="bg-overlay"></div>

    <div class="page">
      <div class="page-head">
        <div class="page-title">请留下你的真知灼见</div>
        <div class="page-subtitle">关于技术性的相关建议或是其他的想法可以留言</div>
      </div>

      <div class="message-form">
        <div class="form-row">
          <el-input
            v-model="nickname"
            placeholder="你的联系方式"
            maxlength="32"
            clearable
          />
        </div>
        <div class="form-row">
          <el-input
            v-model="content"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="请规范你的言辞，避免使用敏感词汇或内容，否则可能会被拦截发布"
          />
        </div>
        <div class="form-row form-actions">
          <el-button type="primary" :loading="submitting" :disabled="!content.trim()" @click="submit">
            发布留言
          </el-button>
        </div>
      </div>

      <el-skeleton v-if="loading" :rows="6" animated />
      <div v-else class="message-list">
        <div v-if="list.length === 0" class="empty">
          还没有留言，来写下第一条吧 ✍️
        </div>
        <div
          v-for="item in list"
          :key="item.id"
          class="message-item"
        >
          <div class="message-head">
            <div class="message-author">{{ item.nickname || '匿名' }}</div>
            <div class="message-time">{{ formatTime(item.created_at) }}</div>
            <button
              v-if="isAuthed"
              class="del-btn"
              type="button"
              title="删除"
              @click="remove(item.id)"
            >
              <el-icon :size="15"><Delete /></el-icon>
            </button>
          </div>
          <div class="message-content">{{ item.content }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap {
  min-height: calc(100vh - 56px);
  position: relative;
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

.page {
  position: relative;
  z-index: 2;
  max-width: 600px;
  margin: 0 auto;
  padding: 20px 20px 80px;
}

.page-head {
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-1);
}

.page-subtitle {
  font-size: 13px;
  color: var(--text-3);
  margin-top: 4px;
}

.message-form {
  background: var(--card-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  display: grid;
  gap: 10px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.form-row {
  display: flex;
}

.form-actions {
  justify-content: flex-end;
}

.message-list {
  display: grid;
  gap: 10px;
}

.message-item {
  background: var(--card-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  transition: box-shadow 0.3s, transform 0.3s;
}

.message-item:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.message-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.message-author {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-1);
}

.message-time {
  font-size: 11px;
  color: var(--text-3);
  flex: 1;
}

.del-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-3);
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  transition: background 0.15s, color 0.15s;
}

.del-btn:hover {
  background: rgba(255, 60, 60, 0.08);
  color: #f56c6c;
}

.message-content {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-1);
  white-space: pre-wrap;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: var(--text-3);
  font-size: 14px;
}
</style>
