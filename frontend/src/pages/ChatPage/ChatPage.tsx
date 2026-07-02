import { AgentComposer } from '../../layouts/AgentComposer/AgentComposer'
import styles from './ChatPage.module.css'
import { useEffect, useRef, useState, type CSSProperties } from 'react'
import ui from '../../styles/ui.module.css'
import { useToast } from '../../components/Toast/ToastProvider'
import { CopyOutlined, DeleteOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { fileBaseName, sourceColor } from '../../lib/sourceColor'
import { useTheme } from '../../context/ThemeContext'
import { formatMonthDayTime } from '../../lib/dateTime'

import {
  chatStream,
  deleteConversation,
  getConversationMessages,
  listConversations,
  type ConversationSummary,
  type SourceItem,
} from '../../features/chat/api'
import { listKnowledgeBases } from '../../features/knowledge-bases/api'
import type { KnowledgeBase } from '../../features/knowledge-bases/types'

type ChatRole = 'user' | 'assistant'

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
  sources?: SourceItem[]
  progress?: string[]
  status?: 'streaming' | 'done' | 'error'
}

type SearchScope = 'kb' | 'global'

function randomId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`
}

function uniqueSources(sources?: SourceItem[]) {
  if (!Array.isArray(sources) || !sources.length) return []

  return Array.from(
    new Map(
      sources.map((source) => [
        source.original_filename || source.document_id,
        source,
      ]),
    ).values(),
  )
}

function isAssistantPlaceholderContent(content: string) {
  const text = content.trim()
  return !text || text === 'AI 正在思考…' || text === 'AI 正在生成回答...'
}

export function ChatPage() {
  const { showToast } = useToast()
  const { theme } = useTheme()

  // Dynamically load highlight.js theme based on color mode
  useEffect(() => {
    const linkId = 'highlight-theme'
    let link = document.getElementById(linkId) as HTMLLinkElement | null
    if (!link) {
      link = document.createElement('link')
      link.id = linkId
      link.rel = 'stylesheet'
      document.head.appendChild(link)
    }
    link.href =
      theme === 'dark'
        ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github-dark.min.css'
        : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github.min.css'
  }, [theme])
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<string>(() => localStorage.getItem('conversation_id') ?? '')
  const [scope, setScope] = useState<SearchScope>(() => (localStorage.getItem('chat_scope') === 'kb' ? 'kb' : 'global'))
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [knowledgeBaseId, setKnowledgeBaseId] = useState<string>(() => localStorage.getItem('knowledge_base_id') ?? '')
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loadingConversationId, setLoadingConversationId] = useState<string | null>(null)
  const [streaming, setStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const streamingAssistantIdRef = useRef<string | null>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const progressViewportRefs = useRef<Record<string, HTMLDivElement | null>>({})
  const kbLoadedRef = useRef(false)
  const convLoadedRef = useRef(false)

  useEffect(() => {
    if (conversationId) localStorage.setItem('conversation_id', conversationId)
  }, [conversationId])

  useEffect(() => {
    localStorage.setItem('chat_scope', scope)
  }, [scope])

  useEffect(() => {
    localStorage.setItem('knowledge_base_id', knowledgeBaseId)
  }, [knowledgeBaseId])

  useEffect(() => {
    if (kbLoadedRef.current) return
    kbLoadedRef.current = true

    async function loadKnowledgeBases() {
      try {
        const items = await listKnowledgeBases()
        setKnowledgeBases(items)
        if (!knowledgeBaseId && items.length && scope === 'kb') setKnowledgeBaseId(items[0].id)
      } catch (err) {
        const message = err instanceof Error ? err.message : '请求失败'
        showToast({ type: 'error', title: '加载知识库失败', message })
      }
    }

    loadKnowledgeBases()
  }, [knowledgeBaseId, scope, showToast])

  useEffect(() => {
    if (convLoadedRef.current) return
    convLoadedRef.current = true

    async function loadConversations() {
      try {
        const items = await listConversations()
        items.sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1))
        setConversations(items)
      } catch (err) {
        const message = err instanceof Error ? err.message : '请求失败'
        showToast({ type: 'error', title: '加载会话失败', message })
      }
    }

    loadConversations()
  }, [showToast])

  const openedFromStorageRef = useRef(false)
  useEffect(() => {
    if (openedFromStorageRef.current) return
    if (!conversationId) return
    if (messages.length) return
    openedFromStorageRef.current = true
    openConversation(conversationId)
  }, [conversationId, messages.length])

  useEffect(() => {
    const el = listRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [messages, streaming])

  useEffect(() => {
    const frameId = requestAnimationFrame(() => {
      messages.forEach((message) => {
        if (message.role !== 'assistant') return
        if (message.status !== 'streaming') return
        if (!Array.isArray(message.progress) || !message.progress.length) return
        const viewport = progressViewportRefs.current[message.id]
        if (!viewport) return
        viewport.scrollTop = viewport.scrollHeight
      })
    })

    return () => cancelAnimationFrame(frameId)
  }, [messages])

  async function writeClipboard(text: string) {
    if (typeof navigator === 'undefined' || !navigator.clipboard?.writeText) {
      const hint = typeof window !== 'undefined' && !window.isSecureContext ? '（需 HTTPS 或 localhost）' : ''
      throw new Error(`当前环境不支持一键复制${hint}`)
    }
    await navigator.clipboard.writeText(text)
  }

  async function copyMessage(text: string) {
    const value = text.trim()
    if (!value) return
    try {
      await writeClipboard(value)
      showToast({ type: 'success', title: '已复制', message: '已复制到剪贴板' })
    } catch (err) {
      const message = err instanceof Error ? err.message : '复制失败'
      showToast({ type: 'error', title: '复制失败', message })
    }
  }

  function stopStreaming() {
    const currentAssistantId = streamingAssistantIdRef.current
    abortRef.current?.abort()
    abortRef.current = null
    streamingAssistantIdRef.current = null
    setStreaming(false)

    if (currentAssistantId) {
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== currentAssistantId) return m
          if (m.role !== 'assistant') return m
          const isPlaceholder = isAssistantPlaceholderContent(m.content || '')
          return { ...m, status: 'done', content: isPlaceholder ? '已停止生成。' : m.content }
        }),
      )
    }
  }

  function clearConversation() {
    stopStreaming()
    setMessages([])
    setConversationId('')
    localStorage.removeItem('conversation_id')
  }

  async function refreshConversations() {
    try {
      const items = await listConversations()
      items.sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1))
      setConversations(items)
    } catch (err) {
      const message = err instanceof Error ? err.message : '请求失败'
      showToast({ type: 'error', title: '刷新会话失败', message })
    }
  }

  async function openConversation(id: string) {
    if (!id) return
    if (streaming) stopStreaming()
    setLoadingConversationId(id)
    try {
      const items = await getConversationMessages(id)
      const mapped: ChatMessage[] = items.map((m) => ({
        id: m.id,
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content,
        sources: m.sources,
        status: 'done',
      }))
      setConversationId(id)
      setMessages(mapped)
    } catch (err) {
      const message = err instanceof Error ? err.message : '请求失败'
      showToast({ type: 'error', title: '加载会话消息失败', message })
    } finally {
      setLoadingConversationId(null)
    }
  }

  async function onDeleteConversation(id: string) {
    if (!id) return
    if (streaming) stopStreaming()
    try {
      const deleted = await deleteConversation(id)
      if (deleted) {
        setConversations((prev) => prev.filter((c) => c.id !== id))
        if (conversationId === id) clearConversation()
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '请求失败'
      showToast({ type: 'error', title: '删除会话失败', message })
    }
  }

  async function send() {
    const query = draft.trim()
    if (!query) return
    if (streaming) stopStreaming()

    setDraft('')
    const userMessage: ChatMessage = { id: `u_${randomId()}`, role: 'user', content: query, status: 'done' }
    const assistantId = `a_${randomId()}`
    streamingAssistantIdRef.current = assistantId
    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: assistantId, role: 'assistant', content: '', progress: [], status: 'streaming' },
    ])
    setStreaming(true)

    const controller = new AbortController()
    abortRef.current = controller
    let streamFinished = false
    let streamFailed = false

    try {
      await chatStream({
        query,
        conversationId,
        knowledgeBaseId: scope === 'global' ? '' : knowledgeBaseId,
        signal: controller.signal,
        onEvent: (evt) => {
          const currentAssistantId = streamingAssistantIdRef.current
          if (!currentAssistantId) return

          if (evt.event === 'message_start') {
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== currentAssistantId) return m
                if (!isAssistantPlaceholderContent(m.content)) return m
                return { ...m, status: 'streaming' }
              }),
            )
            if (evt.data && typeof (evt.data as { conversation_id?: string }).conversation_id === 'string') {
              const newId = (evt.data as { conversation_id?: string }).conversation_id
              setConversationId(newId || '')
              setConversations((prev) => {
                if (prev.some((c) => c.id === newId)) return prev
                const now = new Date().toISOString()
                const kbId = scope === 'global' ? null : knowledgeBaseId
                const next: ConversationSummary = { id: newId || '', knowledge_base_id: kbId, title: query, updated_at: now }
                return [next, ...prev]
              })
            }
            return
          }

          if (evt.event === 'custom') {
            const statusEvent = evt.data as { event?: string; message?: string } | null
            const statusMessage =
              statusEvent?.event === 'status' && typeof statusEvent.message === 'string'
                ? statusEvent.message.trim()
                : ''
            if (!statusMessage) return

            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== currentAssistantId) return m
                if (m.role !== 'assistant') return m
                const progress = Array.isArray(m.progress) ? m.progress : []
                const nextProgress =
                  progress[progress.length - 1] === statusMessage ? progress : [...progress, statusMessage]
                return { ...m, progress: nextProgress, status: 'streaming' }
              }),
            )
            return
          }

          if (evt.event === 'message_delta') {
            const delta =
              evt.data && typeof (evt.data as { delta?: string }).delta === 'string'
                ? (evt.data as { delta?: string }).delta
                : ''
            if (!delta) return
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== currentAssistantId) return m
                const shouldOverwritePlaceholder = isAssistantPlaceholderContent(m.content)
                return {
                  ...m,
                  content: shouldOverwritePlaceholder ? delta : `${m.content}${delta}`,
                  status: 'streaming',
                }
              }),
            )
            return
          }

          if (evt.event === 'messages') {
            const delta = typeof evt.data === 'string' ? evt.data : ''
            if (!delta) return
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== currentAssistantId) return m
                const shouldOverwritePlaceholder = isAssistantPlaceholderContent(m.content)
                return {
                  ...m,
                  content: shouldOverwritePlaceholder ? delta : `${m.content}${delta}`,
                  status: 'streaming',
                }
              }),
            )
            return
          }

          if (evt.event === 'sources') {
            const sources = evt.data && Array.isArray((evt.data as { sources?: unknown }).sources) ? (evt.data as { sources: SourceItem[] }).sources : undefined
            if (!sources?.length) return
            setMessages((prev) => prev.map((m) => (m.id === currentAssistantId ? { ...m, sources } : m)))
            return
          }

          if (evt.event === 'message_done') {
            streamFinished = true
            setMessages((prev) =>
              prev.map((m) => (m.id === currentAssistantId ? { ...m, status: 'done' } : m)),
            )
            streamingAssistantIdRef.current = null
            refreshConversations()
          }
        },
      })
    } catch (err) {
      if ((err as { name?: unknown } | null)?.name === 'AbortError') return
      streamFailed = true
      const message = err instanceof Error ? err.message : '请求失败'
      showToast({ type: 'error', title: '发送失败', message })

      const currentAssistantId = streamingAssistantIdRef.current
      if (currentAssistantId) {
        setMessages((prev) =>
          prev.map((m) => (m.id === currentAssistantId ? { ...m, status: 'error' } : m)),
        )
      }
    } finally {
      abortRef.current = null
      if (!controller.signal.aborted && !streamFinished && !streamFailed) {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId && m.role === 'assistant' ? { ...m, status: 'done' } : m)),
        )
        await refreshConversations()
      }
      if (streamingAssistantIdRef.current === assistantId) streamingAssistantIdRef.current = null
      setStreaming(false)
    }
  }

  function kbLabelForConversation(kbId: string | null) {
    if (!kbId) return '全局'
    const kb = knowledgeBases.find((k) => k.id === kbId)
    return kb?.name ?? '知识库'
  }

  function safeLinkHref(href: unknown): string | undefined {
    if (typeof href !== 'string') return undefined
    const trimmed = href.trim()
    if (!trimmed) return undefined
    if (trimmed.startsWith('#')) return trimmed
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('mailto:')) return trimmed
    return undefined
  }

  /** 提取 React children 中的纯文本（递归处理嵌套对象/数组，避免 String(obj) 产生 [object Object]） */
  function extractTextContent(node: unknown): string {
    if (typeof node === 'string') return node
    if (typeof node === 'number') return String(node)
    if (Array.isArray(node)) return node.map(extractTextContent).join('')
    if (node && typeof node === 'object') {
      const obj = node as any
      if (obj.props?.children !== undefined) return extractTextContent(obj.props.children)
      if (typeof obj.value === 'string') return obj.value
      if (Array.isArray(obj.children)) return obj.children.map(extractTextContent).join('')
    }
    return ''
  }

  /** 将 AI 返回内容中的 [数字] 引用标记转义，避免被 markdown 解析为快捷引用链接 */
  function escapeCitationRefs(md: string): string {
    if (!md) return md
    // 匹配 [数字] 或 [数字,数字] 格式，但排除 [text](url) 和 [text][ref]
    return md.replace(/(?<!!)\[(\d+(?:,\s*\d+)*)\](?!\s*[\(\[])/g, '\\[$1\\]')
  }

  function renderMessageContent(content: string) {
    return (
      <div className={styles.rich} dir="auto">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[[rehypeHighlight, { ignoreMissing: true }]]}
          components={{
            a: ({ href, children }: any) => {
              const safeHref = safeLinkHref(href)
              if (!safeHref) return <>{children}</>
              return (
                <a href={safeHref} target="_blank" rel="noreferrer">
                  {children}
                </a>
              )
            },
            code: ({ inline, className, children, ...props }: any) => {
              if (!inline) {
                const codeString = extractTextContent(children).replace(/\n$/, '')
                return (
                  <code className={className} dir="auto" {...props}>
                    {codeString}
                  </code>
                )
              }

              return (
                <code className={className} dir="auto" {...props}>
                  {children}
                </code>
              )
            },
          }}
        >
          {escapeCitationRefs(content)}
        </ReactMarkdown>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.body}>
        <aside className={styles.convPanel}>
          <div className={styles.convHeader}>
            <div className={styles.convTitle}>会话</div>
            <div className={styles.convActions}>
              <button 
                className={`${ui.btn} ${ui.btnGhost}`} 
                type="button" 
                onClick={refreshConversations} 
                disabled={streaming}>
                刷新
              </button>
              <button 
                className={`${ui.btn} ${ui.btnPrimary}`} 
                type="button" 
                onClick={clearConversation} 
                disabled={streaming}>
                新建
              </button>
            </div>
          </div>
          <div className={styles.convList}>
            {conversations.map((c) => (
              <div key={c.id} className={styles.convRow}>
                <button
                  className={[styles.convItem, conversationId === c.id ? styles.convItemActive : ''].filter(Boolean).join(' ')}
                  type="button"
                  onClick={() => openConversation(c.id)}
                  disabled={streaming}
                >
                  <div className={styles.convItemTop}>
                    <div className={styles.convItemTitle}>{c.title}</div>
                    <div className={styles.convItemTime}>{formatMonthDayTime(c.updated_at)}</div>
                  </div>
                  <div className={styles.convItemBottom}>
                    {/* <span className={styles.convItemTag}>{kbLabelForConversation(c.knowledge_base_id)}</span> */}
                    {loadingConversationId === c.id ? <span className={styles.convItemLoading}>加载中…</span> : null}
                  </div>
                </button>
                <button
                  className={styles.convDelete}
                  type="button"
                  onClick={() => onDeleteConversation(c.id)}
                  disabled={streaming}
                  aria-label="删除会话"
                >
                  <DeleteOutlined className={styles.convDeleteIcon} aria-hidden="true" />
                </button>
              </div>
            ))}
            {!conversations.length ? <div className={styles.convEmpty}>暂无会话</div> : null}
          </div>
        </aside>

        <section className={styles.thread}>
          <div className={styles.header}>
            <div>
              <h1 className={styles.title}>Agent 对话</h1>
            </div>
            {/* <div className={styles.headerActions}>
              <button 
                className={`${ui.btn} ${ui.btnGhost}`} 
                type="button" 
                onClick={clearConversation} 
                disabled={!messages.length && !conversationId}>
                清空
              </button>
            </div> */}
          </div>

          <div ref={listRef} className={styles.messages} aria-live="polite">
            {messages.length ? (
              <div className={styles.list}>
                {messages.map((m, idx) => {
                  const prev = idx > 0 ? messages[idx - 1] : undefined
                  const next = idx < messages.length - 1 ? messages[idx + 1] : undefined
                  const groupedPrev = prev?.role === m.role
                  const groupedNext = next?.role === m.role
                  const displayText =
                    m.content ||
                    (m.role === 'assistant' && m.status === 'streaming'
                      ? '正在处理，请稍候…'
                      : m.role === 'assistant' && m.status === 'error'
                        ? '发送失败，请重试。'
                        : '')
                  const copyText = m.content || displayText
                  const canCopy = Boolean(copyText.trim())
                  const showProgress =
                    m.role === 'assistant' &&
                    m.status === 'streaming' &&
                    Array.isArray(m.progress) &&
                    m.progress.length > 0
                  const currentProgressIndex = showProgress ? (m.progress?.length ?? 1) - 1 : -1

                  return (
                    <div
                      key={m.id}
                      className={[
                        styles.row,
                        m.role === 'user' ? styles.rowUser : styles.rowAssistant,
                        groupedPrev ? styles.rowGrouped : '',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                    >
                      <div className={styles.rowInner}>
                        {m.role === 'assistant' ? (
                          <div className={[styles.avatar, styles.avatarAssistant].join(' ')} aria-hidden="true">
                            AI
                          </div>
                        ) : null}
                        <div className={styles.bubbleWrap}>
                          <div className={styles.msgActions}>
                            <button
                              className={styles.msgCopyBtn}
                              type="button"
                              onClick={() => copyMessage(copyText)}
                              disabled={!canCopy}
                              aria-label="复制消息"
                              title="复制"
                            >
                              <CopyOutlined className={styles.msgCopyIcon} aria-hidden="true" />
                            </button>
                          </div>
                          {showProgress ? (
                            <div className={styles.progressPanel}>
                              <div className={styles.progressPanelHeader}>
                                <div className={styles.progressPanelSummary}>
                                  <span className={styles.progressPanelTitle}>处理流程</span>
                                  <span className={styles.progressPanelStatus}>
                                    执行中
                                  </span>
                                  <span className={styles.progressPanelCount}>
                                    {m.progress?.length ?? 0} 个节点
                                  </span>
                                </div>
                              </div>
                              <div
                                ref={(node) => {
                                  progressViewportRefs.current[m.id] = node
                                }}
                                className={styles.progressViewport}
                              >
                                <div className={styles.progressTimeline} role="list" aria-label="AI 处理节点">
                                  {m.progress?.map((item, progressIdx) => {
                                    const isCurrent = progressIdx === currentProgressIndex && m.status === 'streaming'
                                    const isDone = progressIdx < currentProgressIndex || m.status === 'done'
                                    return (
                                      <div
                                        key={`${m.id}_${progressIdx}`}
                                        className={[
                                          styles.progressNode,
                                          isCurrent ? styles.progressNodeActive : '',
                                          isDone ? styles.progressNodeDone : '',
                                        ]
                                          .filter(Boolean)
                                          .join(' ')}
                                        role="listitem"
                                      >
                                        <div className={styles.progressDot} aria-hidden="true" />
                                        <div className={styles.progressContent}>
                                          <div className={styles.progressLabel}>{item}</div>
                                          <div className={styles.progressMeta}>
                                            {isCurrent ? '当前节点' : isDone ? '已完成' : '待处理'}
                                          </div>
                                        </div>
                                      </div>
                                    )
                                  })}
                                </div>
                              </div>
                            </div>
                          ) : null}
                          <div
                            className={[
                              styles.bubble,
                              m.role === 'user' ? styles.bubbleUser : styles.bubbleAssistant,
                              groupedPrev ? styles.bubbleJoinedTop : '',
                              groupedNext ? styles.bubbleJoinedBottom : '',
                              m.status === 'streaming' ? styles.bubbleStreaming : '',
                              m.status === 'error' ? styles.bubbleError : '',
                            ]
                              .filter(Boolean)
                              .join(' ')}
                          >
                            <div className={styles.text}>{renderMessageContent(displayText)}</div>
                            {m.role === 'assistant' && uniqueSources(m.sources).length ? (
                              <div className={styles.sources}>
                                <div className={styles.sourcesTitle}>来源</div>
                                <div className={styles.sourcesList}>
                                  {uniqueSources(m.sources).map((s) => {
                                    const displayName = fileBaseName(s.original_filename)
                                    const fullName = displayName || s.original_filename
                                    const { h, s: sat, l } = sourceColor(s.original_filename)
                                    const sourceStyle = { '--source-h': h, '--source-s': `${sat}%`, '--source-l': `${l}%` } as CSSProperties
                                    return (
                                      <div
                                        key={`${s.document_id}_${s.original_filename}`}
                                        className={styles.sourceItem}
                                        title={fullName}
                                        style={sourceStyle}
                                      >
                                        <div className={styles.sourceName}>{fullName}</div>
                                      </div>
                                    )
                                  })}
                                </div>
                              </div>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className={styles.empty}>
                <div className={styles.emptyTitle}>开始一段对话</div>
                <div className={styles.emptyHint}>输入问题后回车发送（Shift+Enter 换行）。</div>
              </div>
            )}
          </div>

          <div className={styles.composerBar}>
            <AgentComposer
              value={draft}
              onChange={setDraft}
              onSend={send}
              sending={streaming}
              onStop={stopStreaming}
              disabled={!draft.trim()}
            />
            <div className={styles.kbBar}>
              <div className={styles.scopeLeft}>
                <div className={styles.kbLabel}>检索范围</div>
                <div className={styles.scopeTabs} role="tablist" aria-label="检索范围">
                  <button
                    className={[styles.scopeBtn, scope === 'kb' ? styles.scopeBtnActive : ''].filter(Boolean).join(' ')}
                    type="button"
                    onClick={() => setScope('kb')}
                    disabled={streaming}
                  >
                    当前知识库
                  </button>
                  <button
                    className={[styles.scopeBtn, scope === 'global' ? styles.scopeBtnActive : ''].filter(Boolean).join(' ')}
                    type="button"
                    onClick={() => setScope('global')}
                    disabled={streaming}
                  >
                    全局搜索
                  </button>
                </div>
              </div>

              {scope === 'kb' ? (
                <div className={styles.scopeRight}>
                  <div className={styles.kbLabel}>当前知识库</div>
                  <select
                    className={styles.kbSelect}
                    value={knowledgeBaseId}
                    onChange={(e) => setKnowledgeBaseId(e.target.value)}
                    disabled={streaming || !knowledgeBases.length}
                  >
                    {knowledgeBases.map((kb) => (
                      <option key={kb.id} value={kb.id}>
                        {kb.name}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
