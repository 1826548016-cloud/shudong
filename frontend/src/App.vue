<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchProfileAdmin, fetchProfilePublic } from './api/profile'
import { fetchUnreadCount } from './api/inbox'

const router = useRouter()
const isAuthed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const avatarUrl = ref<string | null>(null)
const nickname = ref('树洞主人')
const unreadCount = ref(0)
const unreadHandler = () => void loadUnreadCount()
let unreadTimer: number | null = null

function goHome() {
  router.push('/')
}

function goProfile() {
  if (!isAuthed.value) return
  router.push('/profile')
}

function goAdmin() {
  router.push(isAuthed.value ? '/admin/editor' : '/admin/login')
}

function goConnection() {
  router.push('/connection')
}

function goInbox() {
  router.push('/admin/inbox')
}

function logout() {
  localStorage.removeItem('treehole_token')
  router.push('/')
}

async function loadProfileForHeader() {
  avatarUrl.value = null
  try {
    const pub = await fetchProfilePublic()
    nickname.value = pub.nickname || '树洞主人'
  } catch (e) {
    nickname.value = '树洞主人'
  }

  if (!isAuthed.value) return

  try {
    const admin = await fetchProfileAdmin()
    avatarUrl.value = admin.avatar_url
    nickname.value = admin.nickname || nickname.value
  } catch (e) {
    avatarUrl.value = null
  }
}

onMounted(() => {
  void loadProfileForHeader()
  if (!isAuthed.value) return
  void loadUnreadCount()
  window.addEventListener('treehole-unread-refresh', unreadHandler)
  unreadTimer = window.setInterval(() => void loadUnreadCount(), 15000)
})

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

onUnmounted(() => {
  window.removeEventListener('treehole-unread-refresh', unreadHandler)
  if (unreadTimer) window.clearInterval(unreadTimer)
  unreadTimer = null
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <button class="brand" type="button" @click="goHome">
          主页
          <span class="brand-sub">· {{ nickname }}</span>
        </button>
        <div class="topbar-actions">
          <button
            v-if="isAuthed"
            class="avatar-btn"
            type="button"
            title="编辑本人主页"
            @click="goProfile"
          >
            <el-avatar v-if="avatarUrl" :src="avatarUrl" :size="32" />
            <el-avatar v-else :size="32">{{ nickname.slice(0, 1) }}</el-avatar>
          </button>
          <el-badge
            v-if="isAuthed"
            :value="unreadCount"
            :hidden="unreadCount === 0"
            class="inbox-badge"
          >
            <el-button text @click="goInbox">消息</el-button>
          </el-badge>
          <el-button type="primary" size="default" @click="goAdmin">
            {{ isAuthed ? '发布动态' : '管理员登录' }}
          </el-button>
          <el-button v-if="isAuthed" text @click="logout">退出</el-button>
          <el-button text @click="goConnection">联系我</el-button>
        </div>
      </div>
    </header>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>
