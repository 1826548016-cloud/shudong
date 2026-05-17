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
      '/api/admin/login/',
      {
        username: form.username,
        password: form.password,
      },
    )
    localStorage.setItem('treehole_token', data.access)
    localStorage.setItem('treehole_refresh', data.refresh)
    ElMessage.success('登录成功')
    await router.push('/')
  } catch (e) {
    ElMessage.error('登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page">
    <div class="bg-mask"></div>
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
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

.bg-img {
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

.bg-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1;
  background: rgba(0, 0, 0, 0.6);
  pointer-events: none;
}

.card {
  position: relative;
  z-index: 2;
  width: min(420px, 100%);
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius);
  padding: 28px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12);
}

.title {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-1);
  margin-bottom: 10px;
}
</style>
