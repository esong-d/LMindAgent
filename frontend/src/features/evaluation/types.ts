type AnyRecord = Record<string, unknown>

function asRecord(value: unknown): AnyRecord | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as AnyRecord) : null
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function asNullableNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function asNullableNumericValue(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function asNullableRecord(value: unknown): Record<string, unknown> | null {
  const record = asRecord(value)
  return record ? record : null
}

function asNullableString(value: unknown): string | null {
  return typeof value === 'string' ? value : null
}

function asNullableStringArray(value: unknown): string[] | null {
  if (!Array.isArray(value)) return null
  return value.map((item) => asString(item)).filter(Boolean)
}

function coerceItems(value: unknown): unknown[] {
  if (Array.isArray(value)) return value
  const record = asRecord(value)
  if (!record) return []
  if (Array.isArray(record.items)) return record.items
  if (Array.isArray(record.list)) return record.list
  return []
}

export type EvaluationQuestion = {
  id: string
  group: EvaluationGroupOption | null
  question: string
  expected_answer: string | null
  source: string
  created_at: string
}

export type EvaluationChunk = {
  id: string
  content: string
}

export type EvaluationQuestionDetail = EvaluationQuestion & {
  chunks: EvaluationChunk[]
}

export type EvaluationQuestionListResult = {
  items: EvaluationQuestion[]
  total: number
  page: number
  page_size: number
}

export type EvaluationQuestionOption = {
  id: string
  question: string
}

export type EvaluationGroup = {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export type EvaluationGroupOption = {
  id: string
  name: string
}

export type EvaluationGroupListResult = {
  items: EvaluationGroup[]
  total: number
  page: number
  page_size: number
}

export type CreateEvaluationGroupBody = {
  name: string
  description?: string
}

export type UpdateEvaluationGroupBody = {
  name?: string
  description?: string
}

export type CreateEvaluationQuestionBody = {
  group_id?: string
  question?: string
  expected_answer?: string | null
  source?: string
  chunk_ids?: string[]
  knowledge_base_id?: string
  document_id?: string
  model_config_id?: string
  question_count?: number
}

export type UpdateEvaluationQuestionBody = {
  group_id?: string
  question?: string
  expected_answer?: string | null
  source?: string
}

export type EvaluationTask = {
  id: string
  name: string
  group: EvaluationGroupOption | null
  type: string
  knowledge_base: KnowledgeBaseItem | null
  total_questions: number
  question_ids: string[] | null
  config: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export type EvaluationTaskListResult = {
  items: EvaluationTask[]
  total: number
  page: number
  page_size: number
}

export type CreateEvaluationTaskBody = {
  name: string
  group_id: string
  knowledge_base_id: string
  question_ids?: string[] | null
  model_config_id: string
}

export type KnowledgeBaseItem = {
  id: string
  name: string
}
export type ModelConfigItem = {
  id: string
  name: string
  provider: string
}
export type EvaluationRun = {
  id: string
  task_id: string
  type: string
  status: string
  knowledge_base: KnowledgeBaseItem | null
  total_questions: number
  completed_questions: number
  avg_recall: number | Record<string, number | null> | null
  avg_mrr: number | null
  avg_correctness: number | null
  avg_faithfulness: number | null
  config: Record<string, unknown> | null
  error_message: string | null
  model: ModelConfigItem | null
  created_at: string
  updated_at: string
}

export type EvaluationRunListResult = {
  items: EvaluationRun[]
  total: number
  page: number
  page_size: number
}

export type ExecuteEvaluationResponse = {
  task_id: string
  run_id: string
  queue_id: string
}

export type EvaluationResult = {
  id: string
  run_id: string
  question_id: string
  answer: string
  status: string
  mrr: number | null
  correctness: number | null
  faithfulness: number | null
  retrieval_metrics: Record<string, unknown> | null
  latency_ms: number | null
  trace_data: Record<string, unknown> | null
  error_message: string | null
  created_at: string
}

export type EvaluationResultListResult = {
  items: EvaluationResult[]
  total: number
  page: number
  page_size: number
}

export type EvaluationResultDetail = {
  result: EvaluationResult
  question: EvaluationQuestion | null
  task_name: string
}

export type EvaluationListParams = {
  page: number
  pageSize: number
  groupId?: string
}

export type EvaluationRunListParams = {
  page: number
  pageSize: number
  taskId?: string
}

export type EvaluationResultListParams = {
  page: number
  pageSize: number
  runId?: string
}

export function coerceEvaluationQuestion(value: unknown): EvaluationQuestion | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    group: coerceEvaluationGroupOption(record.group),
    question: asString(record.question),
    expected_answer: typeof record.expected_answer === 'string' ? record.expected_answer : null,
    source: asString(record.source, 'human'),
    created_at: asString(record.created_at),
  }
}

export function coerceEvaluationQuestionOption(value: unknown): EvaluationQuestionOption | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    question: asString(record.question, id),
  }
}

