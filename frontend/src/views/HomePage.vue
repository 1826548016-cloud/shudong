<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { http } from '../api/http'
import { fetchProfilePublic } from '../api/profile'
import PostCard from '../components/PostCard.vue'

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

const loading = ref(false)
const posts = ref<Post[]>([])
const siteNickname = ref('树洞主人')

async function loadPosts() {
  loading.value = true
  try {
    const { data } = await http.get<Post[]>('/api/posts/')
    posts.value = data
  } catch (e) {
    ElMessage.error('加载动态失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProfilePublic()
    .then((p) => {
      siteNickname.value = p.nickname || '树洞主人'
    })
    .catch(() => {})
  void loadPosts()
})
</script>

<template>
  <section class="page">
    <div class="page-head">
      <div class="page-title">邂逅一方静谧天地，慢品日常，倾诉心声</div>
      <div class="page-subtitle">这里是 {{ siteNickname }} 的树洞 · 无需繁杂登录，随便看看，想说就说</div>
    </div>

    <el-skeleton v-if="loading" :rows="10" animated />
    <div v-else class="feed">
      <PostCard v-for="p in posts" :key="p.id" :post="p" />
      <div v-if="posts.length === 0" class="empty">还没有动态</div>
    </div>
  </section>
</template>

<style scoped>
.page-head {
  margin: 8px 0 14px;
}

.page-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-1);
}

.page-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-3);
}

.feed {
  display: grid;
  gap: 14px;
}

.empty {
  text-align: center;
  padding: 36px 0;
  color: var(--text-3);
  font-size: 14px;
}
</style>
