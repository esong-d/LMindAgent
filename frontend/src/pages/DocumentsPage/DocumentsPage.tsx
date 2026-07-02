import styles from './DocumentsPage.module.css'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Descriptions, Empty, Modal, Popconfirm, Select, Skeleton, Space, Table, Tag, Typography, Upload } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { UploadFile, UploadProps } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { useToast } from '../../components/Toast/ToastProvider'
import { ApiError } from '../../lib/apiClient'
import { uploadFile } from '../../lib/fileUpload'
import { deleteDocument, getDocument, listKnowledgeBaseDocuments, uploadDocumentFromFile } from '../../features/documents/api'
import type { DocumentItem } from '../../features/documents/types'
import { listKnowledgeBases } from '../../features/knowledge-bases/api'
import type { KnowledgeBase } from '../../features/knowledge-bases/types'

export function DocumentsPage() {
  const { showToast } = useToast()
  const location = useLocation()
  const navigate = useNavigate()

  const supportedExtensions = useMemo(() => ['pdf', 'doc', 'docx', 'txt', 'md', 'markdown'], [])
  const accept = useMemo(() => supportedExtensions.map((e) => `.${e}`).join(','), [supportedExtensions])

  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [kbId, setKbId] = useState<string>('')
  const [items, setItems] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadFileList, setUploadFileList] = useState<UploadFile<File>[]>([])

  const [detailOpen, setDetailOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detail, setDetail] = useState<DocumentItem | null>(null)

  const normalizeErrorMessage = useCallback((err: unknown) => {
    if (err instanceof ApiError) return err.message || '请求失败'
    if (err instanceof Error) return err.message || '请求失败'
    return '请求失败'
  }, [])

  const loadKnowledgeBases = useCallback(async () => {
    try {
      const list = await listKnowledgeBases()
      setKnowledgeBases(list)
      if (!kbId && list.length) setKbId(list[0].id)
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '加载知识库失败', message })
    }
  }, [kbId, normalizeErrorMessage, showToast])

  const reload = useCallback(async () => {
    if (!kbId) return
    setLoading(true)
    try {
      const list = await listKnowledgeBaseDocuments(kbId)
      setItems(list)
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '加载文档列表失败', message })
    } finally {
      setLoading(false)
    }
  }, [kbId, normalizeErrorMessage, showToast])

  useEffect(() => {
    loadKnowledgeBases().catch(() => {})
  }, [loadKnowledgeBases])

  useEffect(() => {
    reload().catch(() => {})
  }, [reload])

  useEffect(() => {
    const action = new URLSearchParams(location.search).get('action')
    if (action !== 'upload') return
    setUploadOpen(true)
    navigate('/documents', { replace: true })
  }, [location.search, navigate])

  useEffect(() => {
    setUploadFileList([])
  }, [kbId])

   const statusTag = useCallback((status: string) => {
    if (status === 'pending') return <Tag color="green">待处理</Tag>
    if (status === 'parsing') return <Tag color="orange">解析中</Tag>
    if (status === 'chunking') return <Tag color="blue">分块中</Tag>
    if (status === 'embedding') return <Tag color="blue">嵌入中</Tag>
    if (status === 'completed') return <Tag color="green">已完成</Tag>
    if (status === 'failed') return <Tag color="red">处理失败</Tag>
    return status || <Tag color="orange">未知状态</Tag>
  }, [])

  const formatBytes = useCallback((bytes: number) => {
    if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    const idx = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)))
    const value = bytes / 1024 ** idx
    const fixed = value >= 10 || idx === 0 ? 0 : 1
    return `${value.toFixed(fixed)} ${units[idx]}`
  }, [])

  const formatDateTime = useCallback((value?: string | null) => {
    if (!value) return '—'
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return '—'
    return d.toLocaleString()
  }, [])

  const columns = useMemo<ColumnsType<DocumentItem>>(
    () => [
      {
        title: '文件名',
        dataIndex: 'original_filename',
        key: 'original_filename',
        width: 250,
        ellipsis: { showTitle: false },
        render: (value: DocumentItem['original_filename']) => (
          <Typography.Text strong ellipsis={{ tooltip: value }}>
            {value}
          </Typography.Text>
        ),
      },
      {
        title: '类型',
        dataIndex: 'file_type',
        key: 'file_type',
        width: 160,
      },
      {
        title: '大小',
        dataIndex: 'file_size',
        key: 'file_size',
        width: 120,
        render: (value: DocumentItem['file_size']) => formatBytes(value),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 130,
        render: (value: DocumentItem['status']) => statusTag(String(value)),
      },
      {
        title: '处理开始时间',
        dataIndex: 'processing_started_at',
        key: 'processing_started_at',
        width: 200,
        render: (value: DocumentItem['processing_started_at']) => (value ? new Date(value).toLocaleString() : '—'),
      },
      {
        title: '处理完成时间',
        dataIndex: 'processing_completed_at',
        key: 'processing_completed_at',
        width: 200,
        render: (value: DocumentItem['processing_completed_at']) => (value ? new Date(value).toLocaleString() : '—'),
      },
      {
        title: '分块数',
        dataIndex: 'chunk_cnt',
        key: 'chunk_cnt',
        width: 120,
        render: (value: DocumentItem['chunk_cnt']) => value,
      },
      {
        title: "错误信息",
        dataIndex: 'error_message',
        key: 'error_message',
        width: 250,
        ellipsis: { showTitle: false },
        render: (value: DocumentItem['error_message']) => value || '—',
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 200,
        render: (value: DocumentItem['updated_at']) => (value ? new Date(value).toLocaleString() : '—'),
      },
      {
        title: '操作',
        key: 'actions',
        align: 'right',
        width: 220,
        fixed: 'right',
        render: (_, row) => (
          <div style={{ display: 'inline-flex', justifyContent: 'flex-end', gap: 8, flexWrap: 'nowrap', whiteSpace: 'nowrap' }}>
            <Button
              size="small"
              onClick={async () => {
                setDetailOpen(true)
                setDetailLoading(true)
                try {
                  const data = await getDocument(row.id)
                  setDetail(data)
                } catch (err) {
                  const message = normalizeErrorMessage(err)
                  showToast({ type: 'error', title: '加载文档详情失败', message })
                  setDetailOpen(false)
                } finally {
                  setDetailLoading(false)
                }
              }}
            >
              详情
            </Button>
            <Popconfirm
              title="确定删除这个文档吗？"
              description={`将删除「${row.original_filename}」`}
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              disabled={loading || deletingId === row.id}
              onConfirm={async () => {
                setDeletingId(row.id)
                try {
                  await deleteDocument(row.id)
                  showToast({ type: 'success', title: '已删除', message: '文档已删除' })
                  await reload()
                } catch (err) {
                  const message = normalizeErrorMessage(err)
                  showToast({ type: 'error', title: '删除失败', message })
                } finally {
                  setDeletingId(null)
                }
              }}
            >
              <Button size="small" danger loading={deletingId === row.id} disabled={loading || deletingId === row.id}>
                删除
              </Button>
            </Popconfirm>
          </div>
        ),
      },
    ],
    [deletingId, formatBytes, loading, normalizeErrorMessage, reload, showToast, statusTag],
  )

  const selectedFile = useMemo(() => {
    const item = uploadFileList[0]
    const origin = item?.originFileObj
    return origin && origin instanceof File ? origin : null
  }, [uploadFileList])

  const onStartUpload = useCallback(async () => {
    if (!kbId) {
      showToast({ type: 'warn', title: '未选择知识库', message: '请先选择知识库' })
      return
    }
    if (!selectedFile) {
      showToast({ type: 'warn', title: '未选择文件', message: '请先选择一个文件' })
      return
    }

    setUploading(true)
    try {
      const uploaded = await uploadFile({ file: selectedFile })
      await uploadDocumentFromFile({ knowledgeBaseId: kbId, file: uploaded })
      showToast({ type: 'success', title: '上传成功', message: '已提交文档处理任务' })
      setUploadOpen(false)
      setUploadFileList([])
      await reload()
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '上传失败', message })
    } finally {
      setUploading(false)
    }
  }, [kbId, normalizeErrorMessage, reload, selectedFile, showToast])

  const uploadProps = useMemo<UploadProps>(
    () => ({
      multiple: false,
      accept,
      maxCount: 1,
      fileList: uploadFileList,
      showUploadList: { showRemoveIcon: true, showPreviewIcon: false },
      beforeUpload: (file) => {
        const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
        if (ext && supportedExtensions.includes(ext)) return false
        showToast({ type: 'warn', title: '不支持的文件类型', message: `仅支持：${supportedExtensions.join(', ')}` })
        return Upload.LIST_IGNORE
      },
      onChange: (info) => {
        setUploadFileList(info.fileList.slice(-1) as UploadFile<File>[])
      },
      onRemove: () => {
        setUploadFileList([])
        return true
      },
    }),
    [accept, showToast, supportedExtensions, uploadFileList],
  )

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>文档管理</h1>
        </div>
        <div className={styles.headerRight}>
          <Select
            className={styles.kbSelect}
            value={kbId || undefined}
            placeholder="选择知识库"
            options={knowledgeBases.map((k) => ({ value: k.id, label: k.name }))}
            onChange={(v) => setKbId(v)}
            disabled={!knowledgeBases.length}
          />
          <Button type="primary" onClick={() => setUploadOpen(true)} disabled={!kbId}>
            上传文档
          </Button>
          <Button onClick={() => reload()} loading={loading} disabled={!kbId}>
            刷新
          </Button>
        </div>
      </div>

      <Card title="文档列表">
        <Table<DocumentItem>
          rowKey={(r) => r.id}
          dataSource={items}
          columns={columns}
          loading={loading}
          pagination={false}
          tableLayout="fixed"
          scroll={{ x: 1250 }}
        />
      </Card>

      <Modal
        title="上传文档"
        open={uploadOpen}
        onCancel={() => {
          if (uploading) return
          setUploadOpen(false)
          setUploadFileList([])
        }}
        okText="开始上传"
        cancelText="取消"
        onOk={onStartUpload}
        confirmLoading={uploading}
        okButtonProps={{ disabled: !kbId || !selectedFile }}
        width={620}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%' }}>
          <Alert
            type="info"
            showIcon
            message="上传流程"
            description="先选择文件（仅选择，不会立即上传），确认无误后点击「开始上传」。"
          />

          <div>
            <Typography.Text type="secondary">支持类型：</Typography.Text>{' '}
            <Space size={6} wrap>
              {supportedExtensions.map((e) => (
                <Tag key={e} color="blue">
                  .{e}
                </Tag>
              ))}
            </Space>
          </div>

          <Upload.Dragger {...uploadProps} disabled={!kbId || uploading} style={{ borderRadius: 12, background: '#f7f8fa' }}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ color: '#2f6bff' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到这里</p>
            <p className="ant-upload-hint">仅支持单文件上传</p>
          </Upload.Dragger>

          {selectedFile ? (
            <div>
              <Typography.Text type="secondary">已选择：</Typography.Text>{' '}
              <Typography.Text>{selectedFile.name}</Typography.Text>
            </div>
          ) : (
            <Typography.Text type="secondary">未选择文件</Typography.Text>
          )}
        </div>
      </Modal>

      <Modal
        title="文档详情"
        open={detailOpen}
        onCancel={() => {
          setDetailOpen(false)
          setDetail(null)
        }}
        footer={null}
        width="40%"
      >
        {detailLoading ? (
          <Skeleton active paragraph={{ rows: 10 }} />
        ) : detail ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%' }}>
            {detail.error_message ? (
              <Alert type="error" showIcon message="处理失败" description={detail.error_message} />
            ) : null}

            <Descriptions
              size="small"
              column={1}
              styles={{ label: { width: 120, color: 'rgba(0, 0, 0, 0.45)' }, content: { wordBreak: 'break-all' } }}
            >
              <Descriptions.Item label="文件名">
                <Typography.Text copyable ellipsis={{ tooltip: detail.original_filename }} style={{ display: 'inline-block', maxWidth: '100%' }}>
                  {detail.original_filename}
                </Typography.Text>
              </Descriptions.Item>
              {/* <Descriptions.Item label="文件名">
                <Typography.Text code copyable>
                  {detail.filename}
                </Typography.Text>
              </Descriptions.Item> */}
              <Descriptions.Item label="类型">{detail.file_type || '—'}</Descriptions.Item>
              <Descriptions.Item label="大小">{formatBytes(detail.file_size)}</Descriptions.Item>
              <Descriptions.Item label="状态">{statusTag(String(detail.status))}</Descriptions.Item>
              <Descriptions.Item label="处理开始时间">{formatDateTime(detail.processing_started_at)}</Descriptions.Item>
              <Descriptions.Item label="处理完成时间">{formatDateTime(detail.processing_completed_at)}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{formatDateTime(detail.created_at)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{formatDateTime(detail.updated_at)}</Descriptions.Item>
            </Descriptions>
          </div>
        ) : (
          <Empty description="暂无数据" />
        )}
      </Modal>
    </div>
  )
}
