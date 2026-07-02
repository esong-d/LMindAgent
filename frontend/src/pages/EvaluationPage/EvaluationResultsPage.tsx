import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Alert, Button, Card, Empty, Input, Modal, Pagination, Skeleton, Space, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useSearchParams } from 'react-router-dom'
import { useToast } from '../../components/Toast/ToastProvider'
import { getEvaluationResult, listEvaluationResults, listEvaluationRuns } from '../../features/evaluation/api'
import type { EvaluationResult, EvaluationResultDetail, EvaluationRun } from '../../features/evaluation/types'
import { formatJson, formatLatency, formatMetric, formatMonthDayTimeWithSecond, metricTone, normalizeErrorMessage, pageSizeOptions } from './evaluationShared'
import styles from './EvaluationPage.module.css'

function resultMetricClass(value: number | null | undefined) {
  const tone = metricTone(value)
  if (tone === 'green') return styles.taskMetricGreen
  if (tone === 'gold') return styles.taskMetricGold
  if (tone === 'red') return styles.taskMetricRed
  return styles.taskMetricMuted
}

function formatRetrievalMetricsSummary(value: Record<string, unknown> | null | undefined) {
  if (!value) return '—'
  const entries = Object.entries(value)
  if (!entries.length) return '{}'
  return entries
    .slice(0, 2)
    .map(([key, itemValue]) => {
      if (typeof itemValue === 'number' && Number.isFinite(itemValue)) return `${key}: ${formatMetric(itemValue, 2)}`
      if (typeof itemValue === 'string' && itemValue.trim()) return `${key}: ${itemValue}`
      try {
        return `${key}: ${JSON.stringify(itemValue)}`
      } catch {
        return `${key}: [unserializable]`
      }
    })
    .join(' · ')
}

function formatRetrievalMetricLabel(key: string) {
  if (key === 'rrf_recall') return 'RRF Recall'
  if (key === 'bm25_recall') return 'BM25 Recall'
  if (key === 'ranker_recall') return 'Ranker Recall'
  if (key === 'vector_recall') return 'Vector Recall'
  return key.replace(/_/g, ' ')
}

function formatResultMetricLabel(key: 'Latency' | 'MRR' | 'Correctness' | 'Faithfulness') {
  if (key === 'Latency') return '耗时'
  if (key === 'MRR') return 'MRR'
  if (key === 'Correctness') return '正确性'
  return '忠实性'
}

function getTraceJudge(
  traceData: Record<string, unknown> | null | undefined,
  key: 'correctness' | 'faithfulness',
): { score: number | null; reason: string } | null {
  if (!traceData) return null
  const value = traceData[key]
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  const scoreRaw = (value as { score?: unknown }).score
  const reasonRaw = (value as { reason?: unknown }).reason
  const score =
    typeof scoreRaw === 'number' && Number.isFinite(scoreRaw)
      ? scoreRaw
      : typeof scoreRaw === 'string' && scoreRaw.trim() && Number.isFinite(Number(scoreRaw))
        ? Number(scoreRaw)
        : null
  return {
    score,
    reason: typeof reasonRaw === 'string' ? reasonRaw : '',
  }
}


function resultStatusLabel(status: string) {
  switch (status.toLowerCase()) {
    case 'pending':
      return '待处理'
    case 'running':
      return '运行中'
    case 'success':
      return '成功'
    case 'failed':
      return '失败'
    default:
      return status || '未知'
  }
}

function resultStatusTag(status: string) {
  const normalized = status.toLowerCase()
  if (normalized === 'success') return <Tag color="success">{resultStatusLabel(status)}</Tag>
  if (normalized === 'running') return <Tag color="processing">{resultStatusLabel(status)}</Tag>
  if (normalized === 'pending') return <Tag color="gold">{resultStatusLabel(status)}</Tag>
  if (normalized === 'failed') return <Tag color="error">{resultStatusLabel(status)}</Tag>
  return <Tag>{resultStatusLabel(status)}</Tag>
}

const STATUS_FILTERS = [
  { key: '', label: '全部' },
  { key: 'pending', label: '待处理' },
  { key: 'running', label: '运行中' },
  { key: 'success', label: '成功' },
  { key: 'failed', label: '失败' },
] as const

