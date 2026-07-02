import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Form, Input, Modal, Pagination, Popconfirm, Skeleton, Space, Typography } from 'antd'
import { useToast } from '../../components/Toast/ToastProvider'
import {
  createEvaluationGroup,
  deleteEvaluationGroup,
  listEvaluationGroups,
  updateEvaluationGroup,
} from '../../features/evaluation/api'
import type {
  CreateEvaluationGroupBody,
  EvaluationGroup,
  UpdateEvaluationGroupBody,
} from '../../features/evaluation/types'
import { formatMonthDayTimeWithSecond, normalizeErrorMessage, pageSizeOptions, questionPreview } from './evaluationShared'
import styles from './EvaluationPage.module.css'

type GroupFormValues = {
  name: string
  description?: string
}

export function EvaluationGroupsPage() {
  const { showToast } = useToast()
  const [form] = Form.useForm<GroupFormValues>()

  const [groups, setGroups] = useState<EvaluationGroup[]>([])
  const [groupsTotal, setGroupsTotal] = useState(0)
  const [groupsPage, setGroupsPage] = useState(1)
  const [groupsPageSize, setGroupsPageSize] = useState(10)
  const [groupsLoading, setGroupsLoading] = useState(false)

  const [modalOpen, setModalOpen] = useState(false)
  const [modalSaving, setModalSaving] = useState(false)
  const [editingGroup, setEditingGroup] = useState<EvaluationGroup | null>(null)
  const [deletingGroupId, setDeletingGroupId] = useState<string | null>(null)

  const [searchText, setSearchText] = useState('')
  const [animReady, setAnimReady] = useState(false)
  const animLock = useRef(false)

  const filteredGroups = useMemo(() => {
    if (!searchText.trim()) return groups
    const keyword = searchText.trim().toLowerCase()
    return groups.filter(
      (item) =>
        item.name.toLowerCase().includes(keyword) ||
        item.description.toLowerCase().includes(keyword),
    )
  }, [groups, searchText])

  const loadGroups = useCallback(async () => {
    setGroupsLoading(true)
    try {
      const data = await listEvaluationGroups({ page: groupsPage, pageSize: groupsPageSize })
      setGroups(data.items)
      setGroupsTotal(data.total)
    } catch (err) {
      showToast({ type: 'error', title: '加载分组列表失败', message: normalizeErrorMessage(err) })
    } finally {
      setGroupsLoading(false)
    }
  }, [groupsPage, groupsPageSize, showToast])

  useEffect(() => {
    loadGroups().catch(() => {})
  }, [loadGroups])

  useEffect(() => {
    if (!groupsLoading && filteredGroups.length > 0 && !animLock.current) {
      animLock.current = true
      const timer = setTimeout(() => setAnimReady(true), 60)
      return () => clearTimeout(timer)
    }
    if (groupsLoading) {
      setAnimReady(false)
      animLock.current = false
    }
  }, [filteredGroups.length, groupsLoading])

  const openCreateModal = useCallback(() => {
    setEditingGroup(null)
    form.setFieldsValue({ name: '', description: '' })
    setModalOpen(true)
  }, [form])

  const openEditModal = useCallback(
    (group: EvaluationGroup) => {
      setEditingGroup(group)
      form.setFieldsValue({
        name: group.name,
        description: group.description,
      })
      setModalOpen(true)
    },
    [form],
  )

  const submitGroup = useCallback(async () => {
    if (modalSaving) return

    let values: GroupFormValues
    try {
      values = await form.validateFields()
    } catch {
      return
    }

    const trimmedName = values.name.trim()
    const trimmedDescription = values.description?.trim() ?? ''

    setModalSaving(true)
    try {
      if (editingGroup) {
        const body: UpdateEvaluationGroupBody = {
          name: trimmedName,
          description: trimmedDescription,
        }
        await updateEvaluationGroup(editingGroup.id, body)
        showToast({ type: 'success', title: '已更新', message: '测评分组已更新' })
      } else {
        const body: CreateEvaluationGroupBody = {
          name: trimmedName,
          description: trimmedDescription,
        }
        await createEvaluationGroup(body)
        showToast({ type: 'success', title: '已创建', message: '测评分组已创建' })
      }

      setModalOpen(false)
      await loadGroups()
    } catch (err) {
      showToast({
        type: 'error',
        title: editingGroup ? '更新分组失败' : '创建分组失败',
        message: normalizeErrorMessage(err),
      })
    } finally {
      setModalSaving(false)
    }
  }, [editingGroup, form, loadGroups, modalSaving, showToast])

  const handleDeleteGroup = useCallback(
    async (groupId: string) => {
      if (deletingGroupId) return
      setDeletingGroupId(groupId)
      try {
        await deleteEvaluationGroup(groupId)
        showToast({ type: 'success', title: '已删除', message: '测评分组已删除' })
        const nextPage = groups.length === 1 && groupsPage > 1 ? groupsPage - 1 : groupsPage
        if (nextPage !== groupsPage) setGroupsPage(nextPage)
        else await loadGroups()
      } catch (err) {
        showToast({ type: 'error', title: '删除分组失败', message: normalizeErrorMessage(err) })
      } finally {
        setDeletingGroupId(null)
      }
    },
    [deletingGroupId, groups.length, groupsPage, loadGroups, showToast],
  )

  return (
    <div className={styles.sectionPage}>
      <div className={styles.toolbar}>
        <Input
          className={styles.searchInput}
          placeholder="搜索分组名称或描述…"
          allowClear
          prefix={<span style={{ fontSize: 14, opacity: 0.45 }}>⌕</span>}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <div className={styles.toolbarSpacer} />
        <Space wrap>
          <Button onClick={() => loadGroups()} loading={groupsLoading}>
            刷新
          </Button>
          <Button type="primary" onClick={() => openCreateModal()}>
            新建分组
          </Button>
        </Space>
      </div>

      <Card className={styles.sectionCard} title={`分组列表${filteredGroups.length !== groups.length ? ` · 筛选 ${filteredGroups.length} 条` : ''}`}>
        <div className={styles.sectionBody}>
          <div className={styles.taskTable}>
            {groupsLoading ? (
              <Skeleton active paragraph={{ rows: 8 }} />
            ) : filteredGroups.length ? (
              <>
                <div className={styles.groupTableHead}>
                  <div className={styles.groupTableHeadCell}>分组名称</div>
                  <div className={styles.groupTableHeadCell}>分组描述</div>
                  <div className={styles.groupTableHeadCell}>创建时间</div>
                  <div className={styles.groupTableHeadCell}>更新时间</div>
                  <div className={[styles.groupTableHeadCell, styles.groupTableHeadActions].join(' ')}>操作</div>
                </div>
                <div className={styles.groupTableBody}>
                  {filteredGroups.map((item, idx) => (
                    <div
                      key={item.id}
                      className={[styles.groupTableRow, animReady ? styles.cardAnimEnter : ''].join(' ')}
                      style={animReady ? { animationDelay: `${idx * 40}ms` } : undefined}
                    >
                      <div className={[styles.groupTableCell, styles.groupTableNameCell].join(' ')}>
                        <Typography.Text strong ellipsis={{ tooltip: item.name }}>
                          {questionPreview(item.name, '未命名分组')}
                        </Typography.Text>
                      </div>
                      <div className={[styles.groupTableCell, styles.groupTableDescriptionCell].join(' ')}>
                        <Typography.Paragraph className={styles.groupTableDescriptionText} ellipsis={{ rows: 2, tooltip: item.description || '未填写描述' }}>
                          {questionPreview(item.description, '未填写描述')}
                        </Typography.Paragraph>
                      </div>
                      <div className={[styles.groupTableCell, styles.groupTableMutedCell].join(' ')}>
                        {formatMonthDayTimeWithSecond(item.created_at)}
                      </div>
                      <div className={[styles.groupTableCell, styles.groupTableMutedCell].join(' ')}>
                        {formatMonthDayTimeWithSecond(item.updated_at)}
                      </div>
                      <div className={styles.groupTableActions}>
                        <Button size="small" onClick={() => openEditModal(item)}>
                          编辑
                        </Button>
                        <Popconfirm
                          title="确定删除这个分组吗？"
                          description="删除后将按后端软删除逻辑处理"
                          okText="删除"
                          cancelText="取消"
                          okButtonProps={{ danger: true }}
                          onConfirm={() => handleDeleteGroup(item.id)}
                          disabled={deletingGroupId === item.id}
                        >
                          <Button danger size="small" loading={deletingGroupId === item.id} disabled={deletingGroupId === item.id}>
                            删除
                          </Button>
                        </Popconfirm>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className={styles.emptyState}>
                <div className={styles.emptyStateIcon}>{searchText ? '🔍' : '🗂️'}</div>
                <h3 className={styles.emptyStateHeading}>{searchText ? '没有匹配的分组' : '暂无测评分组'}</h3>
                <p className={styles.emptyStateText}>
                  {searchText ? '尝试调整搜索关键词' : '点击「新建分组」创建第一个测评分组，便于后续统一组织测评资源'}
                </p>
              </div>
            )}
          </div>

          <div className={styles.paginationBar}>
            <Typography.Text type="secondary">{`共 ${groupsTotal} 条`}</Typography.Text>
            <Pagination
              size="small"
              current={groupsPage}
              pageSize={groupsPageSize}
              total={groupsTotal}
              showSizeChanger
              pageSizeOptions={pageSizeOptions}
              onChange={(page, pageSize) => {
                if (pageSize !== groupsPageSize) {
                  setGroupsPage(1)
                  setGroupsPageSize(pageSize)
                  return
                }
                setGroupsPage(page)
              }}
            />
          </div>
        </div>
      </Card>

      <Modal
        title={editingGroup ? '编辑测评分组' : '新建测评分组'}
        open={modalOpen}
        onCancel={() => {
          if (!modalSaving) setModalOpen(false)
        }}
        onOk={() => submitGroup()}
        okText={editingGroup ? '保存修改' : '创建分组'}
        cancelText="取消"
        confirmLoading={modalSaving}
        width={680}
        afterClose={() => {
          form.resetFields()
          setEditingGroup(null)
        }}
      >
        <Form form={form} layout="vertical" preserve={false} requiredMark={false}>
          <Form.Item
            name="name"
            label="分组名称"
            rules={[
              { required: true, message: '请填写分组名称' },
              {
                validator: async (_, value: string | undefined) => {
                  if (!value?.trim()) throw new Error('请填写分组名称')
                },
              },
            ]}
          >
            <Input placeholder="例如：核心问题集 / RAG 基线对比" maxLength={200} />
          </Form.Item>
          <Form.Item name="description" label="分组描述">
            <Input.TextArea rows={6} placeholder="可选，用于补充分组用途、适用范围或备注信息" maxLength={2000} showCount />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
