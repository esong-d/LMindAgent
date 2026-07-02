export type DateInput = string | number | Date | null | undefined


export function toDate(input: DateInput) {
  if (!input) return null
  const date = input instanceof Date ? input : new Date(input)
  if (Number.isNaN(date.getTime())) return null
  return date
}

export function formatDateTime(
  input: DateInput,
  options: Intl.DateTimeFormatOptions,
  locale: string = 'zh-CN',
) {
  const date = toDate(input)
  if (!date) return ''
  return new Intl.DateTimeFormat(locale, options).format(date)
}

// 03/03 14:00
export function formatMonthDayTime(input: DateInput, locale: string = 'zh-CN') {
  return formatDateTime(
    input, 
    { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' },
    locale)
}

// 2026/03/03 14:00:03
export function formatMonthDayTimeWithSecond(input: DateInput, locale: string = 'zh-CN') {
  return formatDateTime(
    input, 
    { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' },
    locale)
}
