// TrangDangNhap.jsx - Trang đăng nhập / đăng ký nâng cấp giao diện
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText, Mail, Lock, Eye, EyeOff, ArrowRight, User, Loader2, Info, CheckCircle2, Crown, Zap, Download
} from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../../context/AuthContext'
import { DIA_CHI_API_GOC } from '../../config/apiConfig'

const PasswordStrengthMeter = ({ password }) => {
  const getStrength = (p) => {
    let score = 0
    if (!p) return 0
    if (p.length > 5) score += 1
    if (p.length > 8) score += 1
    if (/[A-Z]/.test(p)) score += 1
    if (/[0-9]/.test(p)) score += 1
    if (/[^A-Za-z0-9]/.test(p)) score += 1
    return Math.min(score, 4)
  }
  const score = getStrength(password)
  const colors = ['bg-white/10', 'bg-red-400', 'bg-amber-400', 'bg-emerald-400', 'bg-emerald-500']
  const labels = ['Rất yếu', 'Yếu', 'Trung bình', 'Mạnh', 'Rất mạnh']

  return (
    <div className="mt-2 flex items-center gap-2">
      <div className="flex-1 flex gap-1 h-1.5 rounded-full overflow-hidden">
        {[1, 2, 3, 4].map(idx => (
          <div key={idx} className={`h-full flex-1 transition-all duration-300 ${score >= idx ? colors[score] : 'bg-white/10'}`} />
        ))}
      </div>
      <span className="text-[10px] text-white/50 w-12 text-right">{password ? labels[score] : ''}</span>
    </div>
  )
}

