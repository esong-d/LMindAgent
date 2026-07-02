import { useCallback, useEffect, useMemo, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useToast } from '../../components/Toast/ToastProvider'
import { getOverview } from '../../features/overview/api'
import type { OverviewData, OverviewDocumentItem } from '../../features/overview/types'
import { ApiError } from '../../lib/apiClient'
import { formatMonthDayTime } from '../../lib/dateTime'
import { navItems } from '../../router/nav'
import ui from '../../styles/ui.module.css'
import styles from './DashboardPage.module.css'

function formatCount(value: number | undefined) {
  return new Intl.NumberFormat('zh-CN').format(value ?? 0)
}

function formatFileSize(bytes: number | undefined) {
  const size = Number(bytes ?? 0)
  if (!Number.isFinite(size) || size <= 0) return '0 B'
  if (size < 1024) return `${size} B`

  const units = ['KB', 'MB', 'GB', 'TB']
  let current = size / 1024
  let unitIndex = 0

  while (current >= 1024 && unitIndex < units.length - 1) {
    current /= 1024
    unitIndex += 1
  }

  const digits = current >= 100 ? 0 : current >= 10 ? 1 : 2
  return `${current.toFixed(digits)} ${units[unitIndex]}`
}

function statusText(status: string) {
  if (status === 'completed') return '已完成'
  if (status === 'embedding') return '向量化中'
  if (status === 'chunking') return '分段中'
  if (status === 'parsing') return '解析中'
  if (status === 'failed') return '失败'
  if (status === 'pending') return '排队中'
  return status || '未知'
}

function statusBadgeClass(status: string) {
  if (status === 'completed') return `${ui.badge} ${ui.badgeSuccess}`
  if (status === 'embedding' || status === 'chunking' || status === 'parsing' || status === 'pending') {
    return `${ui.badge} ${ui.badgeWarn}`
  }
  if (status === 'failed') return `${ui.badge} ${styles.badgeDanger}`
  return `${ui.badge} ${styles.badgeMuted}`
}

function docMetaLabel(doc: OverviewDocumentItem) {
  const time = doc.processing_completed_at ?? doc.updated_at ?? doc.created_at
  const prefix = doc.status === 'completed' ? '完成于' : '更新于'
  const timeLabel = formatMonthDayTime(time) || '刚刚'
  return `${formatFileSize(doc.file_size)} · ${prefix} ${timeLabel}`
}

