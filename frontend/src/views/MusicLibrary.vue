<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Delete, Headset, VideoCamera } from '@element-plus/icons-vue'
import { ElMessage, type UploadFile } from 'element-plus'

import { deleteMusic, fetchMusicList, uploadMusic, type MusicItem } from '../api/music'
import { usePlayer } from '../composables/usePlayer'

const { playMusic, state } = usePlayer()

const list = ref<MusicItem[]>([])
const loading = ref(false)
const isAuthed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const uploadFile = ref<File | null>(null)
const uploadTitle = ref('')
const uploadArtist = ref('')
const uploading = ref(false)

async function load() {
  loading.value = true
  try {
    list.value = await fetchMusicList()
  } catch (e) {
    ElMessage.error('加载音乐列表失败')
  } finally {
    loading.value = false
  }
}

function play(item: MusicItem) {
  playMusic(item)
}

function formatTime(seconds: number): string {
  if (!seconds || !isFinite(seconds)) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function onFileChange(uploadFileObj: UploadFile) {
  uploadFile.value = (uploadFileObj.raw as File) ?? null
  if (uploadFile.value && !uploadTitle.value) {
    const name = uploadFile.value.name
    uploadTitle.value = name.replace(/\.(mp3|mp4|wav|flac|ogg|aac|wma|m4a|webm|mov)$/i, '')
  }
}

function onFileRemove() {
  uploadFile.value = null
}

async function submitUpload() {
  if (!uploadFile.value) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('title', uploadTitle.value.trim() || uploadFile.value.name)
    formData.append('artist', uploadArtist.value.trim() || '未知艺术家')
    formData.append('file', uploadFile.value)
    await uploadMusic(formData)
    ElMessage.success('上传成功')
    uploadFile.value = null
    uploadTitle.value = ''
    uploadArtist.value = ''
    await load()
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

async function remove(id: number) {
  try {
    await deleteMusic(id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function isVideoFile(url: string): boolean {
  return /\.(mp4|webm|mov|avi|mkv)$/i.test(url)
}

function playAll() {
  if (list.value.length === 0) return
  playMusic(list.value[0])
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="page-wrap">
    <div class="bg-overlay"></div>

    <section class="page">
      <div class="page-head">
        <div class="page-title">🎵 音乐盒</div>
        <div class="page-subtitle">本地音乐，随时听</div>
      </div>

    <div v-if="list.length" class="play-all-bar">
      <el-button type="primary" @click="playAll">▶ 播放全部（{{ list.length }}）</el-button>
    </div>

    <div v-if="isAuthed" class="upload-card">
      <div class="card-title">上传音乐</div>
      <div class="upload-form">
        <div class="form-row">
          <el-input v-model="uploadTitle" placeholder="歌曲名称（选填，默认文件名）" maxlength="128" />
          <el-input v-model="uploadArtist" placeholder="艺术家（选填）" maxlength="64" />
        </div>
        <div class="form-row">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
            accept="audio/*,video/mp4,video/webm,video/quicktime"
          >
            <el-button>选择音乐/视频文件</el-button>
          </el-upload>
          <el-button type="primary" :loading="uploading" :disabled="!uploadFile" @click="submitUpload">
            上传
          </el-button>
        </div>
      </div>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />
    <div v-else class="music-list">
      <div
        v-for="item in list"
        :key="item.id"
        class="music-row"
        :class="{ active: state.current?.id === item.id }"
        @click="play(item)"
      >
        <div class="music-cover">
          <el-icon :size="20">
            <VideoCamera v-if="isVideoFile(item.file_url)" />
            <Headset v-else />
          </el-icon>
        </div>
        <div class="music-info">
          <div class="music-title">{{ item.title }}</div>
          <div class="music-artist">{{ item.artist }}</div>
        </div>
        <div class="music-meta">
          <span class="music-dur">{{ formatTime(item.duration) }}</span>
          <el-button
            v-if="isAuthed"
            :icon="Delete"
            text
            type="danger"
            size="small"
            @click.stop="remove(item.id)"
          >
            删除
          </el-button>
        </div>
      </div>
      <div v-if="list.length === 0" class="empty">还没有音乐，去上传一些吧 🎶</div>
    </div>
  </section>
  </div>
</template>

<style scoped>
.page-wrap {
  min-height: calc(100vh - 56px);
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

.page {
  position: relative;
  z-index: 2;
  max-width: 640px;
  margin: 0 auto;
  padding: 20px 20px 80px;
}

.page-head {
  margin-bottom: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-1);
}

.page-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-3);
}

.play-all-bar {
  margin-bottom: 14px;
}

.upload-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card-bg);
  padding: 16px;
  margin-bottom: 14px;
  box-shadow: var(--shadow-1);
}

.card-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-1);
  margin-bottom: 12px;
}

.upload-form {
  display: grid;
  gap: 10px;
}

.form-row {
  display: flex;
  gap: 10px;
}

.music-list {
  display: grid;
  gap: 8px;
}

.music-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.3s, box-shadow 0.3s, transform 0.3s;
}

.music-row:hover {
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(22, 100, 255, 0.06);
  transform: translateY(-2px);
}

.music-row.active {
  background: rgba(22, 100, 255, 0.06);
  border-color: rgba(22, 100, 255, 0.15);
}

.music-cover {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.music-info {
  flex: 1;
  min-width: 0;
}

.music-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.music-artist {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
}

.music-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.music-dur {
  font-size: 12px;
  color: var(--text-3);
  font-variant-numeric: tabular-nums;
}

.empty {
  text-align: center;
  padding: 40px 0;
  color: var(--text-3);
  font-size: 14px;
}

@media (max-width: 640px) {
  .form-row {
    flex-direction: column;
  }
}
</style>
