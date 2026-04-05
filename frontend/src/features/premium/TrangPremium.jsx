import { useEffect, useMemo, useState } from 'react'
import { Crown, Zap, Coins, Wallet, CreditCard } from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../../context/AuthContext'
import { dangKyGoiPremium, layThongTinGoiPremium } from '../../services/api'
import { NutBam } from '../../components'
import NapTokenModal from './NapTokenModal'

const TrangPremium = () => {
  const { nguoiDung, lamMoiThongTinNguoiDung } = dungXacThuc()
  const [dangTai, setDangTai] = useState(true)
  const [dangDangKy, setDangDangKy] = useState('')
  const [danhSachGoi, setDanhSachGoi] = useState({})
  const [isNapModalOpen, setIsNapModalOpen] = useState(false)

  const taiThongTin = async () => {
    setDangTai(true)
    try {
      const ketQua = await layThongTinGoiPremium()
      if (!ketQua.thanhCong) throw new Error(ketQua.loiMessage || 'Không tải được thông tin gói premium')
      setDanhSachGoi(ketQua.data?.danh_sach_goi || {})
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
    return !Number.isNaN(ngayHetHan.getTime()) && ngayHetHan.getTime() > Date.now()
  }, [nguoiDung?.plan_type, nguoiDung?.premium_expires_at])

  const xuLyDangKyPremium = async (planKey) => {
    setDangDangKy(planKey)
    try {
      const ketQua = await dangKyGoiPremium(planKey)
      if (!ketQua.thanhCong) throw new Error(ketQua.loiMessage || 'Đăng ký premium thất bại')
      toast.success(ketQua.data?.thong_bao || 'Đăng ký gói premium thành công')
      await lamMoiThongTinNguoiDung({ imLang: true })
    } catch (error) {
      toast.error(error.message || 'Không thể đăng ký premium')
    } finally {
      setDangDangKy('')
    }
  }

  const dinhDangVND = (so) => {
    return new Intl.NumberFormat('vi-VN').format(so) + ' ₫'
  }

  const tokenHienTai = nguoiDung?.token_balance ?? 0

  return (
    <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-10 gap-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <Crown className="w-8 h-8 text-amber-300" />
              Nâng cấp tài khoản
            </h1>
            <p className="text-white/60">Chọn gói Premium phù hợp để mở khóa toàn bộ tính năng chuyển đổi.</p>
          </div>
          
          {/* Ví Token */}
          <div className="flex items-center gap-4 bg-white/5 border border-white/10 p-4 rounded-2xl w-full md:w-auto shadow-xl backdrop-blur-md">
            <div>
              <p className="text-xs text-white/50 uppercase tracking-widest font-semibold mb-1">Ví của bạn</p>
              <div className="flex items-center gap-2">
                <Wallet className="w-5 h-5 text-amber-400" />
                <span className="text-2xl font-bold text-white">{dinhDangVND(tokenHienTai)}</span>
              </div>
              <p className="text-[10px] text-white/30 mt-0.5">1 Token = 1 VNĐ</p>
            </div>
            <div className="w-px h-12 bg-white/10 mx-2"></div>
            <button 
              onClick={() => setIsNapModalOpen(true)}
              className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white font-bold rounded-xl shadow-lg transition transform hover:scale-105 inline-flex items-center gap-2"
            >
              <CreditCard className="w-4 h-4" />
              Nạp tiền
            </button>
          </div>
        </div>

        {/* Premium Status Banner */}
        {premiumDangHieuLuc && (
          <div className="bg-emerald-500/15 border border-emerald-500/30 p-5 rounded-2xl mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 text-emerald-100">
            <div>
              <p className="font-bold text-lg">✨ Bạn đang là thành viên Premium!</p>
              <p className="text-sm opacity-80 mt-1">Đăng ký thêm sẽ cộng dồn hạn sử dụng thay vì thay thế gói hiện tại.</p>
            </div>
            <div className="px-4 py-2 bg-emerald-500/20 rounded-xl text-sm font-mono whitespace-nowrap">
              Hết hạn: {new Date(nguoiDung.premium_expires_at).toLocaleDateString('vi-VN')}
            </div>
          </div>
        )}

        {/* Pricing Cards */}
        {dangTai ? (
          <div className="flex justify-center py-20"><Zap className="w-10 h-10 animate-bounce text-amber-300" /></div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
            {Object.entries(danhSachGoi).map(([key, plan]) => {
              const isPopular = key === 'premium_30d'
              const isAffordable = tokenHienTai >= plan.token_cost
              const thieu = plan.token_cost - tokenHienTai

              return (
                <div 
                  key={key} 
                  className={`relative glass-card rounded-3xl flex flex-col transition-all duration-300 transform overflow-hidden
                    ${isPopular 
                      ? 'border-2 border-primary-500/60 shadow-2xl shadow-primary-500/20 md:-translate-y-4 md:scale-[1.03]' 
                      : 'border border-white/10 hover:border-white/20 hover:-translate-y-2'}`}
                >
                  {/* Popular Badge */}
                  {isPopular && (
                    <div className="bg-gradient-to-r from-primary-600 to-purple-600 text-white text-xs font-bold uppercase tracking-wider py-2 px-4 text-center">
                      ⭐ Phổ biến nhất
                    </div>
                  )}

                  <div className="p-8 flex flex-col flex-1">
                    {/* Plan Name & Price */}
                    <div className="mb-6">
                      <p className={`text-sm font-semibold uppercase tracking-wider mb-3 ${isPopular ? 'text-primary-300' : 'text-white/50'}`}>
                        {plan.name}
                      </p>
                      <div className="flex items-baseline gap-1">
                        <span className="text-4xl font-extrabold text-white">{new Intl.NumberFormat('vi-VN').format(plan.token_cost)}</span>
                        <span className="text-lg text-white/40">₫</span>
                      </div>
                      <p className="text-sm text-white/50 mt-2">{plan.phu_hop}</p>
                    </div>

                    {/* Features List */}
                    <div className="bg-white/5 rounded-xl p-4 mb-6 flex-1">
                      <ul className="space-y-3 text-sm text-white/80 list-none">
                        <li className="flex items-center gap-3">
                          <CheckIcon /> <span className="font-semibold text-white">{plan.so_ngay} ngày</span> sử dụng Premium
                        </li>
                        <li className="flex items-center gap-3">
                          <CheckIcon /> Xử lý <span className="font-semibold text-white">công thức phức tạp</span>
                        </li>
                        <li className="flex items-center gap-3">
                          <CheckIcon /> Ưu tiên hàng đợi chuyển đổi
                        </li>
                        <li className="flex items-center gap-3">
                          <CheckIcon /> Không giới hạn số lần dùng
                        </li>
                        {plan.tiet_kiem && (
                          <li className="flex items-center gap-3 text-emerald-300 font-medium">
                            <CheckIcon color="text-emerald-400" /> Tiết kiệm hơn so với gói Tháng
                          </li>
                        )}
                      </ul>
                    </div>

                    {/* Action Button */}
                    <div className="mt-auto">
                      {isAffordable ? (
                        <NutBam 
                          onClick={() => xuLyDangKyPremium(key)}
                          dangTai={dangDangKy === key}
                          disabled={dangDangKy !== '' && dangDangKy !== key}
                          className={`w-full !py-3.5 !rounded-xl !font-bold !text-base ${isPopular ? '!bg-primary-600 hover:!bg-primary-500' : '!bg-white/10 hover:!bg-white/20'}`}
                        >
                          Kích hoạt ngay
                        </NutBam>
                      ) : (
                        <button 
                          onClick={() => setIsNapModalOpen(true)}
                          className={`w-full py-3.5 rounded-xl font-bold text-sm transition flex justify-center items-center gap-2
                            ${isPopular 
                              ? 'bg-primary-600/20 border border-primary-500/40 text-primary-200 hover:bg-primary-600/30' 
                              : 'bg-white/5 border border-dashed border-white/20 text-white/50 hover:text-white hover:border-white/40'}`}
                        >
                          <CreditCard className="w-4 h-4" />
                          Nạp thêm {dinhDangVND(thieu)}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Hướng dẫn nạp tiền */}
        <div className="mt-12 bg-white/5 border border-white/10 rounded-2xl p-6">
          <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
            <Coins className="w-5 h-5 text-amber-400" />
            Hướng dẫn nạp tiền
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-white/70">
            <div className="flex gap-3">
              <span className="bg-primary-600/20 text-primary-300 w-8 h-8 rounded-full flex items-center justify-center font-bold shrink-0">1</span>
              <p>Nhấn nút <strong className="text-white">"Nạp tiền"</strong> ở phía trên và chọn số tiền muốn nạp.</p>
            </div>
            <div className="flex gap-3">
              <span className="bg-primary-600/20 text-primary-300 w-8 h-8 rounded-full flex items-center justify-center font-bold shrink-0">2</span>
              <p>Quét <strong className="text-white">mã QR</strong> hiện ra bằng App ngân hàng và chuyển khoản <strong className="text-white">đúng nội dung</strong>.</p>
            </div>
            <div className="flex gap-3">
              <span className="bg-primary-600/20 text-primary-300 w-8 h-8 rounded-full flex items-center justify-center font-bold shrink-0">3</span>
              <p>Hệ thống tự động xác nhận trong <strong className="text-white">3-10 giây</strong> và cộng tiền vào ví.</p>
            </div>
          </div>
        </div>
      </div>

      <NapTokenModal isOpen={isNapModalOpen} onClose={() => setIsNapModalOpen(false)} />
    </div>
  )
}

const CheckIcon = ({ color = "text-primary-400" }) => (
  <svg className={`w-5 h-5 ${color} shrink-0`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
)

export default TrangPremium
