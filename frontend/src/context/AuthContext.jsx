// AuthContext.jsx - Quản lý trạng thái xác thực JWT toàn ứng dụng

import { createContext, useContext, useEffect, useState } from 'react'
import { DIA_CHI_API_GOC } from '../config/apiConfig'

const TOKEN_KEY = 'word2latex_token'
const USER_KEY = 'word2latex_user'

const NguCanhXacThuc = createContext(null)

export const BoBaoBocXacThuc = ({ children }) => {
    const [token, datToken] = useState(() => localStorage.getItem(TOKEN_KEY))
    const [nguoiDung, datNguoiDung] = useState(() => {
        try {
            const raw = localStorage.getItem(USER_KEY)
            return raw ? JSON.parse(raw) : null
        } catch {
            return null
        }
    })
    const [dangTai, datDangTai] = useState(true)

    const luuPhien = (accessToken, duLieuNguoiDung) => {
        localStorage.setItem(TOKEN_KEY, accessToken)
        localStorage.setItem(USER_KEY, JSON.stringify(duLieuNguoiDung))
        datToken(accessToken)
        datNguoiDung(duLieuNguoiDung)
    }

    const xoaPhien = () => {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        datToken(null)
        datNguoiDung(null)
    }

    // Validate token on mount by calling /api/auth/me
    useEffect(() => {
        const xacThucTokenDaLuu = async () => {
            const tokenDaLuu = localStorage.getItem(TOKEN_KEY)
            if (!tokenDaLuu) {
                datDangTai(false)
                return
            }
            try {
                const controller = new AbortController()
                const timeoutId = setTimeout(() => controller.abort(), 5000)
                const resp = await fetch(`${DIA_CHI_API_GOC}/api/auth/me`, {
                    headers: { 'Authorization': `Bearer ${tokenDaLuu}` },
                    signal: controller.signal
                })
                clearTimeout(timeoutId)
                if (resp.ok) {
                    const duLieuNguoiDung = await resp.json()
                    luuPhien(tokenDaLuu, duLieuNguoiDung)
                } else {
                    xoaPhien()
                }
            } catch {
                // Server unreachable - keep local state
            }
            datDangTai(false)
        }
        xacThucTokenDaLuu()
    }, [])

    const dangNhap = async (email, password) => {
        const resp = await fetch(`${DIA_CHI_API_GOC}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        })
        const data = await resp.json()
        if (!resp.ok) throw new Error(data.detail || 'Đăng nhập thất bại')
        luuPhien(data.access_token, data.user)
        return data.user
    }

    const dangKy = async (username, email, password) => {
        const resp = await fetch(`${DIA_CHI_API_GOC}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        })
        const data = await resp.json()
        if (!resp.ok) throw new Error(data.detail || 'Đăng ký thất bại')
        luuPhien(data.access_token, data.user)
        return data.user
    }

    const dangXuat = () => {
        xoaPhien()
    }

    if (dangTai) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        )
    }

    return (
        <NguCanhXacThuc.Provider
            value={{ nguoiDung, token, dangTai, dangNhap, dangKy, dangXuat }}
        >
            {children}
        </NguCanhXacThuc.Provider>
    )
}

export const dungXacThuc = () => {
    const nguCanh = useContext(NguCanhXacThuc)
    if (!nguCanh) throw new Error('dungXacThuc phải được dùng bên trong BoBaoBocXacThuc')
    return nguCanh
}
export default NguCanhXacThuc
