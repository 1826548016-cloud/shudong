<script setup lang="ts">
import { computed } from 'vue'

export type Comment = {
  id: number
  post: number
  parent: number | null
  nickname: string
  content: string
  admin_reply: string
  replied_at: string | null
  replies: Comment[]
  created_at: string
}

const props = defineProps<{
  comment: Comment
  replyingId: number | null
  replyText: string
  replySaving: boolean
  isAuthed: boolean
  commentNickname: string
  isNested?: boolean
  deletingId: number | null
}>()

const emit = defineEmits<{
  (e: 'startReply', comment: Comment): void
  (e: 'update:replyText', val: string): void
  (e: 'submitReplyTo'): void
  (e: 'submitAdminReply'): void
  (e: 'cancelReply'): void
  (e: 'deleteComment', id: number): void
}>()

const isReplying = computed(() => props.replyingId === props.comment.id)

function formatTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString()
}
</script>

<template>
  <div class="comment-body">
    <div class="comment-head">
      <div class="name">{{ comment.nickname || '匿名' }}</div>
      <div class="time">{{ new Date(comment.created_at).toLocaleString() }}</div>
    </div>
    <div class="comment-content">{{ comment.content }}</div>

    <div v-if="comment.admin_reply" class="reply-box">
      <div class="reply-head">
        <span class="reply-title">管理员回复</span>
        <span v-if="comment.replied_at" class="reply-time">{{ formatTime(comment.replied_at) }}</span>
      </div>
      <div class="reply-content">{{ comment.admin_reply }}</div>
    </div>

    <div class="comment-actions">
      <el-button text size="small" @click="emit('startReply', comment)">回复</el-button>
      <el-button v-if="isAuthed" text size="small" type="primary" @click="emit('startReply', comment)">
        管理员回复
      </el-button>
      <el-button
        v-if="isAuthed"
        text
        size="small"
        type="danger"
        :loading="deletingId === comment.id"
        @click="emit('deleteComment', comment.id)"
      >
        删除
      </el-button>
    </div>

    <div v-if="isReplying" class="reply-editor">
      <el-input
        :model-value="replyText"
        type="textarea"
        :rows="3"
        maxlength="500"
        show-word-limit
        :placeholder="isAuthed ? '写下管理员回复…（将作为官方回复显示在原评论下）' : '写下你的回复…'"
        @update:model-value="(val: string) => emit('update:replyText', val)"
      />
      <div class="reply-actions">
        <el-button size="small" @click="emit('cancelReply')">取消</el-button>
        <el-button
          v-if="isAuthed"
          size="small"
          type="primary"
          :loading="replySaving"
          @click="emit('submitAdminReply')"
        >
          作为管理员回复
        </el-button>
        <el-button
          size="small"
          type="primary"
          :loading="replySaving"
          @click="emit('submitReplyTo')"
        >
          提交回复
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comment-body {
  min-width: 0;
}

.comment-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-3);
  font-size: 12px;
}

.name {
  font-weight: 600;
  color: var(--text-2);
}

.comment-content {
  margin-top: 6px;
  white-space: pre-wrap;
  line-height: 1.6;
  color: var(--text-1);
  font-size: 14px;
}

.reply-box {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px dashed var(--border);
}

.reply-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  gap: 8px;
}

.reply-title {
  font-size: 12px;
  color: var(--text-3);
}

.reply-time {
  font-size: 11px;
  color: var(--text-3);
}

.reply-content {
  color: var(--text-1);
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 13px;
}

.comment-actions {
  margin-top: 8px;
  display: flex;
  gap: 4px;
}

.reply-editor {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
