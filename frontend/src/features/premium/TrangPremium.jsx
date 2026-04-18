import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Crown, Zap, Coins, CreditCard, Plus, CheckCircle2, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../../context/AuthContext'
import { layThongTinGoiPremium } from '../../services/api'
import { NutBam } from '../../components'

const TrangPremium = () => {
  const navigate = useNavigate()
  const { nguoiDung, lamMoiThongTinNguoiDung } = dungXacThuc()
  const [dangTai, setDangTai] = useState(true)
  const [danhSachGoi, setDanhSachGoi] = useState({})

  const taiThongTin = async () => {
    setDangTai(true)
    try {
      const ketQua = await layThongTinGoiPremium()
      if (!ketQua.thanhCong) throw new Error(ketQua.loiMessage || 'Không tải được thông tin premium')
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

  const dinhDangVND = (so) => new Intl.NumberFormat('vi-VN').format(so) + ' ₫'
  const dinhDangToken = (so) => new Intl.NumberFormat('vi-VN').format(so) + ' token'

  const tokenHienTai = nguoiDung?.token_balance ?? 0

  const xuLyMuaTokenLe = (amountVnd, tokenAmount) => {
    navigate('/thanh-toan', {
      state: {
        amountVnd,
        planName: `Nạp lẻ ${tokenAmount} Token`,
        tokenAmount,
        type: 'topup'
      }
    })
  }

  const xuLyMuaCombo = (key) => {
    const plan = danhSachGoi?.[key]
    if (!plan) return

    // Quy đổi VND dựa trên plan (Giả định giá cố định cho combo Way A)
    let comboVnd = 50000
    let tokenBonus = 600
    if (key === 'premium_7d') { comboVnd = 20000; tokenBonus = 200 }
    if (key === 'premium_365d') { comboVnd = 500000; tokenBonus = 7000 }

    navigate('/thanh-toan', {
      state: {
        amountVnd: comboVnd,
        planKey: key,
        planName: `Combo ${plan.name}`,
        planDays: plan.so_ngay,
        tokenAmount: tokenBonus,
        type: 'combo'
      }
    })
  }

  return (
    <div className="min-h-screen bg-[#0a0c10] pt-24 pb-20 px-4 overflow-hidden relative">
      {/* Background Decor */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary-600/10 rounded-full blur-[120px] -translate-y-1/2 pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-amber-500/5 rounded-full blur-[100px] translate-y-1/2 pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        
        {/* Header Section */}
        <div className="text-center mb-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-bold mb-4"
          >
            <Crown className="w-3.5 h-3.5" />
            NÂNG CẤP TRẢI NGHIỆM
          </motion.div>
          <h1 className="text-3xl md:text-5xl font-black text-white mb-4 tracking-tight leading-tight">
            Chọn gói phù hợp với <br /> 
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 via-white to-amber-300">
              nhu cầu của bạn
            </span>
          </h1>
          <p className="text-white/50 max-w-2xl mx-auto text-base">
            Sử dụng hệ thống Token linh hoạt hoặc đăng ký Premium để nhận ưu đãi lên đến 60% chi phí xử lý tài liệu.
          </p>
        </div>

        {/* User Status Summary */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card rounded-[1.5rem] p-6 mb-12 border border-white/5 flex flex-col md:flex-row items-center justify-between gap-6"
        >
          <div className="flex items-center gap-5">
            <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-lg transform rotate-3">
              <Coins className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-white/40 text-[10px] uppercase tracking-widest font-bold mb-0.5">Số dư hiện tại</p>
              <div className="flex items-baseline gap-1.5">
                <span className="text-3xl font-black text-white tracking-tighter">{new Intl.NumberFormat('vi-VN').format(tokenHienTai)}</span>
                <span className="text-amber-400 font-bold text-xs uppercase italic">Tokens</span>
              </div>
            </div>
          </div>

          <div className="h-10 w-px bg-white/10 hidden md:block" />

          <div className="flex items-center gap-5">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-lg transform -rotate-3 transition-colors duration-500 ${premiumDangHieuLuc ? 'bg-gradient-to-br from-primary-500 to-primary-700' : 'bg-white/5 border border-white/10'}`}>
              <Crown className={`w-6 h-6 ${premiumDangHieuLuc ? 'text-white' : 'text-white/20'}`} />
            </div>
            <div>
              <p className="text-white/40 text-[10px] uppercase tracking-widest font-bold mb-0.5">Trạng thái tài khoản</p>
              <div className="flex items-center gap-2">
                <span className={`text-lg font-bold ${premiumDangHieuLuc ? 'text-primary-400' : 'text-white/60'}`}>
                  {premiumDangHieuLuc ? 'Thành viên Premium' : 'Tài khoản Miễn phí'}
                </span>
                {premiumDangHieuLuc && (
                  <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 text-[9px] font-bold uppercase">Active</span>
                )}
              </div>
              {premiumDangHieuLuc && (
                <p className="text-white/30 text-[10px] mt-0.5 font-mono">Hết hạn: {new Date(nguoiDung.premium_expires_at).toLocaleDateString('vi-VN')}</p>
              )}
            </div>
          </div>
        </motion.div>

        {/* Section 1: Premium Combo (Combo Gói) - NOW ON TOP */}
        <div className="mb-16">
          <div className="flex items-center gap-4 mb-6">
            <div className="h-px bg-gradient-to-r from-transparent to-primary-500/30 flex-1" />
            <h2 className="text-xl font-bold text-white flex items-center gap-3">
              <Crown className="w-6 h-6 text-primary-400" />
              Gói Combo Premium
            </h2>
            <div className="h-px bg-gradient-to-l from-transparent to-primary-500/30 flex-1" />
          </div>

          {dangTai ? (
            <div className="flex justify-center py-20"><Zap className="w-10 h-10 animate-bounce text-primary-400" /></div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(danhSachGoi).map(([key, plan]) => {
                const isPopular = key === 'premium_30d'
                let comboVnd = 50000
                let tokenBonus = 600
                if (key === 'premium_7d') { comboVnd = 20000; tokenBonus = 200 }
                if (key === 'premium_365d') { comboVnd = 500000; tokenBonus = 7000 }

                return (
                  <motion.div 
                    key={key} 
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ y: -8 }}
                    className={`relative overflow-hidden rounded-[2rem] p-0.5 flex flex-col transition-all duration-500
                      ${isPopular 
                        ? 'bg-gradient-to-br from-primary-500 via-purple-500 to-amber-500' 
                        : 'bg-white/10 border border-white/5'}`}
                  >
                    <div className="bg-[#0f1115] rounded-[1.9rem] p-6 flex flex-col h-full">
                      {isPopular && (
                        <div className="absolute top-4 right-4 px-2 py-0.5 rounded-full bg-primary-500 text-white text-[9px] font-black uppercase tracking-wider">
                          Đề xuất
                        </div>
                      )}

                      <div className="mb-6">
                        <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center mb-4">
                          {key === 'premium_7d' ? <Zap className="w-5 h-5 text-blue-400" /> : <Crown className="w-5 h-5 text-primary-400" />}
                        </div>
                        <h3 className="text-xl font-bold text-white mb-1">{plan.name}</h3>
                        <div className="flex items-baseline gap-1">
                          <span className="text-3xl font-black text-white tracking-tighter lowercase">{dinhDangVND(comboVnd)}</span>
                          <span className="text-white/40 text-xs">/ kỳ</span>
                        </div>
                      </div>

                      <div className="space-y-3 mb-6 flex-1">
                        <div className="p-3 rounded-xl bg-primary-500/10 border border-primary-500/20">
                          <p className="text-primary-300 text-[10px] font-bold uppercase mb-0.5">Tặng kèm ngay</p>
                          <div className="text-lg font-bold text-white">+{tokenBonus} Tokens</div>
                        </div>

                        <ul className="space-y-3 text-xs text-white/60">
                          <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                            <span>Kích hoạt <strong className="text-white">{plan.so_ngay} ngày</strong> Premium</span>
                          </li>
                          <li className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                            <span>Phí chuyển đổi <strong className="text-white">0.4 Token/trang</strong></span>
                          </li>
                        </ul>
                      </div>

                      <button 
                        onClick={() => xuLyMuaCombo(key)}
                        className={`w-full py-3 rounded-xl font-black text-[11px] uppercase tracking-wider transition-all duration-300 flex items-center justify-center gap-2
                          ${isPopular 
                            ? 'bg-primary-600 hover:bg-primary-500 text-white shadow-lg shadow-primary-500/20' 
                            : 'bg-white/5 hover:bg-white/10 text-white border border-white/10'}`}
                      >
                        Bắt đầu ngay
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
        </div>

        {/* Section 2: Individual Top-up (Nạp lẻ) - NOW AT BOTTOM */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-6">
            <div className="h-px bg-gradient-to-r from-transparent to-white/10 flex-1" />
            <h2 className="text-xl font-bold text-white flex items-center gap-3">
              <Zap className="w-5 h-5 text-amber-500" />
              Nạp lẻ Token tự do
            </h2>
            <div className="h-px bg-gradient-to-l from-transparent to-white/10 flex-1" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { amount: 100, price: 10000, label: 'Khởi đầu', color: 'bg-slate-500/10' },
              { amount: 250, price: 20000, label: 'Cơ bản', color: 'bg-blue-500/10', bonus: '25%' },
              { amount: 700, price: 50000, label: 'Phổ biến', color: 'bg-primary-500/10', bonus: '40%' },
              { amount: 1500, price: 100000, label: 'Pro', color: 'bg-emerald-500/10', bonus: '50%' }
            ].map((item, idx) => (
              <motion.div 
                key={idx}
                whileHover={{ y: -4 }}
                className="glass-card rounded-2xl p-4 border border-white/5 flex flex-col items-center group cursor-pointer"
                onClick={() => xuLyMuaTokenLe(item.price, item.amount)}
              >
                <div className={`w-10 h-10 ${item.color} rounded-lg flex items-center justify-center mb-3 transition-transform group-hover:scale-110`}>
                  <Coins className="w-5 h-5 text-white" />
                </div>
                <p className="text-white/40 text-[9px] font-bold uppercase mb-0.5">{item.label}</p>
                <h3 className="text-2xl font-black text-white mb-0.5 tracking-tight">{item.amount}</h3>
                <p className="text-amber-400 font-bold text-[10px] mb-3 uppercase italic">Tokens</p>
                <div className="w-full h-px bg-white/5 mb-3" />
                <div className="flex flex-col items-center gap-2 w-full">
                  <div className="text-base font-bold text-white">{dinhDangVND(item.price)}</div>
                  {item.bonus && (
                    <span className="px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[8px] font-bold">Thưởng {item.bonus}</span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Footer info */}
        <div className="mt-20 text-center">
          <p className="text-white/30 text-sm">
            Thanh toán an toàn qua QR Code ngân hàng. <br />
            Nếu gặp sự cố, vui lòng liên hệ Admin qua kênh hỗ trợ để được cộng Token thủ công.
          </p>
        </div>
      </div>
    </div>
  )
}

export default TrangPremium
