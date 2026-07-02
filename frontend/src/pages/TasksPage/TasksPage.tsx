import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Pagination, Popconfirm, Progress, Select, Space, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../../components/Toast/ToastProvider'
import { cancelTask, listTasks } from '../../features/tasks/api'
import { getTaskStatusLabel, getTaskTypeLabel, normalizeTaskStatus, type TaskOut, type TaskStatus, type TaskType } from '../../features/tasks/types'
import { ApiError } from '../../lib/apiClient'
import styles from './TasksPage.module.css'

const pageSizeOptions = [10, 20, 50, 100]

const statusOptions: Array<{ label: string; value: '' | TaskStatus }> = [
  { label: '全部状态', value: '' },
  { label: '排队中', value: 'queued' },
  { label: '运行中', value: 'running' },
  { label: '已成功', value: 'success' },
  { label: '已失败', value: 'failed' },
  { label: '已取消', value: 'canceled' },
]

function isCancelable(status: string) {
  const normalized = normalizeTaskStatus(status)
  return normalized === 'queued' || normalized === 'running'
}

function statusTag(status: string) {
  const normalized = normalizeTaskStatus(status)
  if (normalized === 'queued') return <Tag color="gold">{getTaskStatusLabel(status)}</Tag>
  if (normalized === 'running') return <Tag color="processing">{getTaskStatusLabel(status)}</Tag>
  if (normalized === 'success') return <Tag color="success">{getTaskStatusLabel(status)}</Tag>
  if (normalized === 'failed') return <Tag color="error">{getTaskStatusLabel(status)}</Tag>
  if (normalized === 'canceled') return <Tag>{getTaskStatusLabel(status)}</Tag>
  return <Tag>{getTaskStatusLabel(status)}</Tag>
}

function typeTag(type: TaskType | string | null | undefined) {
  return <Tag color="blue">{getTaskTypeLabel(type as TaskType)}</Tag>
}

function formatDateTime(value: string) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString()
}

