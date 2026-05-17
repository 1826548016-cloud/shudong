import { rmSync, existsSync } from 'node:fs'

const dist = 'dist'
if (existsSync(dist)) {
  try {
    rmSync(dist, { recursive: true, force: true })
    console.log('[prebuild] dist cleared')
  } catch (e) {
    console.warn('[prebuild] failed to clear dist, retrying...')
    rmSync(dist, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 })
  }
}
