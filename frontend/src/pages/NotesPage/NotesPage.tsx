import styles from './NotesPage.module.css'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Alert, Button, Card, Empty, Form, Input, Modal, Popconfirm, Select, Skeleton, Space, Tag, Typography } from 'antd'
import { useToast } from '../../components/Toast/ToastProvider'
import { ApiError } from '../../lib/apiClient'
import { formatMonthDayTimeWithSecond } from '../../lib/dateTime'
import { listKnowledgeBases } from '../../features/knowledge-bases/api'
import type { KnowledgeBase } from '../../features/knowledge-bases/types'
import { createNote, deleteNote, getNote, listKnowledgeBaseNotes, type NoteOut } from '../../features/notes/api'

const SUGGESTED_TAGS = ['待整理', '灵感', '总结', '重要', 'AI', '问题', '方案', '技术']

export function NotesPage() {
  const { showToast } = useToast()

  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [loadingKbs, setLoadingKbs] = useState(false)
  const [kbId, setKbId] = useState('')

  const [notes, setNotes] = useState<NoteOut[]>([])
  const [loadingNotes, setLoadingNotes] = useState(false)

  const [createOpen, setCreateOpen] = useState(false)
  const [createSaving, setCreateSaving] = useState(false)
  const [createForm] = Form.useForm<{ title: string; content: string; tags_json: string[] }>()
  const selectedCreateTags = Form.useWatch('tags_json', createForm) ?? []
  const [tagDraft, setTagDraft] = useState('')
  const tagInputRef = useRef<HTMLInputElement | null>(null)

  const [detailOpen, setDetailOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailDeleting, setDetailDeleting] = useState(false)
  const [activeNoteId, setActiveNoteId] = useState<string | null>(null)
  const [activeNote, setActiveNote] = useState<NoteOut | null>(null)

  const normalizeErrorMessage = useCallback((err: unknown) => {
    if (err instanceof ApiError) return err.message || '请求失败'
    if (err instanceof Error) return err.message || '请求失败'
    return '请求失败'
  }, [])

  const kbOptions = useMemo(() => knowledgeBases.map((kb) => ({ label: kb.name, value: kb.id })), [knowledgeBases])

  const fetchNotes = useCallback(
    async (currentKbId: string) => {
      if (!currentKbId) {
        setNotes([])
        return
      }
      setLoadingNotes(true)
      try {
        const items = await listKnowledgeBaseNotes(currentKbId)
        setNotes(items)
      } catch (err) {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '加载笔记列表失败', message })
      } finally {
        setLoadingNotes(false)
      }
    },
    [normalizeErrorMessage, showToast],
  )

  useEffect(() => {
    setLoadingKbs(true)
    listKnowledgeBases()
      .then((items) => {
        setKnowledgeBases(items)
        if (!kbId && items.length) setKbId(items[0].id)
      })
      .catch((err) => {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '加载知识库失败', message })
      })
      .finally(() => setLoadingKbs(false))
  }, [kbId, normalizeErrorMessage, showToast])

  useEffect(() => {
    fetchNotes(kbId).catch(() => {})
  }, [fetchNotes, kbId])

  const openDetail = useCallback(
    async (noteId: string) => {
      setDetailOpen(true)
      setDetailLoading(true)
      setActiveNoteId(noteId)
      setActiveNote(null)

      try {
        const note = await getNote(noteId)
        setActiveNote(note)
      } catch (err) {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '加载笔记详情失败', message })
      } finally {
        setDetailLoading(false)
      }
    },
    [normalizeErrorMessage, showToast],
  )

  const closeDetail = useCallback(() => {
    setDetailOpen(false)
    setActiveNoteId(null)
    setActiveNote(null)
    setDetailLoading(false)
    setDetailDeleting(false)
  }, [])

  const confirmDeleteActiveNote = useCallback(async () => {
    if (!kbId) return
    const noteId = activeNoteId
    if (!noteId) return

    setDetailDeleting(true)
    try {
      await deleteNote(noteId)
      showToast({ type: 'success', title: '已删除', message: '笔记已删除' })
      closeDetail()
      await fetchNotes(kbId)
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '删除笔记失败', message })
    } finally {
      setDetailDeleting(false)
    }
  }, [activeNoteId, closeDetail, fetchNotes, kbId, normalizeErrorMessage, showToast])

  const openCreate = useCallback(() => {
    if (!kbId) {
      showToast({ type: 'warn', title: '请先选择知识库', message: '创建笔记需要选择一个知识库。' })
      return
    }
    createForm.setFieldsValue({ title: '', content: '', tags_json: [] })
    setTagDraft('')
    setCreateOpen(true)
  }, [createForm, kbId, showToast])

  const closeCreate = useCallback(() => {
    setCreateOpen(false)
    setCreateSaving(false)
    setTagDraft('')
  }, [])

  const submitCreate = useCallback(
    async (values: { title: string; content: string; tags_json: string[] }) => {
      if (!kbId) return
      const tags = (values.tags_json ?? []).map((t) => t.trim()).filter(Boolean)

      setCreateSaving(true)
      try {
        const created = await createNote({
          knowledge_base_id: kbId,
          title: values.title.trim(),
          content: values.content ?? '',
          tags_json: tags,
        })
        showToast({ type: 'success', title: '创建成功', message: created.title })
        setCreateOpen(false)
        await fetchNotes(kbId)
        setDetailOpen(true)
        setDetailLoading(false)
        setActiveNoteId(created.id)
        setActiveNote(created)
      } catch (err) {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '创建笔记失败', message })
      } finally {
        setCreateSaving(false)
      }
    },
    [fetchNotes, kbId, normalizeErrorMessage, showToast],
  )

  const setCreateTags = useCallback(
    (nextTags: string[]) => {
      const normalized = nextTags.map((t) => t.trim()).filter(Boolean)
      const unique = Array.from(new Set(normalized))
      createForm.setFieldsValue({ tags_json: unique })
    },
    [createForm],
  )

  const toggleSuggestedTag = useCallback(
    (tagValue: string, checked: boolean) => {
      const current = (selectedCreateTags ?? []).map((t) => t.trim()).filter(Boolean)
      const next = checked ? [...current, tagValue] : current.filter((t) => t !== tagValue)
      setCreateTags(next)
    },
    [selectedCreateTags, setCreateTags],
  )

  const addCreateTag = useCallback(
    (value: string) => {
      const nextValue = value.trim()
      if (!nextValue) return
      setCreateTags([...selectedCreateTags, nextValue])
    },
    [selectedCreateTags, setCreateTags],
  )

  const removeCreateTag = useCallback(
    (value: string) => {
      const next = selectedCreateTags.filter((t) => t !== value)
      setCreateTags(next)
    },
    [selectedCreateTags, setCreateTags],
  )

  const handleTagInputKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        const value = tagDraft.trim()
        if (!value) return
        addCreateTag(value)
        setTagDraft('')
        return
      }
      if (e.key === 'Backspace' && !tagDraft) {
        const last = selectedCreateTags[selectedCreateTags.length - 1]
        if (last) removeCreateTag(last)
      }
    },
    [addCreateTag, removeCreateTag, selectedCreateTags, tagDraft],
  )

  function renderTags(tags: string[]) {
    const normalized = tags.map((t) => t.trim()).filter(Boolean)
    if (!normalized.length) return <span className={styles.muted}>无标签</span>
    const visible = normalized.slice(0, 3)
    const rest = normalized.length - visible.length
    return (
      <Space size={[6, 6]} wrap>
        {visible.map((t) => (
          <Tag key={t} className={styles.noteTag}>
            {t}
          </Tag>
        ))}
        {rest > 0 ? <Tag className={styles.noteTag}>+{rest}</Tag> : null}
      </Space>
    )
  }

  function createdLabelForNote(note: NoteOut) {
    if (!note.created_at) return ''
    const labelWithTime = formatMonthDayTimeWithSecond(note.created_at)
    return labelWithTime ? `创建于: ${labelWithTime}` : ''
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>笔记</h1>
        <div className={styles.toolbar}>
          <div className={styles.label}>知识库</div>
          <Select
            value={kbId || undefined}
            onChange={(v) => setKbId(v)}
            options={kbOptions}
            loading={loadingKbs}
            placeholder="请选择知识库"
            style={{ minWidth: 220 }}
          />
          <Button type="primary" onClick={openCreate} disabled={!kbId || !knowledgeBases.length}>
            创建笔记
          </Button>
        </div>
      </div>

      {!loadingKbs && !knowledgeBases.length ? (
        <Alert
          type="info"
          showIcon
          title="暂无知识库"
          description="请先在「知识库」页面创建知识库，然后再查看该知识库下的笔记。"
        />
      ) : loadingNotes ? (
        <Skeleton active />
      ) : notes.length ? (
        <div className={styles.cards}>
          {notes.map((note) => {
            const createdLabel = createdLabelForNote(note)
            return (
              <Card
                key={note.id}
                hoverable
                className={styles.card}
                title={
                  <div className={styles.cardHead}>
                    <Typography.Text ellipsis={{ tooltip: note.title }} className={styles.cardTitle}>
                      {note.title}
                    </Typography.Text>
                    {createdLabel ? <div className={styles.cardSub}>{createdLabel}</div> : null}
                  </div>
                }
                onClick={() => openDetail(note.id)}
              >
                <div className={styles.cardPreview}>{note.content || '（无内容）'}</div>
                <div className={styles.cardFooter}>
                  <div className={styles.tagsRow}>{renderTags(note.tags_json)}</div>
                  <div className={styles.cardAction}>查看</div>
                </div>
              </Card>
            )
          })}
        </div>
      ) : kbId ? (
        <Empty description="暂无笔记" />
      ) : (
        <Empty description="请选择知识库" />
      )}

      <Modal
        open={detailOpen}
        onCancel={closeDetail}
        title={activeNote?.title ?? (activeNoteId ? '笔记详情' : '笔记')}
        footer={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Button onClick={closeDetail} disabled={detailDeleting}>
              关闭
            </Button>
            <Popconfirm
              title="确定删除这条笔记吗？"
              description="删除后不可恢复。"
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true, loading: detailDeleting }}
              onConfirm={() => confirmDeleteActiveNote()}
              disabled={!activeNoteId || detailLoading || detailDeleting}
            >
              <Button danger loading={detailDeleting} disabled={!activeNoteId || detailLoading || detailDeleting}>
                删除
              </Button>
            </Popconfirm>
          </div>
        }
        width={760}
        destroyOnHidden
        styles={{ body: { height: '70vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' } }}
      >
        {detailLoading ? (
          <Skeleton active />
        ) : activeNote ? (
          <>
            <div className={styles.detailMeta}>
              <div className={styles.detailRow}>
                <Typography.Text type="secondary">标签：</Typography.Text> {renderTags(activeNote.tags_json)}
              </div>
              {(() => {
                const createdLabel = createdLabelForNote(activeNote)
                return createdLabel ? (
                  <div className={styles.detailRow}>
                    <Typography.Text type="secondary">{createdLabel}</Typography.Text>
                  </div>
                ) : null
              })()}
            </div>
            <div className={styles.detailContent}>
              {activeNote.content ? (
                <div className={styles.detailActions}>
                  <Typography.Text className={styles.copyAction} copyable={{ text: activeNote.content }}>
                    复制
                  </Typography.Text>
                </div>
              ) : null}
              <div className={styles.detailScroll}>
                <Typography.Paragraph className={styles.content}>{activeNote.content || '（无内容）'}</Typography.Paragraph>
              </div>
            </div>
          </>
        ) : (
          <Empty description="未加载到笔记内容" />
        )}
      </Modal>

      <Modal
        open={createOpen}
        onCancel={closeCreate}
        title="创建笔记"
        okText="创建"
        cancelText="取消"
        confirmLoading={createSaving}
        onOk={() => createForm.submit()}
        destroyOnHidden
      >
        <Form form={createForm} layout="vertical" onFinish={submitCreate}>
          <Form.Item
            label="标题"
            name="title"
            rules={[
              { required: true, message: '请输入标题' },
              { max: 200, message: '标题不能超过 200 个字符' },
            ]}
          >
            <Input placeholder="请输入标题" />
          </Form.Item>
          <Form.Item label="标签">
            <Form.Item name="tags_json" noStyle>
              <Input type="hidden" />
            </Form.Item>
            <div className={styles.tagField}>
              <div
                className={styles.tagInputBox}
                role="button"
                tabIndex={0}
                onClick={() => tagInputRef.current?.focus()}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') tagInputRef.current?.focus()
                }}
              >
                {selectedCreateTags.map((t) => (
                  <Tag
                    key={t}
                    className={styles.noteTag}
                    closable
                    onClose={(e) => {
                      e.preventDefault()
                      removeCreateTag(t)
                    }}
                  >
                    {t}
                  </Tag>
                ))}
                <input
                  ref={(el) => {
                    tagInputRef.current = el
                  }}
                  className={styles.tagInput}
                  value={tagDraft}
                  onChange={(e) => setTagDraft(e.target.value)}
                  onKeyDown={handleTagInputKeyDown}
                  placeholder={selectedCreateTags.length ? '' : '输入后回车添加标签'}
                />
              </div>
              <div className={styles.tagPicker}>
                <div className={styles.tagPickerLabel}>常用标签</div>
                <Space size={[6, 6]} wrap>
                  {SUGGESTED_TAGS.map((t) => (
                    <Tag.CheckableTag
                      key={t}
                      className={styles.noteTagCheckable}
                      checked={selectedCreateTags.includes(t)}
                      onChange={(checked) => toggleSuggestedTag(t, checked)}
                    >
                      {t}
                    </Tag.CheckableTag>
                  ))}
                </Space>
              </div>
            </div>
          </Form.Item>
          <Form.Item label="内容" name="content">
            <Input.TextArea placeholder="请输入笔记内容" rows={10} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