const TABLE_HEADER_OFFSET = 56

export function EvaluationResultsPage() {
  const { showToast } = useToast()
  const [searchParams] = useSearchParams()

  const [runOptions, setRunOptions] = useState<EvaluationRun[]>([])
  const [runsLoading, setRunsLoading] = useState(false)

  const [results, setResults] = useState<EvaluationResult[]>([])
  const [resultsTotal, setResultsTotal] = useState(0)
  const [resultsPage, setResultsPage] = useState(1)
  const [resultsPageSize, setResultsPageSize] = useState(10)
  const [resultsLoading, setResultsLoading] = useState(false)

  const [resultDetailOpen, setResultDetailOpen] = useState(false)
  const [resultDetailLoading, setResultDetailLoading] = useState(false)
  const [resultDetail, setResultDetail] = useState<EvaluationResultDetail | null>(null)

  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const tableWrapperRef = useRef<HTMLDivElement>(null)
  const [tableBodyHeight, setTableBodyHeight] = useState(0)

  const selectedTaskId = searchParams.get('taskId') ?? ''
  const selectedRunId = searchParams.get('runId') ?? ''

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

  const selectedRun = useMemo(
    () => runOptions.find((item) => item.id === selectedRunId) ?? null,
    [runOptions, selectedRunId],
  )

  const loadRunOptions = useCallback(async () => {
    setRunsLoading(true)
    try {
      const data = await listEvaluationRuns({
        page: 1,
        pageSize: 100,
        taskId: selectedTaskId || undefined,
      })
      setRunOptions(data.items)
    } catch (err) {
      showToast({ type: 'error', title: '加载测评记录失败', message: normalizeErrorMessage(err) })
    } finally {
      setRunsLoading(false)
    }
  }, [selectedTaskId, showToast])

  const loadResults = useCallback(async () => {
    setResultsLoading(true)
    try {
      const data = await listEvaluationResults({
        page: resultsPage,
        pageSize: resultsPageSize,
        runId: selectedRunId || undefined,
      })
      setResults(data.items)
      setResultsTotal(data.total)
    } catch (err) {
      showToast({ type: 'error', title: '加载结果列表失败', message: normalizeErrorMessage(err) })
    } finally {
      setResultsLoading(false)
    }
  }, [resultsPage, resultsPageSize, selectedRunId, showToast])

  const refreshAll = useCallback(async () => {
    await Promise.all([loadRunOptions(), loadResults()])
  }, [loadResults, loadRunOptions])

  useEffect(() => {
    loadRunOptions().catch(() => {})
  }, [loadRunOptions])

  useEffect(() => {
    loadResults().catch(() => {})
  }, [loadResults])

  useEffect(() => {
    setResultsPage(1)
  }, [searchText, statusFilter, selectedRunId])

  const openResultDetail = useCallback(async (resultId: string) => {
    setResultDetailOpen(true)
    setResultDetailLoading(true)
    setResultDetail(null)
    try {
      const data = await getEvaluationResult(resultId)
      setResultDetail(data)
    } catch (err) {
      showToast({ type: 'error', title: '加载结果详情失败', message: normalizeErrorMessage(err) })
    } finally {
      setResultDetailLoading(false)
    }
  }, [showToast])

  const filteredResults = useMemo(() => {
    let list = results

    if (statusFilter) {
      list = list.filter((item) => item.status.toLowerCase() === statusFilter)
    }

    if (searchText.trim()) {
      const keyword = searchText.trim().toLowerCase()
      list = list.filter(
        (item) =>
          item.answer.toLowerCase().includes(keyword) ||
          item.question_id.toLowerCase().includes(keyword) ||
          (item.error_message ?? '').toLowerCase().includes(keyword),
      )
    }

    return list
  }, [results, searchText, statusFilter])
  const hasFilteredResults = filteredResults.length > 0
  const tableScroll = tableBodyHeight > 0
    ? hasFilteredResults
      ? { x: 1800, y: tableBodyHeight }
      : { y: tableBodyHeight }
    : hasFilteredResults
      ? { x: 1800, y: 400 }
      : { y: 400 }

  const columns = useMemo<ColumnsType<EvaluationResult>>(
    () => [
      {
        title: '问题 ID',
        dataIndex: 'question_id',
        key: 'question_id',
        width: 140,
        ellipsis: { showTitle: false },
        sorter: (a, b) => a.question_id.localeCompare(b.question_id),
        render: (value: string) => (
          <Typography.Text strong ellipsis={{ tooltip: value }}>
            {value}
          </Typography.Text>
        ),
      },
      {
        title: '回答',
        dataIndex: 'answer',
        key: 'answer',
        width: 200,
        ellipsis: { showTitle: false },
        render: (value: string) => (
          <Typography.Paragraph ellipsis={{ rows: 2, tooltip: value || '暂无回答' }} style={{ margin: 0 }}>
            {value || '暂无回答'}
          </Typography.Paragraph>
        ),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        sorter: (a, b) => a.status.localeCompare(b.status),
        render: (value: string, _: EvaluationResult) => resultStatusTag(value),
      },
      {
        title: '检索指标',
        dataIndex: 'retrieval_metrics',
        key: 'retrieval_metrics',
        width: 150,
        ellipsis: { showTitle: false },
        render: (value: Record<string, unknown> | null) => (
          <Typography.Text style={{ fontSize: 12, color: 'var(--text)' }} ellipsis={{ tooltip: formatJson(value) }}>
            {formatRetrievalMetricsSummary(value)}
          </Typography.Text>
        ),
      },
      {
        title: 'Correct',
        dataIndex: 'correctness',
        key: 'correctness',
        width: 100,
        align: 'right',
        sorter: (a, b) => (a.correctness ?? -1) - (b.correctness ?? -1),
        render: (value: number | null) => <span className={resultMetricClass(value)}>{formatMetric(value)}</span>,
      },
      {
        title: 'Faith',
        dataIndex: 'faithfulness',
        key: 'faithfulness',
        width: 100,
        align: 'right',
        sorter: (a, b) => (a.faithfulness ?? -1) - (b.faithfulness ?? -1),
        render: (value: number | null) => <span className={resultMetricClass(value)}>{formatMetric(value)}</span>,
      },
      {
        title: 'MRR',
        dataIndex: 'mrr',
        key: 'mrr',
        width: 100,
        align: 'right',
        sorter: (a, b) => (a.mrr ?? -1) - (b.mrr ?? -1),
        render: (value: number | null) => <span className={resultMetricClass(value)}>{formatMetric(value)}</span>,
      },
      {
        title: '耗时',
        dataIndex: 'latency_ms',
        key: 'latency_ms',
        width: 80,
        align: 'right',
        sorter: (a, b) => (a.latency_ms ?? -1) - (b.latency_ms ?? -1),
        render: (value: number | null) => formatLatency(value),
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 80,
        sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        render: (value: string) => <Typography.Text style={{ fontSize: 12, color: 'var(--text)' }}>{formatMonthDayTimeWithSecond(value)}</Typography.Text>,
      },
      {
        title: '操作',
        key: 'actions',
        align: 'right',
        width: 120,
        fixed: 'right',
        render: (_: unknown, record: EvaluationResult) => (
          <div style={{ display: 'inline-flex', justifyContent: 'flex-end', gap: 8, flexWrap: 'nowrap', whiteSpace: 'nowrap' }}>
            <Button size="small" onClick={() => openResultDetail(record.id)}>
              详情
            </Button>
          </div>
        ),
      },
    ],
    [openResultDetail],
  )

  const isFiltered = searchText.trim() !== '' || statusFilter !== ''

  return (
    <div className={styles.sectionPage}>
      <div className={styles.toolbar}>
        <Input
          className={styles.searchInput}
          placeholder="搜索回答、问题 ID 或错误信息…"
          allowClear
          prefix={<span style={{ fontSize: 14, opacity: 0.45 }}>⌕</span>}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <div className={styles.statusFilterGroup}>
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.key}
              type="button"
              className={[styles.statusFilterPill, statusFilter === f.key ? styles.statusFilterPillActive : ''].join(' ')}
              onClick={() => setStatusFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className={styles.toolbarSpacer} />
        <Button onClick={() => refreshAll()} loading={runsLoading || resultsLoading}>
          刷新
        </Button>
      </div>

      <div className={styles.listSection}>
        <Card
          className={styles.sectionCard}
          title={
            <Space>
              <span>结果列表</span>
              {isFiltered && (
                <span className={[styles.countBadge, styles.countBadgeActive].join(' ')}>
                  筛选 {filteredResults.length} 条
                </span>
              )}
            </Space>
          }
        >
          {selectedRun?.error_message ? (
            <Alert
              type="error"
              showIcon
              message="当前测评记录存在异常"
              description={selectedRun.error_message}
              style={{ marginBottom: 16 }}
            />
          ) : null}

          <div ref={tableWrapperRef} style={{ flex: 1, minHeight: 0 }}>
            <Table<EvaluationResult>
              className={styles.resultAntTable}
              rowKey={(r) => r.id}
              dataSource={filteredResults}
              columns={columns}
              loading={resultsLoading}
              tableLayout="fixed"
              showHeader={hasFilteredResults}
              scroll={tableScroll}
              pagination={false}
              locale={{
                emptyText: (
                  <div className={styles.emptyState}>
                    <div className={styles.emptyStateIcon}>{isFiltered ? '🔍' : '📊'}</div>
                    <h3 className={styles.emptyStateHeading}>{isFiltered ? '没有匹配的结果' : '暂无测评结果'}</h3>
                    <p className={styles.emptyStateText}>
                      {isFiltered ? '尝试调整搜索关键词或切换筛选条件' : '当前条件下还没有可展示的测评结果，稍后可刷新重试'}
                    </p>
                  </div>
                ),
              }}
            />
          </div>
        </Card>

        <div className={styles.paginationBar}>
          <Typography.Text type="secondary">{`共 ${resultsTotal} 条`}</Typography.Text>
          <Pagination
            size="small"
            current={resultsPage}
            pageSize={resultsPageSize}
            total={resultsTotal}
            showSizeChanger
            pageSizeOptions={pageSizeOptions}
            onChange={(page, pageSize) => {
              if (pageSize !== resultsPageSize) {
                setResultsPage(1)
                setResultsPageSize(pageSize)
                return
              }
              setResultsPage(page)
            }}
          />
        </div>
      </div>

      <Modal
        title="测评结果详情"
        open={resultDetailOpen}
        footer={null}
        onCancel={() => setResultDetailOpen(false)}
        width={820}
        styles={{ body: { maxHeight: 'calc(100vh - 200px)', overflow: 'auto' } }}
        classNames={{ body: styles.modalBody }}
      >
        {resultDetailLoading ? (
          <Skeleton active paragraph={{ rows: 10 }} />
        ) : !resultDetail ? (
          <Empty description="未获取到结果详情" />
        ) : (
          <div className={styles.detailStack}>
            {resultDetail.result.error_message ? (
              <Alert type="error" showIcon message="当前结果存在异常" description={resultDetail.result.error_message} />
            ) : null}

            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>基本信息</h4>
              <div className={styles.detailMetaRow}>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>结果 ID</span>
                  <span className={styles.detailMetaVal}>{resultDetail.result.id}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>运行 ID</span>
                  <span className={styles.detailMetaVal}>{resultDetail.result.run_id}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>状态</span>
                  <span className={styles.detailMetaVal}>{resultStatusTag(resultDetail.result.status)}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>任务名称</span>
                  <span className={styles.detailMetaVal}>{resultDetail.task_name || '—'}</span>
                </div>
                {/* <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>问题 ID</span>
                  <span className={styles.detailMetaVal}>{resultDetail.result.question_id}</span>
                </div> */}
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>创建时间</span>
                  <span className={styles.detailMetaVal}>{formatMonthDayTimeWithSecond(resultDetail.result.created_at)}</span>
                </div>
              </div>
            </div>

            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>评估指标</h4>
              <div className={styles.detailMetricGrid}>
                {([
                  { key: 'Latency', value: formatLatency(resultDetail.result.latency_ms) },
                  { key: 'MRR', value: formatMetric(resultDetail.result.mrr) },
                  { key: 'Correctness', value: formatMetric(resultDetail.result.correctness) },
                  { key: 'Faithfulness', value: formatMetric(resultDetail.result.faithfulness) },
                ] as const).map((m) => {
                  const rawValue =
                    m.key === 'Latency'
                      ? resultDetail.result.latency_ms
                      : m.key === 'MRR'
                        ? resultDetail.result.mrr
                        : m.key === 'Correctness'
                          ? resultDetail.result.correctness
                          : resultDetail.result.faithfulness
                  const tone = m.key === 'Latency' ? undefined : metricTone(rawValue as number | null | undefined)
                  const blockClass =
                    tone === 'green'
                      ? styles.metricChipGreen
                      : tone === 'gold'
                        ? styles.metricChipGold
                        : tone === 'red'
                          ? styles.metricChipRed
                          : ''
                  return (
                    <div key={m.key} className={[styles.detailMetricBlock, blockClass].join(' ')}>
                      <span className={styles.detailMetricBlockLabel}>{formatResultMetricLabel(m.key)}</span>
                      <span className={styles.detailMetricBlockValue}>{m.value}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {resultDetail.question ? (
              <div className={styles.detailSection}>
                <h4 className={styles.detailSectionLabel}>关联问题</h4>
                <div className={styles.detailMetaRow}>
                  <div className={styles.detailMetaItem}>
                    <span className={styles.detailMetaKey}>分组</span>
                    <span className={styles.detailMetaVal}>{resultDetail.question.group?.name || '—'}</span>
                  </div>
                  <div className={styles.detailMetaItem}>
                    <span className={styles.detailMetaKey}>来源</span>
                    <span className={styles.detailMetaVal}>{resultDetail.question.source || '—'}</span>
                  </div>
                  <div className={styles.detailMetaItem}>
                    <span className={styles.detailMetaKey}>问题内容</span>
                    <span className={styles.detailMetaVal}>{resultDetail.question.question || '—'}</span>
                  </div>
                  <div className={styles.detailMetaItem}>
                    <span className={styles.detailMetaKey}>期望答案</span>
                    <span className={styles.detailMetaVal}>{resultDetail.question.expected_answer || '—'}</span>
                  </div>
                </div>
              </div>
            ) : null}

            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>回答内容</h4>
              <Typography.Paragraph className={styles.preWrap}>{resultDetail.result.answer || '—'}</Typography.Paragraph>
            </div>

            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>检索指标</h4>
              {resultDetail.result.retrieval_metrics && Object.keys(resultDetail.result.retrieval_metrics).length > 0 ? (
                <div className={styles.detailMetricGrid}>
                  {Object.entries(resultDetail.result.retrieval_metrics).map(([key, value]) => {
                    const numericValue = typeof value === 'number' ? value : typeof value === 'string' ? Number(value) : null
                    const tone = numericValue != null && Number.isFinite(numericValue) ? metricTone(numericValue) : undefined
                    const blockClass =
                      tone === 'green'
                        ? styles.metricChipGreen
                        : tone === 'gold'
                          ? styles.metricChipGold
                          : tone === 'red'
                            ? styles.metricChipRed
                            : ''
                    return (
                      <div key={key} className={[styles.detailMetricBlock, blockClass].join(' ')}>
                        <span className={styles.detailMetricBlockLabel}>{formatRetrievalMetricLabel(key)}</span>
                        <span className={styles.detailMetricBlockValue}>
                          {numericValue != null && Number.isFinite(numericValue) ? formatMetric(numericValue) : String(value ?? '—')}
                        </span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <pre className={styles.jsonBlock}>{formatJson(resultDetail.result.retrieval_metrics)}</pre>
              )}
            </div>

            {(getTraceJudge(resultDetail.result.trace_data, 'correctness') || getTraceJudge(resultDetail.result.trace_data, 'faithfulness')) && (
              <div className={styles.detailSection}>
                <h4 className={styles.detailSectionLabel}>评估说明</h4>
                <div className={styles.detailMetaRow}>
                  {(['correctness', 'faithfulness'] as const).map((key) => {
                    const judge = getTraceJudge(resultDetail.result.trace_data, key)
                    if (!judge) return null
                    return (
                      <div key={key} className={styles.detailMetaItem}>
                        <span className={styles.detailMetaKey}>{key === 'correctness' ? 'Correctness' : 'Faithfulness'}</span>
                        <span className={styles.detailMetaVal}>
                          {judge.score != null ? `得分 ${formatMetric(judge.score)} · ` : ''}
                          {judge.reason || '—'}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
