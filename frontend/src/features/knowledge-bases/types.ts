export type KnowledgeBase = {
  id: string
  name: string
}

export type KnowledgeBaseItem = {
  id: string
  user_id: number
  name: string
  description: string
  doc_cnt: number
  note_cnt: number
  settings_json: Record<string, unknown>
}

export type KnowledgeBaseListData = {
  list: KnowledgeBaseItem[]
  total: number
  page: number
  per_page: number
}

export type CreateKnowledgeBaseBody = {
  name: string
  description: string
  settings_json: Record<string, unknown>
}

export type UpdateKnowledgeBaseBody = CreateKnowledgeBaseBody
