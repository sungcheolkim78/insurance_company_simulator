import { beforeEach, describe, expect, it } from 'vitest'
import { DEFAULT_LAYOUT, PANEL_KEYS, loadLayout, resetLayout, saveLayout } from './dashboardLayout'

const STORAGE_KEY = 'dashboard-layout-v1'

beforeEach(() => {
  localStorage.clear()
})

describe('PANEL_KEYS / DEFAULT_LAYOUT', () => {
  it('기본 레이아웃은 6개 패널 키를 정확히 한 번씩만 포함한다', () => {
    const flat = DEFAULT_LAYOUT.flat()
    expect(flat.sort()).toEqual([...PANEL_KEYS].sort())
  })

  it('기본 레이아웃은 3개 컬럼으로 구성된다', () => {
    expect(DEFAULT_LAYOUT).toHaveLength(3)
  })
})

describe('loadLayout', () => {
  it('저장된 값이 없으면 기본 레이아웃을 반환한다', () => {
    expect(loadLayout()).toEqual(DEFAULT_LAYOUT)
  })

  it('저장된 JSON이 깨져 있으면 기본 레이아웃으로 폴백한다', () => {
    localStorage.setItem(STORAGE_KEY, 'not-json{')
    expect(loadLayout()).toEqual(DEFAULT_LAYOUT)
  })

  it('columns 필드가 없거나 배열이 아니면 기본 레이아웃으로 폴백한다', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ foo: 'bar' }))
    expect(loadLayout()).toEqual(DEFAULT_LAYOUT)
  })

  it('컬럼 개수가 3이 아니면 기본 레이아웃으로 완전히 폴백한다', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ columns: [['kpi'], ['charts']] }))
    expect(loadLayout()).toEqual(DEFAULT_LAYOUT)
  })

  it('알 수 없는 패널 키는 무시하고 제거한다', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ columns: [['kpi', 'bogus', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']] }),
    )
    expect(loadLayout()).toEqual([['kpi', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']])
  })

  it('레지스트리에는 있지만 저장된 값에 없는 키는 컬럼1 끝에 자동으로 추가한다', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ columns: [['kpi'], ['charts'], ['financials', 'decision', 'turncontrol']] }),
    )
    expect(loadLayout()).toEqual([['kpi', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']])
  })

  it('중복된 키는 처음 등장한 위치만 남기고 제거한다', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ columns: [['kpi', 'kpi', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']] }),
    )
    expect(loadLayout()).toEqual([['kpi', 'monitoring'], ['charts'], ['financials', 'decision', 'turncontrol']])
  })

  it('정상적인 커스텀 레이아웃은 그대로 반환한다', () => {
    const custom = [['monitoring'], ['kpi', 'charts'], ['financials', 'decision', 'turncontrol']]
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ columns: custom }))
    expect(loadLayout()).toEqual(custom)
  })
})

describe('saveLayout', () => {
  it('전달받은 columns를 그대로 localStorage에 JSON으로 저장한다', () => {
    const custom = [['monitoring'], ['kpi', 'charts'], ['financials', 'decision', 'turncontrol']]
    saveLayout(custom)
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).toEqual({ columns: custom })
  })
})

describe('resetLayout', () => {
  it('저장된 값을 지우고 기본 레이아웃을 반환한다', () => {
    saveLayout([['monitoring'], ['kpi', 'charts'], ['financials', 'decision', 'turncontrol']])
    const result = resetLayout()
    expect(result).toEqual(DEFAULT_LAYOUT)
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
  })
})
