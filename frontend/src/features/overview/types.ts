export type OverviewDocumentStatus =
  | 'pending'
  | 'parsing'
  | 'chunking'
  | 'embedding'
  | 'completed'
  | 'failed'
  | string


export type OverviewDocumentItem = {
  id: string
  knowledge_base_id: string
  user_id: number
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  status: OverviewDocumentStatus
  error_message: string
  metadata_json: Record<string, unknown>
  processing_started_at: string | null
  processing_completed_at: string | null
  retry_count: number
  created_at: string
  updated_at: string
}

export type OverviewNoteItem = {
  id: string
  knowledge_base_id: string
  user_id: number
  title: string
  tags_json: string[]
  created_at: string
}

export type OverviewData = {
  document_cnt: number
  chunk_cnt: number
  note_cnt: number
  recent: {
    doc: OverviewDocumentItem[]
    note: OverviewNoteItem[]
  }
}
