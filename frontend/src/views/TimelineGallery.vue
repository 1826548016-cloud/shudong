<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { http } from '../api/http'

const router = useRouter()

type TimelineItem = {
  id: number
  file_url: string
  media_type: 'image' | 'video'
  caption: string
  shot_at: string
  created_at: string
}

const isAuthed = computed(() => Boolean(localStorage.getItem('treehole_token')))

const items = ref<TimelineItem[]>([])
const loading = ref(true)

const previewIndex = ref(-1)
const previewVisible = ref(false)

const uploadOpen = ref(false)
const uploadFile = ref<File | null>(null)
const uploadCaption = ref('')
const uploadShotAt = ref('')
const uploadSaving = ref(false)

const editItem = ref<TimelineItem | null>(null)
const editCaption = ref('')
const editShotAt = ref('')
const editSaving = ref(false)
const editOpen = ref(false)
const editFile = ref<File | null>(null)

const axisRef = ref<HTMLElement | null>(null)
let scrollTimer: ReturnType<typeof setInterval> | null = null

async function loadItems() {
  loading.value = true
  try {
    const { data } = await http.get<TimelineItem[]>('/api/timeline/')
    items.value = data
  } catch (e) {
    ElMessage.error('加载图库失败')
  } finally {
    loading.value = false
  }
}

const sortedItems = computed(() =>
  [...items.value].sort(
    (a, b) => new Date(a.shot_at).getTime() - new Date(b.shot_at).getTime(),
  ),
)

type DayGroup = {
  dateLabel: string
  dateValue: string
  items: TimelineItem[]
}

