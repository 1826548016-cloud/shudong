<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchProfileAdmin, fetchProfilePublic } from './api/profile'
import { fetchUnreadCount } from './api/inbox'
import { fetchReviewCount } from './api/review'
import { usePlayer } from './composables/usePlayer'
import { Sunny, Moon } from '@element-plus/icons-vue'

const MusicPlayer = defineAsyncComponent(() => import('./components/MusicPlayer.vue'))

const router = useRouter()
const route = useRoute()

const { pauseForMedia, resumeAfterMedia, setPlaylist } = usePlayer()

const isAuthed = ref(Boolean(localStorage.getItem('treehole_token')))

const avatarUrl = ref<string | null>(null)
const nickname = ref('树洞主人')
const unreadCount = ref(0)
const reviewCount = ref(0)
const unreadHandler = () => { loadUnreadCount() }
let unreadTimer: number | null = null

const showWelcome = ref(false)
const randomPlayStarted = ref(false)
const isDark = ref(false)
const moreOpen = ref(false)

function initTheme() {
  const saved = localStorage.getItem('treehole_theme')
  if (saved === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
    document.documentElement.classList.remove('light')
  } else if (!saved && !document.documentElement.classList.contains('light')) {
    document.documentElement.classList.add('light')
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    document.documentElement.classList.remove('light')
    localStorage.setItem('treehole_theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    document.documentElement.classList.add('light')
    localStorage.setItem('treehole_theme', 'light')
  }
}

async function startRandomPlay() {
  if (randomPlayStarted.value) return
  randomPlayStarted.value = true
  try {
    const { fetchMusicList } = await import('./api/music')
    const list = await fetchMusicList()
    if (list.length === 0) return
    setPlaylist(list, Math.floor(Math.random() * list.length))
  } catch (_) {
    /* ignore */
  }
}

let _firstInteractionDone = false

function tryStartRandomPlay() {
  if (!_firstInteractionDone) {
    _firstInteractionDone = true
    startRandomPlay()
  }
}

function dismissWelcome() {
  showWelcome.value = false
  tryStartRandomPlay()
}

function goHome() {
  router.push('/')
}

function goProfile() {
  if (!isAuthed.value) return
  router.push('/profile')
}

function goConnection() {
  router.push('/connection')
}

function goAIChat() {
  router.push('/ai-chat')
}

function goTimeline() {
  router.push('/timeline')
}

function goMusic() {
  router.push('/music')
}

function logout() {
  localStorage.removeItem('treehole_token')
  isAuthed.value = false
  router.push('/')
}

async function loadReviewCount() {
  if (!isAuthed.value) return
  try {
    reviewCount.value = await fetchReviewCount()
  } catch {
    reviewCount.value = 0
  }
}

async function loadProfileForHeader() {
  avatarUrl.value = null
  try {
    const pub = await fetchProfilePublic()
    nickname.value = pub.nickname || '树洞主人'
    avatarUrl.value = pub.avatar_url
  } catch (e) {
    nickname.value = '树洞主人'
    avatarUrl.value = null
  }

  if (!isAuthed.value) return

  try {
    const admin = await fetchProfileAdmin()
    avatarUrl.value = admin.avatar_url || avatarUrl.value
    nickname.value = admin.nickname || nickname.value
  } catch (e) {
    // ignore
  }
}

async function loadUnreadCount() {
  if (!isAuthed.value) {
    unreadCount.value = 0
    return
  }
  try {
    const data = await fetchUnreadCount()
    unreadCount.value = data.count
  } catch (e) {
    unreadCount.value = 0
  }
}

watch(isAuthed, (authed) => {
  void loadProfileForHeader()
  if (authed) {
    void loadUnreadCount()
    window.addEventListener('treehole-unread-refresh', unreadHandler)
    unreadTimer = window.setInterval(() => void loadUnreadCount(), 15000)
  } else {
    unreadCount.value = 0
    window.removeEventListener('treehole-unread-refresh', unreadHandler)
    if (unreadTimer) window.clearInterval(unreadTimer)
    unreadTimer = null
  }
})

function checkAuth() {
  isAuthed.value = Boolean(localStorage.getItem('treehole_token'))
}

watch(() => route.path, () => {
  checkAuth()
  moreOpen.value = false
  if (route.path.startsWith('/posts/')) {
    pauseForMedia()
  } else {
    window.setTimeout(resumeAfterMedia, 300)
  }
})

function handleAuthExpired() {
  isAuthed.value = false
  unreadCount.value = 0
  window.removeEventListener('treehole-unread-refresh', unreadHandler)
  if (unreadTimer) window.clearInterval(unreadTimer)
  unreadTimer = null
}

onMounted(() => {
  initTheme()
  checkAuth()
  requestIdleCallback(() => {
    void loadProfileForHeader()
    if (isAuthed.value) {
      void loadUnreadCount()
      void loadReviewCount()
      window.addEventListener('treehole-unread-refresh', unreadHandler)
      unreadTimer = window.setInterval(() => void loadUnreadCount(), 15000)
    }
  })
  window.addEventListener('treehole-auth-expired', handleAuthExpired)

  if (!sessionStorage.getItem('treehole_welcomed')) {
    showWelcome.value = true
    sessionStorage.setItem('treehole_welcomed', '1')
  }
})

onUnmounted(() => {
  window.removeEventListener('treehole-unread-refresh', unreadHandler)
  window.removeEventListener('treehole-auth-expired', handleAuthExpired)
  if (unreadTimer) window.clearInterval(unreadTimer)
  unreadTimer = null
})

const showTopbar = computed(() => !route.meta?.hideTopbar)
</script>

<template>
  <div class="app-shell" @click="tryStartRandomPlay(); moreOpen = false">
    <header v-if="showTopbar" class="topbar">
      <div class="topbar-inner">
        <button class="brand" type="button" @click="goHome">
          主页
          <span class="brand-sub">· {{ nickname }}</span>
        </button>
        <div class="topbar-actions">
          <el-button text :icon="isDark ? Sunny : Moon" @click="toggleTheme" :title="isDark ? '切换亮色' : '切换暗色'" />
          <button
            v-if="avatarUrl"
            class="avatar-btn"
            type="button"
            :title="isAuthed ? '编辑本人主页' : '树洞主人'"
            @click="goProfile"
          >
            <el-avatar :src="avatarUrl" :size="32" />
          </button>
          <el-button
            v-if="isAuthed"
            text
            @click="router.push('/admin/inbox')"
          >
            消息<el-badge v-if="unreadCount" :value="unreadCount" class="inbox-badge" />
          </el-button>
          <el-button type="primary" size="default" @click="isAuthed ? logout() : router.push('/admin/login')">
            {{ isAuthed ? '退出' : '登录' }}
          </el-button>
          <div class="more-wrap" @click.stop>
            <el-button text @click="moreOpen = !moreOpen">更多 ▾</el-button>
            <div v-if="moreOpen" class="more-menu">
              <el-button text @click="router.push('/'); moreOpen = false">主页</el-button>
              <el-button text @click="router.push('/about'); moreOpen = false">关于</el-button>
              <el-button text @click="goConnection(); moreOpen = false">联系我</el-button>
              <el-button text @click="goAIChat(); moreOpen = false">AI 对话</el-button>
              <el-button text @click="goTimeline(); moreOpen = false">图库</el-button>
              <el-button text @click="goMusic(); moreOpen = false">音乐</el-button>
              <el-button text @click="router.push('/messages'); moreOpen = false">留言</el-button>
              <template v-if="isAuthed">
                <div class="more-divider"></div>
                <el-button text @click="router.push('/admin/editor'); moreOpen = false">发布动态</el-button>
                <el-button text @click="router.push('/admin/announcements'); moreOpen = false">公告</el-button>
                <el-button text @click="router.push('/admin/reviews'); moreOpen = false">
                  审核<el-badge v-if="reviewCount" :value="reviewCount" class="review-badge" />
                </el-button>
                <el-button text @click="router.push('/profile'); moreOpen = false">编辑主页</el-button>
              </template>
            </div>
          </div>
        </div>
      </div>
    </header>
    <main class="main" :class="{ 'no-topbar': !showTopbar }">
      <router-view />
    </main>

    <footer class="site-footer">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" class="icp-link">豫ICP备2026020102号</a>
    </footer>

    <MusicPlayer />

    <!-- Welcome Modal -->
    <Teleport to="body">
      <div v-if="showWelcome" class="welcome-overlay" @click.self="dismissWelcome">
        <div class="welcome-modal">
          <div class="welcome-content">
            <!-- <div class="welcome-icon">🌳</div> -->
            <h1 class="welcome-title">Welcome</h1>

            <button class="welcome-btn" type="button" @click="dismissWelcome">开始探索</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--app-bg);
}

.topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 56px;
  background: rgba(255,255,255,.78);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border);
}

html.dark .topbar {
  background: rgba(15,17,23,.82);
  border-bottom-color: var(--border);
}

.topbar-inner {
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 24px;
  height: 56px;
}

.brand {
  background: none;
  border: none;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-1);
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: -.02em;
  transition: opacity .15s;
  white-space: nowrap;
}

.brand:hover {
  opacity: .75;
}

.brand-sub {
  font-weight: 400;
  font-size: 13px;
  color: var(--text-3);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.avatar-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  line-height: 0;
}

.inbox-badge :deep(.el-badge__content) {
  z-index: 10;
}

.more-wrap {
  position: relative;
}

.more-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 6px;
  min-width: 140px;
  box-shadow: 0 8px 32px rgba(0,0,0,.12);
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 200;
}

html.dark .more-menu {
  box-shadow: 0 8px 32px rgba(0,0,0,.4);
}

.more-menu .el-button {
  justify-content: flex-start;
  width: 100%;
}

.more-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

.review-badge {
  margin-left: 4px;
}

.main {
  max-width: 1080px;
  margin: 56px auto 0;
  padding: 24px 24px calc(80px + 42px) 24px;
}

.main.no-topbar {
  margin-top: 0;
}

/* ===== Footer ===== */
.site-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 99999;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--text-1);
}

