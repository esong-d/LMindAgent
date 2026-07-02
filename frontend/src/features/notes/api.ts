import { createApiClient } from '../../lib/apiClient'
import { clearStoredAuth, getAccessToken, getTokenType } from '../auth/store'

export type NoteOut = {
  id: string
  knowledge_base_id: string
  user_id: number
  title: string
  content: string
  tags_json: string[]
  created_at?: string
}

export type CreateNoteBody = {
  knowledge_base_id: string
  title: string
  content: string
  tags_json: string[]
}

export type UpdateNoteBody = {
  title: string
  content: string
  tags_json: string[]
}

const notesApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

function coerceTags(value: unknown): string[] {
  if (Array.isArray(value)) return value.filter((v): v is string => typeof v === 'string').map((t) => t.trim()).filter(Boolean)
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value) as unknown
      if (Array.isArray(parsed)) return coerceTags(parsed)
    } catch {
      return []
    }
  }
  return []
}

function coerceNoteOut(payload: unknown): NoteOut | null {
  if (!payload || typeof payload !== 'object') return null
  const obj = payload as {
    id?: unknown
    note_id?: unknown
    knowledge_base_id?: unknown
    kb_id?: unknown
    user_id?: unknown
    title?: unknown
    content?: unknown
    tags_json?: unknown
    tags?: unknown
    created_at?: unknown
    createdAt?: unknown
    created_time?: unknown
    create_time?: unknown
  }

  const id = (typeof obj.id === 'string' ? obj.id : undefined) ?? (typeof obj.note_id === 'string' ? obj.note_id : undefined)
  if (!id || !id.trim()) return null

  const knowledgeBaseId =
    (typeof obj.knowledge_base_id === 'string' ? obj.knowledge_base_id : undefined) ?? (typeof obj.kb_id === 'string' ? obj.kb_id : undefined) ?? ''

  const userId = typeof obj.user_id === 'number' && Number.isFinite(obj.user_id) ? obj.user_id : 0
  const title = typeof obj.title === 'string' ? obj.title : ''
  const content = typeof obj.content === 'string' ? obj.content : ''
  const tagsJson = coerceTags(obj.tags_json ?? obj.tags)
  const createdAt =
    (typeof obj.created_at === 'string' ? obj.created_at : undefined) ??
    (typeof obj.createdAt === 'string' ? obj.createdAt : undefined) ??
    (typeof obj.created_time === 'string' ? obj.created_time : undefined) ??
    (typeof obj.create_time === 'string' ? obj.create_time : undefined)

  return {
    id: id.trim(),
    knowledge_base_id: knowledgeBaseId,
    user_id: userId,
    title: title.trim() || '未命名笔记',
    content,
    tags_json: tagsJson,
    created_at: createdAt,
  }
}

function coerceNoteList(payload: unknown): NoteOut[] {
  const list = (() => {
    if (Array.isArray(payload)) return payload
    if (!payload || typeof payload !== 'object') return []
    const obj = payload as { list?: unknown; items?: unknown; notes?: unknown; data?: unknown }
    if (Array.isArray(obj.list)) return obj.list
    if (Array.isArray(obj.items)) return obj.items
    if (Array.isArray(obj.notes)) return obj.notes
    if (Array.isArray(obj.data)) return obj.data
    if (obj.data && typeof obj.data === 'object') {
      const dataObj = obj.data as { list?: unknown; items?: unknown; notes?: unknown }
      if (Array.isArray(dataObj.list)) return dataObj.list
      if (Array.isArray(dataObj.items)) return dataObj.items
      if (Array.isArray(dataObj.notes)) return dataObj.notes
    }
    return []
  })()

  return list.map((item) => coerceNoteOut(item)).filter((v): v is NoteOut => !!v)
}

export async function createNote(body: CreateNoteBody): Promise<NoteOut> {
  const payload = await notesApi.post<unknown, CreateNoteBody>('/v1/notes', body)
  const note = coerceNoteOut(payload)
  if (!note) throw new Error('创建笔记失败：响应格式不正确')
  return note
}

export async function listKnowledgeBaseNotes(kbId: string): Promise<NoteOut[]> {
  const payload = await notesApi.get<unknown>(`/v1/knowledge-bases/${encodeURIComponent(kbId)}/notes`)
  return coerceNoteList(payload)
}

export async function getNote(noteId: string): Promise<NoteOut> {
  const payload = await notesApi.get<unknown>(`/v1/notes/${encodeURIComponent(noteId)}`)
  const note = coerceNoteOut(payload)
  if (!note) throw new Error('加载笔记失败：响应格式不正确')
  return note
}

export async function updateNote(noteId: string, body: UpdateNoteBody): Promise<NoteOut> {
  const payload = await notesApi.post<unknown, UpdateNoteBody>(`/v1/notes/${encodeURIComponent(noteId)}`, body)
  const note = coerceNoteOut(payload)
  if (!note) throw new Error('更新笔记失败：响应格式不正确')
  return note
}

export async function deleteNote(noteId: string): Promise<unknown> {
  return notesApi.del<unknown>(`/v1/notes/${encodeURIComponent(noteId)}`)
}
