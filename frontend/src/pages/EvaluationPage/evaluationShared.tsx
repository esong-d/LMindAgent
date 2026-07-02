import { Tag } from 'antd'
import { ApiError } from '../../lib/apiClient'

export const pageSizeOptions = [10, 20, 50, 100]

export const questionSourceOptions = [
  { label: '人工', value: 'human' },
  { label: 'AI', value: 'ai' },
]

export function normalizeErrorMessage(err: unknown) {
  if (err instanceof ApiError) return err.message || '请求失败'
  if (err instanceof Error) return err.message || '请求失败'
  return '请求失败'
}

export type DateInput = string | number | Date | null | undefined

export function toDate(input: DateInput) {
  if (!input) return null
  const date = input instanceof Date ? input : new Date(input)
  if (Number.isNaN(date.getTime())) return null
  return date
}

export function formatDateTime(
  input: DateInput,
  options: Intl.DateTimeFormatOptions,
  locale: string = 'zh-CN',
) {
  const date = toDate(input)
  if (!date) return '—'
  return new Intl.DateTimeFormat(locale, options).format(date)
}

// 03/03 14:00
export function formatMonthDayTime(input: DateInput, locale: string = 'zh-CN') {
  return formatDateTime(
    input,
    { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' },
    locale,
  )
}

// 2026/03/03 14:00:03
export function formatMonthDayTimeWithSecond(input: DateInput, locale: string = 'zh-CN') {
  return formatDateTime(
    input,
    { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' },
    locale,
  )
}

export function formatMetric(value: number | null | undefined, fractionDigits = 2) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—'
  return value.toFixed(fractionDigits)
}

export function formatLatency(value: number | null | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—'
  return `${value} s`
}

export function formatJson(value: unknown) {
  if (value == null) return '无'
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return 'JSON 数据格式化失败'
  }
}

export function questionPreview(value: string, fallback = '未填写内容') {
  const text = value.trim()
  if (!text) return fallback
  return text
}

export function splitChunkIds(value: string | undefined) {
  if (!value) return []
  return value
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

export function parseConfigText(value: string | undefined) {
  if (!value || !value.trim()) return null
  const parsed = JSON.parse(value)
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('测评配置必须是 JSON 对象')
  }
  return parsed as Record<string, unknown>
}

export function taskStatusTag(status: string) {
  const normalized = status.toLowerCase()
  if (normalized.includes('success') || normalized.includes('done') || normalized.includes('completed')) return <Tag color="success">成功</Tag>
  if (normalized.includes('running') || normalized.includes('executing')) return <Tag color="processing">运行中</Tag>
  if (normalized.includes('pending') || normalized.includes('queued') || normalized.includes('created')) return <Tag color="gold">待处理</Tag>
  if (normalized.includes('fail') || normalized.includes('error')) return <Tag color="error">失败</Tag>
  return <Tag>{status}</Tag>
}

export function metricTone(value: number | null | undefined) {
  if (typeof value !== 'number') return undefined
  if (value >= 0.8) return 'green'
  if (value >= 0.6) return 'gold'
  return 'red'
}
