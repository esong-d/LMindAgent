import styles from './Knowledge.module.css'
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Form, Input, Modal, Pagination, Popconfirm, Space, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useLocation, useNavigate } from 'react-router-dom'
import { useToast } from '../../components/Toast/ToastProvider'
import { ApiError } from '../../lib/apiClient'
import { createKnowledgeBase, deleteKnowledgeBase, listKnowledgeBasesPage, updateKnowledgeBase } from '../../features/knowledge-bases/api'
import type { CreateKnowledgeBaseBody, KnowledgeBaseItem } from '../../features/knowledge-bases/types'

const pageSizeOptions = [10, 20, 50, 100]

export function KnowledgePage() {
  const { showToast } = useToast()
  const location = useLocation()
  const navigate = useNavigate()
  const tableWrapRef = useRef<HTMLDivElement | null>(null)

  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(10)
  const [total, setTotal] = useState(0)
  const [items, setItems] = useState<KnowledgeBaseItem[]>([])
  const [loading, setLoading] = useState(false)
  const [tableScrollY, setTableScrollY] = useState<number | undefined>(undefined)

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<KnowledgeBaseItem | null>(null)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const [form] = Form.useForm<{ name: string; description: string; settings_json_text: string }>()

  const normalizeErrorMessage = useCallback((err: unknown) => {
    if (err instanceof ApiError) return err.message || '请求失败'
    if (err instanceof Error) return err.message || '请求失败'
    return '请求失败'
  }, [])

  const stringifySettings = useCallback((value: unknown) => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return '{}'
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return '{}'
    }
  }, [])

  const fetchPage = useCallback(
    async (nextPage: number, nextPerPage: number) => {
      setLoading(true)
      try {
        const data = await listKnowledgeBasesPage({ page: nextPage, perPage: nextPerPage })
        setItems(data.list)
        setTotal(data.total)
      } catch (err) {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '加载知识库失败', message })
      } finally {
        setLoading(false)
      }
    },
    [normalizeErrorMessage, showToast],
  )
  const openCreate = useCallback(() => {
    setEditing(null)
    setModalOpen(true)
  }, [])

  useEffect(() => {
    fetchPage(page, perPage).catch(() => {})
  }, [fetchPage, page, perPage])

  useEffect(() => {
    const action = new URLSearchParams(location.search).get('action')
    if (action !== 'create') return
    openCreate()
    navigate('/knowledge', { replace: true })
  }, [location.search, navigate, openCreate])

  const openEdit = useCallback(
    (kb: KnowledgeBaseItem) => {
      setEditing(kb)
      setModalOpen(true)
    },
    [],
  )

  useEffect(() => {
    if (!modalOpen) return

    if (editing) {
      form.setFieldsValue({
        name: editing.name ?? '',
        description: editing.description ?? '',
        settings_json_text: stringifySettings(editing.settings_json),
      })
      return
    }

    form.setFieldsValue({ name: '', description: '', settings_json_text: '{}' })
  }, [editing, form, modalOpen, stringifySettings])

  const closeModal = useCallback(() => {
    if (saving) return
    setModalOpen(false)
  }, [saving])

  const submit = useCallback(async () => {
    if (saving) return

    let values: { name: string; description: string; settings_json_text: string }
    try {
      values = await form.validateFields()
    } catch {
      return
    }

    const trimmedName = values.name.trim()
    if (!trimmedName) {
      showToast({ type: 'warn', title: '参数不完整', message: '请填写知识库名称' })
      return
    }

    let settingsJson: Record<string, unknown> = {}
    try {
      const raw = values.settings_json_text?.trim() ? JSON.parse(values.settings_json_text) : {}
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
        throw new Error('settings_json 必须是 JSON 对象')
      }
      settingsJson = raw as Record<string, unknown>
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: 'settings_json 解析失败', message })
      return
    }

    const body: CreateKnowledgeBaseBody = {
      name: trimmedName,
      description: values.description?.trim() ?? '',
      settings_json: settingsJson,
    }

    setSaving(true)
    try {
      if (editing) {
        await updateKnowledgeBase(editing.id, body)
        showToast({ type: 'success', title: '已更新', message: '知识库已更新' })
      } else {
        await createKnowledgeBase(body)
        showToast({ type: 'success', title: '已创建', message: '知识库已创建' })
      }
      setModalOpen(false)
      await fetchPage(page, perPage)
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: editing ? '更新失败' : '创建失败', message })
    } finally {
      setSaving(false)
    }
  }, [editing, fetchPage, form, normalizeErrorMessage, page, perPage, saving, showToast])

  const onDelete = useCallback(
    async (kb: KnowledgeBaseItem) => {
      if (deletingId) return
      setDeletingId(kb.id)
      try {
        await deleteKnowledgeBase(kb.id)
        showToast({ type: 'success', title: '已删除', message: '知识库已删除' })
        const nextPage = items.length === 1 && page > 1 ? page - 1 : page
        if (nextPage !== page) setPage(nextPage)
        else await fetchPage(nextPage, perPage)
      } catch (err) {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '删除失败', message })
      } finally {
        setDeletingId(null)
      }
    },
    [deletingId, fetchPage, items.length, normalizeErrorMessage, page, perPage, showToast],
  )

  const columns = useMemo<ColumnsType<KnowledgeBaseItem>>(
    () => [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        width: 200,
        render: (value: KnowledgeBaseItem['name']) => <Typography.Text strong>{value}</Typography.Text>,
      },
      {
        title: '描述',
        dataIndex: 'description',
        key: 'description',
        render: (value: KnowledgeBaseItem['description']) => value || '—',
      },
      {
        title: '文档数',
        dataIndex: 'doc_cnt',
        key: 'doc_cnt',
        width: 100,
        render: (value: KnowledgeBaseItem['doc_cnt']) => value,
      },
      {
        title: '笔记数',
        dataIndex: 'note_cnt',
        key: 'note_cnt',
        width: 100,
        render: (value: KnowledgeBaseItem['note_cnt']) => value,
      },
      {
        title: '操作',
        key: 'actions',
        width: 200,
        fixed: 'right',
        align: 'right',
        render: (_, kb) => (
          <Space size={8}>
            <Button onClick={() => openEdit(kb)} disabled={loading || !!deletingId}>
              编辑
            </Button>
            <Popconfirm
              title="确定删除这个知识库吗？"
              description={`将删除「${kb.name}」`}
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              onConfirm={() => onDelete(kb)}
              disabled={loading || deletingId === kb.id}
            >
              <Button danger loading={deletingId === kb.id} disabled={loading || deletingId === kb.id}>
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [deletingId, loading, onDelete, openEdit],
  )

  // Measure the actual available height for the table body.
  useLayoutEffect(() => {
    const wrapperEl = tableWrapRef.current
    if (!wrapperEl) return

    const updateScrollY = () => {
      const wrapperHeight = wrapperEl.clientHeight
      if (wrapperHeight <= 0) return

      const thead = wrapperEl.querySelector('.ant-table-thead')
      const headerHeight = thead ? thead.clientHeight : 0

      const bodyHeight = Math.max(120, wrapperHeight - headerHeight - 2)

      setTableScrollY((prev) => (prev === bodyHeight ? prev : bodyHeight))
    }

    updateScrollY()

    const observer = new ResizeObserver(() => updateScrollY())
    observer.observe(wrapperEl)

    return () => observer.disconnect()
  }, [])

  const handlePaginationChange = useCallback((nextPage: number, nextPageSize: number) => {
    if (nextPageSize !== perPage) {
      setPage(1)
      setPerPage(nextPageSize)
      return
    }

    setPage(nextPage)
  }, [perPage])

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>知识库</h1>
        </div>
        <div className={styles.headerActions}>
          <Button type="primary" onClick={openCreate}>
            新建知识库
          </Button>
        </div>
      </div>

      <Card
        className={styles.card}
        title="知识库列表"
        extra={
          <Button onClick={() => fetchPage(page, perPage)} loading={loading}>
            刷新
          </Button>
        }
      >
        <div ref={tableWrapRef} className={styles.tableWrap}>
          <Table<KnowledgeBaseItem>
            rowKey={(r) => r.id}
            className={styles.table}
            columns={columns}
            dataSource={items}
            loading={loading}
            pagination={false}
            sticky
            scroll={{ x: 'max-content', y: tableScrollY }}
          />
        </div>
        <div className={styles.paginationBar}>
          <Typography.Text type="secondary">{`共 ${total} 条数据`}</Typography.Text>
          <Pagination
            current={page}
            pageSize={perPage}
            total={total}
            showSizeChanger
            pageSizeOptions={pageSizeOptions}
            onChange={handlePaginationChange}
          />
        </div>
      </Card>

      <Modal
        title={editing ? '编辑知识库' : '新建知识库'}
        open={modalOpen}
        onCancel={closeModal}
        onOk={submit}
        confirmLoading={saving}
        okText="保存"
        cancelText="取消"
        forceRender
        afterClose={() => form.resetFields()}
      >
        <Form form={form} layout="vertical" preserve={false} requiredMark={false}>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请填写知识库名称' }]}>
            <Input placeholder="例如：技术文档" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="可选" rows={3} />
          </Form.Item>

          <Form.Item name="settings_json_text" label="settings_json">
            <Input.TextArea rows={6} style={{ fontFamily: 'var(--mono)' }} placeholder="{}" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
