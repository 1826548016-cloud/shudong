<template>
  <div class="page">
    <div class="bg-overlay"></div>

    <div class="content">
      <div class="contact-header">
        <button class="back-link" type="button" @click="goBack">← 返回主页</button>
        <div class="contact-title">
          <h2>联系我</h2>
          <p>欢迎交流、来访留言</p>
        </div>
      </div>

      <div class="contact-card">
        <div class="contact-list">
          <div class="contact-item" :class="{ disabled: !wechatId }" @click="copyWechat">
            <div class="icon wechat-icon">微</div>
            <div class="info">
              <div class="name">微信</div>
              <div class="desc">
                <span v-if="wechatId">点击复制：{{ wechatId }}</span>
                <span v-else>未设置</span>
              </div>
            </div>
            <div class="arrow">→</div>
          </div>

          <div class="contact-item" :class="{ disabled: !douyinUrl }" @click="openDouyin">
            <div class="icon douyin-icon">抖</div>
            <div class="info">
              <div class="name">抖音</div>
              <div class="desc">
                <span v-if="douyinUrl">点击复制：{{ douyinUrl }}</span>
                <span v-else>未设置</span>
              </div>
            </div>
            <div class="arrow">→</div>
          </div>

          <div class="contact-item" :class="{ disabled: !emailid }" @click="copyEmail">
            <div class="icon email-icon">邮</div>
            <div class="info">
              <div class="name">邮箱</div>
              <div class="desc">
                <span v-if="emailid">点击复制：{{ emailid }}</span>
                <span v-else>未设置</span>
              </div>
            </div>
            <div class="arrow">→</div>
          </div>

          <div v-if="isAuthed && phoneNum" class="contact-item" @click="callPhone">
            <div class="icon phone-icon">电</div>
            <div class="info">
              <div class="name">电话</div>
              <div class="desc">私密联系：{{ phoneNum }}</div>
            </div>
            <div class="arrow">→</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { fetchProfileAdmin, fetchProfilePublic } from '../api/profile'

const router = useRouter()
const isAuthed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const wechatId = ref('')
const douyinUrl = ref('')
const phoneNum = ref('')
const emailid = ref('')

function goBack() {
  router.push('/')
}

async function load() {
  try {
    const data = await fetchProfilePublic()
    wechatId.value = (data.wechat_id ?? '').trim()
    douyinUrl.value = (data.douyin_url ?? '').trim()
    emailid.value = (data.email ?? '').trim()
  } catch (e) {
    wechatId.value = ''
    douyinUrl.value = ''
    emailid.value = ''
  }

  if (!isAuthed.value) {
    phoneNum.value = ''
    return
  }

  try {
    const admin = await fetchProfileAdmin()
    phoneNum.value = (admin.phone_num ?? '').trim()
  } catch (e) {
    phoneNum.value = ''
  }
}

function copyText(text: string) {
  const value = text.trim()
  if (!value) return Promise.reject(new Error('empty'))

  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(value)
  }

  const input = document.createElement('textarea')
  input.value = value
  input.style.position = 'fixed'
  input.style.left = '-9999px'
  document.body.appendChild(input)
  input.focus()
  input.select()
  const ok = document.execCommand('copy')
  document.body.removeChild(input)
  return ok ? Promise.resolve() : Promise.reject(new Error('copy failed'))
}

async function copyWechat() {
  if (!wechatId.value) return
  try {
    await copyText(wechatId.value)
    ElMessage.success('微信号已复制')
  } catch (e) {
    ElMessage.error('复制失败，请手动复制')
  }
}

async function copyEmail() {
  if (!emailid.value) return
  try {
    await copyText(emailid.value)
    ElMessage.success('邮箱已复制')
  } catch (e) {
    ElMessage.error('复制失败，请手动复制')
  }
}

function openDouyin() {
  if (!douyinUrl.value) return
  const url = douyinUrl.value.trim()
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    ElMessage.warning('抖音链接格式不正确')
    return
  }
  window.open(url, '_blank', 'noreferrer')
}

async function callPhone() {
  if (!phoneNum.value) return
  try {
    await ElMessageBox.confirm('确定要拨打电话吗？', '提示', {
      confirmButtonText: '拨打',
      cancelButtonText: '取消',
      type: 'warning',
    })
    window.location.href = `tel:${phoneNum.value}`
  } catch (e) {}
}

onMounted(() => {
  void load()
})
</script>

<style scoped>
.page {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
  box-sizing: border-box;
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
  width: 100%;
  max-width: 420px;
}

.contact-header {
  text-align: center;
  margin-bottom: 24px;
  position: relative;
}

.back-link {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 13px;
  color: #fff;
  cursor: pointer;
  padding: 4px 8px;
  white-space: nowrap;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.back-link:hover {
  opacity: 0.8;
}

.contact-title h2 {
  font-size: 24px;
  color: #fff;
  margin: 0 0 6px;
  font-weight: 600;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.contact-title p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.contact-card {
  width: 100%;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 16px;
  padding: 36px 28px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
}

.contact-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.contact-item {
  display: flex;
  align-items: center;
  padding: 16px 14px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.contact-item:hover {
  background: rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.contact-item.disabled {
  cursor: not-allowed;
  opacity: 0.55;
  transform: none;
}

.contact-item.disabled:hover {
  background: rgba(0, 0, 0, 0.03);
  transform: none;
}

.icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  margin-right: 14px;
}

.wechat-icon {
  background: #07c160;
}

.douyin-icon {
  background: #000000;
}

.email-icon {
  background: #ff8200;
}

.phone-icon {
  background: #4080ff;
}

.info {
  flex: 1;
}

.info .name {
  font-size: 16px;
  color: var(--text-1);
  font-weight: 500;
}

.info .desc {
  font-size: 13px;
  color: var(--text-3);
  margin-top: 2px;
}

.arrow {
  font-size: 18px;
  color: var(--text-3);
}
</style>
