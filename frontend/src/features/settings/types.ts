export type ModelProvider = string

export type ModelConfigStatus = 'untested' | 'ok' | 'failed' | string

export type ModelDataPolicy = 'chunks_only' | string

export type ModelConfigOut = {
  id: string
  user_id: number
  name: string
  provider: ModelProvider
  mode: string
  base_url: string
  chat_model: string
  embedding_model: string
  data_policy: ModelDataPolicy
  is_default: boolean
  status: ModelConfigStatus
  last_tested_at: string | null
  last_test_result_json: Record<string, unknown>
  api_key_masked: string
}

export type CreateModelConfigBody = {
  name: string
  provider: ModelProvider
  mode: string
  base_url: string
  api_key: string
  chat_model: string
  embedding_model: string
  data_policy: ModelDataPolicy
  is_default: boolean
}

export type UpdateModelConfigBody = {
  name: string
  provider: ModelProvider
  mode: string
  base_url: string
  api_key?: string
  chat_model: string
  embedding_model: string
  data_policy: ModelDataPolicy
  is_default: boolean
}
