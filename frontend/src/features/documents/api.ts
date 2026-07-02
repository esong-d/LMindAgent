import { createApiClient } from '../../lib/apiClient'
import type { UploadedFileInfo } from '../../lib/fileUpload'
import { clearStoredAuth, getAccessToken, getTokenType } from '../auth/store'
import type { DocumentItem, UploadDocumentBody, UploadDocumentResult } from './types'

const documentsApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

function coerceDocumentItems(payload: unknown): DocumentItem[] {
  const maybeArray = (() => {
    if (Array.isArray(payload)) return payload
    if (payload && typeof payload === 'object') {
      const obj = payload as { list?: unknown; items?: unknown; documents?: unknown; data?: unknown }
      if (Array.isArray(obj.list)) return obj.list
      if (Array.isArray(obj.items)) return obj.items
      if (Array.isArray(obj.documents)) return obj.documents

      const data = obj.data
      if (Array.isArray(data)) return data
      if (data && typeof data === 'object') {
        const dataObj = data as { list?: unknown; items?: unknown; documents?: unknown }
        if (Array.isArray(dataObj.list)) return dataObj.list
        if (Array.isArray(dataObj.items)) return dataObj.items
        if (Array.isArray(dataObj.documents)) return dataObj.documents
      }
    }
    return []
  })()

  return maybeArray.filter((item): item is DocumentItem => !!item && typeof item === 'object')
}

export async function uploadDocument(body: UploadDocumentBody): Promise<UploadDocumentResult> {
  return documentsApi.post<UploadDocumentResult, UploadDocumentBody>('/v1/documents/upload', body)
}

export async function uploadDocumentFromFile(params: { knowledgeBaseId: string; file: UploadedFileInfo }): Promise<UploadDocumentResult> {
  return uploadDocument({
    knowledge_base_id: params.knowledgeBaseId,
    file_id: params.file.file_id,
    new_filename: params.file.new_filename,
    original_filename: params.file.original_filename,
    file_type: params.file.file_type,
    file_size: params.file.file_size,
  })
}

export async function listKnowledgeBaseDocuments(kbId: string): Promise<DocumentItem[]> {
  return documentsApi.get<DocumentItem[]>(`/v1/knowledge-bases/${encodeURIComponent(kbId)}/documents`)
}

export async function listAllDocuments(params?: { knowledge_base_id?: string }): Promise<DocumentItem[]> {
  const search = new URLSearchParams()
  if (params?.knowledge_base_id) search.set('knowledge_base_id', params.knowledge_base_id)
  const suffix = search.size ? `?${search.toString()}` : ''
  const payload = await documentsApi.get<unknown>(`/v1/documents/all${suffix}`)
  return coerceDocumentItems(payload)
}

export async function getDocument(documentId: string): Promise<DocumentItem> {
  return documentsApi.get<DocumentItem>(`/v1/documents/${encodeURIComponent(documentId)}`)
}

export async function deleteDocument(documentId: string): Promise<unknown> {
  return documentsApi.del<unknown>(`/v1/documents/${encodeURIComponent(documentId)}`)
}
