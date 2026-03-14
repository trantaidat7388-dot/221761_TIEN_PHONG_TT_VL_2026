// AuthContext.jsx - Quản lý trạng thái xác thực JWT toàn ứng dụng

import { createContext, useContext, useEffect, useState } from 'react'
import { API_BASE_URL } from '../config/apiConfig'

const TOKEN_KEY = 'word2latex_token'
const USER_KEY = 'word2latex_user'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
    const [token, setTokenState] = useState(() => localStorage.getItem(TOKEN_KEY))
    const [user, setUser] = useState(() => {
        try {
            const raw = localStorage.getItem(USER_KEY)
            return raw ? JSON.parse(raw) : null
        } catch {
            return null
        }
    })
    const [loading, setLoading] = useState(true)

    const saveSession = (accessToken, userData) => {
        localStorage.setItem(TOKEN_KEY, accessToken)
        localStorage.setItem(USER_KEY, JSON.stringify(userData))
        setTokenState(accessToken)
        setUser(userData)
    }

    const clearSession = () => {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setTokenState(null)
        setUser(null)
    }

    // Validate token on mount by calling /api/auth/me
    useEffect(() => {
        const validateToken = async () => {
            const savedToken = localStorage.getItem(TOKEN_KEY)
            if (!savedToken) {
                setLoading(false)
                return
            }
            try {
                const controller = new AbortController()
                const timeoutId = setTimeout(() => controller.abort(), 5000)
                const resp = await fetch(`${API_BASE_URL}/api/auth/me`, {
                    headers: { 'Authorization': `Bearer ${savedToken}` },
                    signal: controller.signal
                })
                clearTimeout(timeoutId)
                if (resp.ok) {
                    const userData = await resp.json()
                    saveSession(savedToken, userData)
                } else {
                    clearSession()
                }
            } catch {
                // Server unreachable - keep local state
            }
            setLoading(false)
        }
        validateToken()
    }, [])

    const login = async (email, password) => {
        const resp = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        })
        const data = await resp.json()
        if (!resp.ok) throw new Error(data.detail || 'Đăng nhập thất bại')
        saveSession(data.access_token, data.user)
        return data.user
    }

    const register = async (username, email, password) => {
        const resp = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        })
        const data = await resp.json()
        if (!resp.ok) throw new Error(data.detail || 'Đăng ký thất bại')
        saveSession(data.access_token, data.user)
        return data.user
    }

    const logout = () => {
        clearSession()
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        )
    }

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth phải được dùng bên trong AuthProvider')
    return ctx
}

export default AuthContext
