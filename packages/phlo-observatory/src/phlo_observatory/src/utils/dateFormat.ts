export type DateFormatMode = 'iso' | 'local'

export function formatDate(date: Date, mode: DateFormatMode): string {
  if (mode === 'iso') {
    return date.toISOString().slice(0, 10)
  }
  return date.toLocaleDateString()
}

export function formatDateTime(date: Date, mode: DateFormatMode): string {
  if (mode === 'iso') {
    return date.toISOString()
  }
  return date.toLocaleString()
}