export function coerceEvaluationGroup(value: unknown): EvaluationGroup | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    name: asString(record.name, id),
    description: asString(record.description),
    created_at: asString(record.created_at),
    updated_at: asString(record.updated_at),
  }
}

export function coerceEvaluationGroupOption(value: unknown): EvaluationGroupOption | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    name: asString(record.name, id),
  }
}

export function coerceEvaluationGroupListResult(value: unknown): EvaluationGroupListResult {
  const record = asRecord(value) ?? {}
  const items = coerceItems(value)
    .map((item) => coerceEvaluationGroup(item))
    .filter((item): item is EvaluationGroup => !!item)

  return {
    items,
    total: asNumber(record.total, items.length),
    page: asNumber(record.page, 1),
    page_size: asNumber(record.page_size, items.length || 10),
  }
}

export function coerceEvaluationQuestionDetail(value: unknown): EvaluationQuestionDetail | null {
  const question = coerceEvaluationQuestion(value)
  if (!question) return null

  const record = asRecord(value)
  const rawChunks = record?.chunks
  const chunkList = Array.isArray(rawChunks) ? rawChunks : rawChunks ? [rawChunks] : []

  return {
    ...question,
    chunks: chunkList
      .map((item) => {
        const chunk = asRecord(item)
        if (!chunk) return null
        const id = asString(chunk.id)
        if (!id) return null
        return {
          id,
          content: asString(chunk.content),
        } satisfies EvaluationChunk
      })
      .filter((item): item is EvaluationChunk => !!item),
  }
}

export function coerceEvaluationQuestionListResult(value: unknown): EvaluationQuestionListResult {
  const record = asRecord(value) ?? {}
  const items = coerceItems(value)
    .map((item) => coerceEvaluationQuestion(item))
    .filter((item): item is EvaluationQuestion => !!item)

  return {
    items,
    total: asNumber(record.total, items.length),
    page: asNumber(record.page, 1),
    page_size: asNumber(record.page_size, items.length || 10),
  }
}

export function coerceEvaluationTask(value: unknown): EvaluationTask | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    name: asString(record.name, id),
    group: coerceEvaluationGroupOption(record.group),
    type: asString(record.type, ''),
    knowledge_base: coerceKnowledgeBaseItem(record.knowledge_base),
    total_questions: asNumber(record.total_questions),
    question_ids: asNullableStringArray(record.question_ids),
    config: asNullableRecord(record.config),
    created_at: asString(record.created_at),
    updated_at: asString(record.updated_at),
  }
}

export function coerceEvaluationTaskListResult(value: unknown): EvaluationTaskListResult {
  const record = asRecord(value) ?? {}
  const items = coerceItems(value)
    .map((item) => coerceEvaluationTask(item))
    .filter((item): item is EvaluationTask => !!item)

  return {
    items,
    total: asNumber(record.total, items.length),
    page: asNumber(record.page, 1),
    page_size: asNumber(record.page_size, items.length || 10),
  }
}

