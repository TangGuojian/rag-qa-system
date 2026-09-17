<template>
  <div class="qa-page">
    <div class="qa-header">
      <div class="qa-title">智能问答</div>
      <div class="qa-actions">
        <el-button size="small" @click="newSession">✚ 新建对话</el-button>
        <el-button size="small" @click="showHistory = true">📋 历史记录</el-button>
      </div>
    </div>
    <div class="kb-selector">
      <span class="kb-label">知识库：</span>
      <el-checkbox-group v-model="selectedKbs">
        <el-checkbox v-for="kb in kbList" :key="kb.id" :label="kb.id" :value="kb.id">{{ kb.name }}</el-checkbox>
      </el-checkbox-group>
    </div>
    <div class="chat-container">
      <div class="chat-messages" ref="chatRef">
        <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
          <div v-if="msg.role === 'assistant'" class="bot-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4Z"/><path d="M20 18v1a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1"/><path d="M4 14a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4"/></svg>
          </div>
          <div v-if="msg.role === 'user'" class="user-avatar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div class="bubble">
            <div v-if="msg.role === 'assistant' && !msg.streaming" class="msg-text"><MarkdownRender :content="msg.content" /></div>
            <div v-else class="msg-text plain-text">{{ msg.content }}</div>
            <div v-if="msg.sources?.length" class="sources">
              <div class="sources-title">📎 参考来源</div>
              <div class="sources-list">
                <el-tag
                  v-for="(s, si) in msg.sources"
                  :key="si"
                  size="small"
                  :type="tagType(si)"
                  effect="plain"
                  class="source-tag"
                >
                  {{ s.kb_name }} / {{ s.filename }}
                </el-tag>
              </div>
            </div>
            <div v-if="msg.role === 'assistant' && msg.showFeedback && !msg.streaming" class="feedback">
              <el-button size="small" text @click="feedback(msg, true)" class="fb-btn">👍 有帮助</el-button>
              <el-button size="small" text @click="feedback(msg, false)" class="fb-btn">👎 没帮助</el-button>
            </div>
          </div>
        </div>
        <div v-if="streaming" class="msg assistant">
          <div class="bot-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4Z"/><path d="M20 18v1a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1"/><path d="M4 14a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4"/></svg>
          </div>
          <div class="bubble streaming-bubble">
            <div class="msg-text"><MarkdownRender :content="streamingText" /><span class="cursor">▌</span></div>
          </div>
        </div>
        <div v-if="!messages.length && !streaming" class="empty-chat">
          <div class="empty-icon">💬</div>
          <div class="empty-text">选择知识库，开始智能问答</div>
          <div class="empty-hint">支持连续对话、多轮交流</div>
        </div>
      </div>
      <div class="chat-input">
        <el-input
          v-model="question"
          placeholder="输入问题，按回车发送..."
          @keyup.enter="sendQuestion"
          :disabled="streaming"
          size="large"
          class="qa-input"
        >
          <template #prefix>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </template>
        </el-input>
        <el-button type="primary" @click="sendQuestion" :disabled="!question.trim() || streaming" size="large" class="send-btn">
          <svg v-if="!streaming" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          <span v-else>...</span>
        </el-button>
      </div>
    </div>

    <el-dialog v-model="showHistory" title="📋 历史记录" width="640px" :close-on-click-modal="false">
      <el-table :data="historyList" size="small" @row-click="loadHistorySession" style="cursor:pointer" stripe>
        <el-table-column type="index" label="#" width="48" align="center" />
        <el-table-column prop="question" label="问题" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="160" />
      </el-table>
      <div v-if="historyList.length === 0" class="empty-history">暂无历史记录，开始第一轮对话吧</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { kbApi, historyApi, qaApi } from '../api'
import MarkdownRender from '../components/MarkdownRender.vue'

const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const kbList = ref([])
const selectedKbs = ref([])
const question = ref('')
const messages = ref([])
const streaming = ref(false)
const streamingText = ref('')
const chatRef = ref(null)
const sessionId = ref('')
const showHistory = ref(false)
const historyList = ref([])

function newSession() {
  sessionId.value = 'session_' + Date.now()
  messages.value = []
  streamingText.value = ''
  streaming.value = false
}

function addMessage(role, content, sources = [], showFeedback = false) {
  const item = { role, content, sources, showFeedback, streaming: false }
  messages.value.push(item)
  return item
}

function tagType(index) {
  const types = ['', 'success', 'warning', 'info', 'danger']
  return types[index % types.length]
}