export function DashboardPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadOverview = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const data = await getOverview()
      setOverview(data)
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : err instanceof Error ? err.message : '加载首页概览失败'
      setError(message)
      showToast({
        type: 'error',
        title: '加载失败',
        message,
      })
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    void loadOverview()
  }, [loadOverview])

  const recentDocs = overview?.recent.doc ?? []
  const recentNotes = overview?.recent.note ?? []

  const statCards = useMemo(
    () => [
      {
        label: '文档总数',
        value: formatCount(overview?.document_cnt),
        hint: '已进入知识库的原始资料',
      },
      {
        label: '分段总数',
        value: formatCount(overview?.chunk_cnt),
        hint: '可用于召回检索的切片',
      },
      {
        label: '笔记总数',
        value: formatCount(overview?.note_cnt),
        hint: '沉淀的人工总结与记录',
      },
      {
        label: '最近动态',
        value: formatCount(recentDocs.length + recentNotes.length),
        hint: `最近新增 ${recentDocs.length} 篇文档和 ${recentNotes.length} 条笔记`,
      },
    ],
    [overview, recentDocs.length, recentNotes.length],
  )

  const completedDocs = recentDocs.filter((item) => item.status === 'completed').length

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroMain}>
          <span className={styles.heroEyebrow}>Knowledge Overview</span>
          <h1 className={styles.title}>知识库总览</h1>
          <p className={styles.subtitle}>
            把核心指标、最近上传文档和最近沉淀笔记集中在一个入口，方便你快速判断知识库是否可用，以及下一步该从哪里继续工作。
          </p>
          <div className={styles.heroActions}>
            <button className={`${ui.btn} ${ui.btnPrimary}`} type="button" onClick={() => navigate('/chat')}>
              开始提问
            </button>
            <button
              className={`${ui.btn} ${ui.btnGhost}`}
              type="button"
              onClick={() => navigate('/documents?action=upload')}
            >
              上传文档
            </button>
          </div>
        </div>

        <div className={styles.heroSide}>
          <div className={styles.heroPanel}>
            <div className={styles.heroPanelTop}>
              <span className={`${ui.badge} ${ui.badgeSuccess}`}>实时概览</span>
              <button className={`${ui.btn} ${ui.btnGhost}`} type="button" onClick={() => void loadOverview()}>
                刷新数据
              </button>
            </div>
            <div className={styles.heroPanelValue}>{loading ? '...' : formatCount(overview?.document_cnt)}</div>
            <div className={styles.heroPanelTitle}>当前知识库文档规模</div>
            <div className={styles.heroPanelMeta}>
              最近文档 {formatCount(recentDocs.length)} 篇，已完成处理 {formatCount(completedDocs)} 篇
            </div>
          </div>
        </div>
      </section>

      <nav className={styles.tabs} aria-label="功能快捷入口">
        {navItems.map((item) => (
          <NavLink
            key={item.key}
            className={({ isActive }) =>
              [styles.tab, isActive ? styles.tabActive : ''].filter(Boolean).join(' ')
            }
            to={item.path}
            end={item.end}
          >
            <span className={styles.tabLabel}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.layout}>
        <div className={styles.mainColumn}>
          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div>
                <div className={styles.cardTitle}>核心指标</div>
                <div className={styles.cardDesc}>首页顶部直接展示系统关键数据，减少频繁切页查看成本。</div>
              </div>
              <span className={`${ui.badge} ${loading ? styles.badgeMuted : ui.badgeSuccess}`}>
                {loading ? '加载中' : '已同步'}
              </span>
            </div>

            {error ? (
              <div className={styles.noticeRow}>
                <div className={styles.noticeText}>{error}</div>
                <button className={`${ui.btn} ${ui.btnGhost}`} type="button" onClick={() => void loadOverview()}>
                  重试
                </button>
              </div>
            ) : null}

            <div className={styles.metricGrid}>
              {statCards.map((item) => (
                <div key={item.label} className={styles.metricCard}>
                  <div className={styles.metricLabel}>{item.label}</div>
                  <div className={styles.metricValue}>{loading ? '...' : item.value}</div>
                  <div className={styles.metricHint}>{item.hint}</div>
                </div>
              ))}
            </div>
          </section>

          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div>
                <div className={styles.cardTitle}>最近文档</div>
                <div className={styles.cardDesc}>按最新处理结果展示文档状态，优先暴露可检索和异常项目。</div>
              </div>
              <button className={`${ui.btn} ${ui.btnGhost}`} type="button" onClick={() => navigate('/documents')}>
                查看全部
              </button>
            </div>

            {recentDocs.length ? (
              <div className={styles.list}>
                {recentDocs.map((doc) => (
                  <div key={doc.id} className={styles.listRow}>
                    <div className={styles.listMain}>
                      <div className={styles.listTitle}>{doc.original_filename || doc.filename}</div>
                      <div className={styles.listMeta}>{docMetaLabel(doc)}</div>
                    </div>
                    <span className={statusBadgeClass(doc.status)}>{statusText(doc.status)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.emptyState}>
                {loading ? '正在加载最近文档...' : '还没有文档记录，先上传一些资料吧。'}
              </div>
            )}
          </section>
        </div>

        <aside className={styles.sideColumn}>
          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div>
                <div className={styles.cardTitle}>最近笔记</div>
                <div className={styles.cardDesc}>右侧单独收纳笔记流，方便和文档动态并行查看。</div>
              </div>
              <button className={`${ui.btn} ${ui.btnGhost}`} type="button" onClick={() => navigate('/notes')}>
                前往笔记
              </button>
            </div>

            {recentNotes.length ? (
              <div className={styles.noteList}>
                {recentNotes.map((note) => (
                  <div key={note.id} className={styles.noteCard}>
                    <div className={styles.noteTitle}>{note.title}</div>
                    <div className={styles.noteMeta}>{formatMonthDayTime(note.created_at) || '刚刚创建'}</div>
                    <div className={styles.tagRow}>
                      {(note.tags_json ?? []).length ? (
                        note.tags_json.map((tag) => (
                          <span key={`${note.id}_${tag}`} className={styles.tag}>
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span className={styles.tagMuted}>未设置标签</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.emptyState}>{loading ? '正在加载最近笔记...' : '暂无笔记内容。'}</div>
            )}
          </section>

          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div>
                <div className={styles.cardTitle}>快捷操作</div>
                <div className={styles.cardDesc}>把首页变成工作台入口，而不是只放静态统计。</div>
              </div>
            </div>

            <div className={styles.actionList}>
              <button className={styles.actionItem} type="button" onClick={() => navigate('/knowledge?action=create')}>
                <span className={styles.actionTitle}>新建知识库</span>
                <span className={styles.actionMeta}>创建新的资料空间并开始归档</span>
              </button>
              <button className={styles.actionItem} type="button" onClick={() => navigate('/documents?action=upload')}>
                <span className={styles.actionTitle}>上传资料</span>
                <span className={styles.actionMeta}>导入 PDF、TXT 或其他原始文件</span>
              </button>
              <button className={styles.actionItem} type="button" onClick={() => navigate('/chat')}>
                <span className={styles.actionTitle}>进入问答</span>
                <span className={styles.actionMeta}>基于知识库内容发起新的问题</span>
              </button>
            </div>
          </section>
        </aside>
      </div>
    </>
  )
}
