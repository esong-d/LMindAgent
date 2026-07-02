import { createApiClient } from '../../lib/apiClient'
import { clearStoredAuth, getAccessToken, getTokenType } from '../auth/store'
import type { CreateModelConfigBody, ModelConfigOut, UpdateModelConfigBody } from './types'

const settingsApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

function coerceModelConfigOut(payload: unknown): ModelConfigOut | null {
  if (!payload || typeof payload !== 'object') return null
  const obj = payload as Record<string, unknown>

  const id = typeof obj.id === 'string' ? obj.id : null
  if (!id) return null

  const userId = typeof obj.user_id === 'number' && Number.isFinite(obj.user_id) ? obj.user_id : 0
  const name = typeof obj.name === 'string' ? obj.name : ''
  const provider = typeof obj.provider === 'string' ? obj.provider : ''
  const mode = typeof obj.mode === 'string' ? obj.mode : ''
  const baseUrl = typeof obj.base_url === 'string' ? obj.base_url : ''
  const chatModel = typeof obj.chat_model === 'string' ? obj.chat_model : ''
  const embeddingModel = typeof obj.embedding_model === 'string' ? obj.embedding_model : ''
  const dataPolicy = typeof obj.data_policy === 'string' ? obj.data_policy : 'chunks_only'
  const isDefault = typeof obj.is_default === 'boolean' ? obj.is_default : false
  const status = typeof obj.status === 'string' ? obj.status : 'untested'
  const lastTestedAt = 'last_tested_at' in obj ? (obj.last_tested_at as unknown) : null
  const lastTestResultJson =
    obj.last_test_result_json && typeof obj.last_test_result_json === 'object' && !Array.isArray(obj.last_test_result_json)
      ? (obj.last_test_result_json as Record<string, unknown>)
      : {}
  const apiKeyMasked = typeof obj.api_key_masked === 'string' ? obj.api_key_masked : ''

  return {
    id,
    user_id: userId,
    name,
    provider,
    mode,
    base_url: baseUrl,
    chat_model: chatModel,
    embedding_model: embeddingModel,
    data_policy: dataPolicy,
    is_default: isDefault,
    status,
    last_tested_at: lastTestedAt as string | null,
    last_test_result_json: lastTestResultJson,
    api_key_masked: apiKeyMasked,
  }
}

function coerceModelConfigList(payload: unknown): ModelConfigOut[] {
  const list = (() => {
    if (Array.isArray(payload)) return payload
    if (!payload || typeof payload !== 'object') return []
    const obj = payload as { data?: unknown; items?: unknown; list?: unknown; model_configs?: unknown }
    if (Array.isArray(obj.data)) return obj.data
    if (Array.isArray(obj.items)) return obj.items
    if (Array.isArray(obj.list)) return obj.list
    if (Array.isArray(obj.model_configs)) return obj.model_configs
    if (obj.data && typeof obj.data === 'object') {
      const dataObj = obj.data as { items?: unknown; list?: unknown; model_configs?: unknown }
      if (Array.isArray(dataObj.items)) return dataObj.items
      if (Array.isArray(dataObj.list)) return dataObj.list
      if (Array.isArray(dataObj.model_configs)) return dataObj.model_configs
    }
    return []
  })()

  return list.map(coerceModelConfigOut).filter((v): v is ModelConfigOut => !!v)
}

export async function listModelConfigs(): Promise<ModelConfigOut[]> {
  const payload = await settingsApi.get<unknown>('/v1/model-configs')
  return coerceModelConfigList(payload)
}

export async function listAllModelConfigs(): Promise<ModelConfigOut[]> {
  const payload = await settingsApi.get<unknown>('/v1/model-configs/all')
  return coerceModelConfigList(payload)
}

export async function getModelConfig(modelConfigId: string): Promise<ModelConfigOut> {
  const payload = await settingsApi.get<unknown>(`/v1/model-configs/${encodeURIComponent(modelConfigId)}`)
  const config = coerceModelConfigOut(payload)
  if (!config) throw new Error('模型配置数据格式不正确')
  return config
}

export async function createModelConfig(body: CreateModelConfigBody): Promise<ModelConfigOut> {
  const payload = await settingsApi.post<unknown, CreateModelConfigBody>('/v1/model-configs', body)
  const config = coerceModelConfigOut(payload)
  if (!config) throw new Error('创建模型配置失败')
  return config
}

export async function updateModelConfig(modelConfigId: string, body: UpdateModelConfigBody): Promise<ModelConfigOut> {
  const payload = await settingsApi.post<unknown, UpdateModelConfigBody>(`/v1/model-configs/${encodeURIComponent(modelConfigId)}`, body)
  const config = coerceModelConfigOut(payload)
  if (!config) throw new Error('更新模型配置失败')
  return config
}

export async function deleteModelConfig(modelConfigId: string): Promise<unknown> {
  return settingsApi.del<unknown>(`/v1/model-configs/${encodeURIComponent(modelConfigId)}`)
}

export async function testModelConfig(modelConfigId: string): Promise<unknown> {
  return settingsApi.post<unknown, Record<string, never>>(`/v1/model-configs/${encodeURIComponent(modelConfigId)}/test`, {})
}

export async function setDefaultModelConfig(modelConfigId: string): Promise<unknown> {
  return settingsApi.post<unknown, Record<string, never>>(`/v1/model-configs/${encodeURIComponent(modelConfigId)}/set-default`, {})
}
