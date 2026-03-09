// TrangDangNhap.jsx - Trang đăng nhập / đăng ký với JWT (không Firebase)

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  User,
  Loader2
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../../context/AuthContext'

const TrangDangNhap = () => {
  const navigate = useNavigate()
  const { login, register } = useAuth()
  const [cheDoForm, setCheDoForm] = useState('dangNhap')
  const [hienMatKhau, setHienMatKhau] = useState(false)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    matKhau: '',
    xacNhanMatKhau: ''
  })

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
      if (!formData.username.trim()) {
        toast.error('Vui lòng nhập tên đăng nhập')
        return
      }
      if (formData.matKhau !== formData.xacNhanMatKhau) {
        toast.error('Mật khẩu xác nhận không khớp')
        return
      }
      if (formData.matKhau.length < 6) {
        toast.error('Mật khẩu phải có ít nhất 6 ký tự')
        return
      }
    }

    setDangXuLy(true)
    try {
      if (cheDoForm === 'dangNhap') {
        await login(formData.email, formData.matKhau)
        toast.success('Đăng nhập thành công!')
      } else {
        await register(formData.username, formData.email, formData.matKhau)
        toast.success('Đăng ký thành công!')
      }
      navigate('/chuyen-doi')
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

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.2 } }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100, damping: 12 } }
  }

  const formVariants = {
    hidden: { opacity: 0, x: 20 },
    visible: { opacity: 1, x: 0, transition: { type: 'spring', stiffness: 100, damping: 15 } },
    exit: { opacity: 0, x: -20, transition: { duration: 0.2 } }
  }

  return (
    <div className="min-h-screen bg-gradient-animated flex items-center justify-center p-4 relative overflow-hidden">
      {/* Floating orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute w-96 h-96 bg-primary-500/20 rounded-full blur-3xl"
          animate={{ x: [0, 100, 0], y: [0, -50, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
          style={{ top: '10%', left: '10%' }}
        />
        <motion.div
          className="absolute w-80 h-80 bg-purple-500/15 rounded-full blur-3xl"
          animate={{ x: [0, -80, 0], y: [0, 80, 0] }}
          transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut' }}
          style={{ bottom: '10%', right: '15%' }}
        />
      </div>

      <motion.div
        className="w-full max-w-md relative z-10"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Logo */}
        <motion.div className="text-center mb-8" variants={itemVariants}>
          <motion.div
            className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 mb-4 shadow-lg shadow-primary-500/30"
            whileHover={{ scale: 1.05, rotate: 5 }}
            whileTap={{ scale: 0.95 }}
          >
            <FileText className="w-10 h-10 text-white" />
          </motion.div>
          <h1 className="text-3xl font-bold text-white mb-2">Word2LaTeX</h1>
          <p className="text-white/60 text-sm">Chuyển đổi Word sang LaTeX chuẩn học thuật</p>
        </motion.div>

        {/* Card */}
        <motion.div className="glass-card p-8 shadow-2xl" variants={itemVariants}>
          {/* Tab */}
          <div className="flex bg-white/5 rounded-xl p-1 mb-6">
            <button
              onClick={() => setCheDoForm('dangNhap')}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${cheDoForm === 'dangNhap' ? 'bg-primary-600 text-white shadow-lg' : 'text-white/60 hover:text-white'}`}
            >
              Đăng nhập
            </button>
            <button
              onClick={() => setCheDoForm('dangKy')}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${cheDoForm === 'dangKy' ? 'bg-primary-600 text-white shadow-lg' : 'text-white/60 hover:text-white'}`}
            >
              Đăng ký
            </button>
          </div>

          {/* Form */}
          <AnimatePresence mode="wait">
            <motion.form
              key={cheDoForm}
              onSubmit={xuLyGuiForm}
              variants={formVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="space-y-4"
            >
              {/* Username — chỉ khi đăng ký */}
              {cheDoForm === 'dangKy' && (
                <motion.div
                  className="relative"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={xuLyThayDoiInput}
                    placeholder="Tên đăng nhập"
                    className="input-glass pl-12"
                    disabled={dangXuLy}
                    autoComplete="username"
                  />
                </motion.div>
              )}

              {/* Email */}
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={xuLyThayDoiInput}
                  placeholder="Email của bạn"
                  className="input-glass pl-12"
                  disabled={dangXuLy}
                  autoComplete="email"
                />
              </div>

              {/* Mật khẩu */}
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type={hienMatKhau ? 'text' : 'password'}
                  name="matKhau"
                  value={formData.matKhau}
                  onChange={xuLyThayDoiInput}
                  placeholder="Mật khẩu (ít nhất 6 ký tự)"
                  className="input-glass pl-12 pr-12"
                  disabled={dangXuLy}
                  autoComplete={cheDoForm === 'dangNhap' ? 'current-password' : 'new-password'}
                />
                <button
                  type="button"
                  onClick={() => setHienMatKhau(!hienMatKhau)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                >
                  {hienMatKhau ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>

              {/* Xác nhận mật khẩu */}
              {cheDoForm === 'dangKy' && (
                <motion.div
                  className="relative"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                  <input
                    type={hienMatKhau ? 'text' : 'password'}
                    name="xacNhanMatKhau"
                    value={formData.xacNhanMatKhau}
                    onChange={xuLyThayDoiInput}
                    placeholder="Xác nhận mật khẩu"
                    className="input-glass pl-12"
                    disabled={dangXuLy}
                    autoComplete="new-password"
                  />
                </motion.div>
              )}

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={dangXuLy}
                className="btn-primary w-full flex items-center justify-center gap-2 mt-2"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {dangXuLy ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <span>{cheDoForm === 'dangNhap' ? 'Đăng nhập' : 'Tạo tài khoản'}</span>
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </motion.button>
            </motion.form>
          </AnimatePresence>
        </motion.div>

        {/* Link chuyển mode */}
        <motion.p className="text-center mt-6 text-white/50 text-sm" variants={itemVariants}>
          {cheDoForm === 'dangNhap' ? 'Chưa có tài khoản? ' : 'Đã có tài khoản? '}
          <button onClick={chuyenCheDo} className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
            {cheDoForm === 'dangNhap' ? 'Đăng ký ngay' : 'Đăng nhập'}
          </button>
        </motion.p>

        <motion.p className="text-center mt-4 text-white/30 text-xs" variants={itemVariants}>
          © 2026 Word2LaTeX Research Project
        </motion.p>
      </motion.div>
    </div>
  )
}

export default TrangDangNhap
