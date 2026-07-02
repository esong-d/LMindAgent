import { createApiClient } from '../../lib/apiClient'
import { clearStoredAuth, getAccessToken, getTokenType } from '../auth/store'
import {
  coerceExecuteEvaluationResponse,
  coerceEvaluationGroup,
  coerceEvaluationGroupListResult,
  coerceEvaluationGroupOption,
  coerceEvaluationQuestion,
  coerceEvaluationQuestionDetail,
  coerceEvaluationQuestionListResult,
  coerceEvaluationQuestionOption,
  coerceEvaluationResultDetail,
  coerceEvaluationResultListResult,
  coerceEvaluationRun,
  coerceEvaluationRunListResult,
  coerceEvaluationTask,
  coerceEvaluationTaskListResult,
  type CreateEvaluationGroupBody,
  type CreateEvaluationQuestionBody,
  type CreateEvaluationTaskBody,
  type EvaluationGroup,
  type EvaluationGroupListResult,
  type EvaluationGroupOption,
  type EvaluationListParams,
  type EvaluationQuestion,
  type EvaluationQuestionDetail,
  type EvaluationQuestionListResult,
  type EvaluationQuestionOption,
  type EvaluationResultDetail,
  type EvaluationResultListParams,
  type EvaluationResultListResult,
  type EvaluationRun,
  type EvaluationRunListParams,
  type EvaluationRunListResult,
  type EvaluationTask,
  type EvaluationTaskListResult,
  type ExecuteEvaluationResponse,
  type UpdateEvaluationGroupBody,
  type UpdateEvaluationQuestionBody,
} from './types'

const evaluationApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

function buildPaginationSearch(params: EvaluationListParams) {
  const search = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  })
  if (params.groupId) {
    search.set('group_id', params.groupId)
  }
  return search.toString()
}

export async function listEvaluationQuestions(params: EvaluationListParams): Promise<EvaluationQuestionListResult> {
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/questions?${buildPaginationSearch(params)}`)
  return coerceEvaluationQuestionListResult(payload)
}

export async function listEvaluationQuestionsByGroup(groupId: string): Promise<EvaluationQuestionOption[]> {
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/questions/group/${encodeURIComponent(groupId)}`)
  const list = Array.isArray(payload) ? payload : []
  return list
    .map((item) => coerceEvaluationQuestionOption(item))
    .filter((item): item is EvaluationQuestionOption => !!item)
}

export async function listAllEvaluationGroups(): Promise<EvaluationGroupOption[]> {
  const payload = await evaluationApi.get<unknown>('/v1/evaluation/groups/all')
  const list = Array.isArray(payload) ? payload : []
  return list
    .map((item) => coerceEvaluationGroupOption(item))
    .filter((item): item is EvaluationGroupOption => !!item)
}

export async function listEvaluationGroups(params: EvaluationListParams): Promise<EvaluationGroupListResult> {
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/groups?${buildPaginationSearch(params)}`)
  return coerceEvaluationGroupListResult(payload)
}

export async function createEvaluationGroup(body: CreateEvaluationGroupBody): Promise<EvaluationGroup> {
  const payload = await evaluationApi.post<unknown, CreateEvaluationGroupBody>('/v1/evaluation/groups', body)
  const group = coerceEvaluationGroup(payload)
  if (!group) throw new Error('创建测评分组返回数据格式不正确')
  return group
}

export async function updateEvaluationGroup(groupId: string, body: UpdateEvaluationGroupBody): Promise<EvaluationGroup> {
  const payload = await evaluationApi.post<unknown, UpdateEvaluationGroupBody>(
    `/v1/evaluation/groups/${encodeURIComponent(groupId)}`,
    body,
  )
  const group = coerceEvaluationGroup(payload)
  if (!group) throw new Error('更新测评分组返回数据格式不正确')
  return group
}

export async function deleteEvaluationGroup(groupId: string): Promise<void> {
  await evaluationApi.del<unknown>(`/v1/evaluation/groups/${encodeURIComponent(groupId)}`)
}

export async function createEvaluationQuestion(body: CreateEvaluationQuestionBody): Promise<EvaluationQuestion> {
  const payload = await evaluationApi.post<unknown, CreateEvaluationQuestionBody>('/v1/evaluation/questions', body)
  const question = coerceEvaluationQuestion(payload)
  if (!question) throw new Error('创建测评问题返回数据格式不正确')
  return question
}

export async function updateEvaluationQuestion(questionId: string, body: UpdateEvaluationQuestionBody): Promise<EvaluationQuestion> {
  const payload = await evaluationApi.post<unknown, UpdateEvaluationQuestionBody>(
    `/v1/evaluation/questions/${encodeURIComponent(questionId)}`,
    body,
  )
  const question = coerceEvaluationQuestion(payload)
  if (!question) throw new Error('更新测评问题返回数据格式不正确')
  return question
}

export async function getEvaluationQuestion(questionId: string): Promise<EvaluationQuestionDetail> {
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/questions/${encodeURIComponent(questionId)}`)
  const question = coerceEvaluationQuestionDetail(payload)
  if (!question) throw new Error('测评问题详情数据格式不正确')
  return question
}

