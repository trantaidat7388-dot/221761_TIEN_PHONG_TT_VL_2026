import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Crown, Zap, Coins, CreditCard, Plus, CheckCircle2, ArrowRight, Star, Shield, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../../context/AuthContext'
import { layThongTinGoiPremium } from '../../services/api'
import { NutBam } from '../../components'

const TrangPremium = () => {
  const navigate = useNavigate()
  const { nguoiDung, lamMoiThongTinNguoiDung } = dungXacThuc()
  const [dangTai, setDangTai] = useState(true)
  const [danhSachGoi, setDanhSachGoi] = useState({})
  const [activeTab, setActiveTab] = useState('subscription') // 'subscription' | 'payg'

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

  useEffect(() => { taiThongTin() }, [])

  const premiumDangHieuLuc = useMemo(() => {
    if (nguoiDung?.plan_type !== 'premium') return false
    const raw = nguoiDung?.premium_expires_at
    if (!raw) return false
    const ngayHetHan = new Date(raw)
    return !Number.isNaN(ngayHetHan.getTime()) && ngayHetHan.getTime() > Date.now()
  }, [nguoiDung?.plan_type, nguoiDung?.premium_expires_at])

  const fmt = (so) => new Intl.NumberFormat('vi-VN').format(so)
  const tokenHienTai = nguoiDung?.token_balance ?? 0

  const xuLyMuaTokenLe = (amountVnd, tokenAmount) => {
    navigate('/thanh-toan', {
      state: { amountVnd, planName: `Nạp ${fmt(tokenAmount)} Token`, tokenAmount, type: 'topup' }
    })
  }

  const xuLyMuaCombo = (key) => {
    const plan = danhSachGoi?.[key]
    if (!plan) return
    const comboVnd = plan.price_vnd || 50000
    const tokenBonus = plan.token_bonus || 0
    navigate('/thanh-toan', {
      state: {
        amountVnd: comboVnd, planKey: key,
        planName: `Combo ${plan.name}`, planDays: plan.so_ngay,
        tokenAmount: tokenBonus, type: 'combo'
      }
    })
  }

  // Nạp lẻ — KHÔNG THƯỞNG, chỉ nhận đúng số token
  const GOI_NAP_LE = [
    { token: 100, price: 10000, tier: 'Starter' },
    { token: 250, price: 20000, tier: 'Basic' },
    { token: 700, price: 50000, tier: 'Standard' },
    { token: 1500, price: 100000, tier: 'Pro' },
  ]

  return (
    <div className="min-h-screen bg-[#08090d] pt-24 pb-20 px-4 overflow-hidden relative">
      {/* Ambient Glow */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-primary-600/8 rounded-full blur-[150px] -translate-y-1/2 pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-amber-500/5 rounded-full blur-[120px] translate-y-1/2 pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        
        {/* ── HERO ─────────────────────────────────────────────────────────── */}
        <div className="text-center mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-amber-500/10 to-primary-500/10 border border-amber-500/20 text-amber-300 text-[11px] font-black uppercase tracking-[0.2em] mb-5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Premium Experience
          </motion.div>
          <h1 className="text-4xl md:text-6xl font-black text-white mb-5 tracking-tight leading-[1.1]">
            Đầu tư cho <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-white to-primary-300">
              nghiên cứu của bạn
            </span>
          </h1>
          <p className="text-white/40 max-w-xl mx-auto text-sm leading-relaxed font-light">
            Mua gói Premium để nhận Token thưởng và giảm 55% chi phí chuyển đổi.
            <br />Hoặc nạp lẻ Token — trả bao nhiêu nhận bấy nhiêu, không ràng buộc.
          </p>
        </div>

        {/* ── USER STATUS ──────────────────────────────────────────────────── */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-2xl p-6 mb-14 border border-white/[0.06] bg-white/[0.02] backdrop-blur-sm flex flex-col md:flex-row items-center justify-between gap-6"
        >
          <div className="flex items-center gap-5">
            <div className="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 rounded-2xl flex items-center justify-center shadow-lg shadow-amber-500/20 transform rotate-3">
              <Coins className="w-7 h-7 text-white" />
            </div>
            <div>
              <p className="text-white/30 text-[9px] uppercase tracking-[0.25em] font-bold mb-1">Số dư hiện tại</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-black text-white tracking-tighter">{fmt(tokenHienTai)}</span>
                <span className="text-amber-400/80 font-black text-[10px] uppercase tracking-widest">Token</span>
              </div>
            </div>
          </div>

          <div className="h-12 w-px bg-white/[0.06] hidden md:block" />

          <div className="flex items-center gap-5">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg transform -rotate-3 transition-all duration-700 ${premiumDangHieuLuc ? 'bg-gradient-to-br from-primary-500 to-violet-600 shadow-primary-500/20' : 'bg-white/[0.03] border border-white/[0.06]'}`}>
              <Crown className={`w-7 h-7 ${premiumDangHieuLuc ? 'text-white' : 'text-white/15'}`} />
            </div>
            <div>
              <p className="text-white/30 text-[9px] uppercase tracking-[0.25em] font-bold mb-1">Trạng thái</p>
              <div className="flex items-center gap-2.5">
                <span className={`text-lg font-bold ${premiumDangHieuLuc ? 'text-primary-300' : 'text-white/40'}`}>
                  {premiumDangHieuLuc ? 'Premium Member' : 'Free Tier'}
                </span>
                {premiumDangHieuLuc && (
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 text-[8px] font-black uppercase tracking-wider">Active</span>
                )}
              </div>
              {premiumDangHieuLuc && (
                <p className="text-white/20 text-[10px] mt-1 font-mono">Hết hạn: {new Date(nguoiDung.premium_expires_at).toLocaleDateString('vi-VN')}</p>
              )}
            </div>
          </div>
        </motion.div>

        {/* ── PRICING TABS (TOGGLE) ────────────────────────────────────────── */}
        <div className="flex justify-center mb-12">
          <div className="bg-white/[0.03] p-1.5 rounded-2xl border border-white/[0.06] flex items-center backdrop-blur-sm">
            <button
              onClick={() => setActiveTab('subscription')}
              className={`relative px-8 py-3.5 rounded-xl text-sm font-black uppercase tracking-wider transition-all duration-300 ${
                activeTab === 'subscription' ? 'text-white' : 'text-white/40 hover:text-white/70'
              }`}
            >
              {activeTab === 'subscription' && (
                <motion.div
                  layoutId="pricing-tab"
                  className="absolute inset-0 bg-gradient-to-br from-primary-500/20 to-violet-500/20 border border-primary-500/30 shadow-lg rounded-xl"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <Crown className="w-4 h-4" /> Đăng ký Premium
              </span>
            </button>
            <button
              onClick={() => setActiveTab('payg')}
              className={`relative px-8 py-3.5 rounded-xl text-sm font-black uppercase tracking-wider transition-all duration-300 ${
                activeTab === 'payg' ? 'text-white' : 'text-white/40 hover:text-white/70'
              }`}
            >
              {activeTab === 'payg' && (
                <motion.div
                  layoutId="pricing-tab"
                  className="absolute inset-0 bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/30 shadow-lg rounded-xl"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <Coins className="w-4 h-4" /> Nạp lẻ Token (Pay-as-you-go)
              </span>
            </button>
          </div>
        </div>

        {/* ── SECTION 1: PREMIUM COMBO (SUBSCRIPTION) ──────────────────────── */}
        {activeTab === 'subscription' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mb-20"
          >
            <p className="text-center text-white/50 text-sm mb-10 max-w-xl mx-auto leading-relaxed">
              Mua gói Premium để kích hoạt <span className="text-white font-semibold">Trạng thái Premium</span>, nhận ngay Token thưởng, và giảm chi phí chuyển đổi vĩnh viễn xuống <span className="text-primary-400 font-semibold">0.4 Token / 1000 từ</span> (tiết kiệm 55%).
            </p>

          {dangTai ? (
            <div className="flex justify-center py-20"><Zap className="w-10 h-10 animate-bounce text-primary-400" /></div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(danhSachGoi).map(([key, plan]) => {
                const isPopular = key === 'premium_30d'
                const comboVnd = plan.price_vnd || 50000
                const tokenBonus = plan.token_bonus || 0

                return (
                  <motion.div 
                    key={key} 
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ y: -6, scale: 1.02 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    className={`relative overflow-hidden rounded-3xl p-[1px] flex flex-col
                      ${isPopular 
                        ? 'bg-gradient-to-br from-primary-500 via-violet-500 to-amber-400 shadow-2xl shadow-primary-500/20' 
                        : 'bg-gradient-to-br from-white/10 to-white/[0.03]'}`}
                  >
                    <div className="bg-[#0c0e14] rounded-[calc(1.5rem-1px)] p-7 flex flex-col h-full">
                      {isPopular && (
                        <div className="absolute top-5 right-5 px-3 py-1 rounded-full bg-gradient-to-r from-primary-500 to-violet-500 text-white text-[8px] font-black uppercase tracking-widest shadow-lg">
                          Phổ biến nhất
                        </div>
                      )}

                      <div className="mb-7">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 ${isPopular ? 'bg-primary-500/15' : 'bg-white/[0.04]'}`}>
                          {key === 'premium_7d' ? <Zap className="w-5 h-5 text-blue-400" /> : key === 'premium_365d' ? <Star className="w-5 h-5 text-amber-400" /> : <Crown className="w-5 h-5 text-primary-400" />}
                        </div>
                        <h3 className="text-xl font-black text-white mb-2 tracking-tight">{plan.name}</h3>
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-3xl font-black text-white tracking-tighter">{fmt(comboVnd)} ₫</span>
                          <span className="text-white/25 text-xs font-medium">/ kỳ</span>
                        </div>
                      </div>

                      <div className="space-y-4 mb-8 flex-1">
                        {/* Token Bonus Badge */}
                        <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-500/10 to-amber-500/5 border border-amber-500/15">
                          <p className="text-amber-400/70 text-[9px] font-black uppercase tracking-[0.2em] mb-1">Cộng thêm</p>
                          <div className="text-2xl font-black text-amber-300">+{fmt(tokenBonus)} <span className="text-sm text-amber-400/60">Token</span></div>
                        </div>

                        <ul className="space-y-3">
                          <li className="flex items-center gap-3 text-[13px] text-white/50">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400/80 shrink-0" />
                            <span>Kích hoạt <strong className="text-white/80">{plan.so_ngay} ngày</strong> Premium</span>
                          </li>
                          <li className="flex items-center gap-3 text-[13px] text-white/50">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400/80 shrink-0" />
                            <span>Phí chuyển đổi chỉ <strong className="text-emerald-300">0.4 Token / 1000 từ</strong></span>
                          </li>
                          <li className="flex items-center gap-3 text-[13px] text-white/50">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400/80 shrink-0" />
                            <span>Chuyển đổi không giới hạn (theo số dư Token hiện có)</span>
                          </li>
                        </ul>
                      </div>

                      <button 
                        onClick={() => xuLyMuaCombo(key)}
                        className={`w-full py-3.5 rounded-2xl font-black text-[11px] uppercase tracking-[0.15em] transition-all duration-300 flex items-center justify-center gap-2.5
                          ${isPopular 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white shadow-xl shadow-primary-500/25' 
                            : 'bg-white/[0.04] hover:bg-white/[0.08] text-white/80 border border-white/[0.06]'}`}
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
        </motion.div>
        )}

        {/* ── SECTION 2: NẠP LẺ (KHÔNG THƯỞNG) ────────────────────────────── */}
        {activeTab === 'payg' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mb-16"
          >
            <p className="text-center text-white/50 text-sm mb-10 max-w-xl mx-auto leading-relaxed">
              Mua các gói nạp lẻ (Pay-as-you-go). Trả bao nhiêu nhận bấy nhiêu — không ràng buộc thời gian.
              <br />Phí chuyển đổi mặc định: <span className="text-white font-semibold">1 Token / 1000 từ</span>. 
              <br /><span className="text-white/30 text-[11px] italic mt-2 inline-block">Lưu ý: Nạp lẻ Token sẽ không tự động kích hoạt trạng thái Premium.</span>
            </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {GOI_NAP_LE.map((item, idx) => (
              <motion.div 
                key={idx}
                whileHover={{ y: -4 }}
                className="rounded-2xl p-5 border border-white/[0.05] bg-white/[0.015] flex flex-col items-center group cursor-pointer hover:border-white/10 transition-all duration-300"
                onClick={() => xuLyMuaTokenLe(item.price, item.token)}
              >
                <p className="text-white/20 text-[8px] font-black uppercase tracking-[0.2em] mb-3">{item.tier}</p>
                <h3 className="text-3xl font-black text-white mb-1 tracking-tighter">{fmt(item.token)}</h3>
                <p className="text-white/30 font-bold text-[10px] uppercase tracking-widest mb-4">Token</p>
                <div className="w-full h-px bg-white/[0.04] mb-4" />
                <div className="text-sm font-bold text-white/50">{fmt(item.price)} ₫</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
        )}

        {/* ── FOOTER ───────────────────────────────────────────────────────── */}
        <div className="mt-20 text-center">
          <p className="text-white/15 text-xs leading-relaxed">
            Thanh toán an toàn qua QR Code ngân hàng · Xác nhận tự động trong 3–10 giây
            <br />Nếu gặp sự cố, liên hệ Admin để được hỗ trợ cộng Token thủ công.
          </p>
        </div>
      </div>
    </div>
  )
}

export default TrangPremium
