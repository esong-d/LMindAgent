import { createApiClient } from './apiClient'
import { clearStoredAuth, getAccessToken, getTokenType } from '../features/auth/store'

export type UploadedFileInfo = {
  file_id: string
  original_filename: string
  new_filename: string
  file_type: string
  file_size: number
  download_url: string
}

const filesApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

export async function uploadFile(params: { file: File; signal?: AbortSignal }): Promise<UploadedFileInfo> {
  const form = new FormData()
  form.append('file', params.file, params.file.name)
  return filesApi.post<UploadedFileInfo, FormData>('/v1/files/upload', form, { signal: params.signal })
}
