/**
 * AdminThemeContext.jsx — Global theme state management for the entire website.
 * Loads active theme from backend on startup, broadcasts changes to all components.
 */
import { createContext, useContext, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { layThemeHienTai, capNhatCauHinhHeThongAdmin } from '../../../services/api'

const THEMES = {
  'dark-indigo': { name: 'Dark Indigo', emoji: '🟣', desc: 'Tông tím/indigo sang trọng', colors: ['#312e81','#1e1b4b','#6366f1','#818cf8'] },
  'midnight-cyan': { name: 'Midnight Cyan', emoji: '🔵', desc: 'Tông xanh cyan/tối', colors: ['#020617','#083344','#06b6d4','#22d3ee'] },
  'warm-slate': { name: 'Warm Slate', emoji: '🟠', desc: 'Tông ấm amber/stone', colors: ['#1c1917','#44403c','#f59e0b','#fbbf24'] },
  'light-pro': { name: 'Light Pro', emoji: '⚪', desc: 'Nền sáng chuyên nghiệp', colors: ['#f9fafb','#ffffff','#4f46e5','#6366f1'] },
}

const VALID_THEMES = new Set(Object.keys(THEMES))

const ThemeContext = createContext(null)

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('dark-indigo')
  const [dangTai, setDangTai] = useState(true)

  // Load theme from backend on startup
  useEffect(() => {
    const loadTheme = async () => {
      try {
        const res = await layThemeHienTai()
        if (res.theme && VALID_THEMES.has(res.theme)) {
          setTheme(res.theme)
        }
      } finally {
        setDangTai(false)
      }
    }
    loadTheme()
  }, [])

  // Apply theme to DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const doiTheme = async (newTheme) => {
    if (VALID_THEMES.has(newTheme)) {
      setTheme(newTheme)
      try {
        const res = await capNhatCauHinhHeThongAdmin({ active_theme: newTheme })
        if (res.thanhCong) {
          toast.success(`Đã đổi giao diện thành: ${THEMES[newTheme].name}`)
        } else {
          toast.error('Lưu giao diện thất bại (chỉ đổi tạm thời)')
        }
      } catch {
        toast.error('Không thể kết nối máy chủ')
      }
    }
  }

  return (
    <ThemeContext.Provider value={{ theme, doiTheme, dangTai, THEMES, VALID_THEMES }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const dungTheme = () => {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('dungTheme phải được dùng bên trong ThemeProvider')
  return ctx
}

export { THEMES }
export default ThemeContext
