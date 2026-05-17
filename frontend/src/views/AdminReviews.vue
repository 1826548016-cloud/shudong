<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Close } from '@element-plus/icons-vue'

import { approveReview, fetchReviewCount, fetchReviews, rejectReview, type ContentReview } from '../api/review'

const router = useRouter()

const authed = computed(() => Boolean(localStorage.getItem('treehole_token')))
const list = ref<ContentReview[]>([])
const loading = ref(false)
const count = ref(0)

async function loadReviews() {
  loading.value = true
  try {
    list.value = await fetchReviews()
    count.value = await fetchReviewCount()
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function doApprove(item: ContentReview) {
  try {
    await approveReview(item.id)
    ElMessage.success('已通过')
    await loadReviews()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function doReject(item: ContentReview) {
  try {
    await rejectReview(item.id)
    ElMessage.success('已拒绝并删除')
    await loadReviews()
  } catch {
    ElMessage.error('操作失败')
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString()
}

const typeLabel: Record<string, string> = { comment: '评论', message: '留言' }

onMounted(async () => {
  if (!authed.value) {
    await router.push('/admin/login')
    return
  }
  await loadReviews()
})
</script>

<template>
  <section class="page">
    <div class="card">
      <div class="title">内容审核（{{ list.length }} 条待审）</div>
      <el-skeleton v-if="loading" :rows="6" animated />
      <div v-else-if="list.length === 0" class="empty">暂无待审核内容 🎉</div>
      <div v-else class="reviews">
        <div v-for="item in list" :key="item.id" class="review-item">
          <div class="review-left">
            <div class="review-meta">
              <el-tag size="small" type="warning" effect="plain">{{ typeLabel[item.review_type] || item.review_type }}</el-tag>
              <span class="review-nick">{{ item.nickname || '匿名' }}</span>
              <span class="review-time">{{ formatTime(item.created_at) }}</span>
            </div>
            <div class="review-text">{{ item.content }}</div>
            <div v-if="item.ai_reason" class="review-reason">🤖 {{ item.ai_reason }}</div>
          </div>
          <div class="review-actions">
            <el-button type="success" :icon="Check" size="small" @click="doApprove(item)">通过</el-button>
            <el-button type="danger" :icon="Close" size="small" @click="doReject(item)">拒绝</el-button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.page {
  max-width: 760px;
  margin: 0 auto;
}

.card {
  background: var(--card-bg);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 24px;
}

.title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
  color: var(--text-1);
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: var(--text-3);
  font-size: 14px;
}

.reviews {
  display: grid;
  gap: 12px;
}

.review-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: border-color .2s;
}

.review-item:hover {
  border-color: var(--el-color-warning-light-3);
}

.review-left {
  flex: 1;
  min-width: 0;
}

.review-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.review-nick {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-1);
}

.review-time {
  font-size: 12px;
  color: var(--text-3);
}

.review-text {
  font-size: 14px;
  color: var(--text-1);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.review-reason {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-color-warning);
}

.review-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
  margin-left: 14px;
}
</style>
