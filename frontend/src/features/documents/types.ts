export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed' | string

export type DocumentItem = {
  id: string
  knowledge_base_id: string
  user_id: number
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  status: DocumentStatus
  error_message: string
  chunk_cnt: number
  metadata_json: Record<string, unknown>
  processing_started_at: string | null
  processing_completed_at: string | null
  retry_count: number
  created_at: string
  updated_at: string
}

export type UploadDocumentBody = {
  knowledge_base_id: string
  file_id: string
  new_filename: string
  original_filename: string
  file_type: string
  file_size: number
}

export type TaskItem = {
  id: string
  status: string
  created_at?: string
  updated_at?: string
}

export type UploadDocumentResult = {
  document: DocumentItem
  task: TaskItem
}
