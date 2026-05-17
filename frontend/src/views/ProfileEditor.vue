<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadFile } from 'element-plus'

import { http } from '../api/http'

type PostItem = {
  id: number
  content: string
  is_pinned: boolean
  created_at: string
}

type ProfileAdmin = {
  nickname: string
  avatar_url: string | null
  bio: string
  wechat_id: string
  douyin_url: string
  phone_num: string
  email: string
  updated_at: string
}

const router = useRouter()
const authed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const loading = ref(false)
const saving = ref(false)
const postTotal = ref(0)
const keywords = ref<Array<{ id: number; keyword: string }>>([])
const newKeyword = ref('')
const kwSaving = ref(false)

const profileMeta = reactive({
  nickname: '',
  avatar_url: null as string | null,
  updated_at: '',
})

const form = reactive<{
  nickname: string
  bio: string
  wechat_id: string
  douyin_url: string
  phone_num: string
  email: string
  file: File | null
  avatar_url: string | null
}>({
  nickname: '',
  bio: '',
  wechat_id: '',
  douyin_url: '',
  phone_num: '',
  email: '',
  file: null,
  avatar_url: null,
})

function formatTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

function timeAgo(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 2592000) return `${Math.floor(diff / 86400)} 天前`
  return formatTime(iso)
}

async function loadProfile() {
  loading.value = true
  try {
    const [{ data: profile }, { data: posts }, { data: kwList }] = await Promise.all([
      http.get<ProfileAdmin>('/api/admin/profile/'),
      http.get<PostItem[]>('/api/posts/'),
      http.get<Array<{ id: number; keyword: string }>>('/api/admin/keywords/'),
    ])
    form.nickname = profile.nickname
    form.bio = profile.bio
    form.wechat_id = profile.wechat_id
    form.douyin_url = profile.douyin_url
    form.phone_num = profile.phone_num
    form.email = profile.email
    form.avatar_url = profile.avatar_url

    profileMeta.nickname = profile.nickname
    profileMeta.avatar_url = profile.avatar_url
    profileMeta.updated_at = profile.updated_at

    postTotal.value = posts.length
    keywords.value = kwList
  } catch (e) {
    ElMessage.error('加载主页信息失败')
  } finally {
    loading.value = false
  }
}

function onFileChange(uploadFile: UploadFile) {
  form.file = (uploadFile.raw as File) ?? null
}

function onFileRemove() {
  form.file = null
}

async function addKeyword() {
  const kw = newKeyword.value.trim()
  if (!kw) return
  kwSaving.value = true
  try {
    await http.post('/api/admin/keywords/', { keyword: kw })
    newKeyword.value = ''
    const { data } = await http.get<Array<{ id: number; keyword: string }>>('/api/admin/keywords/')
    keywords.value = data
    ElMessage.success('已添加')
  } catch (e) {
    ElMessage.error('添加失败')
  } finally {
    kwSaving.value = false
  }
}