const dayGroups = computed(() => {
  const map = new Map<string, TimelineItem[]>()
  for (const item of sortedItems.value) {
    const key = item.shot_at.slice(0, 10)
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(item)
  }
  const groups: DayGroup[] = []
  for (const [dateValue, dayItems] of map) {
    const d = new Date(dateValue)
    const label = `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
    groups.push({ dateLabel: label, dateValue, items: dayItems })
  }
  groups.sort((a, b) => a.dateValue.localeCompare(b.dateValue))
  return groups
})

function formatTime(iso: string): string {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function openPreview(index: number) {
  stopScroll()
  previewIndex.value = index
  previewVisible.value = true
}

function prevPreview() {
  if (previewIndex.value > 0) previewIndex.value--
}

function nextPreview() {
  if (previewIndex.value < sortedItems.value.length - 1) previewIndex.value++
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files?.[0]) return
  uploadFile.value = target.files[0]
}

async function uploadSubmit() {
  if (!uploadFile.value) { ElMessage.warning('请选择文件'); return }
  if (!uploadShotAt.value) { ElMessage.warning('请选择拍摄时间'); return }
  uploadSaving.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadFile.value)
    fd.append('media_type', uploadFile.value.type.startsWith('video/') ? 'video' : 'image')
    fd.append('caption', uploadCaption.value.trim())
    fd.append('shot_at', uploadShotAt.value)
    await http.post('/api/timeline/', fd)
    ElMessage.success('上传成功')
    uploadOpen.value = false
    uploadFile.value = null
    uploadCaption.value = ''
    uploadShotAt.value = ''
    await loadItems()
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    uploadSaving.value = false
  }
}

function openEdit(item: TimelineItem) {
  editItem.value = item
  editCaption.value = item.caption
  editShotAt.value = item.shot_at.slice(0, 16)
  editFile.value = null
  editOpen.value = true
}

function onEditFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files?.[0]) return
  editFile.value = target.files[0]
}

async function saveEdit() {
  if (!editItem.value) return
  editSaving.value = true
  try {
    const fd = new FormData()
    fd.append('caption', editCaption.value.trim())
    fd.append('shot_at', editShotAt.value)
    if (editFile.value) {
      fd.append('file', editFile.value)
      fd.append('media_type', editFile.value.type.startsWith('video/') ? 'video' : 'image')
    }
    await http.patch(`/api/timeline/${editItem.value.id}/edit/`, fd)
    ElMessage.success('已更新')
    editOpen.value = false
    editFile.value = null
    await loadItems()
  } catch (e) {
    ElMessage.error('更新失败')
  } finally {
    editSaving.value = false
  }
}

async function deleteItem(id: number) {
  try {
    await http.delete(`/api/timeline/${id}/`)
    ElMessage.success('已删除')
    if (previewVisible.value) previewVisible.value = false
    await loadItems()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function startScroll() {
  stopScroll()
  scrollTimer = setInterval(() => {
    const el = axisRef.value
    if (!el) return
    const max = el.scrollHeight - el.clientHeight
    if (max <= 0) return
    const next = el.scrollTop + 1
    if (next >= max) {
      el.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      el.scrollTo({ top: next, behavior: 'smooth' })
    }
  }, 50)
}

function stopScroll() {
  if (scrollTimer) { clearInterval(scrollTimer); scrollTimer = null }
}

function toggleScroll() {
  if (scrollTimer) stopScroll(); else startScroll()
}

function goBack() { router.push('/') }

onMounted(() => { void loadItems() })
onUnmounted(() => { stopScroll() })
</script>

<template>
  <div class="page">
    <div class="bg-mask"></div>
    <!-- Top bar -->
    <header class="topbar">
      <button class="tb-btn" @click="goBack">←</button>
      <span class="tb-title">时光轴</span>
      <span class="tb-count">{{ sortedItems.length }} 项</span>
      <div class="tb-spacer"></div>
      <button class="tb-act" @click="toggleScroll">{{ scrollTimer ? '⏸' : '▶' }}</button>
      <button v-if="isAuthed" class="tb-act tb-upload" @click="uploadOpen = true">＋上传</button>
    </header>

    <!-- Main scroll area -->
    <div
      ref="axisRef"
      class="scroll-area"
      @mouseenter="stopScroll"
      @mouseleave="startScroll"
    >
      <div v-if="loading" class="center-text">加载中…</div>
      <div v-else-if="!sortedItems.length" class="center-text">
        <div class="empty-icon">📸</div>
        <p>时光轴还是空的</p>
        <p v-if="isAuthed" class="sub">点击右上角「＋上传」添加</p>
        <p v-else class="sub">等待主人上传精彩瞬间</p>
      </div>

      <!-- Timeline: each day = one row -->
      <div v-else class="timeline">
        <div v-for="(day, di) in dayGroups" :key="day.dateValue" class="day-row">
          <!-- Y-axis label -->
          <div class="day-label">
            <div class="day-dot"></div>
            <div class="day-text">{{ day.dateLabel }}</div>
          </div>

          <!-- X-axis: multi-image grid, preserve ratio -->
          <div class="day-grid" :style="{ '--n': day.items.length }">
            <div
              v-for="(item, ii) in day.items"
              :key="item.id"
              class="grid-cell"
              :class="{ is_video: item.media_type === 'video' }"
              :style="{ '--i': di * 100 + ii }"
              @click="openPreview(sortedItems.indexOf(item))"
            >
              <img
                v-if="item.media_type === 'image'"
                :src="item.file_url"
                :alt="item.caption"
                class="cell-media"
                loading="lazy"
              />
              <div v-else class="vid-wrap">
                <video :src="item.file_url" muted preload="metadata" class="cell-media"></video>
                <span class="vid-play">▶</span>
              </div>
              <div class="cell-meta">
                <span class="cell-time">{{ formatTime(item.shot_at) }}</span>
                <span v-if="item.caption" class="cell-cap">{{ item.caption }}</span>
              </div>
              <div v-if="isAuthed" class="cell-admin">
                <button class="cell-btn edit" @click.stop="openEdit(item)">✎</button>
                <button class="cell-btn del" @click.stop="deleteItem(item.id)">×</button>
              </div>
            </div>
          </div>
        </div>
        <div class="end-line">—— 已经到底了 ——</div>
      </div>
    </div>

    <!-- Upload dialog -->
    <Teleport to="body">
      <div v-if="uploadOpen" class="overlay" @click.self="uploadOpen = false">
        <div class="modal">
          <div class="modal-title">上传</div>
          <div class="modal-body">
            <label class="fld"><span>文件</span><input type="file" accept="image/*,video/*" @change="onFileSelect" /></label>
            <label class="fld"><span>拍摄时间 *</span><input v-model="uploadShotAt" type="datetime-local" class="inp" /></label>
            <label class="fld"><span>备注</span><input v-model="uploadCaption" type="text" class="inp" maxlength="200" placeholder="写点什么…" /></label>
          </div>
          <div class="modal-acts">
            <button class="mbtn" @click="uploadOpen = false">取消</button>
            <button class="mbtn prim" :disabled="uploadSaving" @click="uploadSubmit">{{ uploadSaving ? '上传中…' : '上传' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Edit dialog -->
    <Teleport to="body">
      <div v-if="editOpen" class="overlay" @click.self="editOpen = false">
        <div class="modal">
          <div class="modal-title">编辑信息</div>
          <div class="modal-body">
            <label class="fld"><span>拍摄时间</span><input v-model="editShotAt" type="datetime-local" class="inp" /></label>
            <label class="fld"><span>备注</span><input v-model="editCaption" type="text" class="inp" maxlength="200" /></label>
            <label class="fld"><span>替换文件</span><input type="file" accept="image/*,video/*" @change="onEditFileSelect" /></label>
            <p v-if="editFile" class="edit-file-name">已选择：{{ editFile.name }}</p>
          </div>
          <div class="modal-acts">
            <button class="mbtn" @click="editOpen = false">取消</button>
            <button class="mbtn prim" :disabled="editSaving" @click="saveEdit">{{ editSaving ? '保存中…' : '保存' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Preview lightbox -->
    <Teleport to="body">
      <div v-if="previewVisible && sortedItems[previewIndex]" class="overlay preview-overlay" @click.self="previewVisible = false">
        <button class="pv-close" @click="previewVisible = false">×</button>
        <button v-if="previewIndex > 0" class="pv-nav prev" @click="prevPreview">‹</button>
        <button v-if="previewIndex < sortedItems.length - 1" class="pv-nav next" @click="nextPreview">›</button>
        <div class="pv-body">
          <img v-if="sortedItems[previewIndex].media_type === 'image'" :src="sortedItems[previewIndex].file_url" class="pv-media" style="object-fit:contain" />
          <video v-else :src="sortedItems[previewIndex].file_url" class="pv-media" controls autoplay></video>
        </div>
        <div class="pv-footer">
          <span>{{ sortedItems[previewIndex].shot_at.slice(0, 16).replace('T', ' ') }}</span>
          <span v-if="sortedItems[previewIndex].caption">{{ sortedItems[previewIndex].caption }}</span>
          <span class="pv-count">{{ previewIndex + 1 }} / {{ sortedItems.length }}</span>
          <button v-if="isAuthed" class="pv-del" @click="deleteItem(sortedItems[previewIndex].id)">删除</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* ===== Reset ===== */
.page { min-height: 100vh; color: #e4e6eb; display: flex; flex-direction: column; position: relative; }

.bg-img {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0;
  background-size: cover; background-position: center; background-repeat: no-repeat;
  pointer-events: none;
}
.bg-mask {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1;
  background: rgba(0,0,0,.55); pointer-events: none;
}

.topbar { position: relative; z-index: 11; display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  background: rgba(255,255,255,.04); border-bottom: 1px solid rgba(255,255,255,.06);
  position: sticky; top: 0; backdrop-filter: blur(12px); flex-shrink: 0; }
.scroll-area { position: relative; z-index: 2; }

.tb-btn { background: none; border: none; color: #8a93a0; font-size: 16px; cursor: pointer; padding: 4px 8px; border-radius: 8px; }
.tb-btn:hover { color: #e4e6eb; background: rgba(255,255,255,.06); }
.tb-title { font-size: 16px; font-weight: 700; letter-spacing: -.3px; }
.tb-count { font-size: 12px; color: #6b7280; }
.tb-spacer { flex: 1; }
.tb-act {
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: #e4e6eb;
  font-size: 12px; padding: 5px 14px; border-radius: 18px; cursor: pointer; transition: background .2s;
}
.tb-act:hover { background: rgba(255,255,255,.12); }
.tb-upload { background: #1664ff; border-color: #1664ff; }
.tb-upload:hover { background: #1d4ed8; }

/* ===== Scroll area ===== */
.scroll-area { flex: 1; overflow-y: auto; padding: 16px; max-width: 960px; margin: 0 auto; width: 100%; box-sizing: border-box; }
.center-text { text-align: center; padding: 80px 20px; }
.center-text p { margin: 6px 0 0; font-size: 15px; }
.center-text .sub { font-size: 13px; color: #6b7280; }
.empty-icon { font-size: 52px; margin-bottom: 8px; }

/* ===== Timeline layout ===== */
.timeline { position: relative; }

/* — Day row — */
.day-row {
  position: relative;
  margin-bottom: 20px;
  padding-left: 56px;
}

/* —— Y-axis label + dot —— */
.day-label {
  position: absolute; left: 0; top: 4px; display: flex; align-items: flex-start; gap: 10px;
  width: 56px;
}
.day-dot {
  width: 12px; height: 12px; border-radius: 50%; background: #1664ff; flex-shrink: 0; margin-top: 4px;
  box-shadow: 0 0 0 3px rgba(22,100,255,.2), 0 0 0 6px rgba(22,100,255,.08);
}
.day-text {
  writing-mode: vertical-rl; font-size: 11px; font-weight: 600; color: #9ca3af;
  letter-spacing: 2px; line-height: 1.2; margin-top: 2px;
}

/* vertical line */
.day-row::before {
  content: ''; position: absolute; left: 5px; top: 20px; bottom: -20px; width: 2px;
  background: linear-gradient(to bottom, rgba(22,100,255,.3), rgba(22,100,255,.05));
}
.day-row:last-child::before { display: none; }

/* —— X-axis multi-image grid —— */
.day-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.day-grid:empty { display: none; }

.grid-cell {
  position: relative;
  flex: 1 1 calc(50% - 5px);
  min-width: 160px;
  max-width: 100%;
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform .2s, background .2s;
  animation: fadeUp .4s ease both;
  animation-delay: calc(var(--i, 0) * .02s);
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.grid-cell:hover { background: rgba(255,255,255,.07); transform: translateY(-2px); }

/* 3+ items: use 1/3 width */
@media (min-width: 601px) {
  .grid-cell { flex: 1 1 calc(33.33% - 7px); }
  .grid-cell:only-child { flex: 1 1 100%; }
  .grid-cell:first-child:nth-last-child(2),
  .grid-cell:first-child:nth-last-child(2) ~ .grid-cell { flex: 1 1 calc(50% - 5px); }
}

.cell-media {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 12px 12px 0 0;
}

.vid-wrap { position: relative; line-height: 0; }
.vid-play {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 40px; height: 40px; border-radius: 50%; background: rgba(0,0,0,.6);
  color: #fff; font-size: 18px; display: flex; align-items: center; justify-content: center;
  pointer-events: none;
}

.cell-meta { padding: 8px 10px 10px; display: flex; flex-wrap: wrap; gap: 4px 8px; font-size: 12px; }
.cell-time { color: #6b7280; }
.cell-cap { color: #9ca3af; width: 100%; line-height: 1.4; }

.cell-admin {
  position: absolute; top: 6px; right: 6px; display: flex; gap: 4px; opacity: 0; transition: opacity .2s;
}
.grid-cell:hover .cell-admin { opacity: 1; }
.cell-btn {
  width: 26px; height: 26px; border-radius: 50%; border: none; font-size: 14px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,.55); color: #fff;
}
.cell-btn.edit { font-size: 13px; }
.cell-btn:hover { background: rgba(0,0,0,.8); }

.end-line { text-align: center; padding: 20px 0 40px; font-size: 13px; color: #4b5563; }

/* ===== Modals ===== */
.overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,.7); display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(6px);
}
.modal {
  background: #1a1a24; border: 1px solid rgba(255,255,255,.1); border-radius: 16px;
  padding: 24px; width: min(400px, 90vw); max-height: 90vh; overflow-y: auto;
}
.modal-title { font-size: 17px; font-weight: 700; margin-bottom: 16px; }
.modal-body { display: flex; flex-direction: column; gap: 14px; }
.fld { display: flex; flex-direction: column; gap: 4px; }
.fld span { font-size: 12px; color: #8a93a0; font-weight: 500; }
.inp {
  width: 100%; padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,.15);
  background: rgba(255,255,255,.05); color: #e4e6eb; font-size: 14px; box-sizing: border-box;
}
.inp:focus { border-color: #1664ff; outline: none; }
.fld input[type='file'] { font-size: 13px; color: #9ca3af; }
.edit-file-name { font-size: 12px; color: #22c55e; margin: 0; }
.modal-acts { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.mbtn { padding: 8px 22px; border-radius: 20px; border: none; font-size: 14px; cursor: pointer; }
.mbtn.prim { background: #1664ff; color: #fff; font-weight: 600; }
.mbtn.prim:disabled { opacity: .5; cursor: not-allowed; }

/* ===== Preview ===== */
.preview-overlay { cursor: pointer; }
.pv-close {
  position: fixed; top: 14px; right: 14px; z-index: 1001;
  width: 38px; height: 38px; border-radius: 50%; border: none;
  background: rgba(0,0,0,.5); color: #fff; font-size: 22px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.pv-nav {
  position: fixed; top: 50%; transform: translateY(-50%); z-index: 1001;
  width: 44px; height: 44px; border-radius: 50%; border: none;
  background: rgba(0,0,0,.4); color: #fff; font-size: 28px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.pv-nav.prev { left: 12px; }
.pv-nav.next { right: 12px; }
.pv-body { display: flex; align-items: center; justify-content: center; max-width: 92vw; max-height: 78vh; }
.pv-media { max-width: 92vw; max-height: 78vh; object-fit: contain; border-radius: 8px; }
.pv-footer {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 1001;
  display: flex; justify-content: center; gap: 14px; flex-wrap: wrap;
  padding: 12px 16px; background: linear-gradient(transparent, rgba(0,0,0,.6));
  color: #d1d5db; font-size: 13px;
}
.pv-count { color: #6b7280; }
.pv-del {
  background: rgba(239,68,68,.4); border: none; color: #fca5a5;
  padding: 2px 12px; border-radius: 12px; font-size: 12px; cursor: pointer;
}
.pv-del:hover { background: rgba(239,68,68,.6); }

/* ===== Responsive ===== */
@media (max-width: 600px) {
  .day-row { padding-left: 40px; margin-bottom: 14px; }
  .day-label { width: 40px; }
  .day-dot { width: 10px; height: 10px; margin-top: 3px; }
  .day-text { font-size: 10px; letter-spacing: 1px; }
  .day-row::before { left: 4px; top: 16px; bottom: -14px; }
  .day-grid { gap: 8px; }
  .grid-cell { flex: 1 1 100% !important; min-width: 0; }
  .scroll-area { padding: 10px; }
  .pv-nav { width: 36px; height: 36px; font-size: 22px; }
  .pv-nav.prev { left: 6px; }
  .pv-nav.next { right: 6px; }
}
</style>
