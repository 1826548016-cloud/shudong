<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchProfilePublic } from '../api/profile'

const router = useRouter()

type Profile = {
  nickname: string
  bio: string
  wechat_id: string
  douyin_url: string
  email: string
  avatar_url: string | null
}

const profile = ref<Profile | null>(null)
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    profile.value = await fetchProfilePublic()
  } catch (e) {
    // ignore
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/')
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <div class="bg-overlay"></div>

    <div class="content">
      <el-button text class="back-btn" @click="goBack">← 返回主页</el-button>

      <el-skeleton v-if="loading" :rows="6" animated />
      <template v-else>
        <div class="profile-card">
          <div class="profile-avatar">
            <el-avatar v-if="profile?.avatar_url" :src="profile.avatar_url" :size="88" />
            <div v-else class="avatar-circle">{{ (profile?.nickname || '我').slice(0, 1) }}</div>
          </div>
          <div class="profile-name">{{ profile?.nickname || '树洞主人' }}</div>
        </div>

        <div class="section-title">简介</div>
        <div class="intro-card">
          <div v-if="profile?.bio" class="intro-text">{{ profile.bio }}</div>
          <div v-else class="intro-empty">这个人很懒，什么都没留下～</div>
        </div>

        <div v-if="profile?.email || profile?.wechat_id" class="section-title">联系方式</div>
        <div class="contact-list">
          <div v-if="profile?.email" class="contact-chip">
            <span class="chip-label">邮箱</span>
            {{ profile.email }}
          </div>
          <div v-if="profile?.wechat_id" class="contact-chip">
            <span class="chip-label">微信</span>
            {{ profile.wechat_id }}
          </div>
        </div>

        <div class="section-title">GitHub</div>
        <a class="github-card" href="https://github.com/1826548016-cloud" target="_blank" rel="noreferrer">
          <span class="github-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          </span>
          <span>1826548016-cloud</span>
          <span class="github-arrow">→</span>
        </a>
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

.content {
  position: relative;
  z-index: 2;
  max-width: 640px;
  margin: 0 auto;
}

.back-btn {
  margin-bottom: 10px;
  color: #fff;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.profile-card {
  text-align: center;
  padding: 32px 0 24px;
}

.profile-avatar {
  display: flex;
  justify-content: center;
}

.avatar-circle {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1664ff, #4080ff);
  color: #fff;
  font-size: 36px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-name {
  margin-top: 14px;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.section-title {
  font-size: 16px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 10px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.intro-card {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius);
  padding: 18px 20px;
  margin-bottom: 20px;
}

.intro-text {
  font-size: 14px;
  color: var(--text-2);
  line-height: 1.7;
  white-space: pre-wrap;
}

.intro-empty {
  font-size: 14px;
  color: var(--text-3);
  text-align: center;
  padding: 8px 0;
}

.contact-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.contact-chip {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 13px;
  color: var(--text-2);
}

.chip-label {
  font-weight: 600;
  color: var(--text-1);
  margin-right: 6px;
}

.github-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 14px;
  color: #1f2937;
  text-decoration: none;
  margin-bottom: 20px;
  transition: background 0.2s, transform 0.2s;
  cursor: pointer;
}

.github-card:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.github-icon {
  color: #1f2937;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.github-arrow {
  margin-left: auto;
  color: var(--text-3);
  font-size: 16px;
}
</style>