async function removeKeyword(kw: { id: number; keyword: string }) {
  try {
    await http.delete(`/api/admin/keywords/${kw.id}/`)
    keywords.value = keywords.value.filter((k) => k.id !== kw.id)
    ElMessage.success('已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function save() {
  const nickname = form.nickname.trim()
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('nickname', nickname)
    fd.append('bio', form.bio.trim())
    fd.append('wechat_id', form.wechat_id.trim())
    fd.append('douyin_url', form.douyin_url.trim())
    fd.append('phone_num', form.phone_num.trim())
    fd.append('email', form.email.trim())
    if (form.file) fd.append('avatar', form.file)
    await http.put('/api/admin/profile/', fd)
    ElMessage.success('已保存')
    await loadProfile()
  } catch (e) {
    ElMessage.error('保存失败（需要管理员权限）')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  if (!authed.value) {
    await router.push('/admin/login')
    return
  }
  await loadProfile()
})
</script>

<template>
  <section class="page">
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else>
      <div class="overview-card">
        <div class="overview-left">
          <el-avatar
            v-if="profileMeta.avatar_url"
            :src="profileMeta.avatar_url"
            :size="72"
            class="overview-avatar"
          />
          <el-avatar v-else :size="72" class="overview-avatar">
            {{ (profileMeta.nickname || '我').slice(0, 1) }}
          </el-avatar>
          <div class="overview-name">{{ profileMeta.nickname || '未设置昵称' }}</div>
        </div>
        <div class="overview-stats">
          <div class="stat-block">
            <span class="stat-num">{{ postTotal }}</span>
            <span class="stat-label">动态总数</span>
          </div>
          <div class="stat-block">
            <span class="stat-num stat-num-sm">{{ timeAgo(profileMeta.updated_at) }}</span>
            <span class="stat-label">最近更新</span>
          </div>
        </div>
        <div class="overview-tags">
          <el-tag size="small" type="success">管理员</el-tag>
          <el-tag size="small" type="primary" v-if="postTotal > 0">已发布 {{ postTotal }} 条</el-tag>
          <el-tag size="small" type="info">在线</el-tag>
        </div>
      </div>

      <div class="card">
        <div class="title">编辑资料</div>
        <div class="form">
          <el-form label-position="top">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="昵称">
                  <el-input v-model="form.nickname" maxlength="32" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="头像">
                  <div class="avatar-row">
                    <el-avatar v-if="form.avatar_url" :src="form.avatar_url" :size="40" />
                    <el-avatar v-else :size="40">{{ (form.nickname || '我').slice(0, 1) }}</el-avatar>
                    <el-upload
                      :auto-upload="false"
                      :limit="1"
                      :on-change="onFileChange"
                      :on-remove="onFileRemove"
                    >
                      <el-button size="small">更换</el-button>
                    </el-upload>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="简介">
              <el-input v-model="form.bio" type="textarea" :rows="3" maxlength="200" show-word-limit />
            </el-form-item>
            <el-divider border-style="dashed" />
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="微信号">
                  <el-input v-model="form.wechat_id" maxlength="64" placeholder="your_wechat" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="联系邮箱">
                  <el-input v-model="form.email" maxlength="128" placeholder="example@email.com" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="抖音链接">
                  <el-input v-model="form.douyin_url" placeholder="https://www.douyin.com/user/xxx" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="电话">
                  <el-input v-model="form.phone_num" maxlength="32" placeholder="13800138000" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-button type="primary" :loading="saving" @click="save">保存</el-button>
          </el-form>
        </div>
      </div>

      <div class="card">
        <div class="title">拦截关键词库</div>
        <p class="card-desc">树洞小助手将自动拦截包含这些关键词的评论和留言</p>
        <div class="keyword-input-row">
          <el-input
            v-model="newKeyword"
            placeholder="输入要拦截的关键词"
            maxlength="64"
            @keyup.enter="addKeyword"
          />
          <el-button type="primary" :loading="kwSaving" :disabled="!newKeyword.trim()" @click="addKeyword">
            添加
          </el-button>
        </div>
        <div v-if="keywords.length" class="keyword-tags">
          <el-tag
            v-for="kw in keywords"
            :key="kw.id"
            closable
            size="default"
            type="danger"
            class="kw-tag"
            @close="removeKeyword(kw)"
          >
            {{ kw.keyword }}
          </el-tag>
        </div>
        <div v-else class="kw-empty">暂无拦截关键词，评论无需审核</div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.page {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px 28px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
  flex-wrap: wrap;
}

.overview-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.overview-avatar {
  flex-shrink: 0;
  border: 2px solid var(--border);
}

.overview-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-1);
}

.overview-stats {
  display: flex;
  gap: 28px;
  flex: 1;
}

.stat-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-num {
  font-size: 22px;
  font-weight: 800;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}

.stat-num-sm {
  font-size: 15px;
  color: var(--text-2);
}

.stat-label {
  font-size: 12px;
  color: var(--text-3);
}

.overview-tags {
  display: flex;
  gap: 6px;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 24px;
  box-shadow: var(--shadow-1);
}

.title {
  font-size: 17px;
  font-weight: 800;
  color: var(--text-1);
  margin-bottom: 16px;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-desc {
  font-size: 13px;
  color: var(--text-3);
  margin: 0 0 12px;
}

.keyword-input-row {
  display: flex;
  gap: 10px;
}

.keyword-input-row .el-input {
  flex: 1;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.kw-tag {
  cursor: pointer;
}

.kw-empty {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-3);
}
</style>
