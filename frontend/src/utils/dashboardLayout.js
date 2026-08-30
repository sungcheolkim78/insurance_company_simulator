export const PANEL_KEYS = ['kpi', 'monitoring', 'charts', 'financials', 'decision', 'turncontrol']

export const DEFAULT_LAYOUT = [
  ['kpi', 'monitoring'],
  ['charts'],
  ['financials', 'decision', 'turncontrol'],
]

const STORAGE_KEY = 'dashboard-layout-v1'

function cloneDefaultLayout() {
  return DEFAULT_LAYOUT.map((column) => [...column])
}

export function loadLayout() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return cloneDefaultLayout()

  let parsed
  try {
    parsed = JSON.parse(raw)
  } catch (err) {
    return cloneDefaultLayout()
  }

  if (!parsed || !Array.isArray(parsed.columns) || parsed.columns.length !== 3) {
    return cloneDefaultLayout()
  }

  const seen = new Set()
  const columns = parsed.columns.map((column) => {
    if (!Array.isArray(column)) return []
    const deduped = []
    for (const key of column) {
      if (!PANEL_KEYS.includes(key)) continue
      if (seen.has(key)) continue
      seen.add(key)
      deduped.push(key)
    }
    return deduped
  })

  const missingKeys = PANEL_KEYS.filter((key) => !seen.has(key))
  columns[0] = [...columns[0], ...missingKeys]

  return columns
}

export function saveLayout(columns) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ columns }))
}

export function resetLayout() {
  localStorage.removeItem(STORAGE_KEY)
  return cloneDefaultLayout()
}
