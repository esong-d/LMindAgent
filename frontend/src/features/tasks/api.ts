import { createApiClient } from '../../lib/apiClient'
import { clearStoredAuth, getAccessToken, getTokenType } from '../auth/store'
import { coerceTaskListData, coerceTaskOut, type TaskListParams, type TaskListResult, type TaskOut } from './types'

const tasksApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

export async function listTasks(params: TaskListParams): Promise<TaskListResult> {
  const search = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  })

  if (params.status) search.set('status', params.status)

  const payload = await tasksApi.get<unknown>(`/v1/tasks?${search.toString()}`)
  const data = coerceTaskListData(payload)

  return {
    items: data.list,
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  }
}

export async function getTask(taskId: string): Promise<TaskOut> {
  const payload = await tasksApi.get<unknown>(`/v1/tasks/${encodeURIComponent(taskId)}`)
  const task = coerceTaskOut(payload)
  if (!task) throw new Error('任务详情数据格式不正确')
  return task
}

export async function cancelTask(taskId: string): Promise<TaskOut> {
  const payload = await tasksApi.post<unknown, Record<string, never>>(`/v1/tasks/${encodeURIComponent(taskId)}/cancel`, {})
  const task = coerceTaskOut(payload)
  if (!task) throw new Error('取消任务返回数据格式不正确')
  return task
}
