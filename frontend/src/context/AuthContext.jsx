// AuthContext.jsx - Quản lý trạng thái xác thực JWT toàn ứng dụng

import { createContext, useContext, useEffect, useState } from 'react'
import { DIA_CHI_API_GOC } from '../config/apiConfig'

const TOKEN_KEY = 'word2latex_token'
const USER_KEY = 'word2latex_user'
const SU_KIEN_PHIEN_HET_HAN = 'xac-thuc:het-han'
const CHU_KY_XAC_THUC_MS = 60 * 1000

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

    const lamMoiThongTinNguoiDung = async ({ imLang = true } = {}) => {
        const tokenDangDung = localStorage.getItem(TOKEN_KEY)
        if (!tokenDangDung) return null
        try {
            const resp = await goiApiThongTinNguoiDung(tokenDangDung)
            if (resp.ok) {
                const duLieuNguoiDung = await resp.json()
                luuPhien(tokenDangDung, duLieuNguoiDung)
                return duLieuNguoiDung
            }
            xoaPhien()
            return null
        } catch {
            if (!imLang) throw new Error('Không thể làm mới thông tin người dùng')
            return null
        }
    }

    const goiApiThongTinNguoiDung = async (tokenDangDung) => {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000)
        try {
            const resp = await fetch(`${DIA_CHI_API_GOC}/api/auth/me`, {
                headers: { 'Authorization': `Bearer ${tokenDangDung}` },
                signal: controller.signal
            })
            return resp
        } finally {
            clearTimeout(timeoutId)
        }
    }

    const luuPhien = (accessToken, duLieuNguoiDung) => {
        const userNormalized = {
            ...duLieuNguoiDung,
            role: duLieuNguoiDung?.role || 'user'
        }
        localStorage.setItem(TOKEN_KEY, accessToken)
        localStorage.setItem(USER_KEY, JSON.stringify(userNormalized))
        datToken(accessToken)
        datNguoiDung(userNormalized)
    }

    const xoaPhien = () => {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        datToken(null)
        datNguoiDung(null)
    }

    // Validate token on mount by calling /api/auth/me
    useEffect(() => {
        let daHuy = false

        const xacThucTokenDaLuu = async ({ imLang = false } = {}) => {
            const tokenDaLuu = localStorage.getItem(TOKEN_KEY)
            if (!tokenDaLuu) {
                if (!daHuy) datDangTai(false)
                return
            }
            try {
                const resp = await goiApiThongTinNguoiDung(tokenDaLuu)
                if (resp.ok) {
                    const duLieuNguoiDung = await resp.json()
                    if (!daHuy) luuPhien(tokenDaLuu, duLieuNguoiDung)
                } else {
                    if (!daHuy) xoaPhien()
                }
            } catch {
                // Server unreachable - keep local state
            }
            if (!imLang && !daHuy) datDangTai(false)
        }

        xacThucTokenDaLuu()

        const xuLyTrangThaiTab = () => {
            if (document.visibilityState === 'visible') {
                xacThucTokenDaLuu({ imLang: true })
            }
        }
        const xuLyDongBoStorage = (event) => {
            if (event.key === TOKEN_KEY || event.key === USER_KEY) {
                const tokenMoi = localStorage.getItem(TOKEN_KEY)
                const userRaw = localStorage.getItem(USER_KEY)
                if (!tokenMoi || !userRaw) {
                    xoaPhien()
                    return
                }
                try {
                    datToken(tokenMoi)
                    datNguoiDung(JSON.parse(userRaw))
                } catch {
                    xoaPhien()
                }
            }
        }
        const xuLyPhienHetHan = () => {
            xoaPhien()
        }

        const intervalId = setInterval(() => {
            xacThucTokenDaLuu({ imLang: true })
        }, CHU_KY_XAC_THUC_MS)

        document.addEventListener('visibilitychange', xuLyTrangThaiTab)
        window.addEventListener('storage', xuLyDongBoStorage)
        window.addEventListener(SU_KIEN_PHIEN_HET_HAN, xuLyPhienHetHan)

        return () => {
            daHuy = true
            clearInterval(intervalId)
            document.removeEventListener('visibilitychange', xuLyTrangThaiTab)
            window.removeEventListener('storage', xuLyDongBoStorage)
            window.removeEventListener(SU_KIEN_PHIEN_HET_HAN, xuLyPhienHetHan)
        }
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

    const dangNhapGoogle = async (googleIdToken) => {
        const resp = await fetch(`${DIA_CHI_API_GOC}/api/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: googleIdToken })
        })
        const data = await resp.json().catch(() => ({}))
        if (!resp.ok) throw new Error(data.detail || 'Đăng nhập Google thất bại')
        luuPhien(data.access_token, data.user)
        return data.user
    }

    const dangXuat = () => {
        xoaPhien()
    }

    const capNhatTaiKhoan = async (payload) => {
        const tokenDangDung = localStorage.getItem(TOKEN_KEY)
        if (!tokenDangDung) throw new Error('Phiên đăng nhập không hợp lệ')

        const resp = await fetch(`${DIA_CHI_API_GOC}/api/auth/me`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${tokenDangDung}`
            },
            body: JSON.stringify(payload)
        })
        const data = await resp.json().catch(() => ({}))
        if (!resp.ok) throw new Error(data.detail || 'Không thể cập nhật thông tin tài khoản')

        luuPhien(tokenDangDung, data.user)
        return data.user
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
            value={{ nguoiDung, token, dangTai, dangNhap, dangKy, dangNhapGoogle, dangXuat, capNhatTaiKhoan, lamMoiThongTinNguoiDung }}
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
