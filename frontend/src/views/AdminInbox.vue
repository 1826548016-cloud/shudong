<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Edit } from '@element-plus/icons-vue'

import {
  fetchUnreadComments,
  markCommentRead,
  replyComment,
  type UnreadComment,
} from '../api/inbox'

const router = useRouter()
const authed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const loading = ref(false)
const list = ref<UnreadComment[]>([])

const replyOpen = ref(false)
const replying = ref(false)
const replyText = ref('')
const current = ref<UnreadComment | null>(null)

async function load() {
  loading.value = true
  try {
    list.value = await fetchUnreadComments()
  } catch (e) {
    ElMessage.error('加载未读消息失败')
  } finally {
    loading.value = false
  }
}

function openReply(item: UnreadComment) {
  current.value = item
  replyText.value = ''
  replyOpen.value = true
}

async function submitReply() {
  if (!current.value) return
  replying.value = true
  try {
    await replyComment(current.value.id, replyText.value.trim())
    ElMessage.success('已回复')
    window.dispatchEvent(new Event('treehole-unread-refresh'))
    replyOpen.value = false
    await router.push({
      name: 'post-detail',
      params: { id: String(current.value.post) },
      query: { comment: String(current.value.id) },
    })
  } catch (e) {
    ElMessage.error('回复失败')
  } finally {
    replying.value = false
  }
}

async function markRead(item: UnreadComment) {
  try {
    await markCommentRead(item.id)
    ElMessage.success('已标为已读')
    window.dispatchEvent(new Event('treehole-unread-refresh'))
    await load()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function jump(item: UnreadComment) {
  router.push({
    name: 'post-detail',
    params: { id: String(item.post) },
    query: { comment: String(item.id) },
  })
}

onMounted(async () => {
  if (!authed.value) {
    await router.push('/admin/login')
    return
  }
  await load()
})
</script>

<template>
  <section class="page">
    <div class="head">
      <div class="title">未读消息</div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />
    <div v-else class="list">
      <div
        v-for="item in list"
        :key="item.id"
        class="row"
        role="button"
        tabindex="0"
        @click="jump(item)"
      >
        <div class="main">
          <div class="meta">
            <span class="nick">{{ item.nickname || '匿名' }}</span>
            <span class="time">{{ new Date(item.created_at).toLocaleString() }}</span>
          </div>
          <div class="content">{{ item.content }}</div>
          <div class="post-snippet">
            动态：{{ item.post_content || '（无内容）' }}
          </div>
        </div>
        <div class="actions" @click.stop>
          <el-button :icon="Edit" text @click="openReply(item)">回复</el-button>
          <el-button :icon="Check" text @click="markRead(item)">已读</el-button>
        </div>
      </div>

      <div v-if="list.length === 0" class="empty">暂无未读消息</div>
    </div>

    <el-dialog v-model="replyOpen" title="管理员回复" width="520px">
      <el-input
        v-model="replyText"
        type="textarea"
        :rows="4"
        maxlength="500"
        show-word-limit
        placeholder="写下回复内容…"
      />
      <template #footer>
        <el-button @click="replyOpen = false">取消</el-button>
        <el-button type="primary" :loading="replying" @click="submitReply">
          回复并跳转
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.title {
  font-size: 16px;
  font-weight: 900;
  color: var(--text-1);
}

.list {
  display: grid;
  gap: 10px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  border-radius: 12px;
  padding: 12px 14px;
}

.main {
  min-width: 0;
}

.meta {
  display: flex;
  gap: 10px;
  color: var(--text-3);
  font-size: 12px;
}

.nick {
  color: var(--text-2);
  font-weight: 700;
}

.content {
  margin-top: 6px;
  color: var(--text-1);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.post-snippet {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-3);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.actions {
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
</style>
