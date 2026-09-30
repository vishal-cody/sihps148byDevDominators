import React, { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '@/services/api'

interface User {
  id: string
  username: string
  email: string
  role: string
  full_name?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem('jocky_token')
    const storedUser = localStorage.getItem('jocky_user')
    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  const login = async (username: string, password: string) => {
    const res = await authAPI.login(username, password)
    const { access_token, user_id, username: uname, role } = res.data
    setToken(access_token)
    const userData = { id: user_id, username: uname, email: '', role }
    setUser(userData)
    localStorage.setItem('jocky_token', access_token)
    localStorage.setItem('jocky_user', JSON.stringify(userData))
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('jocky_token')
    localStorage.removeItem('jocky_user')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
