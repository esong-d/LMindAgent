import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Empty, Form, Input, Modal, Pagination, Popconfirm, Select, Skeleton, Space, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../../components/Toast/ToastProvider'
import {
  createEvaluationTask,
  deleteEvaluationTask,
  executeEvaluationTask,
  getEvaluationTask,
  listAllEvaluationGroups,
  listEvaluationQuestionsByGroup,
  listEvaluationTasks,
} from '../../features/evaluation/api'
import type { CreateEvaluationTaskBody, EvaluationGroupOption, EvaluationQuestionOption, EvaluationTask } from '../../features/evaluation/types'
import { listKnowledgeBases } from '../../features/knowledge-bases/api'
import type { KnowledgeBase } from '../../features/knowledge-bases/types'
import { listAllModelConfigs } from '../../features/settings/api'
import type { ModelConfigOut } from '../../features/settings/types'
import { formatJson, formatMonthDayTimeWithSecond, normalizeErrorMessage, pageSizeOptions } from './evaluationShared'
import styles from './EvaluationPage.module.css'

type TaskFormValues = {
  name: string
  group_id: string
  knowledge_base_id: string
  question_ids: string[]
  model_config_id: string
}

const TABLE_HEADER_OFFSET = 56

function formatTaskType(type: string) {
  if (type === 'generate_question') return '生成问题'
  if (type === 'run_evaluation') return '运行测评'
  return type || '—'
}

function taskTypeColorClass(type: string): string {
  if (type === 'generate_question') return styles.taskTypeGenerate
  if (type === 'run_evaluation') return styles.taskTypeRun
  return ''
}