async function sendQuestion() {
  if (!question.value.trim() || streaming.value) return
  if (!selectedKbs.value.length) {
    ElMessage.warning('请至少选择一个知识库')
    return
  }
  const q = question.value
  addMessage('user', q)
  question.value = ''
  scrollToBottom()

  if (!sessionId.value) {
    sessionId.value = 'session_' + Date.now()
  }

  streaming.value = true
  streamingText.value = ''
  let fullAnswer = ''
  let sources = []
  let lastQaId = null

  try {
    const resp = await fetch(`${baseUrl}/qa/ask/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('token'),
      },
      body: JSON.stringify({
        question: q,
        kb_ids: selectedKbs.value,
        session_id: sessionId.value,
      }),
    })

    // HTTP 层报错（401/400/500 等）时响应体是 JSON 而不是 SSE 流
    if (!resp.ok) {
      let detail = '请求失败（HTTP ' + resp.status + '）'
      try {
        const err = await resp.json()
        if (err?.detail) detail = err.detail
      } catch { /* 忽略解析失败，用默认提示 */ }
      throw new Error(detail)
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        let data
        try {
          data = JSON.parse(line.slice(6))
        } catch {
          continue
        }
        if (data.done) {
          if (data.sources) sources = data.sources
          if (data.qa_id) lastQaId = data.qa_id
          if (data.error) throw new Error(data.error)
        } else {
          fullAnswer += data.token
          streamingText.value = fullAnswer
          scrollToBottom()
        }
      }
    }
  } catch (e) {
    const reason = e.message || '未知错误'
    ElMessage.error('回答生成失败: ' + reason)
    // 一个字都没收到时，把原因写进气泡，避免留下一条空气泡让人摸不着头脑
    if (!fullAnswer) fullAnswer = '⚠️ 回答生成失败：' + reason
  }

  streaming.value = false
  streamingText.value = ''
  const msg = addMessage('assistant', fullAnswer, sources, true)
  if (msg) msg.qa_id = lastQaId
  scrollToBottom()
}

async function feedback(msg, useful) {
  msg.showFeedback = false
  try {
    if (msg.qa_id) {
      await qaApi.feedback({ qa_id: msg.qa_id, useful, feedback: '' })
    }
    ElMessage.success(useful ? '感谢反馈！' : '已记录')
  } catch {
    ElMessage.error('反馈提交失败')
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  })
}

async function loadHistorySession(row) {
  showHistory.value = false
  sessionId.value = row.session_id
  try {
    const res = await historyApi.list({ session_id: row.session_id, size: 50 })
    const items = res.data.data || []
    messages.value = []
    for (const item of items) {
      addMessage('user', item.question)
      addMessage('assistant', item.answer || '', item.sources || [], true)
    }
    scrollToBottom()
  } catch {
    ElMessage.error('加载历史失败')
  }
}

function loadHistoryList() {
  historyApi.list({ size: 50 }).then(res => {
    historyList.value = (res.data.data || []).filter((v, i, a) =>
      a.findIndex(t => t.session_id === v.session_id) === i
    )
  }).catch(() => {
    ElMessage.error('加载历史记录失败')
  })
}

onMounted(async () => {
  try {
    const res = await kbApi.list()
    kbList.value = res.data || []
    selectedKbs.value = kbList.value.slice(0, 1).map(k => k.id)
  } catch {
    ElMessage.error('加载知识库失败')
  }
  newSession()
  loadHistoryList()
})
</script>

<style scoped>
.qa-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 0 12px;
  border-bottom: 1px solid #e8e8e8;
}
.qa-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
}
.qa-actions { display: flex; gap: 8px; }
.kb-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  border-bottom: 1px solid #e8e8e8;
  margin-bottom: 0;
}
.kb-label { font-size: 13px; color: #666; white-space: nowrap; }
.chat-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
  scroll-behavior: smooth;
}
.msg { display: flex; gap: 10px; margin-bottom: 20px; animation: msgIn 0.3s ease; }
@keyframes msgIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.msg.user { flex-direction: row-reverse; }
.bot-avatar {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, #1677ff, #4096ff);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0; margin-top: 4px;
  box-shadow: 0 2px 6px rgba(22,119,255,0.3);
}
.user-avatar {
  width: 34px; height: 34px;
  background: #52c41a;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0; margin-top: 4px;
  box-shadow: 0 2px 6px rgba(82,196,26,0.3);
}
.bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}
.msg.user .bubble {
  background: linear-gradient(135deg, #1677ff, #4096ff);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.msg.assistant .bubble {
  background: #f7f8fa;
  border: 1px solid #e8e8e8;
  border-bottom-left-radius: 4px;
}
.streaming-bubble { border-color: #4096ff; }
.msg-text { word-break: break-word; }
.plain-text { white-space: pre-wrap; }
.sources {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e8e8e8;
}
.sources-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 6px;
  font-weight: 500;
}
.sources-list { display: flex; flex-wrap: wrap; gap: 4px; }
.source-tag { max-width: 100%; cursor: default; }
.feedback {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  gap: 8px;
}
.fb-btn { font-size: 12px; color: #999; }
.fb-btn:hover { color: #1677ff; }
.chat-input {
  display: flex;
  gap: 10px;
  padding: 12px 0 0;
  border-top: 1px solid #e8e8e8;
  align-items: center;
}
.qa-input { flex: 1; }
.send-btn { min-width: 64px; }
.cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #1677ff;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s step-end infinite;
}
@keyframes blink { 50% { opacity: 0; } }
.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #bbb;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-text { font-size: 16px; color: #999; margin-bottom: 8px; }
.empty-hint { font-size: 13px; color: #ccc; }
.empty-history { text-align: center; color: #999; padding: 24px; }
</style>
