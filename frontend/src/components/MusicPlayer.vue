<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  CaretRight,
  Close,
  DArrowLeft,
  DArrowRight,
  Headset,
  List,
  VideoPause,
  VideoCamera,
} from '@element-plus/icons-vue'

import { usePlayer } from '../composables/usePlayer'

const player = usePlayer()
const { state, togglePlay, playMusic, seek, nextTrack, prevTrack } = player

const router = useRouter()

const mediaEl = ref<HTMLVideoElement | null>(null)
watch(mediaEl, (el) => {
  if (el) player.setMediaRef(el)
}, { immediate: true })

const showList = ref(false)
const dragging = ref(false)
const showVideo = ref(false)
const progressRef = ref<HTMLElement | null>(null)
const expanded = ref(false)

const progressPercent = computed(() => {
  if (!state.duration) return 0
  return (state.currentTime / state.duration) * 100
})

const currentTimeText = computed(() => formatTime(state.currentTime))
const durationText = computed(() => formatTime(state.duration))

const isVideoItem = computed(() => {
  if (!state.current) return false
  return isVideoFile(state.current.file_url)
})

function formatTime(seconds: number): string {
  if (!seconds || !isFinite(seconds)) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function onProgressClick(e: MouseEvent) {
  if (!progressRef.value || !state.duration) return
  const rect = progressRef.value.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  seek(ratio * state.duration)
}

function onProgressDrag(e: MouseEvent) {
  if (!dragging.value || !progressRef.value || !state.duration) return
  const rect = progressRef.value.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  seek(ratio * state.duration)
}

function startDrag(e: MouseEvent) {
  dragging.value = true
  onProgressClick(e)
  document.addEventListener('mousemove', onProgressDrag)
  document.addEventListener('mouseup', stopDrag)
}

function stopDrag() {
  dragging.value = false
  document.removeEventListener('mousemove', onProgressDrag)
  document.removeEventListener('mouseup', stopDrag)
}

function goLibrary() {
  router.push('/music')
}

function isVideoFile(url: string): boolean {
  return /\.(mp4|webm|mov|avi|mkv)$/i.test(url)
}

function openVideo() {
  player.pauseForMedia()
  showVideo.value = true
}

function closeVideo() {
  showVideo.value = false
  player.resumeAfterMedia()
}
</script>

<template>
  <Teleport to="body">
    <video
      ref="mediaEl"
      preload="metadata"
      class="player-media"
      playsinline
    ></video>
  </Teleport>

  <Transition name="player-slide">
    <div
      v-if="state.current"
      class="music-player"
      :class="{ expanded }"
      @mouseenter="expanded = true"
      @mouseleave="expanded = false"
      @click="expanded = true"
    >
      <div class="player-body">
        <div class="player-top" @click="isVideoItem ? openVideo() : goLibrary()">
          <div class="player-icon">
            <el-icon :size="18">
              <VideoCamera v-if="isVideoItem" />
              <Headset v-else />
            </el-icon>
          </div>
          <div class="player-text">
            <div class="player-title">{{ state.current.title }}</div>
            <div class="player-artist">{{ state.current.artist }}</div>
          </div>
        </div>

        <div class="player-progress-wrap">
          <span class="player-time-text">{{ currentTimeText }} / {{ durationText }}</span>
          <div
            ref="progressRef"
            class="player-progress"
            @mousedown="startDrag"
          >
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
              <div class="progress-thumb" :style="{ left: progressPercent + '%' }"></div>
            </div>
          </div>
        </div>

        <div class="player-controls">
          <button class="ctrl-btn" type="button" title="上一首" @click.stop="prevTrack">
            <el-icon :size="16"><DArrowLeft /></el-icon>
          </button>
          <button
            class="ctrl-btn ctrl-btn-play"
            type="button"
            @click.stop="togglePlay"
          >
            <el-icon :size="20">
              <VideoPause v-if="state.playing" />
              <CaretRight v-else />
            </el-icon>
          </button>
          <button class="ctrl-btn" type="button" title="下一首" @click.stop="nextTrack">
            <el-icon :size="16"><DArrowRight /></el-icon>
          </button>
        </div>

        <div class="player-bottom">
          <button
            class="ctrl-btn"
            type="button"
            title="播放列表"
            @click.stop="showList = !showList"
          >
            <el-icon :size="16"><List /></el-icon>
            <span class="list-count">{{ state.playlist.length }}</span>
          </button>
        </div>
      </div>

      <Transition name="list-fade">
        <div v-if="showList && state.playlist.length" class="player-playlist">
          <div class="playlist-header">
            <span>播放列表（{{ state.playlist.length }}）</span>
            <button class="ctrl-btn" type="button" @click="showList = false">关闭</button>
          </div>
          <div class="playlist-items">
            <div
              v-for="(item, idx) in state.playlist"
              :key="item.id"
              class="playlist-item"
              :class="{ active: state.current?.id === item.id }"
              @click="playMusic(item)"
            >
              <span class="playlist-idx">{{ idx + 1 }}</span>
              <div class="playlist-info">
                <div class="playlist-title">{{ item.title }}</div>
                <div class="playlist-artist">{{ item.artist }}</div>
              </div>
              <span class="playlist-dur">{{ formatTime(item.duration) }}</span>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>

  <Teleport to="body">
    <Transition name="fade">
      <div v-if="showVideo && state.current" class="video-overlay" @click.self="closeVideo">
        <div class="video-header">
          <span class="video-title">{{ state.current.title }}</span>
          <button class="video-close" type="button" @click="closeVideo">
            <el-icon :size="20"><Close /></el-icon>
          </button>
        </div>
        <div class="video-container">
          <video
            :src="state.current.file_url"
            controls
            autoplay
            class="video-player"
          ></video>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.player-media {
  position: fixed;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

/* ===== 桌面端：右侧固定 ===== */
.music-player {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 200;
  width: 56px;
  border-radius: 12px 0 0 12px;
  background: rgba(255,255,255,.82);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border: 1px solid var(--border);
  border-right: none;
  box-shadow: -2px 0 16px rgba(0,0,0,.06);
  transition: width .25s cubic-bezier(.16,1,.3,1);
  overflow: hidden;
}

html.dark .music-player {
  background: rgba(26,28,35,.88);
}

.music-player.expanded {
  width: 240px;
}

.player-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 14px 10px;
  min-height: 240px;
}

.player-top {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  width: 100%;
}

.player-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.player-text {
  text-align: center;
  width: 100%;
  opacity: 0;
  transition: opacity .15s;
  overflow: hidden;
}

.expanded .player-text {
  opacity: 1;
}

.player-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.player-artist {
  font-size: 11px;
  color: var(--text-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

.player-progress-wrap {
  width: 100%;
  opacity: 0;
  transition: opacity .15s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.expanded .player-progress-wrap {
  opacity: 1;
}

.player-progress {
  width: 100%;
  height: 6px;
  cursor: pointer;
  position: relative;
}

.player-time-text {
  font-size: 10px;
  color: var(--text-3);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.progress-track {
  position: absolute;
  inset: 3px 0 0;
  height: 3px;
  background: rgba(0,0,0,.08);
  border-radius: 2px;
  overflow: visible;
}

html.dark .progress-track {
  background: rgba(255,255,255,.1);
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 2px;
  transition: width .1s linear;
}

.progress-thumb {
  position: absolute;
  top: 50%;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid var(--primary);
  transform: translate(-50%, -50%);
  box-shadow: 0 1px 4px rgba(0,0,0,.15);
  opacity: 0;
  transition: opacity .15s;
}

.player-progress:hover .progress-thumb {
  opacity: 1;
}

.player-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.ctrl-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  border-radius: 8px;
  color: var(--text-2);
  display: flex;
  align-items: center;
  gap: 4px;
  transition: background .15s;
}

.ctrl-btn:hover {
  background: rgba(0,0,0,.05);
  color: var(--text-1);
}

html.dark .ctrl-btn:hover {
  background: rgba(255,255,255,.06);
}

.ctrl-btn-play {
  background: var(--primary);
  color: #fff;
  width: 34px;
  height: 34px;
  justify-content: center;
}

.ctrl-btn-play:hover {
  background: var(--primary) !important;
  opacity: .9;
  color: #fff !important;
}

.player-bottom {
  flex-shrink: 0;
}

.list-count {
  font-size: 11px;
  font-weight: 600;
}

/* ===== 播放列表弹窗（桌面右侧展开）===== */
.player-playlist {
  position: absolute;
  right: 100%;
  top: 0;
  width: 280px;
  max-height: 400px;
  background: rgba(255,255,255,.97);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border);
  border-radius: 12px 0 0 12px;
  box-shadow: -8px 0 24px rgba(0,0,0,.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

html.dark .player-playlist {
  background: rgba(26,28,35,.97);
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-1);
  border-bottom: 1px solid var(--border);
}

.playlist-items {
  overflow-y: auto;
  flex: 1;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background .1s;
}

.playlist-item:hover {
  background: rgba(0,0,0,.03);
}

html.dark .playlist-item:hover {
  background: rgba(255,255,255,.04);
}

.playlist-item.active {
  background: var(--primary-light);
}

.playlist-idx {
  width: 20px;
  text-align: center;
  font-size: 12px;
  color: var(--text-3);
  flex-shrink: 0;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.playlist-artist {
  font-size: 11px;
  color: var(--text-3);
}

.playlist-dur {
  font-size: 12px;
  color: var(--text-3);
  flex-shrink: 0;
}

/* ===== 视频弹窗 ===== */
.video-overlay {
  position: fixed;
  inset: 0;
  z-index: 100001;
  background: rgba(0,0,0,.88);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.video-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 900px;
  padding: 16px 24px;
}

.video-title {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.video-close {
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  transition: background .15s;
}

.video-close:hover {
  background: rgba(255,255,255,.12);
}

.video-container {
  width: 100%;
  max-width: 900px;
  max-height: 80vh;
}

.video-player {
  width: 100%;
  max-height: 80vh;
  border-radius: 8px;
}

/* ===== 动画 ===== */
.player-slide-enter-active,
.player-slide-leave-active {
  transition: opacity .3s ease, transform .3s ease;
}

.player-slide-enter-from,
.player-slide-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(60px);
}

.list-fade-enter-active,
.list-fade-leave-active {
  transition: opacity .2s, transform .2s;
}

.list-fade-enter-from,
.list-fade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity .3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ===== 手机端：底部横条 ===== */
@media (max-width: 767px) {
  .music-player {
    right: 0;
    bottom: 42px;
    top: auto;
    transform: none;
    width: 100%;
    border-radius: 0;
    border: none;
    border-top: 1px solid var(--border);
    box-shadow: 0 -2px 12px rgba(0,0,0,.04);
    transition: none;
  }

  .music-player.expanded {
    width: 100%;
  }

  .player-body {
    flex-direction: row;
    gap: 10px;
    padding: 8px 14px;
    min-height: auto;
    height: 52px;
  }

  .player-top {
    flex-direction: row;
    gap: 10px;
    flex: 1;
    min-width: 0;
  }

  .player-text {
    opacity: 1;
    text-align: left;
  }

  .player-title {
    font-size: 13px;
  }

  .player-progress-wrap {
    display: none;
  }

  .expanded .player-progress-wrap {
    display: none;
  }

  .player-controls {
    flex-direction: row;
    gap: 2px;
  }

  .player-playlist {
    right: 14px;
    bottom: 100%;
    top: auto;
    width: calc(100vw - 28px);
    max-height: 340px;
    border-radius: 12px 12px 0 0;
    box-shadow: 0 -8px 24px rgba(0,0,0,.08);
  }

  .player-slide-enter-active,
  .player-slide-leave-active {
    transition: opacity .3s, transform .3s;
  }

  .player-slide-enter-from,
  .player-slide-leave-to {
    opacity: 0;
    transform: translateY(60px);
  }
}
</style>
