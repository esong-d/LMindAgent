export type SourceColor = { h: number; s: number; l: number }

export function fileBaseName(input: string) {
  const v = (input || '').trim()
  if (!v) return ''
  const normalized = v.replaceAll('\\', '/')
  const parts = normalized.split('/')
  return parts[parts.length - 1] || v
}

export function stableHash(input: string) {
  const value = (input || '').trim()
  if (!value) return 0
  let hash = 0
  for (let i = 0; i < value.length; i++) hash = (hash * 31 + value.charCodeAt(i)) | 0
  return hash >>> 0
}

export function fileExt(input: string) {
  const base = fileBaseName(input)
  const idx = base.lastIndexOf('.')
  if (idx <= 0 || idx === base.length - 1) return ''
  return base.slice(idx + 1).toLowerCase()
}

export function sourceColor(input: string): SourceColor {
  const ext = fileExt(input)
  const byExt: Record<string, SourceColor> = {
    pdf: { h: 2, s: 78, l: 46 },
    doc: { h: 212, s: 72, l: 43 },
    docx: { h: 212, s: 72, l: 43 },
    xls: { h: 140, s: 58, l: 38 },
    xlsx: { h: 140, s: 58, l: 38 },
    ppt: { h: 24, s: 76, l: 44 },
    pptx: { h: 24, s: 76, l: 44 },
    md: { h: 265, s: 62, l: 50 },
    markdown: { h: 265, s: 62, l: 50 },
    txt: { h: 220, s: 8, l: 45 },
    log: { h: 220, s: 8, l: 45 },
    json: { h: 45, s: 82, l: 45 },
    yaml: { h: 45, s: 82, l: 45 },
    yml: { h: 45, s: 82, l: 45 },
    csv: { h: 168, s: 54, l: 40 },
    tsv: { h: 168, s: 54, l: 40 },
    png: { h: 195, s: 70, l: 42 },
    jpg: { h: 195, s: 70, l: 42 },
    jpeg: { h: 195, s: 70, l: 42 },
    webp: { h: 195, s: 70, l: 42 },
  }

  const picked = byExt[ext]
  if (picked) return picked

  const palette = [210, 190, 165, 140, 115, 45, 28, 2, 265]
  const h = palette[stableHash(input) % palette.length]
  return { h, s: 68, l: 44 }
}
