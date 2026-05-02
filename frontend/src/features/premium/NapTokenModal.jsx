import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Loader2, QrCode, Copy, CheckCircle2, Coins, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { taoHoaDonNapTien, kiemTraTrangThaiHoaDon, xacNhanHoaDonThuCongDev } from '../../services/api'
import { dungXacThuc } from '../../context/AuthContext'

// Nạp lẻ — KHÔNG THƯỞNG, trả bao nhiêu nhận bấy nhiêu
const GOI_NAP = [
  { vnd: 10000, token: 100, label: '10K' },
  { vnd: 20000, token: 250, label: '20K' },
  { vnd: 50000, token: 700, label: '50K' },
  { vnd: 100000, token: 1500, label: '100K' },
  { vnd: 200000, token: 3200, label: '200K' },
  { vnd: 500000, token: 8500, label: '500K' },
]

const fmt = (n) => new Intl.NumberFormat('vi-VN').format(n)

const NapTokenModal = ({ isOpen, onClose }) => {
  const { lamMoiThongTinNguoiDung } = dungXacThuc()
  const [goiDaChon, setGoiDaChon] = useState(null)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [hoaDon, setHoaDon] = useState(null)
  const [trangThai, setTrangThai] = useState('chon_goi')
  const [demGiay, setDemGiay] = useState(0)
  const [dangXacNhanThuCong, setDangXacNhanThuCong] = useState(false)
  
  useEffect(() => {
    if (isOpen) {
      setGoiDaChon(null); setHoaDon(null); setTrangThai('chon_goi'); setDemGiay(0)
    }
  }, [isOpen])

  useEffect(() => {
    let intervalId = null, timerId = null
    if (trangThai === 'cho_thanh_toan' && hoaDon?.payment_id) {
      timerId = setInterval(() => setDemGiay(p => p + 1), 1000)
      intervalId = setInterval(async () => {
        try {
          const res = await kiemTraTrangThaiHoaDon(hoaDon.payment_id)
          if (res.thanhCong && res.data.status === 'completed') {
            setTrangThai('thanh_cong'); clearInterval(intervalId); clearInterval(timerId)
            toast.success('Nạp Token thành công!')
            await lamMoiThongTinNguoiDung({ imLang: true })
          }
        } catch (e) { console.error(e) }
      }, 5000)
    }
    return () => { clearInterval(intervalId); clearInterval(timerId) }
  }, [trangThai, hoaDon, lamMoiThongTinNguoiDung])

  const xuLyTaoHoaDon = async () => {
    if (!goiDaChon) { toast.error('Vui lòng chọn gói nạp'); return }
    setDangXuLy(true)
    try {
      const res = await taoHoaDonNapTien(goiDaChon.vnd)
      if (!res.thanhCong) throw new Error(res.loiMessage || 'Không thể tạo hóa đơn')
      setHoaDon(res.data); setTrangThai('cho_thanh_toan'); setDemGiay(0)
    } catch (e) { toast.error(e.message) }
    finally { setDangXuLy(false) }
  }

  const copy = (text) => { navigator.clipboard.writeText(text); toast.success('Đã sao chép!') }

  const xuLyXacNhanDev = async () => {
    if (!hoaDon?.payment_id) return
    setDangXacNhanThuCong(true)
    try {
      const res = await xacNhanHoaDonThuCongDev(hoaDon.payment_id)
      if (!res.thanhCong) throw new Error(res.loiMessage)
      setTrangThai('thanh_cong'); toast.success('Xác nhận thành công (dev)')
      await lamMoiThongTinNguoiDung({ imLang: true })
    } catch (e) { toast.error(e.message) }
    finally { setDangXacNhanThuCong(false) }
  }

  const fmtTime = (s) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`

  const bankBin = import.meta.env.VITE_BANK_BIN || '970422'
  const bankAccount = import.meta.env.VITE_BANK_ACCOUNT || '000000000'
  const bankName = import.meta.env.VITE_BANK_ACCOUNT_NAME || 'ADMIN'
  const isDev = bankAccount === '000000000'

  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          {/* Backdrop — high z-index to cover everything */}
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/70 backdrop-blur-md"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 20 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            className="relative w-full max-w-md bg-[#0e1018] border border-white/[0.08] shadow-2xl rounded-3xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/20">
                  <Coins className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-black text-white tracking-tight">Nạp Token</h2>
                  <p className="text-[10px] text-white/25 font-medium uppercase tracking-widest">Trả bao nhiêu nhận bấy nhiêu</p>
                </div>
              </div>
              <button onClick={onClose} className="w-8 h-8 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] flex items-center justify-center text-white/30 hover:text-white transition">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="px-6 pb-6">
              {/* ── STEP 1: Chọn gói ──────────────────────────────────────── */}
              {trangThai === 'chon_goi' && (
                <div className="space-y-5">
                  <div className="grid grid-cols-3 gap-2.5">
                    {GOI_NAP.map(goi => (
                      <button
                        key={goi.vnd}
                        onClick={() => setGoiDaChon(goi)}
                        className={`relative py-4 rounded-2xl border text-center transition-all duration-200 ${
                          goiDaChon?.vnd === goi.vnd 
                            ? 'bg-primary-500/10 border-primary-500/40 shadow-lg shadow-primary-500/10' 
                            : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04] hover:border-white/10'
                        }`}
                      >
                        <div className="text-xl font-black text-white tracking-tight">{fmt(goi.token)}</div>
                        <div className="text-[8px] text-white/20 font-black uppercase tracking-[0.15em] mt-0.5">Tokens</div>
                        <div className="text-[11px] text-white/30 font-semibold mt-2">{goi.label} ₫</div>
                      </button>
                    ))}
                  </div>

                  {goiDaChon && (
                    <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-white/30 text-xs">Bạn sẽ nhận:</span>
                        <span className="text-white font-black text-lg">{fmt(goiDaChon.token)} <span className="text-amber-400/60 text-xs">Token</span></span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-white/30 text-xs">Thanh toán:</span>
                        <span className="text-white/60 font-bold text-sm">{fmt(goiDaChon.vnd)} ₫</span>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={xuLyTaoHoaDon}
                    disabled={!goiDaChon || dangXuLy}
                    className="w-full bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 disabled:opacity-30 disabled:cursor-not-allowed text-white font-black py-4 rounded-2xl transition-all flex items-center justify-center gap-2.5 text-sm uppercase tracking-wider shadow-xl shadow-primary-500/20"
                  >
                    {dangXuLy ? <Loader2 className="w-5 h-5 animate-spin" /> : <QrCode className="w-5 h-5" />}
                    Tạo mã thanh toán
                  </button>
                </div>
              )}

              {/* ── STEP 2: QR Payment ────────────────────────────────────── */}
              {trangThai === 'cho_thanh_toan' && hoaDon && (
                <div className="flex flex-col items-center space-y-4">
                  <p className="text-white/40 text-center text-xs">Mở App ngân hàng, quét mã QR bên dưới</p>
                  
                  <div className="bg-white p-3 rounded-2xl shadow-2xl">
                    <img 
                      src={`https://api.vietqr.io/image/${bankBin}-${bankAccount}-yXwL0O?accountName=${encodeURIComponent(bankName)}&amount=${hoaDon.amount_vnd}&addInfo=${encodeURIComponent(hoaDon.noidung_ck)}`} 
                      alt="QR" className="w-48 h-48 object-cover rounded-xl"
                      onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
                    />
                    <div className="hidden w-48 h-48 bg-gray-100 items-center justify-center flex-col gap-2 rounded-xl text-gray-400">
                      <QrCode className="w-8 h-8" />
                      <span className="text-[10px]">Chưa cấu hình</span>
                    </div>
                  </div>

                  <div className="w-full bg-white/[0.02] border border-white/[0.06] rounded-2xl overflow-hidden text-sm">
                    <div className="flex justify-between items-center p-3 border-b border-white/[0.04]">
                      <span className="text-white/25 text-xs">Số tiền</span>
                      <span className="font-black text-amber-300">{fmt(hoaDon.amount_vnd)} ₫</span>
                    </div>
                    <div className="flex justify-between items-center p-3 border-b border-white/[0.04]">
                      <span className="text-white/25 text-xs">Nhận được</span>
                      <span className="font-black text-emerald-300">{fmt(hoaDon.token_amount)} Token</span>
                    </div>
                    <div className="flex justify-between items-center p-3">
                      <div>
                        <p className="text-white/25 text-[10px] mb-0.5">Nội dung CK</p>
                        <p className="font-mono text-cyan-300 font-bold text-xs">{hoaDon.noidung_ck}</p>
                      </div>
                      <button onClick={() => copy(hoaDon.noidung_ck)} className="p-2 bg-white/[0.04] hover:bg-white/10 rounded-xl text-white/50 hover:text-white transition">
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 w-full">
                    <div className="flex items-center justify-between gap-3 text-xs bg-amber-500/5 border border-amber-500/10 px-4 py-3 rounded-2xl w-full">
                      <div className="flex items-center gap-2 text-amber-200/60">
                        <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
                        Đang chờ thanh toán...
                      </div>
                      <span className="text-amber-200/30 font-mono text-[10px]">{fmtTime(demGiay)}</span>
                    </div>

                    <button 
                      onClick={async () => {
                        const loading = toast.loading('Đang kiểm tra giao dịch...');
                        try {
                          const res = await kiemTraTrangThaiHoaDon(hoaDon.payment_id);
                          if (res.thanhCong && res.data.status === 'completed') {
                            setTrangThai('thanh_cong');
                            toast.success('Nạp Token thành công!', { id: loading });
                            await lamMoiThongTinNguoiDung({ imLang: true });
                          } else {
                            toast.error('Chưa tìm thấy giao dịch. Vui lòng đợi vài giây.', { id: loading });
                          }
                        } catch (e) { toast.error('Lỗi khi kiểm tra', { id: loading }); }
                      }}
                      className="w-full py-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-bold text-xs hover:bg-emerald-500/20 transition-all flex items-center justify-center gap-2"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      Tôi đã chuyển khoản
                    </button>
                  </div>

                  <div className="flex items-center gap-2 mt-2 opacity-30 grayscale hover:grayscale-0 transition-all">
                    <img src="https://sepay.vn/logo/sepay-logo.png" alt="SePay" className="h-4 object-contain" onError={(e) => e.target.style.display='none'} />
                    <span className="text-[9px] text-white font-medium uppercase tracking-widest">Secured by SePay</span>
                  </div>

                  {isDev && (
                    <button onClick={xuLyXacNhanDev} disabled={dangXacNhanThuCong}
                      className="w-full rounded-2xl border border-amber-400/20 bg-amber-500/5 px-3 py-3 text-xs font-bold text-amber-200/70 hover:bg-amber-500/10 disabled:opacity-50 transition"
                    >
                      {dangXacNhanThuCong ? 'Đang xác nhận...' : '⚡ Xác nhận nạp (Dev Mode)'}
                    </button>
                  )}
                </div>
              )}

              {/* ── STEP 3: Success ───────────────────────────────────────── */}
              {trangThai === 'thanh_cong' && (
                <div className="flex flex-col items-center space-y-5 py-8">
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 300 }}
                    className="w-20 h-20 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center">
                    <CheckCircle2 className="w-10 h-10" />
                  </motion.div>
                  <h3 className="text-xl font-black text-emerald-400">Nạp thành công!</h3>
                  <p className="text-white/30 text-center text-xs">Token đã được cộng vào tài khoản.</p>
                  <button onClick={onClose} className="w-full bg-white/[0.04] hover:bg-white/[0.08] text-white/70 font-bold py-3.5 rounded-2xl transition text-sm">
                    Đóng
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )

  if (typeof document === 'undefined') return null

  return createPortal(modalContent, document.body)
}

export default NapTokenModal
