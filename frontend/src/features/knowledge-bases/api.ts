import { createApiClient } from '../../lib/apiClient'
import { clearStoredAuth, getAccessToken, getTokenType } from '../auth/store'
import type { CreateKnowledgeBaseBody, KnowledgeBase, KnowledgeBaseItem, KnowledgeBaseListData, UpdateKnowledgeBaseBody } from './types'

const knowledgeBasesApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

function coerceKnowledgeBaseItems(payload: unknown): KnowledgeBaseItem[] {
  const maybeArray = (() => {
    if (Array.isArray(payload)) return payload
    if (payload && typeof payload === 'object') {
      const obj = payload as { list?: unknown; items?: unknown; knowledge_bases?: unknown; knowledgeBases?: unknown; data?: unknown }
      if (Array.isArray(obj.list)) return obj.list
      if (Array.isArray(obj.items)) return obj.items
      if (Array.isArray(obj.knowledge_bases)) return obj.knowledge_bases
      if (Array.isArray(obj.knowledgeBases)) return obj.knowledgeBases

      const data = obj.data
      if (Array.isArray(data)) return data
      if (data && typeof data === 'object') {
        const dataObj = data as { list?: unknown; items?: unknown; knowledge_bases?: unknown; knowledgeBases?: unknown }
        if (Array.isArray(dataObj.list)) return dataObj.list
        if (Array.isArray(dataObj.items)) return dataObj.items
        if (Array.isArray(dataObj.knowledge_bases)) return dataObj.knowledge_bases
        if (Array.isArray(dataObj.knowledgeBases)) return dataObj.knowledgeBases
      }
    }
    return []
  })()

  return maybeArray
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      const obj = item as {
        id?: unknown
        kb_id?: unknown
        knowledge_base_id?: unknown
        user_id?: unknown
        name?: unknown
        title?: unknown
        description?: unknown
        settings_json?: unknown
      }

      const id =
        (typeof obj.id === 'string' ? obj.id : undefined) ??
        (typeof obj.knowledge_base_id === 'string' ? obj.knowledge_base_id : undefined) ??
        (typeof obj.kb_id === 'string' ? obj.kb_id : undefined)
      if (!id) return null

      const name = (typeof obj.name === 'string' ? obj.name : undefined) ?? (typeof obj.title === 'string' ? obj.title : undefined) ?? ''
      const userId = typeof obj.user_id === 'number' && Number.isFinite(obj.user_id) ? obj.user_id : 0
      const description = typeof obj.description === 'string' ? obj.description : ''
      const settingsJson =
        obj.settings_json && typeof obj.settings_json === 'object' && !Array.isArray(obj.settings_json)
          ? (obj.settings_json as Record<string, unknown>)
          : {}

      return {
        id,
        user_id: userId,
        name: name.trim() || id,
        description,
        settings_json: settingsJson,
        doc_cnt: 0,
        note_cnt: 0
      } satisfies KnowledgeBaseItem
    })
    .filter((v): v is KnowledgeBaseItem => !!v)
}

export async function listKnowledgeBasesPage(params: { page: number; perPage: number }): Promise<KnowledgeBaseListData> {
  const search = new URLSearchParams({
    page: String(params.page),
    per_page: String(params.perPage),
  }).toString()
  return knowledgeBasesApi.get<KnowledgeBaseListData>(`/v1/knowledge-bases?${search}`)
}

export async function listAllKnowledgeBaseItems(): Promise<KnowledgeBaseItem[]> {
  const payload = await knowledgeBasesApi.get<unknown>('/v1/knowledge-bases/all')
  return coerceKnowledgeBaseItems(payload)
}

export async function createKnowledgeBase(body: CreateKnowledgeBaseBody): Promise<KnowledgeBaseItem> {
  return knowledgeBasesApi.post<KnowledgeBaseItem, CreateKnowledgeBaseBody>('/v1/knowledge-bases', body)
}

export async function updateKnowledgeBase(kbId: string, body: UpdateKnowledgeBaseBody): Promise<KnowledgeBaseItem> {
  return knowledgeBasesApi.post<KnowledgeBaseItem, UpdateKnowledgeBaseBody>(`/v1/knowledge-bases/${encodeURIComponent(kbId)}`, body)
}

export async function deleteKnowledgeBase(kbId: string): Promise<unknown> {
  return knowledgeBasesApi.del<unknown>(`/v1/knowledge-bases/${encodeURIComponent(kbId)}`)
}

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  const items = await listAllKnowledgeBaseItems()
  return items.map((kb) => ({ id: kb.id, name: kb.name?.trim() || kb.id }))
}