export function TasksPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const tableWrapRef = useRef<HTMLDivElement | null>(null)

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [status, setStatus] = useState<'' | Exclude<TaskStatus, 'success'>>('')
  const [items, setItems] = useState<TaskOut[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [cancelingId, setCancelingId] = useState<string | null>(null)
  const [tableScrollY, setTableScrollY] = useState<number | undefined>(undefined)

  const normalizeErrorMessage = useCallback((err: unknown) => {
    console.log("err", err)
    if (err instanceof ApiError) return err.message || '请求失败'
    if (err instanceof Error) return err.message || '请求失败'
    return '请求失败'
  }, [])

  const loadTasks = useCallback(async () => {
    setLoading(true)
    try {
      const result = await listTasks({ page, pageSize, status })
      setItems(result.items)
      setTotal(result.total)
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '加载任务列表失败', message })
    } finally {
      setLoading(false)
    }
  }, [normalizeErrorMessage, page, pageSize, showToast, status])

  useEffect(() => {
    loadTasks().catch(() => {})
  }, [loadTasks])

  // Measure the actual available height for the table body.
  // ResizeObserver is the standard enterprise pattern: it watches the wrapper
  // element and recalculates whenever its size changes (window resize, sidebar
  // toggle, etc.) without needing to observe document.body or listen to resize.
  useLayoutEffect(() => {
    const wrapperEl = tableWrapRef.current
    if (!wrapperEl) return

    const updateScrollY = () => {
      const wrapperHeight = wrapperEl.clientHeight
      if (wrapperHeight <= 0) return

      // Account for the table header so scroll.y defines the body height exactly.
      const thead = wrapperEl.querySelector('.ant-table-thead')
      const headerHeight = thead ? thead.clientHeight : 0

      // Reserve 2px for border-collapse / rounding so the body doesn't push
      // the pagination bar out of the viewport.
      const bodyHeight = Math.max(120, wrapperHeight - headerHeight - 2)

      setTableScrollY((prev) => (prev === bodyHeight ? prev : bodyHeight))
    }

    // Run synchronously inside useLayoutEffect so the browser never paints a
    // stale scroll height.
    updateScrollY()

    const observer = new ResizeObserver(() => updateScrollY())
    observer.observe(wrapperEl)

    return () => observer.disconnect()
  }, [])

  const handleCancel = useCallback(
    async (task: TaskOut) => {
      if (cancelingId) return
      setCancelingId(task.id)
      try {
        const nextTask = await cancelTask(task.id)
        setItems((prev) => prev.map((item) => (item.id === task.id ? nextTask : item)))
        showToast({ type: 'success', title: '任务已取消', message: `任务 ${task.id} 已提交取消` })
      } catch (err) {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '取消任务失败', message })
      } finally {
        setCancelingId(null)
      }
    },
    [cancelingId, normalizeErrorMessage, showToast],
  )
  const hasItems = items.length > 0
  const tableScroll = hasItems
    ? { x: 'max-content', y: tableScrollY }
    : { y: tableScrollY }

  const columns = useMemo<ColumnsType<TaskOut>>(
    () => [
      {
        title: '任务 ID',
        dataIndex: 'id',
        key: 'id',
        width: 240,
        ellipsis: { showTitle: false },
        render: (value: TaskOut['id']) => (
          <Typography.Text copyable ellipsis={{ tooltip: value }} style={{ maxWidth: '100%' }}>
            {value}
          </Typography.Text>
        ),
      },
      {
        title: '文档文件名',
        dataIndex: 'document',
        key: 'document',
        width: 180,
        ellipsis: { showTitle: false },
        render: (value: TaskOut['document']) => (
          value?.filename ? (
            <Typography.Text copyable ellipsis={{ tooltip: value?.filename }} style={{ maxWidth: '100%' }}>
              {value?.filename}
            </Typography.Text>
          ) : (
            '—'
          )
        ),
      },
      {
        title: '任务类型',
        dataIndex: 'type',
        key: 'type',
        width: 150,
        render: (value: TaskOut['type']) => typeTag(value),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (value: TaskOut['status']) => statusTag(String(value)),
      },
      {
        title: '进度',
        dataIndex: 'progress',
        key: 'progress',
        width: 180,
        render: (value: TaskOut['progress']) => <Progress percent={Math.max(0, Math.min(100, Number(value) || 0))} size="small" />,
      },
      {
        title: '重试次数',
        dataIndex: 'retry_count',
        key: 'retry_count',
        width: 110,
      },
      {
        title: '知识库',
        dataIndex: 'knowledge_base',
        key: 'knowledge_base',
        width: 180,
        ellipsis: { showTitle: false },
        render: (value: TaskOut['knowledge_base']) => value?.name || '—',
      },
      {
        title: '错误信息',
        dataIndex: 'error_message',
        key: 'error_message',
        width: 240,
        ellipsis: { showTitle: false },
        render: (value: TaskOut['error_message']) => (
          value ? (
          <Typography.Text copyable ellipsis={{ tooltip: value }} style={{ maxWidth: '100%' }}>
            {value}
          </Typography.Text>
        ) : (
          '—'
        )),
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 180,
        render: (value: TaskOut['created_at']) => formatDateTime(value),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 180,
        render: (value: TaskOut['updated_at']) => formatDateTime(value),
      },
      {
        title: '操作',
        key: 'actions',
        width: 180,
        fixed: 'right',
        align: 'right',
        render: (_, task) => (
          <Space size={8}>
            <Button size="small" onClick={() => navigate(`/tasks/${task.id}`)}>
              详情
            </Button>
            <Popconfirm
              title="确定取消这个任务吗？"
              description={`将取消任务 ${task.id}`}
              okText="取消任务"
              cancelText="关闭"
              disabled={!isCancelable(String(task.status)) || cancelingId === task.id}
              onConfirm={() => handleCancel(task)}
            >
              <Button size="small" danger loading={cancelingId === task.id} disabled={!isCancelable(String(task.status)) || cancelingId === task.id}>
                取消
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [cancelingId, handleCancel, navigate],
  )

  const handlePaginationChange = useCallback((nextPage: number, nextPageSize: number) => {
    if (nextPageSize !== pageSize) {
      setPage(1)
      setPageSize(nextPageSize)
      return
    }

    setPage(nextPage)
  }, [pageSize])

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>任务列表</h1>
          <p className={styles.subtitle}>查看文档处理等后台任务的当前状态、进度和异常信息。</p>
        </div>
        <div className={styles.actions}>
          <Select
            className={styles.filter}
            value={status}
            options={statusOptions}
            onChange={(value) => {
              setPage(1)
              setStatus(value)
            }}
          />
          <Button onClick={() => loadTasks()} loading={loading}>
            刷新
          </Button>
        </div>
      </div>

      <Card
        className={styles.card}
        title="任务记录"
        extra={
          <Typography.Text type="secondary">任务状态不会自动更新，请手动点击刷新</Typography.Text>
        }
      >
        <div ref={tableWrapRef} className={styles.tableWrap}>
          <Table<TaskOut>
            rowKey={(row) => row.id}
            className={styles.table}
            columns={columns}
            dataSource={items}
            loading={loading}
            pagination={false}
            sticky
            showHeader={hasItems}
            scroll={tableScroll}
          />
        </div>
        <div className={styles.paginationBar}>
          <Typography.Text type="secondary">{`共 ${total} 条数据`}</Typography.Text>
          <Pagination
            current={page}
            pageSize={pageSize}
            total={total}
            showSizeChanger
            pageSizeOptions={pageSizeOptions}
            onChange={handlePaginationChange}
          />
        </div>
      </Card>
    </div>
  )
}