.icp-link {
  color: rgba(255,255,255,.7);
  text-decoration: none;
  font-size: 12px;
  letter-spacing: .02em;
}

.icp-link:hover {
  color: #fff;
}

/* ===== Welcome Modal ===== */
.welcome-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000;
  background: rgba(0,0,0,.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding-bottom: 42px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  animation: appFadeIn .35s ease;
}

@keyframes appFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.welcome-modal {
  position: relative;
  width: min(420px, 90vw);
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  box-shadow: 0 24px 64px rgba(0,0,0,.18);
  overflow: hidden;
  animation: appScaleIn .45s cubic-bezier(.16,1,.3,1);
}

html.dark .welcome-modal {
  box-shadow: 0 24px 64px rgba(0,0,0,.4);
}

@keyframes appScaleIn {
  from { opacity: 0; transform: scale(.92); }
  to { opacity: 1; transform: scale(1); }
}

.welcome-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 40px 40px;
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-1);
  margin: 0 0 32px;
  letter-spacing: -.03em;
}

.welcome-btn {
  width: 100%;
  background: var(--primary);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  padding: 12px 0;
  cursor: pointer;
  letter-spacing: .02em;
  transition: background .2s, box-shadow .2s;
}

.welcome-btn:hover {
  background: var(--primary-hover);
  box-shadow: 0 4px 14px rgba(51,112,255,.35);
}

.welcome-btn:active {
  background: var(--primary-active);
}
</style>
