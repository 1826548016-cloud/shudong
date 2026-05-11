<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { http } from '../api/http'

const router = useRouter()

const form = reactive({
  username: '',
  password: '',
})

const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) return

  loading.value = true
  try {
    const { data } = await http.post<{ access: string; refresh: string }>(
      '/api/auth/token/',
      {
        username: form.username,
        password: form.password,
      },
    )
    localStorage.setItem('treehole_token', data.access)
    localStorage.setItem('treehole_refresh', data.refresh)
    ElMessage.success('登录成功')
    await router.push('/admin/editor')
  } catch (e) {
    ElMessage.error('登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page">
    <div class="card">
      <div class="title">管理员登录</div>
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            autocomplete="current-password"
          />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="submit">
          登录
        </el-button>
      </el-form>
    </div>
  </section>
</template>

<style scoped>
.page {
  display: grid;
  place-items: start center;
}

.card {
  width: min(420px, 100%);
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow-1);
}

.title {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-1);
  margin-bottom: 10px;
}
</style>
