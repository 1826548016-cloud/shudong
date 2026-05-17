<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { http } from '../api/http'

const router = useRouter()

type Message = {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([
  {
    role: 'assistant',
    content: '你好呀～ 欢迎来到树洞，我是你的 AI 小助手 🌳\n有什么想聊的、想倾诉的都可以跟我说～',
  },
])

const inputText = ref('')
const sending = ref(false)
const chatEnd = ref<HTMLElement | null>(null)

function goBack() {
  router.push('/')
}

async function send() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const history = messages.value.slice(0, -1).map((m) => ({
      role: m.role,
      content: m.content,
    }))

    const { data } = await http.post<{ reply: string }>('/api/chat/', {
      message: text,
      history,
    })

    messages.value.push({ role: 'assistant', content: data.reply })
  } catch (e) {
    ElMessage.error('AI 回复失败，请稍后再试')
    messages.value.push({
      role: 'assistant',
      content: '抱歉，我暂时无法回复，请稍后再试试～',
    })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatEnd.value) {
      chatEnd.value.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

onMounted(() => {
  scrollToBottom()
})
</script>

<template>
  <div class="chat-shell">
    <div class="bg-overlay"></div>
    <div class="chat-content">

    <!-- 顶栏 -->
    <header class="chat-topbar glass-topbar">
      <button class="back-btn" type="button" @click="goBack">
        <el-icon :size="18"><ArrowLeft /></el-icon>
      </button>
      <div class="topbar-left">
        <div class="ai-avatar-small">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15l-4-4 1.41-1.41L11 14.17l6.59-6.59L19 9l-8 8z" fill="#fff"/></svg>
        </div>
        <div>
          <div class="chat-title">树洞小助手</div>
          <div class="chat-status">在线 · 由 DeepSeek 驱动</div>
        </div>
      </div>
      <div class="spacer"></div>
    </header>

    <!-- 消息列表 -->
    <div class="chat-body" ref="chatBody">
      <div class="msg-list">
        <div v-for="(m, i) in messages" :key="i" class="msg-group" :class="m.role">
          <div v-if="m.role === 'assistant'" class="msg-row">
            <div class="avatar ai-avatar">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15l-4-4 1.41-1.41L11 14.17l6.59-6.59L19 9l-8 8z" fill="#fff"/></svg>
            </div>
            <div class="bubble">{{ m.content }}</div>
          </div>
          <div v-else class="msg-row user">
            <div class="bubble user-bubble">{{ m.content }}</div>
          </div>
        </div>
        <div v-if="sending" class="msg-group assistant">
          <div class="msg-row">
            <div class="avatar ai-avatar">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15l-4-4 1.41-1.41L11 14.17l6.59-6.59L19 9l-8 8z" fill="#fff"/></svg>
            </div>
            <div class="bubble typing">
              <span class="dot-pulse"></span>
            </div>
          </div>
        </div>
        <div ref="chatEnd"></div>
      </div>
    </div>

    <!-- 输入栏 -->
    <div class="chat-inputbar">
      <div class="input-wrapper">
        <el-input
          v-model="inputText"
          :disabled="sending"
          placeholder="给树洞小助手发消息…"
          maxlength="500"
          show-word-limit
          resize="none"
          :autosize="{ minRows: 1, maxRows: 5 }"
          type="textarea"
          @keyup.enter.prevent="send"
        />
        <button
          class="send-btn"
          :class="{ active: inputText.trim() && !sending }"
          :disabled="!inputText.trim() || sending"
          type="button"
          @click="send"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor"/></svg>
        </button>
      </div>
      <div class="input-footer">
        AI 回复仅供参考，请理性判断
      </div>
    </div>
    </div>
  </div>
</template>

<style scoped>
.chat-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
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

.chat-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* ===== 顶栏 ===== */
.chat-topbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
  height: 62px;
  flex-shrink: 0;
}

.glass-topbar {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  width: 32px;
  height: 32px;
}

.back-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-avatar-small {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1664ff, #4080ff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  line-height: 1.3;
}

.chat-status {
  font-size: 12px;
  color: #22c55e;
  line-height: 1.2;
}

.spacer {
  flex: 1;
}

/* ===== 消息区域 ===== */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
}

.msg-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 768px;
  margin: 0 auto;
}

.msg-group {
  padding: 8px 0;
}

.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.msg-group.user .msg-row {
  justify-content: flex-end;
}

/* ===== 头像 ===== */
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 4px;
}

.ai-avatar {
  background: linear-gradient(135deg, #1664ff, #4080ff);
}

/* ===== 气泡 ===== */
.bubble {
  max-width: 85%;
  padding: 12px 18px;
  border-radius: 18px;
  font-size: 14.5px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
  color: #1f2937;
  background: rgba(243, 244, 246, 0.85);
  backdrop-filter: blur(8px);
  border-bottom-left-radius: 6px;
}

.user-bubble {
  background: #1664ff;
  color: #ffffff;
  border-bottom-right-radius: 6px;
  border-bottom-left-radius: 18px;
  text-align: left;
}

.typing {
  padding: 14px 18px;
}

.dot-pulse {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* ===== 输入栏 ===== */
.chat-inputbar {
  flex-shrink: 0;
  padding: 0 20px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 16px;
  padding: 8px 8px 8px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: #1664ff;
  box-shadow: 0 2px 12px rgba(22, 100, 255, 0.10);
}

.input-wrapper :deep(.el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  padding: 0;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  min-height: 24px;
  background: transparent;
}

.input-wrapper :deep(.el-textarea__inner:focus) {
  box-shadow: none !important;
}

.input-wrapper :deep(.el-input__count) {
  bottom: -18px;
  font-size: 11px;
  color: #9ca3af;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: #d1d5db;
  color: #ffffff;
  cursor: not-allowed;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.send-btn.active {
  background: #1664ff;
  cursor: pointer;
}

.send-btn.active:hover {
  background: #1d4ed8;
}

.input-footer {
  text-align: center;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 8px;
}
</style>
