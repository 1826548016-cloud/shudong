import { reactive, ref } from 'vue'

export type MusicItem = {
  id: number
  title: string
  artist: string
  file: string
  file_url: string
  duration: number
  created_at: string
}

export interface PlayerState {
  current: MusicItem | null
  playing: boolean
  currentTime: number
  duration: number
  volume: number
  playlist: MusicItem[]
  playlistIndex: number
}

const state = reactive<PlayerState>({
  current: null,
  playing: false,
  currentTime: 0,
  duration: 0,
  volume: parseFloat(localStorage.getItem('player_volume') ?? '0.6'),
  playlist: [],
  playlistIndex: -1,
})

const mediaRef = ref<HTMLMediaElement | null>(null)

let _wasAutoPaused = false

function attachMediaListeners(el: HTMLMediaElement) {
  el.addEventListener('loadedmetadata', () => {
    if (el.duration && isFinite(el.duration)) {
      state.duration = el.duration
    }
  })
  el.addEventListener('durationchange', () => {
    if (el.duration && isFinite(el.duration)) {
      state.duration = el.duration
    }
  })
  el.addEventListener('timeupdate', () => {
    state.currentTime = el.currentTime
  })
  el.addEventListener('ended', () => {
    state.playing = false
    state.currentTime = 0
    nextTrack()
  })
  el.addEventListener('play', () => {
    state.playing = true
  })
  el.addEventListener('pause', () => {
    state.playing = false
  })
  el.addEventListener('volumechange', () => {
    state.volume = el.volume
    localStorage.setItem('player_volume', String(el.volume))
  })
  el.addEventListener('error', () => {
    console.error('Media error:', el.error?.message)
  })
}

function attemptPlay(el: HTMLMediaElement): Promise<void> {
  const p = el.play()
  if (p === undefined) return Promise.resolve()
  return p
}

function startPlayback() {
  const el = mediaRef.value
  if (!el) return

  if (el.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) {
    attemptPlay(el).catch(() => {
      attemptPlay(el).catch(() => {})
    })
  } else {
    const onCanPlay = () => {
      el.removeEventListener('canplay', onCanPlay)
      attemptPlay(el).catch(() => {})
    }
    el.addEventListener('canplay', onCanPlay)
    el.load()
    attemptPlay(el).catch(() => {})
  }
}

function playMusicInternal(item: MusicItem) {
  state.current = item
  state.currentTime = 0
  state.duration = item.duration || 0
  state.playing = false
  if (mediaRef.value) {
    mediaRef.value.src = item.file_url
    mediaRef.value.load()
    startPlayback()
  }
}

function nextTrack() {
  if (state.playlist.length === 0) return
  const next = (state.playlistIndex + 1) % state.playlist.length
  state.playlistIndex = next
  const item = state.playlist[next]
  playMusicInternal(item)
}

function prevTrack() {
  if (state.playlist.length === 0) return
  const prev = (state.playlistIndex - 1 + state.playlist.length) % state.playlist.length
  state.playlistIndex = prev
  const item = state.playlist[prev]
  playMusicInternal(item)
}

export function usePlayer() {
  function setMediaRef(el: HTMLMediaElement | null) {
    if (mediaRef.value === el) return
    mediaRef.value = el
    if (el) {
      attachMediaListeners(el)
    }
  }

  function playMusic(item: MusicItem) {
    const idx = state.playlist.findIndex((m) => m.id === item.id)
    if (idx !== -1) {
      state.playlistIndex = idx
    } else {
      state.playlist.push(item)
      state.playlistIndex = state.playlist.length - 1
    }
    playMusicInternal(item)
  }

  function togglePlay() {
    if (!mediaRef.value || !state.current) return
    if (state.playing) {
      mediaRef.value.pause()
    } else {
      attemptPlay(mediaRef.value).catch(() => {
        startPlayback()
      })
    }
  }

  function seek(time: number) {
    if (!mediaRef.value) return
    mediaRef.value.currentTime = time
    state.currentTime = time
  }

  function setVolume(v: number) {
    if (!mediaRef.value) return
    mediaRef.value.volume = v
  }

  function setPlaylist(list: MusicItem[], startIndex = 0) {
    state.playlist = list
    state.playlistIndex = startIndex
    if (list.length > 0) {
      playMusic(list[startIndex])
    }
  }

  function pauseForMedia() {
    if (state.playing && mediaRef.value) {
      _wasAutoPaused = true
      mediaRef.value.pause()
    }
  }

  function resumeAfterMedia() {
    if (_wasAutoPaused && mediaRef.value && state.current) {
      _wasAutoPaused = false
      mediaRef.value.play().catch(() => {})
    }
  }

  function removeFromPlaylist(id: number) {
    const idx = state.playlist.findIndex((m) => m.id === id)
    if (idx === -1) return
    if (state.current?.id === id) {
      state.current = null
      state.playing = false
      if (mediaRef.value) {
        mediaRef.value.pause()
        mediaRef.value.removeAttribute('src')
        mediaRef.value.load()
      }
    }
    state.playlist.splice(idx, 1)
    if (state.playlistIndex >= idx && state.playlistIndex > 0) {
      state.playlistIndex--
    }
  }

  return {
    state,
    setMediaRef,
    playMusic,
    togglePlay,
    seek,
    setVolume,
    nextTrack,
    prevTrack,
    setPlaylist,
    pauseForMedia,
    resumeAfterMedia,
    removeFromPlaylist,
  }
}
