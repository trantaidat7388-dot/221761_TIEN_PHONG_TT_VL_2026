import { useEffect, useState } from 'react'
import { UserCog, Save } from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../../context/AuthContext'
import { NutBam } from '../../components'

const TrangTaiKhoan = () => {
  const { nguoiDung, capNhatTaiKhoan, lamMoiThongTinNguoiDung } = dungXacThuc()
  const laTaiKhoanGoogle = (nguoiDung?.auth_provider || '').toLowerCase() === 'google'
  const [dangLuu, setDangLuu] = useState(false)
  const [formData, setFormData] = useState({
    username: nguoiDung?.username || '',
    email: nguoiDung?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: '',
  })

  const xuLyThayDoiInput = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      username: nguoiDung?.username || '',
      email: nguoiDung?.email || '',
    }))
  }, [nguoiDung?.username, nguoiDung?.email])

  useEffect(() => {
    lamMoiThongTinNguoiDung({ imLang: true })

    const xuLyFocus = () => {
      lamMoiThongTinNguoiDung({ imLang: true })
    }

    window.addEventListener('focus', xuLyFocus)
    return () => window.removeEventListener('focus', xuLyFocus)
  }, [])

  const xuLyLuu = async (e) => {
    e.preventDefault()

    if (!laTaiKhoanGoogle && !formData.currentPassword) {
      toast.error('Vui lòng nhập mật khẩu hiện tại để xác nhận')
      return
    }

    if (!laTaiKhoanGoogle && formData.newPassword && formData.newPassword.length < 6) {
      toast.error('Mật khẩu mới phải có ít nhất 6 ký tự')
      return
    }

    if (!laTaiKhoanGoogle && formData.newPassword && formData.newPassword !== formData.confirmNewPassword) {
      toast.error('Xác nhận mật khẩu mới không khớp')
      return
    }

    const payload = {
      username: formData.username,
      email: formData.email,
    }
    if (!laTaiKhoanGoogle && formData.currentPassword) payload.current_password = formData.currentPassword
    if (!laTaiKhoanGoogle && formData.newPassword) payload.new_password = formData.newPassword

    setDangLuu(true)
    try {
      await capNhatTaiKhoan(payload)
      toast.success('Đã cập nhật thông tin tài khoản')
      setFormData((prev) => ({
        ...prev,
        currentPassword: '',
        newPassword: '',
        confirmNewPassword: '',
      }))
    } catch (error) {
      toast.error(error.message || 'Không thể cập nhật tài khoản')
    } finally {
      setDangLuu(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <UserCog className="w-8 h-8 text-primary-400" />
            Thông tin tài khoản
          </h1>
          <p className="text-white/60">Cập nhật tên đăng nhập, email và mật khẩu của bạn</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          <div className="glass-card p-3 bg-white/10">
            <p className="text-white/60 text-xs">Vai trò</p>
            <p className="text-white font-semibold">{nguoiDung?.role || 'user'}</p>
          </div>
          <div className="glass-card p-3 bg-emerald-500/10">
            <p className="text-emerald-200 text-xs">Gói dịch vụ</p>
            <p className="text-emerald-100 font-semibold">{nguoiDung?.plan_type || 'free'}</p>
          </div>
          <div className="glass-card p-3 bg-amber-500/10">
            <p className="text-amber-200 text-xs">Token còn lại</p>
            <p className="text-amber-100 font-semibold">{nguoiDung?.token_balance ?? 0}</p>
          </div>
        </div>

        <form onSubmit={xuLyLuu} className="glass-card p-6 space-y-4">
          <div>
            <label htmlFor="username" className="block text-white/80 text-sm mb-2">Tên đăng nhập</label>
            <input
              id="username"
              name="username"
              value={formData.username}
              onChange={xuLyThayDoiInput}
              className="input-glass"
              placeholder="Tên đăng nhập"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-white/80 text-sm mb-2">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={xuLyThayDoiInput}
              className="input-glass"
              placeholder="Email"
            />
          </div>

          {!laTaiKhoanGoogle ? (
            <div className="pt-2 border-t border-white/10">
              <p className="text-white text-sm font-medium mb-3">Đổi mật khẩu (tùy chọn)</p>

              <div className="mb-3">
                <label htmlFor="currentPassword" className="block text-white/80 text-sm mb-2">Mật khẩu hiện tại (bắt buộc)</label>
                <input
                  id="currentPassword"
                  name="currentPassword"
                  type="password"
                  value={formData.currentPassword}
                  onChange={xuLyThayDoiInput}
                  className="input-glass"
                  placeholder="Nhập mật khẩu hiện tại"
                />
              </div>

              <div className="mb-3">
                <label htmlFor="newPassword" className="block text-white/80 text-sm mb-2">Mật khẩu mới</label>
                <input
                  id="newPassword"
                  name="newPassword"
                  type="password"
                  value={formData.newPassword}
                  onChange={xuLyThayDoiInput}
                  className="input-glass"
                  placeholder="Để trống nếu không đổi"
                />
              </div>

              <div>
                <label htmlFor="confirmNewPassword" className="block text-white/80 text-sm mb-2">Xác nhận mật khẩu mới</label>
                <input
                  id="confirmNewPassword"
                  name="confirmNewPassword"
                  type="password"
                  value={formData.confirmNewPassword}
                  onChange={xuLyThayDoiInput}
                  className="input-glass"
                  placeholder="Nhập lại mật khẩu mới"
                />
              </div>
            </div>
          ) : (
            <div className="pt-2 border-t border-white/10">
              <p className="text-white/70 text-sm">
                Tài khoản của bạn đăng nhập bằng Google. Bạn có thể cập nhật tên và email mà không cần mật khẩu tại đây.
              </p>
            </div>
          )}

          <div className="pt-2">
            <NutBam type="submit" icon={Save} dangTai={dangLuu}>
              Lưu thay đổi
            </NutBam>
          </div>
        </form>
      </div>
    </div>
  )
}

export default TrangTaiKhoan
