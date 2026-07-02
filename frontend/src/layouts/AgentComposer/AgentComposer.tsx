import styles from './AgentComposer.module.css'
import ui from '../../styles/ui.module.css'

type AgentComposerProps = {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  sending?: boolean
  onStop?: () => void
  disabled?: boolean
}

export function AgentComposer({ value, onChange, onSend, sending = false, onStop, disabled = false }: AgentComposerProps) {
  return (
    <div className={styles.inner}>
      <textarea
        className={styles.input}
        placeholder="向知识库提问"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key !== 'Enter') return
          if (e.shiftKey || e.altKey || e.metaKey || e.ctrlKey) return
          e.preventDefault()
          onSend()
        }}
        rows={1}
      />
      {sending ? (
        <button className={`${ui.btn} ${ui.btnGhost}`} type="button" onClick={onStop} disabled={!onStop}>
          停止
        </button>
      ) : (
        <button className={`${ui.btn} ${ui.btnPrimary}`} type="button" onClick={onSend} disabled={disabled}>
          发送
        </button>
      )}
    </div>
  )
}
