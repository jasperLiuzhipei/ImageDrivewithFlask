export const INACTIVITY_LIMIT_MINUTES = Number(import.meta.env.VITE_INACTIVITY_LIMIT_MINUTES || 30)
declare const __APP_VERSION__: string
declare const __BUILD_TIME__: string

function getNow() { return Date.now() }

function get(key: string): string { try { return localStorage.getItem(key) || '' } catch { return '' } }
function set(key: string, val: string) { try { localStorage.setItem(key, val) } catch {} }
function clearTokenAndRedirect() {
  try { localStorage.removeItem('token') } catch {}
  const p = window.location.pathname
  if (p !== '/login' && p !== '/register') window.location.replace('/login')
}

export async function enforceSessionOnLoad() {
  const token = get('token')
  if (!token) return

  // 初始化活跃时间：首次加载没有 last_active 时不应直接登出
  const now = getNow()
  const existing = get('last_active')
  if (!existing) set('last_active', String(now))

  // 前端构建变化：若检测到新构建，则强制重登录
  const prevBuild = get('frontend_build')
  const currBuild = typeof __BUILD_TIME__ === 'string' ? __BUILD_TIME__ : ''
  if (currBuild && prevBuild && prevBuild !== currBuild) {
    clearTokenAndRedirect(); set('frontend_build', currBuild); return
  }
  if (currBuild && !prevBuild) set('frontend_build', currBuild)

  // 后端版本变化：通过健康接口比对 app_version
  try {
    const r = await fetch('/api/v1/health')
    if (r.ok) {
      const j = await r.json()
      const prev = get('backend_version')
      const curr = String(j?.data?.app_version || '')
      if (curr) {
        if (prev && prev !== curr) { clearTokenAndRedirect(); set('backend_version', curr); return }
        if (!prev) set('backend_version', curr)
      }
    }
  } catch {}

  // 长期不活动：超过阈值则重登录
  const lastStr = get('last_active')
  const last = Number(lastStr || now)
  const limitMs = INACTIVITY_LIMIT_MINUTES * 60 * 1000
  if (!last || getNow() - last > limitMs) {
    clearTokenAndRedirect(); return
  }
}

export function bindActivityListeners() {
  const mark = () => set('last_active', String(getNow()))
  window.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') mark() })
  window.addEventListener('focus', mark)
  window.addEventListener('click', mark)
  window.addEventListener('keydown', mark)
}