export function coerceKnowledgeBaseItem(value: unknown): KnowledgeBaseItem | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    name: asString(record.name, id),
  }
}

export function coerceModelConfigItem(value: unknown): ModelConfigItem | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    name: asString(record.name, id),
    provider: asString(record.provider, ''),
  }
}

export function coerceEvaluationRun(value: unknown): EvaluationRun | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    task_id: asString(record.task_id),
    type: asString(record.type, ''),
    status: asString(record.status, 'pending'),
    knowledge_base: coerceKnowledgeBaseItem(record.knowledge_base),
    total_questions: asNumber(record.total_questions),
    completed_questions: asNumber(record.completed_questions),
    avg_recall: (() => {
      const metricRecord = asRecord(record.avg_recall)
      if (metricRecord) {
        return Object.fromEntries(
          Object.entries(metricRecord).map(([key, itemValue]) => [key, asNullableNumericValue(itemValue)]),
        )
      }
      return asNullableNumericValue(record.avg_recall)
    })(),
    avg_mrr: asNullableNumericValue(record.avg_mrr),
    avg_correctness: asNullableNumericValue(record.avg_correctness),
    avg_faithfulness: asNullableNumericValue(record.avg_faithfulness),
    config: asNullableRecord(record.config),
    error_message: asNullableString(record.error_message),
    model: coerceModelConfigItem(record.model),
    created_at: asString(record.created_at),
    updated_at: asString(record.updated_at),
  }
}

export function coerceEvaluationRunListResult(value: unknown): EvaluationRunListResult {
  const record = asRecord(value) ?? {}
  const items = coerceItems(value)
    .map((item) => coerceEvaluationRun(item))
    .filter((item): item is EvaluationRun => !!item)

  return {
    items,
    total: asNumber(record.total, items.length),
    page: asNumber(record.page, 1),
    page_size: asNumber(record.page_size, items.length || 10),
  }
}

export function coerceExecuteEvaluationResponse(value: unknown): ExecuteEvaluationResponse | null {
  const record = asRecord(value)
  if (!record) return null

  const task_id = asString(record.task_id)
  const run_id = asString(record.run_id)
  const queue_id = asString(record.queue_id)
  if (!task_id || !run_id || !queue_id) return null

  return { task_id, run_id, queue_id }
}

export function coerceEvaluationResult(value: unknown): EvaluationResult | null {
  const record = asRecord(value)
  if (!record) return null

  const id = asString(record.id)
  if (!id) return null

  return {
    id,
    run_id: asString(record.run_id),
    question_id: asString(record.question_id),
    answer: asString(record.answer),
    status: asString(record.status, 'pending'),
    mrr: asNullableNumericValue(record.mrr),
    correctness: asNullableNumericValue(record.correctness),
    faithfulness: asNullableNumericValue(record.faithfulness),
    retrieval_metrics: asNullableRecord(record.retrieval_metrics ?? record.recall),
    latency_ms: asNullableNumber(record.latency_ms),
    trace_data: asNullableRecord(record.trace_data),
    error_message: typeof record.error_message === 'string' ? record.error_message : null,
    created_at: asString(record.created_at),
  }
}

export function coerceEvaluationResultListResult(value: unknown): EvaluationResultListResult {
  const record = asRecord(value) ?? {}
  const items = coerceItems(value)
    .map((item) => coerceEvaluationResult(item))
    .filter((item): item is EvaluationResult => !!item)

  return {
    items,
    total: asNumber(record.total, items.length),
    page: asNumber(record.page, 1),
    page_size: asNumber(record.page_size, items.length || 10),
  }
}

export function coerceEvaluationResultDetail(value: unknown): EvaluationResultDetail | null {
  const record = asRecord(value)
  if (!record) return null

  const result = coerceEvaluationResult(record.result)
  if (!result) return null

  return {
    result,
    question: record.question ? coerceEvaluationQuestion(record.question) : null,
    task_name: asString(record.task_name),
  }
}