const TrangDangNhap = () => {
  const navigate = useNavigate()
  const { nguoiDung, dangNhap, dangKy, dangNhapQuaPolling } = dungXacThuc()
  const [cheDoForm, setCheDoForm] = useState('dangNhap')
  const [hienMatKhau, setHienMatKhau] = useState(false)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [dangLoginGoogle, setDangLoginGoogle] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    matKhau: '',
    xacNhanMatKhau: ''
  })

  // Phát hiện WebView qua cookie "viewappmobie" hoặc object window.FlutterBridge
  const dangChayTrongApp = document.cookie.split(';').some(c => c.trim().startsWith('viewappmobie=')) || typeof window.FlutterBridge !== 'undefined'

  const xuLyThayDoiInput = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const xuLyGuiForm = async (e) => {
    e.preventDefault()

    if (!formData.email || !formData.matKhau) {
      toast.error('Vui lòng điền đầy đủ thông tin')
      return
    }

    if (cheDoForm === 'dangKy') {
      if (!formData.username.trim()) { toast.error('Vui lòng nhập tên đăng nhập'); return }
      if (formData.matKhau !== formData.xacNhanMatKhau) { toast.error('Mật khẩu xác nhận không khớp'); return }
      if (formData.matKhau.length < 6) { toast.error('Mật khẩu phải có ít nhất 6 ký tự'); return }
    }

    setDangXuLy(true)
    try {
      let user = null
      if (cheDoForm === 'dangNhap') {
        user = await dangNhap(formData.email, formData.matKhau)
        toast.success('Đăng nhập thành công!')
      } else {
        user = await dangKy(formData.username, formData.email, formData.matKhau)
        toast.success('Đăng ký thành công!')
      }
      // Navigate is handled by useEffect when nguoiDung state changes
    } catch (loi) {
      toast.error(loi.message || 'Đã xảy ra lỗi')
    } finally {
      setDangXuLy(false)
    }
  }

  const chuyenCheDo = () => {
    setCheDoForm(prev => prev === 'dangNhap' ? 'dangKy' : 'dangNhap')
    setFormData({ username: '', email: '', matKhau: '', xacNhanMatKhau: '' })
  }

  // ── Cloud-Sync Polling: Đăng nhập Google qua Flutter Bridge ──────────
  const xuLyDangNhapGoogleTrongApp = async () => {
    if (dangLoginGoogle) return
    setDangLoginGoogle(true)

    const sessionId = crypto.randomUUID()
    let pollInterval = null

    try {
      // 1. Đăng ký phiên chờ trên server
      const formData = new FormData()
      formData.append('session_id', sessionId)
      const regResp = await fetch(`${DIA_CHI_API_GOC}/api/auth/login-session`, {
        method: 'POST',
        body: formData,
      })
      if (!regResp.ok) {
        throw new Error('Không thể khởi tạo phiên đăng nhập')
      }

      // 2. Bắt đầu Polling
      pollInterval = setInterval(async () => {
        try {
          const res = await fetch(`${DIA_CHI_API_GOC}/api/auth/login-session/${sessionId}`)
          if (!res.ok) {
            // 404 hoặc 410 = session hết hạn hoặc đã dùng
            if (res.status === 404 || res.status === 410) {
              clearInterval(pollInterval)
              setDangLoginGoogle(false)
            }
            return
          }
          const data = await res.json()
          if (data.status === 'completed' && data.token) {
            clearInterval(pollInterval)
            // Đồng bộ token về Flutter App
            if (typeof window.FlutterBridge !== 'undefined') {
              window.FlutterBridge.postMessage(`SAVE_TOKEN:${data.token}`)
            }
            // Lưu phiên đăng nhập trên Web
            dangNhapQuaPolling(data.token, data.user)
            toast.success('Đăng nhập thành công!')
            // Navigate is handled by useEffect when nguoiDung state changes
          }
        } catch {
          // Lỗi mạng - tiếp tục polling
        }
      }, 2000)

      // 3. Timeout: dừng polling sau 10 phút
      setTimeout(() => {
        if (pollInterval) {
          clearInterval(pollInterval)
          setDangLoginGoogle(false)
        }
      }, 10 * 60 * 1000)

      // 4. Gọi Flutter Bridge để mở Chrome Custom Tab
      if (window.FlutterBridge) {
        window.FlutterBridge.postMessage(`GOOGLE_LOGIN:${sessionId}`)
      } else {
        throw new Error('Không tìm thấy kết nối với ứng dụng')
      }
    } catch (loi) {
      if (pollInterval) clearInterval(pollInterval)
      setDangLoginGoogle(false)
      toast.error(loi.message || 'Không thể kết nối đăng nhập Google')
    }
  }

  useEffect(() => {
    if (!nguoiDung) {
      // Check for error param from Google OAuth redirect failure
      const params = new URLSearchParams(window.location.search)
      const errorMsg = params.get('error')
      if (errorMsg) {
        toast.error(decodeURIComponent(errorMsg), { duration: 6000 })
        // Clean URL
        const newUrl = window.location.pathname
        window.history.replaceState({}, document.title, newUrl)
      }
      return
    }
    navigate(nguoiDung.role === 'admin' ? '/quan-tri' : '/chuyen-doi', { replace: true })
  }, [nguoiDung, navigate])

  return (
    <div className="flex min-h-screen bg-[#070513] text-white">
      
      {/* Cột trái: Form Auth */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 h-screen overflow-y-auto">
        <div className="w-full max-w-sm">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-10 text-center sm:text-left">
            <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-gradient-to-br from-primary-500/20 to-purple-500/20 border border-primary-500/30 mb-4 text-primary-400">
              <FileText className="w-8 h-8" />
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">Word2LaTeX</h1>
            <p className="text-white/50 mt-2 text-sm">Nền tảng chuyển đổi văn bản sang mã LaTeX chuẩn học thuật.</p>
          </motion.div>

          <div className="flex bg-white/5 p-1 rounded-xl mb-8">
            <button
              onClick={() => setCheDoForm('dangNhap')}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition ${cheDoForm === 'dangNhap' ? 'bg-primary-600 shadow-md text-white' : 'text-white/50 hover:text-white'}`}
            >
              Đăng nhập
            </button>
            <button
              onClick={() => setCheDoForm('dangKy')}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition ${cheDoForm === 'dangKy' ? 'bg-primary-600 shadow-md text-white' : 'text-white/50 hover:text-white'}`}
            >
              Đăng ký
            </button>
          </div>

          <form onSubmit={xuLyGuiForm} className="space-y-4">
            <AnimatePresence mode="popLayout">
              {cheDoForm === 'dangKy' && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="relative group">
                  <User className="absolute left-4 top-3.5 w-5 h-5 text-white/30 group-focus-within:text-primary-400 transition" />
                  <input
                    type="text" name="username" value={formData.username} onChange={xuLyThayDoiInput}
                    placeholder="Tên người dùng"
                    className="w-full bg-white/5 border border-white/10 p-3 pl-12 rounded-xl outline-none focus:border-primary-500 transition focus:bg-white/10"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div className="relative group">
              <Mail className="absolute left-4 top-3.5 w-5 h-5 text-white/30 group-focus-within:text-primary-400 transition" />
              <input
                type="email" name="email" value={formData.email} onChange={xuLyThayDoiInput}
                placeholder="Địa chỉ Email"
                className="w-full bg-white/5 border border-white/10 p-3 pl-12 rounded-xl outline-none focus:border-primary-500 transition focus:bg-white/10"
              />
            </div>

            <div className="relative group">
              <Lock className="absolute left-4 top-3.5 w-5 h-5 text-white/30 group-focus-within:text-primary-400 transition" />
              <input
                type={hienMatKhau ? 'text' : 'password'} name="matKhau" value={formData.matKhau} onChange={xuLyThayDoiInput}
                placeholder="Mật khẩu"
                className="w-full bg-white/5 border border-white/10 p-3 pl-12 pr-12 rounded-xl outline-none focus:border-primary-500 transition focus:bg-white/10"
              />
              <button type="button" onClick={() => setHienMatKhau(!hienMatKhau)} className="absolute right-4 top-3.5 text-white/30 hover:text-white transition">
                {hienMatKhau ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
              {cheDoForm === 'dangKy' && <PasswordStrengthMeter password={formData.matKhau} />}
            </div>

            <AnimatePresence mode="popLayout">
              {cheDoForm === 'dangKy' && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="relative group">
                  <Lock className="absolute left-4 top-3.5 w-5 h-5 text-white/30 group-focus-within:text-primary-400 transition" />
                  <input
                    type={hienMatKhau ? 'text' : 'password'} name="xacNhanMatKhau" value={formData.xacNhanMatKhau} onChange={xuLyThayDoiInput}
                    placeholder="Xác nhận mật khẩu"
                    className="w-full bg-white/5 border border-white/10 p-3 pl-12 rounded-xl outline-none focus:border-primary-500 transition focus:bg-white/10"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <button disabled={dangXuLy} className="w-full bg-primary-600 hover:bg-primary-500 py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition disabled:opacity-50">
              {dangXuLy ? <Loader2 className="w-5 h-5 animate-spin"/> : (
                <>
                  {cheDoForm === 'dangNhap' ? 'Bắt đầu ngay' : 'Tạo tài khoản'} <ArrowRight className="w-5 h-5"/>
                </>
              )}
            </button>
          </form>

          <div className="mt-8 flex items-center justify-between gap-4">
            <span className="flex-1 h-px bg-white/10"></span>
            <span className="text-xs text-white/40">HOẶC DÙNG DỊCH VỤ NGOÀI</span>
            <span className="flex-1 h-px bg-white/10"></span>
          </div>

          <div className="mt-6">
            {dangChayTrongApp ? (
              <button
                onClick={xuLyDangNhapGoogleTrongApp}
                disabled={dangLoginGoogle}
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-sm font-semibold text-white hover:bg-white/10 transition disabled:opacity-50"
              >
                {dangLoginGoogle ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Đang chờ đăng nhập...</>
                ) : (
                  'Đăng nhập với Google'
                )}
              </button>
            ) : (
              <a
                href={`${DIA_CHI_API_GOC}/api/auth/google/login`}
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-sm font-semibold text-white hover:bg-white/10 transition"
              >
                Đăng nhập với Google
              </a>
            )}
          </div>
          
          {!dangChayTrongApp && (
            <div className="mt-4">
               <a
                  href="/word2latex-app.apk"
                  download
                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl border border-primary-500/30 bg-primary-500/10 px-4 py-3 text-sm font-semibold text-primary-300 hover:bg-primary-500/20 transition"
                >
                  <Download className="w-5 h-5" /> Tải Ứng dụng Android (APK)
                </a>
            </div>
          )}
        </div>
      </div>

      {/* Cột phải: Visual - Ẩn trên mobile */}
      <div className="hidden lg:flex w-[55%] relative items-center justify-center p-12 overflow-hidden border-l border-white/5 bg-gradient-to-br from-[#0a071d] via-[#110e28] to-[#1c1240]">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03]"></div>
        
        {/* Glows */}
        <div className="absolute top-[20%] left-[20%] w-96 h-96 bg-primary-600/20 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-[20%] right-[20%] w-96 h-96 bg-purple-600/20 rounded-full blur-[100px] pointer-events-none" />

        <div className="relative z-10 w-full max-w-lg">
          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 -mr-4 -mt-4 opacity-10">
              <Crown className="w-32 h-32" />
            </div>
            
            <h2 className="text-3xl font-bold mb-4 font-serif text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">Trải Nghiệm Nâng Cao</h2>
            <p className="text-white/70 mb-8 leading-relaxed">
              Trở thành viên <strong>Premium</strong> để tận dụng mọi sức mạnh từ Word2LaTeX. Chấp vai cho bài viết nghiên cứu của bạn bằng cấu trúc tối ưu.
            </p>

            <div className="space-y-4">
              <div className="flex items-center gap-4 bg-white/5 p-4 rounded-2xl border border-white/5 hover:bg-white/10 transition cursor-default">
                <div className="bg-emerald-500/20 p-2 rounded-lg text-emerald-400"><CheckCircle2 className="w-6 h-6" /></div>
                <div>
                  <h4 className="font-semibold text-white/90">Xử lý tài liệu vô song</h4>
                  <p className="text-xs text-white/50">Không giới hạn định dạng học thuật.</p>
                </div>
              </div>
              <div className="flex items-center gap-4 bg-white/5 p-4 rounded-2xl border border-white/5 hover:bg-white/10 transition cursor-default">
                <div className="bg-amber-500/20 p-2 rounded-lg text-amber-400"><Zap className="w-6 h-6" /></div>
                <div>
                  <h4 className="font-semibold text-white/90">Chuyển đổi tốc độ cao</h4>
                  <p className="text-xs text-white/50">Được ưu tiên queue chạy lập tức.</p>
                </div>
              </div>
            </div>
            
            <div className="mt-8 flex items-center justify-between text-sm text-white/40">
              <div className="flex items-center gap-2"><Info className="w-4 h-4"/> Nạp token tự động 24/7</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TrangDangNhap
