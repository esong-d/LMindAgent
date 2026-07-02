import { ApiError, createApiClient } from '../../lib/apiClient'
import { clearStoredAuth, getAccessToken, getTokenType } from '../auth/store'


const chatApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

export type SourceItem = {
  document_id: string
  original_filename: string
}

export type ConversationSummary = {
  id: string
  knowledge_base_id: string | null
  title: string
  updated_at: string
}

export type ConversationMessage = {
  id: string
  role: 'user' | 'ai'
  content: string
  sources: SourceItem[]
  created_at: string
}

export type ChatStreamEvent =
  | { event: 'message_start'; data: { conversation_id: string } }
  | { event: 'message_delta'; data: { delta: string } }
  | { event: 'messages'; data: string }
  | { event: 'custom'; data: { event?: string; node?: string; message?: string } }
  | { event: 'sources'; data: { sources: SourceItem[] } }
  | { event: 'message_done'; data: { conversation_id: string; message_id?: string } }
  | { event: string; data: unknown }

function coerceConversationSummaries(payload: unknown): ConversationSummary[] {
  const list = (() => {
    if (Array.isArray(payload)) return payload
    if (!payload || typeof payload !== 'object') return []

    const obj = payload as { data?: unknown; items?: unknown; conversations?: unknown }
    if (Array.isArray(obj.data)) return obj.data
    if (Array.isArray(obj.items)) return obj.items
    if (Array.isArray(obj.conversations)) return obj.conversations
    if ('success' in obj && typeof (obj as { success?: unknown }).success === 'boolean') {
      const data = (obj as { data?: unknown }).data
      if (Array.isArray(data)) return data
    }
    return []
  })()

  return list
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      const obj = item as { id?: unknown; knowledge_base_id?: unknown; title?: unknown; updated_at?: unknown }
      if (typeof obj.id !== 'string' || !obj.id.trim()) return null
      const title = typeof obj.title === 'string' && obj.title.trim() ? obj.title.trim() : '未命名会话'
      const updatedAt = typeof obj.updated_at === 'string' && obj.updated_at.trim() ? obj.updated_at : ''
      const kbId = typeof obj.knowledge_base_id === 'string' && obj.knowledge_base_id.trim() ? obj.knowledge_base_id : null
      return { id: obj.id, knowledge_base_id: kbId, title, updated_at: updatedAt }
    })
    .filter((v): v is ConversationSummary => !!v)
}

function coerceConversationMessages(payload: unknown): ConversationMessage[] {
  const list = (() => {
    if (Array.isArray(payload)) return payload
    if (!payload || typeof payload !== 'object') return []

    const obj = payload as { data?: unknown; items?: unknown; messages?: unknown }
    if (Array.isArray(obj.data)) return obj.data
    if (Array.isArray(obj.items)) return obj.items
    if (Array.isArray(obj.messages)) return obj.messages
    if ('success' in obj && typeof (obj as { success?: unknown }).success === 'boolean') {
      const data = (obj as { data?: unknown }).data
      if (Array.isArray(data)) return data
    }
    return []
  })()

  return list
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      const obj = item as { id?: string; role?: string; content?: string; sources?: SourceItem[]; created_at?: string }
      if (typeof obj.id !== 'string' || !obj.id.trim()) return null
      const role = obj.role === 'user' || obj.role === 'ai' ? obj.role : null
      if (!role) return null
      const content = typeof obj.content === 'string' ? obj.content : ''
      const createdAt = typeof obj.created_at === 'string' ? obj.created_at : ''
      const sources = Array.isArray(obj.sources) ? (obj.sources as SourceItem[]) : []
      return { id: obj.id, role, content, sources, created_at: createdAt }
    })
    .filter((v): v is ConversationMessage => !!v)
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const payload = await chatApi.get<unknown>('/api/v1/conversations')
  return coerceConversationSummaries(payload)
}

export async function getConversationMessages(conversationId: string): Promise<ConversationMessage[]> {
  const payload = await chatApi.get<unknown>(`/api/v1/conversations/${encodeURIComponent(conversationId)}`)
  return coerceConversationMessages(payload)
}

export async function deleteConversation(conversationId: string): Promise<boolean> {
  const payload = await chatApi.del<unknown>(`/api/v1/conversations/${encodeURIComponent(conversationId)}`)
  if (!payload || typeof payload !== 'object') return true
  const obj = payload as { data?: unknown }
  const data = obj.data as { deleted?: unknown } | undefined
  if (data && typeof data.deleted === 'boolean') return data.deleted
  return true
}

function parseSseEvent(raw: string) {
  const lines = raw.split('\n')
  let eventName = ''
  const dataLines: string[] = []

  for (const line of lines) {
    if (line.startsWith('event:')) {
      eventName = line.slice('event:'.length).trim()
      continue
    }
    if (line.startsWith('data:')) {
      dataLines.push(line.slice('data:'.length).trimStart())
    }
  }

  const dataText = dataLines.join('\n').trim()
  if (!eventName) return null
  if (!dataText) return { event: eventName, data: null }

  try {
    return { event: eventName, data: JSON.parse(dataText) as unknown }
  } catch {
    return { event: eventName, data: dataText }
  }
}

export async function chatStream(params: {
  query: string
  conversationId: string
  knowledgeBaseId: string
  signal?: AbortSignal
  onEvent: (evt: ChatStreamEvent) => void
}) {
  let res: Response
  try {
    res = await chatApi.fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        Accept: 'text/event-stream',
      },
      body: {
        query: params.query,
        conversation_id: params.conversationId,
        knowledge_base_id: params.knowledgeBaseId,
      },
      signal: params.signal,
    })
  } catch (err) {
    if (err instanceof ApiError) throw new Error(err.message)
    throw err
  }

  if (!res.body) {
    const text = await res.text().catch(() => '')
    let message = '请求失败'

    try {
      const errorRes = JSON.parse(text) as { error?: { message?: string } }
      message = errorRes.error?.message || message
    } catch {
      if (text.trim()) message = text
    }

    throw new Error(message)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    while (true) {
      const idx = buffer.indexOf('\n\n')
      if (idx === -1) break
      const rawEvent = buffer.slice(0, idx).trim()
      buffer = buffer.slice(idx + 2)
      if (!rawEvent) continue

      const parsed = parseSseEvent(rawEvent)
      if (!parsed) continue
      params.onEvent(parsed as ChatStreamEvent)
    }
  }
}