export async function deleteEvaluationQuestion(questionId: string): Promise<void> {
  await evaluationApi.del<unknown>(`/v1/evaluation/questions/${encodeURIComponent(questionId)}`)
}

export async function listEvaluationTasks(params: EvaluationListParams): Promise<EvaluationTaskListResult> {
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/tasks?${buildPaginationSearch(params)}`)
  return coerceEvaluationTaskListResult(payload)
}

export async function createEvaluationTask(body: CreateEvaluationTaskBody): Promise<EvaluationTask> {
  const payload = await evaluationApi.post<unknown, CreateEvaluationTaskBody>('/v1/evaluation/tasks', body)
  const task = coerceEvaluationTask(payload)
  if (!task) throw new Error('创建测评任务返回数据格式不正确')
  return task
}

export async function getEvaluationTask(taskId: string): Promise<EvaluationTask> {
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/tasks/${encodeURIComponent(taskId)}`)
  const task = coerceEvaluationTask(payload)
  if (!task) throw new Error('测评任务详情数据格式不正确')
  return task
}

export async function deleteEvaluationTask(taskId: string): Promise<void> {
  await evaluationApi.del<unknown>(`/v1/evaluation/tasks/${encodeURIComponent(taskId)}`)
}

export async function listEvaluationRuns(params: EvaluationRunListParams): Promise<EvaluationRunListResult> {
  const search = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  })
  if (params.taskId) {
    search.set('task_id', params.taskId)
  }
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/runs?${search.toString()}`)
  return coerceEvaluationRunListResult(payload)
}

export async function getEvaluationRun(runId: string): Promise<EvaluationRun> {
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/runs/${encodeURIComponent(runId)}`)
  const run = coerceEvaluationRun(payload)
  if (!run) throw new Error('测评记录详情数据格式不正确')
  return run
}

export async function deleteEvaluationRun(runId: string): Promise<void> {
  await evaluationApi.del<unknown>(`/v1/evaluation/runs/${encodeURIComponent(runId)}`)
}

export async function executeEvaluationTask(taskId: string): Promise<ExecuteEvaluationResponse> {
  const payload = await evaluationApi.post<unknown, { task_id: string }>('/v1/evaluation/execute', { task_id: taskId })
  const result = coerceExecuteEvaluationResponse(payload)
  if (!result) throw new Error('执行测评返回数据格式不正确')
  return result
}

export async function listEvaluationResults(params: EvaluationResultListParams): Promise<EvaluationResultListResult> {
  const search = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  })
  if (params.runId) {
    search.set('run_id', params.runId)
  }
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/results?${search.toString()}`)
  return coerceEvaluationResultListResult(payload)
}

export async function getEvaluationResult(resultId: string): Promise<EvaluationResultDetail> {
  const payload = await evaluationApi.get<unknown>(`/v1/evaluation/results/${encodeURIComponent(resultId)}`)
  const detail = coerceEvaluationResultDetail(payload)
  if (!detail) throw new Error('测评结果详情数据格式不正确')
  return detail
}
