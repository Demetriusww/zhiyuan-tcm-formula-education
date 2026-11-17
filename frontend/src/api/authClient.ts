// 用户认证、资源收藏与本地登录态管理
const TOKEN_KEY = 'zhiyuan_access_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t: string) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

// 统一带鉴权 fetch
async function authFetch(path: string, options: RequestInit = {}, isAuth = true) {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers as any),
  }
  if (isAuth) {
    const t = getToken()
    if (t) headers['Authorization'] = `Bearer ${t}`
  }
  const res = await fetch(path, { ...options, headers })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(body.message || body.detail?.message || body.detail || `请求失败(${res.status})`)
    ;(err as any).status = res.status
    ;(err as any).code = body.code
    throw err
  }
  if (body.code && body.code !== 'SUCCESS') {
    const err = new Error(body.message || '请求失败')
    ;(err as any).status = res.status
    ;(err as any).code = body.code
    throw err
  }
  return body
}

export const api = {
  register: (data: { username: string; password: string; email?: string; nickname?: string }) =>
    authFetch('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(data) }, false),
  login: (data: { username: string; password: string }) =>
    authFetch('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(data) }, false),
  me: () => authFetch('/api/v1/auth/me'),
  favoriteIds: () => authFetch('/api/v1/favorites/ids'),
  favoriteAdd: (resourceId: number) => authFetch(`/api/v1/favorites/${resourceId}`, { method: 'POST' }),
  favoriteRemove: (resourceId: number) => authFetch(`/api/v1/favorites/${resourceId}`, { method: 'DELETE' }),
  favoritesList: () => authFetch('/api/v1/favorites'),
}

// 供页面在收藏或同步学习记录前唤起登录弹窗
let openLoginFn: (() => void) | null = null
export const authUI = {
  setOpenLogin: (fn: () => void) => { openLoginFn = fn },
  openLogin: () => { openLoginFn?.() },
}
