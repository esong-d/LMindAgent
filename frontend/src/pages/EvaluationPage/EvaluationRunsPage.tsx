import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Alert, Button, Card, Empty, Input, Modal, Pagination, Popconfirm, Progress, Select, Skeleton, Space, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useToast } from '../../components/Toast/ToastProvider'
import { deleteEvaluationRun, getEvaluationRun, listEvaluationRuns, listEvaluationTasks } from '../../features/evaluation/api'
import type { EvaluationRun, EvaluationTask } from '../../features/evaluation/types'
import { formatJson, formatMetric, formatMonthDayTimeWithSecond, metricTone, normalizeErrorMessage, pageSizeOptions, taskStatusTag } from './evaluationShared'
import styles from './EvaluationPage.module.css'

const STATUS_FILTERS = [
  { key: '', label: '全部' },
  { key: 'running', label: '运行中' },
  { key: 'pending', label: '待处理' },
  { key: 'success', label: '已完成' },
  { key: 'failed', label: '失败' },
] as const

function normalizeStatus(status: string) {
  return status.toLowerCase()
}

function statusGroup(status: string) {
  const value = normalizeStatus(status)
  if (value.includes('success') || value.includes('done') || value.includes('completed')) return 'success'
  if (value.includes('running') || value.includes('executing')) return 'running'
  if (value.includes('pending') || value.includes('queued') || value.includes('created')) return 'pending'
  if (value.includes('fail') || value.includes('error')) return 'failed'
  return ''
}

function formatTaskType(type: string) {
  if (type === 'generate_question') return '生成问题'
  if (type === 'run_evaluation') return '运行测评'
  return type || '—'
}

function getProgressPercent(run: EvaluationRun) {
  if (run.total_questions <= 0) return 0
  return Math.min(100, Math.round((run.completed_questions / run.total_questions) * 100))
}

function isRecallMetricMap(value: EvaluationRun['avg_recall']): value is Record<string, number | null> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

function formatRecallMetricLabel(key: string) {
  if (key === 'rrf_recall') return 'RRF'
  if (key === 'bm25_recall') return 'BM25'
  if (key === 'ranker_recall') return 'Ranker'
  if (key === 'vector_recall') return 'Vector'
  return key.replace(/_recall$/i, '').replace(/_/g, ' ')
}

function getRecallMetricEntries(value: EvaluationRun['avg_recall']) {
  if (!isRecallMetricMap(value)) return []
  return Object.entries(value)
}

function getRecallMetricToneValue(value: EvaluationRun['avg_recall']) {
  if (typeof value === 'number') return value
  const metrics = getRecallMetricEntries(value)
    .map(([, itemValue]) => itemValue)
    .filter((itemValue): itemValue is number => typeof itemValue === 'number' && Number.isFinite(itemValue))
  if (!metrics.length) return null
  return metrics.reduce((sum, itemValue) => sum + itemValue, 0) / metrics.length
}

function formatRecallSummary(value: EvaluationRun['avg_recall'], maxItems = 2) {
  if (typeof value === 'number') return formatMetric(value)
  const entries = getRecallMetricEntries(value)
  if (!entries.length) return '—'
  const visibleEntries = entries.slice(0, maxItems).map(([key, itemValue]) => `${formatRecallMetricLabel(key)}: ${formatMetric(itemValue)}`)
  return entries.length > maxItems ? `${visibleEntries.join(' · ')} · ...` : visibleEntries.join(' · ')
}

const TABLE_HEADER_OFFSET = 56

