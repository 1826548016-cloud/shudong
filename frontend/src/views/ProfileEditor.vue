<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadFile } from 'element-plus'

import { http } from '../api/http'

type ProfileAdmin = {
  nickname: string
  avatar_url: string | null
  bio: string
  wechat_id: string
  douyin_url: string
  phone_num: string
  updated_at: string
}

const router = useRouter()
const authed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const loading = ref(false)
const saving = ref(false)

const form = reactive<{
  nickname: string
  bio: string
  wechat_id: string
  douyin_url: string
  phone_num: string
  file: File | null
  avatar_url: string | null
}>({
  nickname: '',
  bio: '',
  wechat_id: '',
  douyin_url: '',
  phone_num: '',
  file: null,
  avatar_url: null,
})

async function loadProfile() {
  loading.value = true
  try {
    const { data } = await http.get<ProfileAdmin>('/api/admin/profile/')
    form.nickname = data.nickname
    form.bio = data.bio
    form.wechat_id = data.wechat_id
    form.douyin_url = data.douyin_url
    form.phone_num = data.phone_num
    form.avatar_url = data.avatar_url
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
    <div class="card">
      <div class="title">本人主页</div>
      <el-skeleton v-if="loading" :rows="6" animated />
      <div v-else class="form">
        <el-form label-position="top">
          <el-form-item label="昵称">
            <el-input v-model="form.nickname" maxlength="32" />
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="form.bio" maxlength="200" show-word-limit />
          </el-form-item>
          <el-form-item label="头像">
            <div class="avatar-row">
              <el-avatar v-if="form.avatar_url" :src="form.avatar_url" :size="56" />
              <el-avatar v-else :size="56">{{ (form.nickname || '我').slice(0, 1) }}</el-avatar>
              <el-upload
                :auto-upload="false"
                :limit="1"
                :on-change="onFileChange"
                :on-remove="onFileRemove"
              >
                <el-button>更换头像</el-button>
              </el-upload>
            </div>
          </el-form-item>
          <el-divider />
          <el-form-item label="微信号（游客可见）">
            <el-input v-model="form.wechat_id" maxlength="64" placeholder="例如：your_wechat" />
          </el-form-item>
          <el-form-item label="抖音链接（游客可见）">
            <el-input
              v-model="form.douyin_url"
              placeholder="例如：https://www.douyin.com/user/xxx"
            />
          </el-form-item>
          <el-form-item label="电话（仅管理员自用）">
            <el-input v-model="form.phone_num" maxlength="32" placeholder="例如：13800138000" />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        </el-form>
      </div>
    </div>
  </section>
</template>

<style scoped>
.page {
  display: grid;
  place-items: start center;
}

.card {
  width: min(720px, 100%);
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow-1);
}

.title {
  font-size: 18px;
  font-weight: 900;
  color: var(--text-1);
  margin-bottom: 10px;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
