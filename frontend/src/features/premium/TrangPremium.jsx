import { useEffect, useMemo, useState } from 'react'
import { Crown, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../../context/AuthContext'
import { dangKyGoiPremium, layThongTinGoiPremium } from '../../services/api'
import { NutBam } from '../../components'

const TrangPremium = () => {
  const { nguoiDung, lamMoiThongTinNguoiDung } = dungXacThuc()
  const [dangTai, setDangTai] = useState(true)
  const [dangDangKy, setDangDangKy] = useState(false)
  const [goiPremium, setGoiPremium] = useState(null)

  const taiThongTin = async () => {
    setDangTai(true)
    try {
      const ketQua = await layThongTinGoiPremium()
      if (!ketQua.thanhCong) {
        throw new Error(ketQua.loiMessage || 'Không tải được thông tin gói premium')
      }
      setGoiPremium(ketQua.data?.goi_mac_dinh || null)
      await lamMoiThongTinNguoiDung({ imLang: true })
    } catch (error) {
      toast.error(error.message || 'Không tải được trang premium')
    } finally {
      setDangTai(false)
    }
  }

  useEffect(() => {
    taiThongTin()
  }, [])

  const premiumDangHieuLuc = useMemo(() => {
    if (nguoiDung?.plan_type !== 'premium') return false
    const raw = nguoiDung?.premium_expires_at
    if (!raw) return false
    const ngayHetHan = new Date(raw)
    if (Number.isNaN(ngayHetHan.getTime())) return false
    return ngayHetHan.getTime() > Date.now()
  }, [nguoiDung?.plan_type, nguoiDung?.premium_expires_at])

  const xuLyDangKyPremium = async () => {
    if (premiumDangHieuLuc) {
      toast('Tài khoản đã có premium đang hiệu lực')
      return
    }

    setDangDangKy(true)
    try {
      const ketQua = await dangKyGoiPremium()
      if (!ketQua.thanhCong) {
        throw new Error(ketQua.loiMessage || 'Đăng ký premium thất bại')
      }
      toast.success('Đăng ký gói premium thành công')
      await lamMoiThongTinNguoiDung({ imLang: true })
    } catch (error) {
      toast.error(error.message || 'Không thể đăng ký premium')
    } finally {
      setDangDangKy(false)
    }
  }

  const dinhDangNgay = (rawValue) => {
    if (!rawValue) return '-'
    const parsed = new Date(rawValue)
    if (Number.isNaN(parsed.getTime())) return '-'
    return parsed.toLocaleString('vi-VN')
  }

  const tokenCost = goiPremium?.token_cost || 0
  const soNgay = goiPremium?.so_ngay || 30
  const tokenHienTai = nguoiDung?.token_balance ?? 0
  const tokenConLaiSauMua = Math.max(0, tokenHienTai - tokenCost)
  const duToken = tokenHienTai >= tokenCost

  return (
    <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Crown className="w-8 h-8 text-amber-300" />
            Đăng ký gói Premium
          </h1>
          <p className="text-white/60">Nâng cấp tài khoản để tăng hạn mức và ưu tiên chuyển đổi</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="glass-card p-4 bg-emerald-500/10">
            <p className="text-emerald-200 text-sm">Gói hiện tại</p>
            <p className="text-2xl font-bold text-emerald-100">{nguoiDung?.plan_type || 'free'}</p>
          </div>
          <div className="glass-card p-4 bg-amber-500/10">
            <p className="text-amber-200 text-sm">Token hiện tại</p>
            <p className="text-2xl font-bold text-amber-100">{tokenHienTai}</p>
          </div>
          <div className="glass-card p-4 bg-cyan-500/10">
            <p className="text-cyan-200 text-sm">Premium hết hạn</p>
            <p className="text-sm font-semibold text-cyan-100">{dinhDangNgay(nguoiDung?.premium_expires_at)}</p>
          </div>
        </div>

        <section className="glass-card p-6 border border-amber-300/30 bg-amber-500/5">
          <div className="flex items-start justify-between gap-4 mb-5">
            <div>
              <p className="text-amber-200 text-sm uppercase tracking-wide">Gói mặc định</p>
              <h2 className="text-2xl text-white font-bold mt-1">Premium {soNgay} ngày</h2>
            </div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-300/20 text-amber-100 text-sm">
              <Sparkles className="w-4 h-4" />
              {tokenCost} token
            </div>
          </div>

          <ul className="text-white/85 text-sm space-y-2 mb-6">
            <li>- Ưu tiên hỗ trợ và theo dõi chuyển đổi.</li>
            <li>- Tăng quyền sử dụng theo chính sách premium của hệ thống.</li>
            <li>- Kích hoạt ngay sau khi xác nhận đăng ký.</li>
          </ul>

          <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm mb-5">
            <p className="text-white/70">Sau khi đăng ký:</p>
            <p className="text-white mt-1">Token dự kiến còn lại: <span className="font-semibold text-amber-200">{tokenConLaiSauMua}</span></p>
          </div>

          <NutBam
            onClick={xuLyDangKyPremium}
            icon={Crown}
            dangTai={dangDangKy || dangTai}
            disabled={!goiPremium || !duToken || premiumDangHieuLuc}
          >
            {premiumDangHieuLuc ? 'Premium đang hiệu lực' : `Đăng ký ngay (${tokenCost} token)`}
          </NutBam>

          {!duToken && !premiumDangHieuLuc && (
            <p className="text-red-300 text-sm mt-3">Bạn chưa đủ token để đăng ký gói premium.</p>
          )}
        </section>
      </div>
    </div>
  )
}

export default TrangPremium
