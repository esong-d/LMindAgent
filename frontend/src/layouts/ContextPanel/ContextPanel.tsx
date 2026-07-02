import styles from './ContextPanel.module.css'

export function ContextPanel() {
  return (
    <aside className={styles.panel}>
      <div className={styles.header}>
        <div className={styles.title}>来源与步骤</div>
      </div>

      <section className={styles.card}>
        <div className={styles.cardTitle}>Sources</div>
        <div className={styles.list}>
          <div>
            <div className={styles.itemTitle}>RAG 产品调研.pdf · p12</div>
            <div className={styles.itemMeta}>用于回答本次问题，上下文引用较多。</div>
          </div>
          <div>
            <div className={styles.itemTitle}>用户访谈.md · #03</div>
            <div className={styles.itemMeta}>用户痛点与需求在此处有补充信息。</div>
          </div>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardTitle}>Steps</div>
        <div className={styles.steps}>
          <div>
            <div className={styles.stepTitle}>1. 检索知识库</div>
            <div className={styles.stepMeta}>找到 5 个相关片段，保留 3 个高相关。</div>
          </div>
          <div>
            <div className={styles.stepTitle}>2. 组合答案</div>
            <div className={styles.stepMeta}>合并重要观点，并补上可追溯引用。</div>
          </div>
        </div>
      </section>
    </aside>
  )
}
