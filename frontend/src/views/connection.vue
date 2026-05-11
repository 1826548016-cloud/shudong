<template>
  <div class="contact-container">
    <div class="contact-card">
      <div class="contact-title">
        <h2>联系我</h2>
        <p>欢迎交流、来访留言</p>
      </div>

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
              <span v-if="douyinUrl">打开主页</span>
              <span v-else>未设置</span>
            </div>
          </div>
          <div class="arrow">→</div>
        </div>

        <div class="contact-item" :class="{ disabled: !emailid}" @click="openDouyin">
          <div class="icon douyin-icon">邮</div>
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
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { fetchProfileAdmin, fetchProfilePublic } from '../api/profile'

const isAuthed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const wechatId = ref('Y18836286216')
const douyinUrl = ref('')
const phoneNum = ref('')
const emailid = ref('')
async function load() {
  try {
    const data = await fetchProfilePublic()
    wechatId.value = (data.wechat_id ?? '').trim()
    douyinUrl.value = (data.douyin_url ?? '').trim()
  } catch (e) {
    wechatId.value = ''
    douyinUrl.value = ''
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

function openDouyin() {
  if (!douyinUrl.value) return
  const url = douyinUrl.value.trim()
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
/* 字节风全局底色 极简留白 */
.contact-container {
  min-height: 80vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--app-bg);
  padding: 20px;
  box-sizing: border-box;
}

.contact-card {
  width: 100%;
  max-width: 420px;
  background: var(--card-bg);
  border-radius: 16px;
  padding: 36px 28px;
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border);
}

.contact-title {
  text-align: center;
  margin-bottom: 32px;
}

.contact-title h2 {
  font-size: 24px;
  color: var(--text-1);
  margin: 0 0 6px;
  font-weight: 600;
}

.contact-title p {
  font-size: 14px;
  color: var(--text-3);
  margin: 0;
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