export function EvaluationTasksPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const tableWrapperRef = useRef<HTMLDivElement>(null)
  const [tableBodyHeight, setTableBodyHeight] = useState(0)

  const [tasks, setTasks] = useState<EvaluationTask[]>([])
  const [tasksTotal, setTasksTotal] = useState(0)
  const [tasksPage, setTasksPage] = useState(1)
  const [tasksPageSize, setTasksPageSize] = useState(10)
  const [tasksLoading, setTasksLoading] = useState(false)

  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [groupOptions, setGroupOptions] = useState<EvaluationGroupOption[]>([])
  const [groupOptionsLoading, setGroupOptionsLoading] = useState(false)
  const [knowledgeBasesLoading, setKnowledgeBasesLoading] = useState(false)
  const [modelConfigs, setModelConfigs] = useState<ModelConfigOut[]>([])
  const [modelConfigsLoading, setModelConfigsLoading] = useState(false)
  const [questionOptions, setQuestionOptions] = useState<EvaluationQuestionOption[]>([])
  const [questionOptionsLoading, setQuestionOptionsLoading] = useState(false)

  const [taskModalOpen, setTaskModalOpen] = useState(false)
  const [taskModalSaving, setTaskModalSaving] = useState(false)
  const [taskForm] = Form.useForm<TaskFormValues>()

  const [taskDetailOpen, setTaskDetailOpen] = useState(false)
  const [taskDetailLoading, setTaskDetailLoading] = useState(false)
  const [taskDetail, setTaskDetail] = useState<EvaluationTask | null>(null)

  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null)
  const [executingTaskId, setExecutingTaskId] = useState<string | null>(null)

  const [searchText, setSearchText] = useState('')
  const [groupFilter, setGroupFilter] = useState('')

  const selectedGroupId = Form.useWatch('group_id', taskForm)

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

  const modelConfigOptions = useMemo(
    () =>
      modelConfigs.map((item) => ({
        label: item.provider ? `${item.name || item.id} (${item.provider})` : item.name || item.id,
        value: item.id,
      })),
    [modelConfigs],
  )

  const filteredTasks = useMemo(() => {
    if (!searchText.trim()) return tasks
    const keyword = searchText.trim().toLowerCase()
    return tasks.filter(
      (item) =>
        item.id.toLowerCase().includes(keyword) ||
        item.name.toLowerCase().includes(keyword) ||
        (item.group?.name ?? '').toLowerCase().includes(keyword) ||
        formatTaskType(item.type).toLowerCase().includes(keyword) ||
        (item.knowledge_base?.id ?? '').toLowerCase().includes(keyword),
    )
  }, [searchText, tasks])
  const hasFilteredTasks = filteredTasks.length > 0
  const tableScroll = tableBodyHeight > 0
    ? hasFilteredTasks
      ? { x: 1540, y: tableBodyHeight }
      : { y: tableBodyHeight }
    : hasFilteredTasks
      ? { x: 1540, y: 400 }
      : { y: 400 }

  const loadTasks = useCallback(async () => {
    setTasksLoading(true)
    try {
      const data = await listEvaluationTasks({
        page: tasksPage,
        pageSize: tasksPageSize,
        groupId: groupFilter || undefined,
      })
      setTasks(data.items)
      setTasksTotal(data.total)
    } catch (err) {
      showToast({ type: 'error', title: '加载任务列表失败', message: normalizeErrorMessage(err) })
    } finally {
      setTasksLoading(false)
    }
  }, [groupFilter, showToast, tasksPage, tasksPageSize])

  const loadKnowledgeBases = useCallback(async () => {
    setKnowledgeBasesLoading(true)
    try {
      const data = await listKnowledgeBases()
      setKnowledgeBases(data)
    } catch (err) {
      showToast({ type: 'error', title: '加载知识库失败', message: normalizeErrorMessage(err) })
    } finally {
      setKnowledgeBasesLoading(false)
    }
  }, [showToast])

  const loadModelConfigs = useCallback(async () => {
    setModelConfigsLoading(true)
    try {
      const data = await listAllModelConfigs()
      setModelConfigs(data)
    } catch (err) {
      showToast({ type: 'error', title: '加载模型配置失败', message: normalizeErrorMessage(err) })
    } finally {
      setModelConfigsLoading(false)
    }
  }, [showToast])

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

  const loadQuestionOptions = useCallback(async (groupId: string) => {
    setQuestionOptionsLoading(true)
    try {
      const data = await listEvaluationQuestionsByGroup(groupId)
      setQuestionOptions(data)
    } catch (err) {
      showToast({ type: 'error', title: '加载问题选项失败', message: normalizeErrorMessage(err) })
    } finally {
      setQuestionOptionsLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    loadTasks().catch(() => {})
  }, [loadTasks])

  useEffect(() => {
    loadKnowledgeBases().catch(() => {})
  }, [loadKnowledgeBases])

  useEffect(() => {
    loadModelConfigs().catch(() => {})
  }, [loadModelConfigs])

  useEffect(() => {
    loadGroupOptions().catch(() => {})
  }, [loadGroupOptions])

  useEffect(() => {
    if (!taskModalOpen) return
    taskForm.setFieldValue('question_ids', [])
    if (!selectedGroupId) {
      setQuestionOptions([])
      return
    }
    loadQuestionOptions(selectedGroupId).catch(() => {})
  }, [loadQuestionOptions, selectedGroupId, taskForm, taskModalOpen])

  const openCreateTask = useCallback(async () => {
    if (!groupOptions.length) await loadGroupOptions()
    if (!knowledgeBases.length) await loadKnowledgeBases()
    if (!modelConfigs.length) await loadModelConfigs()

    taskForm.setFieldsValue({
      name: '',
      group_id: '',
      knowledge_base_id: '',
      question_ids: [],
      model_config_id: '',
    })
    setQuestionOptions([])
    setTaskModalOpen(true)
  }, [
    groupOptions.length,
    knowledgeBases.length,
    loadGroupOptions,
    loadKnowledgeBases,
    loadModelConfigs,
    modelConfigs.length,
    taskForm,
  ])

  const submitTask = useCallback(async () => {
    if (taskModalSaving) return

    let values: TaskFormValues
    try {
      values = await taskForm.validateFields()
    } catch {
      return
    }

    const body: CreateEvaluationTaskBody = {
      name: values.name.trim(),
      group_id: values.group_id,
      knowledge_base_id: values.knowledge_base_id,
      question_ids: values.question_ids.length ? values.question_ids : null,
      model_config_id: values.model_config_id,
    }

    setTaskModalSaving(true)
    try {
      await createEvaluationTask(body)
      showToast({ type: 'success', title: '已创建', message: '测评任务已创建' })
      setTaskModalOpen(false)
      await loadTasks()
    } catch (err) {
      showToast({ type: 'error', title: '创建任务失败', message: normalizeErrorMessage(err) })
    } finally {
      setTaskModalSaving(false)
    }
  }, [loadTasks, showToast, taskForm, taskModalSaving])

  const handleDeleteTask = useCallback(async (taskId: string) => {
    if (deletingTaskId) return
    setDeletingTaskId(taskId)
    try {
      await deleteEvaluationTask(taskId)
      showToast({ type: 'success', title: '已删除', message: '测评任务已删除' })
      const nextPage = tasks.length === 1 && tasksPage > 1 ? tasksPage - 1 : tasksPage
      if (nextPage !== tasksPage) setTasksPage(nextPage)
      else await loadTasks()
    } catch (err) {
      showToast({ type: 'error', title: '删除任务失败', message: normalizeErrorMessage(err) })
    } finally {
      setDeletingTaskId(null)
    }
  }, [deletingTaskId, loadTasks, showToast, tasks.length, tasksPage])

  const handleExecuteTask = useCallback(async (taskId: string) => {
    if (executingTaskId) return
    setExecutingTaskId(taskId)
    try {
      const result = await executeEvaluationTask(taskId)
      showToast({
        type: 'success',
        title: '执行已启动',
        message: `已创建测评记录 ${result.run_id}`,
      })
      navigate(`/evaluation/runs?taskId=${encodeURIComponent(taskId)}`)
    } catch (err) {
      showToast({ type: 'error', title: '执行任务失败', message: normalizeErrorMessage(err) })
    } finally {
      setExecutingTaskId(null)
    }
  }, [executingTaskId, navigate, showToast])

  const openTaskDetail = useCallback(async (taskId: string) => {
    setTaskDetailOpen(true)
    setTaskDetailLoading(true)
    setTaskDetail(null)
    try {
      const data = await getEvaluationTask(taskId)
      setTaskDetail(data)
    } catch (err) {
      showToast({ type: 'error', title: '加载任务详情失败', message: normalizeErrorMessage(err) })
    } finally {
      setTaskDetailLoading(false)
    }
  }, [showToast])

  const columns = useMemo<ColumnsType<EvaluationTask>>(
    () => [
      {
        title: '任务名称',
        dataIndex: 'name',
        key: 'name',
        width: 220,
        ellipsis: { showTitle: false },
        sorter: (a, b) => a.name.localeCompare(b.name),
        render: (value: EvaluationTask['name']) => (
          <Typography.Text strong ellipsis={{ tooltip: value }}>
            {value}
          </Typography.Text>
        ),
      },
      {
        title: '分组',
        dataIndex: 'group',
        key: 'group',
        width: 160,
        ellipsis: { showTitle: false },
        sorter: (a, b) => (a.group?.name ?? '').localeCompare(b.group?.name ?? ''),
        render: (value: EvaluationTask['group']) => value?.name || '—',
      },
      {
        title: '类型',
        dataIndex: 'type',
        key: 'type',
        width: 120,
        sorter: (a, b) => formatTaskType(a.type).localeCompare(formatTaskType(b.type)),
        render: (value: EvaluationTask['type']) => (
          <Tag color={value === 'generate_question' ? 'processing' : value === 'run_evaluation' ? 'cyan' : 'default'}>
            {formatTaskType(value)}
          </Tag>
        ),
      },
      {
        title: '知识库',
        dataIndex: 'knowledge_base',
        key: 'knowledge_base',
        width: 220,
        ellipsis: { showTitle: false },
        sorter: (a, b) => (a.knowledge_base?.name ?? '').localeCompare(b.knowledge_base?.name ?? ''),
        render: (value: EvaluationTask['knowledge_base']) => (
          <Typography.Text ellipsis={{ tooltip: value?.name }}>{value?.name || '—'}</Typography.Text>
        ),
      },
      {
        title: '题量',
        dataIndex: 'total_questions',
        key: 'total_questions',
        width: 100,
        align: 'right',
        sorter: (a, b) => a.total_questions - b.total_questions,
      },
      {
        title: '参与问题',
        dataIndex: 'question_ids',
        key: 'question_ids',
        width: 140,
        align: 'right',
        sorter: (a, b) => (a.question_ids?.length ?? 0) - (b.question_ids?.length ?? 0),
        render: (value: EvaluationTask['question_ids']) => (value?.length ? `${value.length} 个指定问题` : '全部问题'),
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 180,
        sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        render: (value: EvaluationTask['created_at']) => formatMonthDayTimeWithSecond(value),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 180,
        sorter: (a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
        render: (value: EvaluationTask['updated_at']) => formatMonthDayTimeWithSecond(value),
      },
      {
        title: '操作',
        key: 'actions',
        align: 'right',
        width: 240,
        fixed: 'right',
        render: (_, row) => (
          <div style={{ display: 'inline-flex', justifyContent: 'flex-end', gap: 8, flexWrap: 'nowrap', whiteSpace: 'nowrap' }}>
            <Button size="small" onClick={() => openTaskDetail(row.id)}>
              详情
            </Button>
            <Button size="small" onClick={() => navigate(`/evaluation/runs?taskId=${encodeURIComponent(row.id)}`)}>
              记录
            </Button>
            <Button size="small" type="primary" loading={executingTaskId === row.id} onClick={() => handleExecuteTask(row.id)}>
              执行
            </Button>
            <Popconfirm
              title="确定删除这个任务吗？"
              description={`将删除「${row.name}」`}
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              onConfirm={() => handleDeleteTask(row.id)}
              disabled={deletingTaskId === row.id}
            >
              <Button danger size="small" loading={deletingTaskId === row.id} disabled={deletingTaskId === row.id}>
                删除
              </Button>
            </Popconfirm>
          </div>
        ),
      },
    ],
    [deletingTaskId, executingTaskId, handleDeleteTask, handleExecuteTask, navigate, openTaskDetail],
  )

  return (
    <div className={styles.sectionPage}>
      <div className={styles.toolbar}>
        <Input
          className={styles.searchInput}
          placeholder="搜索任务 ID、名称、分组、类型或知识库 ID…"
          allowClear
          prefix={<span style={{ fontSize: 14, opacity: 0.45 }}>⌕</span>}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <Select
          className={styles.filterSelect}
          placeholder="按分组筛选"
          allowClear
          loading={groupOptionsLoading}
          value={groupFilter || undefined}
          onChange={(value) => {
            setGroupFilter(value ?? '')
            setTasksPage(1)
          }}
          options={groupOptions.map((item) => ({ label: item.name, value: item.id }))}
        />
        <div className={styles.toolbarSpacer} />
        <Space wrap>
          <Button onClick={() => loadTasks()} loading={tasksLoading}>
            刷新
          </Button>
          <Button type="primary" onClick={() => openCreateTask()}>
            新建任务
          </Button>
        </Space>
      </div>

      <div className={styles.listSection}>
        <Card className={styles.sectionCard} title="任务列表">
          <div ref={tableWrapperRef} style={{ flex: 1, minHeight: 0 }}>
            <Table<EvaluationTask>
              className={styles.resultAntTable}
              rowKey={(r) => r.id}
              dataSource={filteredTasks}
              columns={columns}
              loading={tasksLoading}
              pagination={false}
              tableLayout="fixed"
              showHeader={hasFilteredTasks}
              scroll={tableScroll}
              locale={{
                emptyText: (
                  <div className={styles.taskTableEmpty}>
                    <div className={styles.emptyStateIcon}>{searchText ? '🔍' : '📋'}</div>
                    <h3 className={styles.emptyStateHeading}>{searchText ? '没有匹配的任务' : '暂无测评任务'}</h3>
                    <p className={styles.emptyStateText}>
                      {searchText
                        ? '尝试调整搜索关键词或筛选条件'
                        : '点击「新建任务」创建测评任务模板，再从记录页查看每次执行的运行结果'}
                    </p>
                  </div>
                ),
              }}
            />
          </div>
          <div className={styles.paginationBar}>
            <Typography.Text type="secondary">{`共 ${tasksTotal} 条`}</Typography.Text>
            <Pagination
              size="small"
              current={tasksPage}
              pageSize={tasksPageSize}
              total={tasksTotal}
              showSizeChanger
              pageSizeOptions={pageSizeOptions}
              onChange={(page, pageSize) => {
                if (pageSize !== tasksPageSize) {
                  setTasksPage(1)
                  setTasksPageSize(pageSize)
                  return
                }
                setTasksPage(page)
              }}
            />
          </div>
        </Card>
      </div>

      <Modal
        title="新建测评任务"
        open={taskModalOpen}
        onCancel={() => {
          if (!taskModalSaving) setTaskModalOpen(false)
        }}
        onOk={() => submitTask()}
        okText="创建任务"
        cancelText="取消"
        confirmLoading={taskModalSaving}
        width={760}
        afterClose={() => taskForm.resetFields()}
      >
        <Form form={taskForm} layout="vertical" preserve={false} requiredMark={false}>
          <Form.Item name="name" label="任务名称" rules={[{ required: true, message: '请填写任务名称' }]}>
            <Input placeholder="例如：知识库 A 第一轮测评" maxLength={200} />
          </Form.Item>
          <Form.Item name="knowledge_base_id" label="知识库" rules={[{ required: true, message: '请选择知识库' }]}>
            <Select
              placeholder="请选择知识库"
              loading={knowledgeBasesLoading}
              options={knowledgeBases.map((item) => ({ label: item.name, value: item.id }))}
            />
          </Form.Item>
          <Form.Item name="group_id" label="测试问题组" rules={[{ required: true, message: '请选择测试问题组' }]}>
            <Select
              placeholder="请选择测试问题组"
              loading={groupOptionsLoading}
              showSearch
              options={groupOptions.map((item) => ({ label: item.name, value: item.id }))}
            />
          </Form.Item>
          <Form.Item name="question_ids" label="参与问题">
            <Select
              mode="multiple"
              placeholder={selectedGroupId ? '可选，不选则使用该组下所有问题' : '请先选择测试问题组'}
              loading={questionOptionsLoading}
              disabled={!selectedGroupId}
              options={questionOptions.map((item) => ({
                label: item.question || item.id,
                value: item.id,
              }))}
              maxTagCount="responsive"
            />
          </Form.Item>
          <Form.Item name="model_config_id" label="模型配置" rules={[{ required: true, message: '请选择模型配置' }]}>
            <Select placeholder="请选择模型配置" loading={modelConfigsLoading} showSearch options={modelConfigOptions} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="测评任务详情" open={taskDetailOpen} footer={null} onCancel={() => setTaskDetailOpen(false)} width={720}>
        {taskDetailLoading ? (
          <Skeleton active paragraph={{ rows: 8 }} />
        ) : !taskDetail ? (
          <Empty description="未获取到任务详情" />
        ) : (
          <div className={styles.detailStack}>
            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>基本信息</h4>
              <div className={styles.detailMetaRow}>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>名称</span>
                  <span className={styles.detailMetaVal}>{taskDetail.name}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>所属分组</span>
                  <span className={styles.detailMetaVal}>{taskDetail.group?.name || '—'}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>任务类型</span>
                  <span className={`${styles.detailMetaVal} ${taskTypeColorClass(taskDetail.type)}`}>{formatTaskType(taskDetail.type)}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>知识库 ID</span>
                  <span className={styles.detailMetaVal}>{taskDetail.knowledge_base?.id || '—'}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>题量</span>
                  <span className={styles.detailMetaVal}>{taskDetail.total_questions}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>参与问题</span>
                  <span className={styles.detailMetaVal}>
                    {taskDetail.question_ids?.length ? `${taskDetail.question_ids.length} 个指定问题` : '使用该组全部问题'}
                  </span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>创建时间</span>
                  <span className={styles.detailMetaVal}>{formatMonthDayTimeWithSecond(taskDetail.created_at)}</span>
                </div>
                <div className={styles.detailMetaItem}>
                  <span className={styles.detailMetaKey}>更新时间</span>
                  <span className={styles.detailMetaVal}>{formatMonthDayTimeWithSecond(taskDetail.updated_at)}</span>
                </div>
              </div>
            </div>

            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>问题范围</h4>
              <Typography.Paragraph className={styles.preWrap} style={{ marginBottom: 0 }}>
                {taskDetail.question_ids?.length
                  ? taskDetail.question_ids.join('\n')
                  : '当前任务未指定 question_ids，执行时将使用该分组下的全部问题。'}
              </Typography.Paragraph>
            </div>

            <div className={styles.detailSection}>
              <h4 className={styles.detailSectionLabel}>任务配置</h4>
              <pre className={styles.jsonBlock}>{formatJson(taskDetail.config)}</pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
