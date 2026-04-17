import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Crown, Zap, Coins, CreditCard } from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../../context/AuthContext'
import { dangKyGoiPremium, layThongTinGoiPremium } from '../../services/api'
import { NutBam } from '../../components'

const TrangPremium = () => {
  const navigate = useNavigate()
  const { nguoiDung, lamMoiThongTinNguoiDung } = dungXacThuc()
  const [dangTai, setDangTai] = useState(true)
  const [dangDangKy, setDangDangKy] = useState('')
  const [danhSachGoi, setDanhSachGoi] = useState({})

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

  const dinhDangToken = (so) => {
    return new Intl.NumberFormat('vi-VN').format(so) + ' token'
  }

  const tokenHienTai = nguoiDung?.token_balance ?? 0

  const xuLyMuaGoi = async (key, tokenCost) => {
    if (tokenHienTai >= tokenCost) {
      await xuLyDangKyPremium(key)
      return
    }
    const plan = danhSachGoi?.[key] || null
    const soTienCanNap = tokenCost
    navigate('/thanh-toan', {
      state: {
        amountVnd: tokenCost * 100, // 1 Token = 100 VNĐ
        planKey: key,
        planName: plan?.name || 'Premium',
        planDays: plan?.so_ngay || 0,
        planCost: tokenCost,
      }
    })
  }

  return (
    <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4">
      <div className="max-w-6xl mx-auto">
        
        {/* Global Token Balance Hero Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative overflow-hidden glass-card rounded-3xl p-8 mb-10 border border-amber-500/20 shadow-2xl shadow-amber-500/10"
        >
          {/* Decorative background elements */}
          <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-amber-500/10 rounded-full blur-[100px] pointer-events-none" />
          <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-60 h-60 bg-primary-600/10 rounded-full blur-[80px] pointer-events-none" />
          
          <div className="relative flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 bg-gradient-to-br from-amber-400 to-amber-600 rounded-2xl flex items-center justify-center shadow-lg transform rotate-3 hover:rotate-0 transition-transform duration-500">
                <Coins className="w-10 h-10 text-white" />
              </div>
              <div className="text-center md:text-left">
                <p className="text-amber-200/60 text-xs uppercase tracking-[0.2em] font-black mb-1">Tài khoản của bạn hiện có</p>
                <div className="flex items-baseline gap-3">
                  <h2 className="text-5xl md:text-6xl font-black text-white tracking-tighter drop-shadow-md">
                    {new Intl.NumberFormat('vi-VN').format(tokenHienTai)}
                  </h2>
                  <span className="text-amber-400 font-bold text-xl uppercase italic">Token</span>
                </div>
              </div>
            </div>

            <div className="flex flex-col items-center md:items-end gap-2">
              <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white/50 text-sm backdrop-blur-sm">
                Đổi được khoảng <span className="text-white font-bold">{(tokenHienTai).toLocaleString()}</span> trang LaTeX tiêu chuẩn
              </div>
              <p className="text-white/30 text-[10px] italic">1.000 từ quy đổi thành 1 trang chuẩn IEEE.</p>
            </div>
          </div>
        </motion.div>

        {/* Premium Packages Header */}
        <div className="mb-10 text-center md:text-left">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3 justify-center md:justify-start">
            <Crown className="w-8 h-8 text-amber-300" />
            Bảng giá các gói Premium
          </h1>
          <p className="text-white/60">Lựa chọn gói phù hợp để đẩy nhanh tiến độ nghiên cứu của bạn.</p>
        </div>

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

        {dangTai ? (
          <div className="flex justify-center py-20"><Zap className="w-10 h-10 animate-bounce text-amber-300" /></div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
            {Object.entries(danhSachGoi).map(([key, plan]) => {
              const isPopular = key === 'premium_30d'
              const isAffordable = tokenHienTai >= plan.token_cost

              return (
                <div 
                  key={key} 
                  className={`relative glass-card rounded-3xl flex flex-col transition-all duration-300 transform overflow-hidden
                    ${isPopular 
                      ? 'border-2 border-primary-500/60 shadow-2xl shadow-primary-500/20 md:-translate-y-4 md:scale-[1.03]' 
                      : 'border border-white/10 hover:border-white/20 hover:-translate-y-2'}`}
                >
                  {isPopular && (
                    <div className="bg-gradient-to-r from-primary-600 to-purple-600 text-white text-xs font-bold uppercase tracking-wider py-2 px-4 text-center">
                      ⭐ Phổ biến nhất
                    </div>
                  )}

                  <div className="p-8 flex flex-col flex-1">
                    <div className="mb-6">
                      <p className={`text-sm font-semibold uppercase tracking-wider mb-3 ${isPopular ? 'text-primary-300' : 'text-white/50'}`}>
                        {plan.name}
                      </p>
                      <div className="flex items-baseline gap-1">
                        <span className="text-4xl font-extrabold text-white">{new Intl.NumberFormat('vi-VN').format(plan.token_cost)}</span>
                        <span className="text-lg text-white/40">Token</span>
                      </div>
                      <p className="text-sm text-white/50 mt-2">({dinhDangVND(plan.token_cost * 100)}) - {plan.phu_hop}</p>
                    </div>

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

                    <div className="mt-auto">
                      {isAffordable ? (
                        <NutBam 
                          onClick={() => xuLyMuaGoi(key, plan.token_cost)}
                          dangTai={dangDangKy === key}
                          disabled={dangDangKy !== '' && dangDangKy !== key}
                          className={`w-full !py-3.5 !rounded-xl !font-bold !text-base ${isPopular ? '!bg-primary-600 hover:!bg-primary-500' : '!bg-white/10 hover:!bg-white/20'}`}
                        >
                          {premiumDangHieuLuc ? 'Gia hạn gói này' : 'Mua gói này'}
                        </NutBam>
                      ) : (
                        <button 
                          onClick={() => xuLyMuaGoi(key, plan.token_cost)}
                          className={`w-full py-3.5 rounded-xl font-bold text-sm transition flex justify-center items-center gap-2
                            ${isPopular 
                              ? 'bg-primary-600/20 border border-primary-500/40 text-primary-200 hover:bg-primary-600/30' 
                              : 'bg-white/5 border border-dashed border-white/20 text-white/50 hover:text-white hover:border-white/40'}`}
                        >
                          <CreditCard className="w-4 h-4" />
                          {premiumDangHieuLuc ? 'Nạp & Gia hạn' : 'Mua Gói'} ({dinhDangToken(plan.token_cost)})
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        <div className="mt-12 bg-white/5 border border-white/10 rounded-2xl p-6">
          <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            Hướng dẫn mua gói Premium
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-white/70">
            <div className="flex gap-3">
              <span className="bg-primary-600/20 text-primary-300 w-8 h-8 rounded-full flex items-center justify-center font-bold shrink-0">1</span>
              <p>Chọn gói ở phía trên và nhấn nút <strong className="text-white">"Mua gói"</strong> tương ứng.</p>
            </div>
            <div className="flex gap-3">
              <span className="bg-primary-600/20 text-primary-300 w-8 h-8 rounded-full flex items-center justify-center font-bold shrink-0">2</span>
              <p>Quét <strong className="text-white">mã QR</strong> hiện ra bằng App ngân hàng và chuyển khoản <strong className="text-white">đúng nội dung</strong>.</p>
            </div>
            <div className="flex gap-3">
              <span className="bg-primary-600/20 text-primary-300 w-8 h-8 rounded-full flex items-center justify-center font-bold shrink-0">3</span>
              <p>Hệ thống sẽ <strong className="text-white">tự động kích hoạt</strong> gói Premium của bạn trong vài giây ngay sau khi tiền về.</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}

const CheckIcon = ({ color = "text-primary-400" }) => (
  <svg className={`w-5 h-5 ${color} shrink-0`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
)

export default TrangPremium