export function EvaluationRunsPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const tableWrapperRef = useRef<HTMLDivElement>(null)
  const [tableBodyHeight, setTableBodyHeight] = useState(0)

  const [tasks, setTasks] = useState<EvaluationTask[]>([])
  const [tasksLoading, setTasksLoading] = useState(false)

  const [runs, setRuns] = useState<EvaluationRun[]>([])
  const [runsTotal, setRunsTotal] = useState(0)
  const [runsPage, setRunsPage] = useState(1)
  const [runsPageSize, setRunsPageSize] = useState(10)
  const [runsLoading, setRunsLoading] = useState(false)

  const [detailOpen, setDetailOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detail, setDetail] = useState<EvaluationRun | null>(null)

  const [deletingRunId, setDeletingRunId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [searchText, setSearchText] = useState('')

  const selectedTaskId = searchParams.get('taskId') ?? ''

  useLayoutEffect(() => {
    const el = tableWrapperRef.current
    if (!el) return

    const updateHeight = () => {
      const nextHeight = Math.max(el.getBoundingClientRect().height - TABLE_HEADER_OFFSET, 160)
      setTableBodyHeight(nextHeight)
    }
    updateHeight()

    const ro = new ResizeObserver(() => updateHeight())
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const taskNameMap = useMemo(
    () => new Map(tasks.map((item) => [item.id, item.name])),
    [tasks],
  )
  const selectedTaskLabel = selectedTaskId ? taskNameMap.get(selectedTaskId) ?? selectedTaskId : '全部任务'

  const loadTasks = useCallback(async () => {
    setTasksLoading(true)
    try {
      const data = await listEvaluationTasks({ page: 1, pageSize: 100 })
      setTasks(data.items)
    } catch (err) {
      showToast({ type: 'error', title: '加载任务选项失败', message: normalizeErrorMessage(err) })
    } finally {
      setTasksLoading(false)
    }
  }, [showToast])

  const loadRuns = useCallback(async () => {
    setRunsLoading(true)
    try {
      const data = await listEvaluationRuns({
        page: runsPage,
        pageSize: runsPageSize,
        taskId: selectedTaskId || undefined,
      })
      setRuns(data.items)
      setRunsTotal(data.total)
    } catch (err) {
      showToast({ type: 'error', title: '加载测评记录失败', message: normalizeErrorMessage(err) })
    } finally {
      setRunsLoading(false)
    }
  }, [runsPage, runsPageSize, selectedTaskId, showToast])

  useEffect(() => {
    loadTasks().catch(() => {})
  }, [loadTasks])

  useEffect(() => {
    loadRuns().catch(() => {})
  }, [loadRuns])

  const filteredRuns = useMemo(() => {
    let list = runs

    if (statusFilter) {
      list = list.filter((item) => statusGroup(item.status) === statusFilter)
    }

    if (searchText.trim()) {
      const keyword = searchText.trim().toLowerCase()
      list = list.filter(
        (item) =>
          (taskNameMap.get(item.task_id) ?? item.task_id).toLowerCase().includes(keyword) ||
          item.id.toLowerCase().includes(keyword) ||
          (item.knowledge_base?.id ?? "").toLowerCase().includes(keyword) ||
          formatTaskType(item.type).toLowerCase().includes(keyword) ||
          (item.error_message ?? '').toLowerCase().includes(keyword),
      )
    }

    return list
  }, [runs, searchText, statusFilter, taskNameMap])
  const hasFilteredRuns = filteredRuns.length > 0
  const tableScroll = tableBodyHeight > 0
    ? hasFilteredRuns
      ? { x: 1840, y: tableBodyHeight }
      : { y: tableBodyHeight }
    : hasFilteredRuns
      ? { x: 1840, y: 400 }
      : { y: 400 }

  const openDetail = useCallback(async (runId: string) => {
    setDetailOpen(true)
    setDetailLoading(true)
    setDetail(null)
    try {
      const data = await getEvaluationRun(runId)
      setDetail(data)
    } catch (err) {
      showToast({ type: 'error', title: '加载测评记录详情失败', message: normalizeErrorMessage(err) })
    } finally {
      setDetailLoading(false)
    }
  }, [showToast])

  const handleDeleteRun = useCallback(async (runId: string) => {
    if (deletingRunId) return
    setDeletingRunId(runId)
    try {
      await deleteEvaluationRun(runId)
      showToast({ type: 'success', title: '已删除', message: '测评记录已删除' })
      const nextPage = runs.length === 1 && runsPage > 1 ? runsPage - 1 : runsPage
      if (nextPage !== runsPage) setRunsPage(nextPage)
      else await loadRuns()
    } catch (err) {
      showToast({ type: 'error', title: '删除测评记录失败', message: normalizeErrorMessage(err) })
    } finally {
      setDeletingRunId(null)
    }
  }, [deletingRunId, loadRuns, runs.length, runsPage, showToast])

  const columns = useMemo<ColumnsType<EvaluationRun>>(
    () => [
      {
        title: '任务',
        key: 'task',
        width: 120,
        ellipsis: { showTitle: false },
        sorter: (a, b) => (taskNameMap.get(a.task_id) ?? a.task_id).localeCompare(taskNameMap.get(b.task_id) ?? b.task_id),
        render: (_, row) => (
            <Typography.Text strong ellipsis={{ tooltip: taskNameMap.get(row.task_id) ?? row.task_id }}>
              {taskNameMap.get(row.task_id) ?? row.task_id}
            </Typography.Text>
        ),
      },
      {
        title: '任务类型',
        dataIndex: 'type',
        key: 'type',
        width: 80,
        sorter: (a, b) => formatTaskType(a.type).localeCompare(formatTaskType(b.type)),
        render: (value: EvaluationRun['type']) => <Typography.Text>{formatTaskType(value)}</Typography.Text>,
      },
      {
        title: '知识库',
        dataIndex: 'knowledge_base',
        key: 'knowledge_base',
        width: 120,
        ellipsis: { showTitle: false },
        sorter: (a, b) => (a.knowledge_base?.name ?? '').localeCompare(b.knowledge_base?.name ?? ''),
        render: (value: EvaluationRun['knowledge_base']) => (
          <Typography.Text ellipsis={{ tooltip: value?.name }}>{value?.name || '—'}</Typography.Text>
        ),
      },
      // {
      //   title: '记录 ID',
      //   dataIndex: 'id',
      //   key: 'id',
      //   width: 220,
      //   ellipsis: { showTitle: false },
      //   sorter: (a, b) => a.id.localeCompare(b.id),
      //   render: (value: EvaluationRun['id']) => <Typography.Text ellipsis={{ tooltip: value }}>{value}</Typography.Text>,
      // },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 80,
        sorter: (a, b) => statusGroup(a.status).localeCompare(statusGroup(b.status)),
        render: (value: EvaluationRun['status']) => taskStatusTag(value),
      },
      // {
      //   title: '知识库 ID',
      //   dataIndex: 'knowledge_base_id',
      //   key: 'knowledge_base_id',
      //   width: 220,
      //   ellipsis: { showTitle: false },
      //   sorter: (a, b) => a.knowledge_base_id.localeCompare(b.knowledge_base_id),
      //   render: (value: EvaluationRun['knowledge_base_id']) => (
      //     <Typography.Text ellipsis={{ tooltip: value }}>{value || '—'}</Typography.Text>
      //   ),
      // },
      {
        title: '进度',
        key: 'progress',
        width: 180,
        sorter: (a, b) => getProgressPercent(a) - getProgressPercent(b),
        render: (_, row) => (
          <div>
            <Progress percent={getProgressPercent(row)} size="small" status={statusGroup(row.status) === 'failed' ? 'exception' : 'normal'} />
            <Typography.Text type="secondary">{`${row.completed_questions}/${row.total_questions}`}</Typography.Text>
          </div>
        ),
      },
      // {
      //   title: '评估指标',
      //   key: 'metrics',
      //   width: 300,
      //   render: (_, row) => (
      //     <div
      //       style={{
      //         display: 'grid',
      //         gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
      //         gap: 6,
      //       }}
      //     >
      //       {([
      //         { label: 'Recall', value: formatRecallSummary(row.avg_recall), toneValue: getRecallMetricToneValue(row.avg_recall) },
      //         { label: 'MRR', value: formatMetric(row.avg_mrr), toneValue: row.avg_mrr },
      //         { label: 'Correct', value: formatMetric(row.avg_correctness), toneValue: row.avg_correctness },
      //         { label: 'Faith', value: formatMetric(row.avg_faithfulness), toneValue: row.avg_faithfulness },
      //       ] as const).map((item) => {
      //         const tone = metricTone(item.toneValue)
      //         const color = tone === 'green' ? '#389e0d' : tone === 'gold' ? '#d48806' : tone === 'red' ? '#cf1322' : 'rgba(0,0,0,0.45)'
      //         return (
      //           <Typography.Text key={item.label} style={{ color }}>
      //             {`${item.label}: ${item.value}`}
      //           </Typography.Text>
      //         )
      //       })}
      //     </div>
      //   ),
      // },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 180,
        sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        defaultSortOrder: 'descend',
        render: (value: EvaluationRun['created_at']) => formatMonthDayTimeWithSecond(value),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 180,
        sorter: (a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
        render: (value: EvaluationRun['updated_at']) => formatMonthDayTimeWithSecond(value),
      },
      {
        title: '操作',
        key: 'actions',
        align: 'right',
        width: 120,
        fixed: 'right',
        render: (_, row) => (
          <div style={{ display: 'inline-flex', justifyContent: 'flex-end', gap: 8, flexWrap: 'nowrap', whiteSpace: 'nowrap' }}>
            <Button size="small" onClick={() => openDetail(row.id)}>
              详情
            </Button>
            <Button
              size="small"
              disabled={row.type === 'generate_question'}
              onClick={() => navigate(`/evaluation/results?taskId=${encodeURIComponent(row.task_id)}&runId=${encodeURIComponent(row.id)}`)}
            >
              结果
            </Button>
            <Popconfirm
              title="确定删除这条测评记录吗？"
              description="删除后该次运行的统计信息和结果展示将不可见"
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              onConfirm={() => handleDeleteRun(row.id)}
              disabled={deletingRunId === row.id}
            >
              <Button danger size="small" loading={deletingRunId === row.id} disabled={deletingRunId === row.id}>
                删除
              </Button>
            </Popconfirm>
          </div>
        ),
      },
    ],
    [deletingRunId, handleDeleteRun, navigate, openDetail, taskNameMap],
  )

  return (
    <div className={styles.sectionPage}>
      <div className={styles.toolbar}>
        <Input
          className={styles.searchInput}
          placeholder="搜索任务、记录 ID、知识库或错误信息…"
          allowClear
          value={searchText}
          prefix={<span style={{ fontSize: 14, opacity: 0.45 }}>⌕</span>}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <Select
          className={styles.filterSelect}
          placeholder="按任务筛选"
          allowClear
          showSearch
          loading={tasksLoading}
          value={selectedTaskId || undefined}
          options={tasks.map((item) => ({ label: item.name, value: item.id }))}
          onChange={(value) => {
            const next = new URLSearchParams(searchParams)
            if (value) next.set('taskId', value)
            else next.delete('taskId')
            setSearchParams(next, { replace: true })
            setRunsPage(1)
          }}
        />
        <Select
          className={styles.filterSelect}
          placeholder="按状态筛选"
          allowClear
          value={statusFilter || undefined}
          options={STATUS_FILTERS.filter((item) => item.key).map((item) => ({ label: item.label, value: item.key }))}
          onChange={(value) => setStatusFilter(value ?? '')}
        />
        <div className={styles.toolbarSpacer} />
        <Space wrap>
          <Button onClick={() => loadRuns()} loading={runsLoading}>
            刷新
          </Button>
        </Space>
      </div>

      <div className={styles.listSection}>
        <Card
          className={styles.sectionCard}
          title="测评记录"
          extra={
            <Space size={16} wrap>
              <Typography.Text type="secondary">{`任务：${selectedTaskLabel}`}</Typography.Text>
              <Typography.Text type="secondary">{`状态：${STATUS_FILTERS.find((item) => item.key === statusFilter)?.label ?? '全部'}`}</Typography.Text>
            </Space>
          }
        >
          <div ref={tableWrapperRef} style={{ flex: 1, minHeight: 0 }}>
            <Table<EvaluationRun>
              className={styles.resultAntTable}
              rowKey={(row) => row.id}
              dataSource={filteredRuns}
              columns={columns}
              loading={runsLoading}
              pagination={false}
              tableLayout="fixed"
            showHeader={hasFilteredRuns}
            scroll={tableScroll}
              locale={{
                emptyText: (
                  <div className={styles.taskTableEmpty}>
                    <div className={styles.emptyStateIcon}>{searchText || statusFilter || selectedTaskId ? '🔍' : '🧾'}</div>
                    <h3 className={styles.emptyStateHeading}>
                      {searchText || statusFilter || selectedTaskId ? '没有匹配的测评记录' : '暂无测评记录'}
                    </h3>
                    <p className={styles.emptyStateText}>
                      {searchText || statusFilter || selectedTaskId
                        ? '尝试调整搜索关键词或筛选条件'
                        : '执行测评任务后，每次运行都会在这里生成一条测评记录'}
                    </p>
                  </div>
                ),
              }}
            />
          </div>
          <div className={styles.paginationBar}>
            <Typography.Text type="secondary">{`共 ${runsTotal} 条`}</Typography.Text>
            <Pagination
              size="small"
              current={runsPage}
              pageSize={runsPageSize}
              total={runsTotal}
              showSizeChanger
              pageSizeOptions={pageSizeOptions}
              onChange={(page, pageSize) => {
                if (pageSize !== runsPageSize) {
                  setRunsPage(1)
                  setRunsPageSize(pageSize)
                  return
                }
                setRunsPage(page)
              }}
            />
          </div>
        </Card>
      </div>

      <Modal
        title="测评记录详情"
        open={detailOpen}
        footer={null}
        onCancel={() => setDetailOpen(false)}
        width={760}
        styles={{ body: { maxHeight: 'calc(100vh - 200px)', overflow: 'auto' } }}
        classNames={{ body: styles.modalBody }}
      >
        {detailLoading ? (
          <Skeleton active paragraph={{ rows: 8 }} />
        ) : !detail ? (
          <Empty description="未获取到测评记录详情" />
        ) : (
          <div className={styles.detailStack}>
            {detail.error_message ? (
              <Alert type="error" showIcon message="当前记录存在异常" description={detail.error_message} />
            ) : null}

            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>基本信息</h4>
              <div className={styles.detailMetaRow}>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>记录 ID</span>
                  <span className={styles.detailMetaVal}>{detail.id}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>任务</span>
                  <span className={styles.detailMetaVal}>{taskNameMap.get(detail.task_id) ?? detail.task_id}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>类型</span>
                  <span className={styles.detailMetaVal}>{formatTaskType(detail.type)}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>状态</span>
                  <span className={styles.detailMetaVal}>{taskStatusTag(detail.status)}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>知识库</span>
                  <span className={styles.detailMetaVal}>{detail.knowledge_base?.name || '—'}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>进度</span>
                  <span className={styles.detailMetaVal}>{`${detail.completed_questions}/${detail.total_questions}`}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>创建时间</span>
                  <span className={styles.detailMetaVal}>{formatMonthDayTimeWithSecond(detail.created_at)}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>更新时间</span>
                  <span className={styles.detailMetaVal}>{formatMonthDayTimeWithSecond(detail.updated_at)}</span>
                </div>
              </div>
            </div>

            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>评估指标(运行问题结果平均值)</h4>
              <div className={styles.detailMetricGrid}>
                {([
                  {
                    key: 'Recall',
                    value:
                      getRecallMetricEntries(detail.avg_recall).length > 0
                        ? getRecallMetricEntries(detail.avg_recall)
                            .map(([metricKey, metricValue]) => `${formatRecallMetricLabel(metricKey)}: ${formatMetric(metricValue)}`)
                            .join('\n')
                        : formatRecallSummary(detail.avg_recall, 4),
                    toneValue: getRecallMetricToneValue(detail.avg_recall),
                  },
                  { key: 'MRR', value: formatMetric(detail.avg_mrr), toneValue: detail.avg_mrr },
                  { key: 'Correctness', value: formatMetric(detail.avg_correctness), toneValue: detail.avg_correctness },
                  { key: 'Faithfulness', value: formatMetric(detail.avg_faithfulness), toneValue: detail.avg_faithfulness },
                ] as const).map((item) => {
                  const tone = metricTone(item.toneValue)
                  const cls =
                    tone === 'green'
                      ? styles.metricChipGreen
                      : tone === 'gold'
                        ? styles.metricChipGold
                        : tone === 'red'
                          ? styles.metricChipRed
                          : ''
                  return (
                    <div key={item.key} className={[styles.detailMetricBlock, cls].join(' ')}>
                      <span className={styles.detailMetricBlockLabel}>{item.key}</span>
                      <span className={styles.detailMetricBlockValue}>{item.value}</span>
                    </div>
                  )
                })}
              </div>
            </div>
            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>模型配置</h4>
              {detail.model ? (
                <div className={styles.detailMetaRow}>
                  <div className={styles.detailMetaItem}>
                    <span className={styles.detailMetaKey}>模型名</span>
                    <span className={styles.detailMetaVal}>{detail.model.name || '—'}</span>
                  </div>
                  <div className={styles.detailMetaItem}>
                    <span className={styles.detailMetaKey}>Provider</span>
                    <span className={styles.detailMetaVal}>{detail.model.provider || '—'}</span>
                  </div>
                </div>
              ) : (
                <span className={styles.detailMetaVal}>—</span>
              )}
            </div>
            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>运行配置</h4>
              <pre className={styles.jsonBlock}>{formatJson(detail.config)}</pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
