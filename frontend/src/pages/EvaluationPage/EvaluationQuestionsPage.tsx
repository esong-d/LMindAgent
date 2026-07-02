import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Empty, Input, Modal, Pagination, Popconfirm, Select, Skeleton, Space, Tag, Typography } from 'antd'
import { useToast } from '../../components/Toast/ToastProvider'
import {
  createEvaluationQuestion,
  deleteEvaluationQuestion,
  getEvaluationQuestion,
  listAllEvaluationGroups,
  listEvaluationQuestions,
  updateEvaluationQuestion,
} from '../../features/evaluation/api'
import type {
  CreateEvaluationQuestionBody,
  EvaluationGroupOption,
  EvaluationQuestion,
  EvaluationQuestionDetail,
  UpdateEvaluationQuestionBody,
} from '../../features/evaluation/types'
import { CreateQuestionModal, EditQuestionModal, type QuestionFormValues } from './QuestionFormModals'
import {
  formatMonthDayTimeWithSecond,
  normalizeErrorMessage,
  pageSizeOptions,
  questionPreview,
  questionSourceOptions,
  splitChunkIds,
} from './evaluationShared'
import styles from './EvaluationPage.module.css'

export function EvaluationQuestionsPage() {
  const { showToast } = useToast()
  const [questions, setQuestions] = useState<EvaluationQuestion[]>([])
  const [questionsTotal, setQuestionsTotal] = useState(0)
  const [questionsPage, setQuestionsPage] = useState(1)
  const [questionsPageSize, setQuestionsPageSize] = useState(10)
  const [questionsLoading, setQuestionsLoading] = useState(false)
  const [groupOptions, setGroupOptions] = useState<EvaluationGroupOption[]>([])
  const [groupOptionsLoading, setGroupOptionsLoading] = useState(false)

  const [createQuestionModalOpen, setCreateQuestionModalOpen] = useState(false)
  const [createQuestionSaving, setCreateQuestionSaving] = useState(false)
  const [editQuestionModalOpen, setEditQuestionModalOpen] = useState(false)
  const [editQuestionSaving, setEditQuestionSaving] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<EvaluationQuestion | null>(null)

  const [questionDetailOpen, setQuestionDetailOpen] = useState(false)
  const [questionDetailLoading, setQuestionDetailLoading] = useState(false)
  const [questionDetail, setQuestionDetail] = useState<EvaluationQuestionDetail | null>(null)
  const [deletingQuestionId, setDeletingQuestionId] = useState<string | null>(null)

  const [searchText, setSearchText] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [groupFilter, setGroupFilter] = useState('')
  const [animReady, setAnimReady] = useState(false)
  const animLock = useRef(false)

  const filteredQuestions = useMemo(() => {
    let list = questions
    if (sourceFilter) {
      list = list.filter((item) => item.source === sourceFilter)
    }
    if (searchText.trim()) {
      const kw = searchText.trim().toLowerCase()
      list = list.filter(
        (item) =>
          (item.group?.name ?? '').toLowerCase().includes(kw) ||
          item.question.toLowerCase().includes(kw) ||
          (item.expected_answer ?? '').toLowerCase().includes(kw),
      )
    }
    return list
  }, [questions, sourceFilter, searchText])

  const loadQuestions = useCallback(async () => {
    setQuestionsLoading(true)
    try {
      const data = await listEvaluationQuestions({ page: questionsPage, pageSize: questionsPageSize, groupId: groupFilter || undefined })
      setQuestions(data.items)
      setQuestionsTotal(data.total)
    } catch (err) {
      showToast({ type: 'error', title: '加载问题列表失败', message: normalizeErrorMessage(err) })
    } finally {
      setQuestionsLoading(false)
    }
  }, [groupFilter, questionsPage, questionsPageSize, showToast])

  const loadGroupOptions = useCallback(async () => {
    setGroupOptionsLoading(true)
    try {
      const data = await listAllEvaluationGroups()
      setGroupOptions(data)
    } catch (err) {
      showToast({ type: 'error', title: '加载分组选项失败', message: normalizeErrorMessage(err) })
    } finally {
      setGroupOptionsLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    loadQuestions().catch(() => {})
  }, [loadQuestions])

  useEffect(() => {
    loadGroupOptions().catch(() => {})
  }, [loadGroupOptions])

  useEffect(() => {
    if (!questionsLoading && filteredQuestions.length > 0 && !animLock.current) {
      animLock.current = true
      const timer = setTimeout(() => setAnimReady(true), 60)
      return () => clearTimeout(timer)
    }
    if (questionsLoading) {
      setAnimReady(false)
    }
  }, [questionsLoading, filteredQuestions.length])

  const openCreateQuestion = useCallback(() => {
    setCreateQuestionModalOpen(true)
  }, [])

  const openEditQuestion = useCallback(
    (question: EvaluationQuestion) => {
      setEditingQuestion(question)
      setEditQuestionModalOpen(true)
    },
    [],
  )

  const submitCreateQuestion = useCallback(async (values: QuestionFormValues) => {
    if (createQuestionSaving) return

    setCreateQuestionSaving(true)
    try {
      const source = values.source?.trim() || 'ai'
      const body: CreateEvaluationQuestionBody =
        source === 'ai'
          ? {
              group_id: values.group_id,
              source,
              knowledge_base_id: values.knowledge_base_id,
              document_id: values.document_id,
              model_config_id: values.model_config_id,
              question_count: values.question_count,
            }
          : {
              group_id: values.group_id,
              question: (values.question ?? '').trim(),
              expected_answer: values.expected_answer?.trim() || null,
              source,
              chunk_ids: splitChunkIds(values.chunk_ids_text),
            }
      await createEvaluationQuestion(body)
      showToast({ type: 'success', title: '已创建', message: '测评问题已创建' })

      setCreateQuestionModalOpen(false)
      await loadQuestions()
    } catch (err) {
      showToast({ type: 'error', title: '创建问题失败', message: normalizeErrorMessage(err) })
    } finally {
      setCreateQuestionSaving(false)
    }
  }, [createQuestionSaving, loadQuestions, showToast])

  const submitEditQuestion = useCallback(async (values: QuestionFormValues) => {
    if (editQuestionSaving || !editingQuestion) return

    setEditQuestionSaving(true)
    try {
      const questionText = (values.question ?? '').trim()
      const expectedAnswer = values.expected_answer?.trim() || null
      const source = values.source?.trim() || 'human'

      const body: UpdateEvaluationQuestionBody = {
        group_id: values.group_id,
        question: questionText,
        expected_answer: expectedAnswer,
        source,
      }
      await updateEvaluationQuestion(editingQuestion.id, body)
      showToast({ type: 'success', title: '已更新', message: '测评问题已更新' })

      setEditQuestionModalOpen(false)
      await loadQuestions()
    } catch (err) {
      showToast({ type: 'error', title: '更新问题失败', message: normalizeErrorMessage(err) })
    } finally {
      setEditQuestionSaving(false)
    }
  }, [editQuestionSaving, editingQuestion, loadQuestions, showToast])

  const handleDeleteQuestion = useCallback(
    async (questionId: string) => {
      if (deletingQuestionId) return
      setDeletingQuestionId(questionId)
      try {
        await deleteEvaluationQuestion(questionId)
        showToast({ type: 'success', title: '已删除', message: '测评问题已删除' })
        const nextPage = questions.length === 1 && questionsPage > 1 ? questionsPage - 1 : questionsPage
        if (nextPage !== questionsPage) setQuestionsPage(nextPage)
        else await loadQuestions()
      } catch (err) {
        showToast({ type: 'error', title: '删除问题失败', message: normalizeErrorMessage(err) })
      } finally {
        setDeletingQuestionId(null)
      }
    },
    [deletingQuestionId, loadQuestions, questions.length, questionsPage, showToast],
  )

  const openQuestionDetail = useCallback(
    async (questionId: string) => {
      setQuestionDetailOpen(true)
      setQuestionDetailLoading(true)
      setQuestionDetail(null)
      try {
        const data = await getEvaluationQuestion(questionId)
        setQuestionDetail(data)
      } catch (err) {
        showToast({ type: 'error', title: '加载问题详情失败', message: normalizeErrorMessage(err) })
      } finally {
        setQuestionDetailLoading(false)
      }
    },
    [showToast],
  )

  return (
    <div className={styles.sectionPage}>
      <div className={styles.toolbar}>
        <Input
          className={styles.searchInput}
          placeholder="搜索问题内容、期望答案或分组…"
          allowClear
          prefix={<span style={{ fontSize: 14, opacity: 0.45 }}>⌕</span>}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <Select
          className={styles.filterSelect}
          placeholder="按分组筛选"
          allowClear
          value={groupFilter || undefined}
          onChange={(value) => {
            setGroupFilter(value ?? '')
            setQuestionsPage(1)
          }}
          disabled={groupOptionsLoading}
          options={groupOptions.map((item) => ({ label: item.name, value: item.id }))}
        />
        <div className={styles.statusFilterGroup}>
          <button
            type="button"
            className={[styles.statusFilterPill, sourceFilter === '' ? styles.statusFilterPillActive : ''].join(' ')}
            onClick={() => setSourceFilter('')}
          >
            全部
          </button>
          {questionSourceOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={[styles.statusFilterPill, sourceFilter === opt.value ? styles.statusFilterPillActive : ''].join(' ')}
              onClick={() => setSourceFilter(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className={styles.toolbarSpacer} />
        <Space wrap>
          <Button onClick={() => loadQuestions()} loading={questionsLoading}>
            刷新
          </Button>
          <Button type="primary" onClick={() => openCreateQuestion()}>
            新建问题
          </Button>
        </Space>
      </div>

      <Card className={styles.sectionCard} title={`问题列表${filteredQuestions.length !== questions.length ? ` · 筛选 ${filteredQuestions.length} 条` : ''}`}>
        <div className={styles.sectionBody}>
          <div className={styles.listWrap}>
            {questionsLoading ? (
              <Skeleton active paragraph={{ rows: 8 }} />
            ) : filteredQuestions.length ? (
              filteredQuestions.map((item, idx) => (
                <div
                  key={item.id}
                  className={[styles.itemCard, animReady ? styles.cardAnimEnter : ''].join(' ')}
                  style={animReady ? { animationDelay: `${idx * 55}ms` } : undefined}
                >
                  <div className={styles.itemHead}>
                    <Space size={8} wrap>
                      <Tag color="purple">{item.group?.name || '未分组'}</Tag>
                      <Tag color="blue">{item.source || 'human'}</Tag>
                    </Space>
                    <Typography.Text type="secondary">{formatMonthDayTimeWithSecond(item.created_at)}</Typography.Text>
                  </div>
                  <Typography.Paragraph className={styles.itemTitle} ellipsis={{ rows: 2, tooltip: item.question }}>
                    {questionPreview(item.question)}
                  </Typography.Paragraph>
                  <Typography.Paragraph className={styles.itemMeta} ellipsis={{ rows: 2, tooltip: item.expected_answer ?? '' }}>
                    期望答案：{questionPreview(item.expected_answer ?? '', '未设置')}
                  </Typography.Paragraph>
                  <div className={styles.itemActions}>
                    <Button size="small" onClick={() => openQuestionDetail(item.id)}>
                      详情
                    </Button>
                    <Button size="small" onClick={() => openEditQuestion(item)}>
                      编辑
                    </Button>
                    <Popconfirm
                      title="确定删除这个问题吗？"
                      description="删除后不可恢复"
                      okText="删除"
                      cancelText="取消"
                      okButtonProps={{ danger: true }}
                      onConfirm={() => handleDeleteQuestion(item.id)}
                      disabled={deletingQuestionId === item.id}
                    >
                      <Button danger size="small" loading={deletingQuestionId === item.id} disabled={deletingQuestionId === item.id}>
                        删除
                      </Button>
                    </Popconfirm>
                  </div>
                </div>
              ))
            ) : (
              <div className={styles.emptyState}>
                <div className={styles.emptyStateIcon}>{searchText || sourceFilter ? '🔍' : '📝'}</div>
                <h3 className={styles.emptyStateHeading}>{searchText || sourceFilter ? '没有匹配的问题' : '暂无测评问题'}</h3>
                <p className={styles.emptyStateText}>
                  {searchText || sourceFilter
                    ? '尝试调整搜索关键词或切换筛选条件'
                    : '点击「新建问题」添加第一个测评问题，支持手动输入或 AI 批量生成'}
                </p>
              </div>
            )}
          </div>
          <div className={styles.paginationBar}>
            <Typography.Text type="secondary">{`共 ${questionsTotal} 条`}</Typography.Text>
            <Pagination
              size="small"
              current={questionsPage}
              pageSize={questionsPageSize}
              total={questionsTotal}
              showSizeChanger
              pageSizeOptions={pageSizeOptions}
              onChange={(page, pageSize) => {
                if (pageSize !== questionsPageSize) {
                  setQuestionsPage(1)
                  setQuestionsPageSize(pageSize)
                  return
                }
                setQuestionsPage(page)
              }}
            />
          </div>
        </div>
      </Card>

      <CreateQuestionModal
        open={createQuestionModalOpen}
        confirmLoading={createQuestionSaving}
        onCancel={() => {
          if (!createQuestionSaving) setCreateQuestionModalOpen(false)
        }}
        onSubmit={submitCreateQuestion}
      />

      <EditQuestionModal
        open={editQuestionModalOpen}
        confirmLoading={editQuestionSaving}
        question={editingQuestion}
        onCancel={() => {
          if (!editQuestionSaving) setEditQuestionModalOpen(false)
        }}
        onSubmit={submitEditQuestion}
        onAfterClose={() => setEditingQuestion(null)}
      />

      <Modal
        title="测评问题详情"
        open={questionDetailOpen}
        footer={null}
        onCancel={() => setQuestionDetailOpen(false)}
        centered
        width="60%"
        styles={{
          body: {
            maxHeight: 'calc(100vh - 180px)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        {questionDetailLoading ? (
          <Skeleton active paragraph={{ rows: 8 }} />
        ) : !questionDetail ? (
          <Empty description="未获取到问题详情" />
        ) : (
          <div className={[styles.detailStack, styles.questionDetailLayout].join(' ')}>
            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>基本信息</h4>
              <div className={styles.detailMetaRow}>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>所属分组</span>
                  <span className={styles.detailMetaVal}>{questionDetail.group?.name || '—'}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>来源</span>
                  <span className={styles.detailMetaVal}>{questionDetail.source}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>创建时间</span>
                  <span className={styles.detailMetaVal}>{formatMonthDayTimeWithSecond(questionDetail.created_at)}</span>
                </div>
              </div>
            </div>
            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>问题内容</h4>
              <Typography.Paragraph copyable={true} className={styles.preWrap}>{questionDetail.question || '—'}</Typography.Paragraph>
            </div>
            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>期望答案</h4>
              <Typography.Paragraph copyable={true} className={styles.preWrap}>{questionDetail.expected_answer || '—'}</Typography.Paragraph>
            </div>
            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>{`关联 Chunk（${questionDetail.chunks.length}）`}</h4>
              {questionDetail.chunks.length ? (
                <div className={styles.chunkList}>
                  {questionDetail.chunks.map((chunk) => (
                    <div key={chunk.id} className={styles.chunkItem}>
                      <Typography.Paragraph className={styles.chunkContent}>{chunk.content || '—'}</Typography.Paragraph>
                    </div>
                  ))}
                </div>
              ) : (
                <Empty description="暂无关联 Chunk" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
