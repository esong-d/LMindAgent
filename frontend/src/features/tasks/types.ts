export type TaskStatus = 'queued' | 'running' | 'success' | 'failed' | 'canceled'
export type TaskType = 'document_ingest'

type KnowledgeBase = {
    id: string
    name: string
}

type Document = {
    id: string
    filename: string
}

export type TaskOut = {
  id: string
  user_id: number
  knowledge_base?: KnowledgeBase | null
  document?: Document | null
  type?: TaskType | string | null
  status: TaskStatus | string
  progress: number
  retry_count: number
  input_json: Record<string, unknown>
  output_json: Record<string, unknown>
  error_message: string
  created_at: string
  updated_at: string
}

export type TaskListData = {
  list: TaskOut[]
  total: number
  page: number
  page_size: number
}

export type TaskListParams = {
  page: number
  pageSize: number
  status?: Exclude<TaskStatus, 'success'> | ''
}

export type TaskListResult = {
  items: TaskOut[]
  total: number
  page: number
  pageSize: number
}

function toObject(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {}
  return value as Record<string, unknown>
}

function toNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function toKnowledgeBase(value: unknown): KnowledgeBase | null {
  if (!value || typeof value !== 'object') return null

  const obj = value as Record<string, unknown>

  return {
    id: typeof obj.id === 'string' ? obj.id : '',
    name: typeof obj.name === 'string' ? obj.name : '',
  }
}

function toDocument(value: unknown): Document | null {
  if (!value || typeof value !== 'object') return null

  const obj = value as Record<string, unknown>

  return {
    id: typeof obj.id === 'string' ? obj.id : '',
    filename: typeof obj.filename === 'string' ? obj.filename : '',
  }
}

function toTask(item: unknown): TaskOut | null {
  if (!item || typeof item !== 'object') return null
  const obj = item as Record<string, unknown>
  const id = typeof obj.id === 'string' ? obj.id : ''
  if (!id) return null

  return {
    id,
    user_id: typeof obj.user_id === 'number' && Number.isFinite(obj.user_id) ? obj.user_id : 0,
    knowledge_base: obj.knowledge_base ? toKnowledgeBase(obj.knowledge_base) : null,
    document: obj.document ? toDocument(obj.document) : null,
    type: obj.type ? typeof obj.type === 'string' ? obj.type : '' : null,
    status: typeof obj.status === 'string' ? obj.status : 'queued',
    progress: typeof obj.progress === 'number' && Number.isFinite(obj.progress) ? obj.progress : 0,
    retry_count: typeof obj.retry_count === 'number' && Number.isFinite(obj.retry_count) ? obj.retry_count : 0,
    input_json: toObject(obj.input_json),
    output_json: toObject(obj.output_json),
    error_message: typeof obj.error_message === 'string' ? obj.error_message : '',
    created_at: typeof obj.created_at === 'string' ? obj.created_at : '',
    updated_at: typeof obj.updated_at === 'string' ? obj.updated_at : '',
  }
}

export function coerceTaskOut(payload: unknown): TaskOut | null {
  if (Array.isArray(payload)) return null
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return toTask((payload as { data?: unknown }).data)
  }
  return toTask(payload)
}

export function coerceTaskList(payload: unknown): TaskOut[] {
  const list = (() => {
    if (Array.isArray(payload)) return payload
    if (!payload || typeof payload !== 'object') return []

    const obj = payload as { data?: unknown; items?: unknown; list?: unknown; tasks?: unknown }
    if (Array.isArray(obj.data)) return obj.data
    if (Array.isArray(obj.items)) return obj.items
    if (Array.isArray(obj.list)) return obj.list
    if (Array.isArray(obj.tasks)) return obj.tasks

    if (obj.data && typeof obj.data === 'object') {
      const dataObj = obj.data as { items?: unknown; list?: unknown; tasks?: unknown }
      if (Array.isArray(dataObj.items)) return dataObj.items
      if (Array.isArray(dataObj.list)) return dataObj.list
      if (Array.isArray(dataObj.tasks)) return dataObj.tasks
    }

    return []
  })()

  return list.map((item) => toTask(item)).filter((item): item is TaskOut => !!item)
}

export function coerceTaskListData(payload: unknown): TaskListData {
  const source =
    payload && typeof payload === 'object' && 'data' in payload && (payload as { data?: unknown }).data && typeof (payload as { data?: unknown }).data === 'object'
      ? (payload as { data?: unknown }).data
      : payload

  const obj = source && typeof source === 'object' ? (source as Record<string, unknown>) : {}
  const list = coerceTaskList(source)

  return {
    list,
    total: toNumber(obj.total, list.length),
    page: toNumber(obj.page, 1),
    page_size: toNumber(obj.page_size ?? obj.per_page, list.length || 10),
  }
}

export function normalizeTaskStatus(status: string | undefined | null): TaskStatus | string {
  if (status === 'succeeded') return 'success'
  return status ?? 'queued'
}

export function getTaskStatusLabel(status: string | undefined | null) {
  const normalized = normalizeTaskStatus(status)
  if (normalized === 'queued') return '排队中'
  if (normalized === 'running') return '运行中'
  if (normalized === 'success') return '已成功'
  if (normalized === 'failed') return '已失败'
  if (normalized === 'canceled') return '已取消'
  return normalized || '未知'
}

export function getTaskTypeLabel(type: TaskType | undefined | null) {
  if (type === 'document_ingest') return '文档导入'
  return type || '未知'
}
