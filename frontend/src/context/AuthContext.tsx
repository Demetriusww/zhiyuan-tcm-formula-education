import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type FC,
  type ReactNode,
} from 'react'

interface UserInfo {
  id: number
  username: string
  nickname: string
  email?: string
  role: string
}

interface AuthCtx {
  user: UserInfo | null
  initializing: boolean
  login: (username: string, password: string) => Promise<UserInfo>
  register: (data: { username: string; password: string; email?: string; nickname?: string }) => Promise<UserInfo>
  logout: () => void
}

const AuthContext = createContext<AuthCtx>(null as any)
const DEMO_USER_KEY = 'zhiyuan-demo-user'

const loadDemoUser = (): UserInfo | null => {
  try {
    const value = localStorage.getItem(DEMO_USER_KEY)
    return value ? (JSON.parse(value) as UserInfo) : null
  } catch {
    return null
  }
}

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [initializing, setInitializing] = useState(true)

  useEffect(() => {
    setUser(loadDemoUser())
    setInitializing(false)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    if (!username.trim() || !password.trim()) {
      throw new Error('请输入用户名和密码')
    }
    const nextUser: UserInfo = {
      id: username === 'admin' ? 1 : Date.now(),
      username: username.trim(),
      nickname: username === 'admin' ? '平台管理员' : username.trim(),
      email: `${username.trim()}@demo.zhiyuan`,
      role: username === 'admin' ? 'admin' : 'user',
    }
    localStorage.setItem(DEMO_USER_KEY, JSON.stringify(nextUser))
    setUser(nextUser)
    return nextUser
  }, [])

  const register = useCallback(async (data: any) => {
    if (!data.username?.trim() || !data.password?.trim()) {
      throw new Error('请输入用户名和密码')
    }
    const nextUser: UserInfo = {
      id: Date.now(),
      username: data.username.trim(),
      nickname: data.nickname?.trim() || data.username.trim(),
      email: data.email,
      role: 'user',
    }
    localStorage.setItem(DEMO_USER_KEY, JSON.stringify(nextUser))
    setUser(nextUser)
    return nextUser
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(DEMO_USER_KEY)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, initializing, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
