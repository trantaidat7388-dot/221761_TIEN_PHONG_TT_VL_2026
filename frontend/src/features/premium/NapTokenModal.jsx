import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Loader2, QrCode, Copy, CheckCircle2, CreditCard, Wallet, Coins } from 'lucide-react'
import toast from 'react-hot-toast'
import { taoHoaDonNapTien, kiemTraTrangThaiHoaDon, xacNhanHoaDonThuCongDev } from '../../services/api'
import { dungXacThuc } from '../../context/AuthContext'

const MENH_GIA = [
  { value: 20000, label: '20.000 ₫' },
  { value: 50000, label: '50.000 ₫' },
  { value: 100000, label: '100.000 ₫' },
  { value: 200000, label: '200.000 ₫' },
  { value: 500000, label: '500.000 ₫' },
  { value: 1000000, label: '1.000.000 ₫' },
]

const NapTokenModal = ({ isOpen, onClose }) => {
  const { lamMoiThongTinNguoiDung } = dungXacThuc()
  const [soTien, setSoTien] = useState('')
  const [dangXuLy, setDangXuLy] = useState(false)
  const [hoaDon, setHoaDon] = useState(null)
  const [trangThai, setTrangThai] = useState('chon_menh_gia') // 'chon_menh_gia' -> 'cho_thanh_toan' -> 'thanh_cong'
  const [demGiay, setDemGiay] = useState(0)
  const [dangXacNhanThuCong, setDangXacNhanThuCong] = useState(false)
  
  // Reset khi đóng mở
  useEffect(() => {
    if (isOpen) {
      setSoTien('')
      setHoaDon(null)
      setTrangThai('chon_menh_gia')
      setDemGiay(0)
    }
  }, [isOpen])

  // Polling + timer đếm giây
  useEffect(() => {
    let intervalId = null
    let timerId = null
    if (trangThai === 'cho_thanh_toan' && hoaDon?.payment_id) {
      timerId = setInterval(() => setDemGiay(prev => prev + 1), 1000)
      intervalId = setInterval(async () => {
        try {
          const res = await kiemTraTrangThaiHoaDon(hoaDon.payment_id)
          if (res.thanhCong && res.data.status === 'completed') {
            setTrangThai('thanh_cong')
            clearInterval(intervalId)
            clearInterval(timerId)
            toast.success('Mua gói thành công!')
            await lamMoiThongTinNguoiDung({ imLang: true })
          }
        } catch (e) {
          console.error(e)
        }
      }, 5000) // Poll mỗi 5s
    }
    return () => {
      clearInterval(intervalId)
      clearInterval(timerId)
    }
  }, [trangThai, hoaDon, lamMoiThongTinNguoiDung])

  const xuLyTaoHoaDon = async () => {
    const amount = Number(soTien)
    if (amount < 10000) {
      toast.error('Số tiền mua gói tối thiểu là 10.000 ₫')
      return
    }

    setDangXuLy(true)
    try {
      const res = await taoHoaDonNapTien(amount)
      if (!res.thanhCong) throw new Error(res.loiMessage || 'Không thể tạo đơn hàng mua gói')
      setHoaDon(res.data)
      setTrangThai('cho_thanh_toan')
      setDemGiay(0)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setDangXuLy(false)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    toast.success('Đã sao chép!')
  }

  const xuLyXacNhanThuCongDev = async () => {
    if (!hoaDon?.payment_id) return
    setDangXacNhanThuCong(true)
    try {
      const res = await xacNhanHoaDonThuCongDev(hoaDon.payment_id)
      if (!res.thanhCong) throw new Error(res.loiMessage || 'Không thể xác nhận thủ công')
      setTrangThai('thanh_cong')
      toast.success('Đã xác nhận mua gói (chế độ dev)')
      await lamMoiThongTinNguoiDung({ imLang: true })
    } catch (e) {
      toast.error(e.message || 'Xác nhận thủ công thất bại')
    } finally {
      setDangXacNhanThuCong(false)
    }
  }

  const dinhDangVND = (so) => new Intl.NumberFormat('vi-VN').format(so) + ' ₫'

  const formatTime = (s) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  // Build QR URL
  const bankBin = import.meta.env.VITE_BANK_BIN || '970422'
  const bankAccount = import.meta.env.VITE_BANK_ACCOUNT || '000000000'
  const bankName = import.meta.env.VITE_BANK_ACCOUNT_NAME || 'ADMIN'
  const chuaCauHinhNganHang = bankAccount === '000000000'

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="relative w-full max-w-md bg-[#1a1a2e] border border-white/10 shadow-2xl rounded-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-500/20 rounded-lg">
                  <Coins className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">Mua Gói Token</h2>
                  <p className="text-xs text-white/40">Chuyển khoản theo gói qua mã QR</p>
                </div>
              </div>
              <button onClick={onClose} className="text-white/40 hover:text-white transition p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5">
              {/* Bước 1: Chọn mệnh giá */}
              {trangThai === 'chon_menh_gia' && (
                <div className="space-y-5">
                  <div>
                    <label className="text-sm text-white/60 mb-2 block font-medium">Chọn số Token muốn mua</label>
                    <div className="grid grid-cols-3 gap-2">
                      {MENH_GIA.map(item => (
                        <button
                          key={item.value}
                          onClick={() => setSoTien(item.value.toString())}
                          className={`py-2.5 rounded-xl border text-sm font-medium transition-all ${
                            soTien === item.value.toString() 
                              ? 'bg-primary-500/20 border-primary-500 text-primary-300 shadow-lg shadow-primary-500/10' 
                              : 'bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:text-white'
                          }`}
                        >
                          {new Intl.NumberFormat('vi-VN').format(Math.floor(item.value / 100))} Token
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="relative">
                    <label className="text-sm text-white/60 mb-2 block font-medium">Hoặc nhập số tiền tùy ý</label>
                    <div className="relative">
                      <input
                        type="number"
                        min="10000"
                        step="10000"
                        placeholder="Nhập số tiền..."
                        value={soTien}
                        onChange={(e) => setSoTien(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-12 text-white outline-none focus:border-primary-500 transition focus:bg-white/[0.08]"
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 text-sm font-medium">VNĐ</span>
                    </div>
                    <p className="text-xs text-white/30 mt-1.5">Tối thiểu: 10.000 ₫</p>
                  </div>

                  {soTien && Number(soTien) >= 10000 && (
                    <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white/60">
                      Bạn sẽ nhận được: <span className="text-amber-300 font-bold text-lg">{new Intl.NumberFormat('vi-VN').format(Math.floor(Number(soTien) / 100))} Token</span> vào ví
                    </div>
                  )}

                  <button
                    onClick={xuLyTaoHoaDon}
                    disabled={!soTien || Number(soTien) < 10000 || dangXuLy}
                    className="w-full bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold py-3.5 rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-primary-500/20"
                  >
                    {dangXuLy ? <Loader2 className="w-5 h-5 animate-spin" /> : <QrCode className="w-5 h-5" />}
                    Quét mã mua gói
                  </button>
                </div>
              )}

              {/* Bước 2: Hiển thị QR chờ thanh toán */}
              {trangThai === 'cho_thanh_toan' && hoaDon && (
                <div className="flex flex-col items-center space-y-4">
                  <p className="text-white/70 text-center text-sm">
                    Mở App ngân hàng, quét mã QR bên dưới để thanh toán
                  </p>
                  
                  {/* QR Code */}
                  <div className="bg-white p-3 rounded-2xl shadow-2xl">
                    <img 
                      src={`https://api.vietqr.io/image/${bankBin}-${bankAccount}-yXwL0O?accountName=${encodeURIComponent(bankName)}&amount=${hoaDon.amount_vnd}&addInfo=${encodeURIComponent(hoaDon.noidung_ck)}`} 
                      alt="QR Thanh toán"
                      className="w-52 h-52 object-cover rounded-lg"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                    <div className="hidden w-52 h-52 bg-gray-100 items-center justify-center flex-col gap-2 rounded-xl text-gray-500">
                      <QrCode className="w-10 h-10" />
                      <span className="text-xs">Chưa cấu hình ngân hàng</span>
                    </div>
                  </div>

                  {/* Payment Info */}
                  <div className="w-full bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                    <div className="flex justify-between items-center p-3 border-b border-white/5">
                      <span className="text-xs text-white/40">Số tiền</span>
                      <span className="text-base font-bold text-amber-300">{dinhDangVND(hoaDon.amount_vnd)}</span>
                    </div>
                    <div className="flex justify-between items-center p-3">
                      <div>
                        <p className="text-xs text-white/40 mb-0.5">Nội dung CK</p>
                        <p className="font-mono text-cyan-300 font-bold text-sm">{hoaDon.noidung_ck}</p>
                      </div>
                      <button onClick={() => copyToClipboard(hoaDon.noidung_ck)} className="p-2 bg-white/5 hover:bg-white/15 rounded-lg text-white transition" title="Sao chép">
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Polling Status */}
                  <div className="flex items-center justify-between gap-3 text-sm bg-amber-500/10 border border-amber-500/20 px-4 py-3 rounded-xl w-full">
                    <div className="flex items-center gap-2 text-amber-200/80">
                      <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                      Đang chờ thanh toán...
                    </div>
                    <span className="text-xs text-amber-200/50 font-mono">{formatTime(demGiay)}</span>
                  </div>

                  <p className="text-[11px] text-white/25 text-center">
                    ⚠ Vui lòng chuyển đúng số tiền và nội dung. Hệ thống tự xác nhận trong 3-10 giây.
                  </p>

                  {chuaCauHinhNganHang && (
                    <div className="w-full rounded-xl border border-amber-400/30 bg-amber-500/10 p-3">
                      <p className="text-xs text-amber-200/90 mb-2">Hệ thống thanh toán đang chạy ở chế độ thử nghiệm. Bạn có thể xác nhận mua gói bằng nút bên dưới.</p>
                      <button
                        onClick={xuLyXacNhanThuCongDev}
                        disabled={dangXacNhanThuCong}
                        className="w-full rounded-lg border border-amber-400/40 bg-amber-500/20 px-3 py-2 text-sm font-medium text-amber-100 hover:bg-amber-500/30 disabled:opacity-50"
                      >
                        {dangXacNhanThuCong ? 'Đang xác nhận...' : 'Xác nhận mua gói (Dev)'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Bước 3: Thành công */}
              {trangThai === 'thanh_cong' && (
                <div className="flex flex-col items-center space-y-4 py-6">
                  <motion.div 
                    initial={{ scale: 0 }} animate={{ scale: 1 }} 
                    className="w-20 h-20 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center"
                  >
                    <CheckCircle2 className="w-10 h-10" />
                  </motion.div>
                  <h3 className="text-xl font-bold text-emerald-400">Mua gói thành công!</h3>
                  <p className="text-white/60 text-center text-sm">Số Token đã được cộng vào tài khoản của bạn. Bạn có thể quay lại chọn gói Premium.</p>
                  <button
                    onClick={onClose}
                    className="mt-2 w-full bg-white/10 hover:bg-white/20 text-white font-medium py-3 rounded-xl transition"
                  >
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
}

export default NapTokenModal
