import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, Mail, Shield, ArrowRight, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../../context/AuthContext'

const TrangAdminDangNhap = () => {
  const navigate = useNavigate()
  const { nguoiDung, dangNhap, dangXuat } = dungXacThuc()
  const [email, setEmail] = useState('')
  const [matKhau, setMatKhau] = useState('')
  const [dangXuLy, setDangXuLy] = useState(false)

  useEffect(() => {
    if (!nguoiDung) return
    if (nguoiDung.role === 'admin') {
      navigate('/quan-tri', { replace: true })
      return
    }
    navigate('/chuyen-doi', { replace: true })
  }, [nguoiDung, navigate])

  const xuLyDangNhapAdmin = async (e) => {
    e.preventDefault()

    if (!email.trim() || !matKhau) {
      toast.error('Vui long nhap day du email va mat khau')
      return
    }

    setDangXuLy(true)
    try {
      const user = await dangNhap(email.trim(), matKhau)
      if (user?.role !== 'admin') {
        dangXuat()
        toast.error('Tai khoan nay khong co quyen quan tri')
        return
      }
      toast.success('Dang nhap cong quan tri thanh cong')
      window.location.replace('/quan-tri')
    } catch (error) {
      toast.error(error.message || 'Dang nhap admin that bai')
    } finally {
      setDangXuLy(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-10 text-slate-100">
      <div className="mx-auto max-w-md">
        <div className="mb-8 rounded-2xl border border-cyan-400/25 bg-cyan-400/10 p-5">
          <p className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-cyan-200">
            <Shield className="h-4 w-4" />
            Admin Entry Point
          </p>
          <h1 className="text-2xl font-extrabold text-white">Dang nhap cong quan tri</h1>
          <p className="mt-2 text-sm text-cyan-100/80">Chi danh cho tai khoan co quyen admin. Sau khi dang nhap, he thong chuyen den khu vuc /quan-tri.</p>
        </div>

        <form onSubmit={xuLyDangNhapAdmin} className="rounded-2xl border border-white/15 bg-white/5 p-6 backdrop-blur">
          <label className="mb-2 block text-sm text-white/70">Email admin</label>
          <div className="mb-4 flex items-center gap-2 rounded-xl border border-white/15 bg-slate-900/70 px-3 py-2">
            <Mail className="h-4 w-4 text-white/50" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-transparent text-white outline-none"
              placeholder="admin@example.com"
              autoComplete="email"
            />
          </div>

          <label className="mb-2 block text-sm text-white/70">Mat khau</label>
          <div className="mb-6 flex items-center gap-2 rounded-xl border border-white/15 bg-slate-900/70 px-3 py-2">
            <Lock className="h-4 w-4 text-white/50" />
            <input
              type="password"
              value={matKhau}
              onChange={(e) => setMatKhau(e.target.value)}
              className="w-full bg-transparent text-white outline-none"
              placeholder="Nhap mat khau"
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={dangXuLy}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 font-semibold text-slate-900 transition hover:bg-cyan-300 disabled:opacity-60"
          >
            {dangXuLy ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowRight className="h-5 w-5" />}
            Dang nhap admin
          </button>
        </form>
      </div>
    </div>
  )
}

export default TrangAdminDangNhap
