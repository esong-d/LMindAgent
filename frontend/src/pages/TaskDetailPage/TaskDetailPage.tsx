import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Descriptions, Empty, Progress, Skeleton, Space, Tag, Typography } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { useToast } from '../../components/Toast/ToastProvider'
import { cancelTask, getTask } from '../../features/tasks/api'
import { getTaskStatusLabel, normalizeTaskStatus, type TaskOut } from '../../features/tasks/types'
import { ApiError } from '../../lib/apiClient'
import styles from './TaskDetailPage.module.css'

function statusTag(status: string) {
  const normalized = normalizeTaskStatus(status)
  if (normalized === 'queued') return <Tag color="gold">{getTaskStatusLabel(status)}</Tag>
  if (normalized === 'running') return <Tag color="processing">{getTaskStatusLabel(status)}</Tag>
  if (normalized === 'success') return <Tag color="success">{getTaskStatusLabel(status)}</Tag>
  if (normalized === 'failed') return <Tag color="error">{getTaskStatusLabel(status)}</Tag>
  if (normalized === 'canceled') return <Tag>{getTaskStatusLabel(status)}</Tag>
  return <Tag>{getTaskStatusLabel(status)}</Tag>
}

function isCancelable(status: string | undefined) {
  const normalized = normalizeTaskStatus(status)
  return normalized === 'queued' || normalized === 'running'
}

function formatJson(value: Record<string, unknown>) {
  const keys = Object.keys(value ?? {})
  if (!keys.length) return '无'

  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return 'JSON 数据格式化失败'
  }
}

function formatDateTime(value: string | undefined) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString()
}

export function TaskDetailPage() {
  const navigate = useNavigate()
  const { taskId } = useParams()
  const { showToast } = useToast()
  const [task, setTask] = useState<TaskOut | null>(null)
  const [loading, setLoading] = useState(true)
  const [canceling, setCanceling] = useState(false)

  const normalizeErrorMessage = useCallback((err: unknown) => {
    if (err instanceof ApiError) return err.message || '请求失败'
    if (err instanceof Error) return err.message || '请求失败'
    return '请求失败'
  }, [])

  const loadTask = useCallback(async () => {
    if (!taskId) {
      setTask(null)
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      const data = await getTask(taskId)
      setTask(data)
    } catch (err) {
      const message = normalizeErrorMessage(err)
      setTask(null)
      showToast({ type: 'error', title: '加载任务详情失败', message })
    } finally {
      setLoading(false)
    }
  }, [normalizeErrorMessage, showToast, taskId])

  useEffect(() => {
    loadTask().catch(() => {})
  }, [loadTask])

  const detailItems = useMemo(
    () => [
      { label: '任务 ID', value: task?.id || '—' },
      { label: '任务类型', value: task?.type || '—' },
      { label: '状态', value: task ? statusTag(String(task.status)) : '—' },
      { label: '进度', value: <Progress percent={Math.max(0, Math.min(100, Number(task?.progress) || 0))} /> },
      { label: '重试次数', value: task?.retry_count ?? '—' },
      { label: '知识库名称', value: task?.knowledge_base?.name || '—' },
      { label: '文档文件名', value: task?.document?.filename || '—' },
      { label: '创建时间', value: formatDateTime(task?.created_at) },
      { label: '更新时间', value: formatDateTime(task?.updated_at) },
    ],
    [task],
  )

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>任务详情</h1>
        </div>
        <Space wrap>
          <Button onClick={() => navigate('/tasks')}>返回列表</Button>
          <Button onClick={() => loadTask()} loading={loading}>
            刷新
          </Button>
          <Button
            danger
            type="primary"
            loading={canceling}
            disabled={!isCancelable(task?.status)}
            onClick={async () => {
              if (!taskId || !task) return
              setCanceling(true)
              try {
                const nextTask = await cancelTask(taskId)
                setTask(nextTask)
                showToast({ type: 'success', title: '任务已取消', message: `任务 ${task.id} 已提交取消` })
              } catch (err) {
                const message = normalizeErrorMessage(err)
                showToast({ type: 'error', title: '取消任务失败', message })
              } finally {
                setCanceling(false)
              }
            }}
          >
            取消任务
          </Button>
        </Space>
      </div>

      <Alert className={styles.notice} type="info" showIcon message="任务状态不会自动更新" description="如需查看最新进度，请手动点击上方刷新按钮。" />

      {loading ? (
        <Card>
          <Skeleton active paragraph={{ rows: 10 }} />
        </Card>
      ) : !task ? (
        <Card>
          <Empty description="未获取到任务详情" />
        </Card>
      ) : (
        <div className={styles.stack}>
          {task.error_message ? <Alert type="error" showIcon message="任务异常" description={task.error_message} /> : null}

          <Card title="基础信息">
            <Descriptions
              column={1}
              size="small"
              styles={{ label: { width: 120, color: 'rgba(0, 0, 0, 0.45)' }, content: { wordBreak: 'break-all' } }}
            >
              {detailItems.map((item) => (
                <Descriptions.Item key={item.label} label={item.label}>
                  {item.value}
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>

          <Card title="输入参数">
            <Typography.Paragraph className={styles.codeBlock}>
              <pre>{formatJson(task.input_json)}</pre>
            </Typography.Paragraph>
          </Card>

          <Card title="输出结果">
            <Typography.Paragraph className={styles.codeBlock}>
              <pre>{formatJson(task.output_json)}</pre>
            </Typography.Paragraph>
          </Card>
        </div>
      )}
    </div>
  )
}
