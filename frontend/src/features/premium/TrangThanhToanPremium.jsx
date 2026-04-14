import { useEffect, useMemo, useState, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { CheckCircle2, Copy, ShieldCheck, ArrowLeft, Loader2, QrCode } from 'lucide-react'
import toast from 'react-hot-toast'
import { taoHoaDonNapTien, kiemTraTrangThaiHoaDon, xacNhanHoaDonThuCongDev } from '../../services/api'
import { dungXacThuc } from '../../context/AuthContext'

const TrangThanhToanPremium = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { lamMoiThongTinNguoiDung } = dungXacThuc()

  const initAmount = Number(location.state?.amountVnd || 50000)
  const [soTien, setSoTien] = useState(Number.isFinite(initAmount) ? Math.max(10000, initAmount) : 50000)
  const [dangTaoHoaDon, setDangTaoHoaDon] = useState(false)
  const [dangXacNhanThuCong, setDangXacNhanThuCong] = useState(false)
  const [hoaDon, setHoaDon] = useState(null)
  const [demGiay, setDemGiay] = useState(0)
  const [thanhToanThanhCong, setThanhToanThanhCong] = useState(false)

  const planName = location.state?.planName || 'Premium Package'
  const planDays = Number(location.state?.planDays || 30)
  const planCost = Number(location.state?.planCost || 0)

  const bankBin = import.meta.env.VITE_BANK_BIN || '970422'
  const bankAccount = import.meta.env.VITE_BANK_ACCOUNT || '000000000'
  const bankName = import.meta.env.VITE_BANK_ACCOUNT_NAME || 'ADMIN'
  const chuaCauHinhNganHang = bankAccount === '000000000'

  const dinhDangVND = (n) => `${new Intl.NumberFormat('vi-VN').format(Number(n) || 0)} ₫`

  const mucTietKiemUocTinh = useMemo(() => {
    if (planDays < 300 || !planCost) return 0
    const giaThangGiaLap = 50000
    return Math.max(0, giaThangGiaLap * 12 - planCost)
  }, [planDays, planCost])

  useEffect(() => {
    if (!hoaDon?.payment_id) return
    let tickId = null
    let pollId = null

    tickId = setInterval(() => {
      setDemGiay((prev) => prev + 1)
    }, 1000)

    pollId = setInterval(async () => {
      const kq = await kiemTraTrangThaiHoaDon(hoaDon.payment_id)
      if (kq.thanhCong && kq.data?.status === 'completed') {
        clearInterval(tickId)
        clearInterval(pollId)
        toast.success('Thanh toán thành công')
        await lamMoiThongTinNguoiDung({ imLang: true })
        setThanhToanThanhCong(true)
      }
    }, 5000)

    return () => {
      clearInterval(tickId)
      clearInterval(pollId)
    }
  }, [hoaDon?.payment_id, lamMoiThongTinNguoiDung, navigate])

  const xuLyTaoHoaDon = async (overrideAmount) => {
    const amount = Number(overrideAmount || soTien)
    if (!Number.isFinite(amount) || amount < 10000) {
      toast.error('Số tiền tối thiểu là 10.000 ₫')
      return
    }

    setDangTaoHoaDon(true)
    try {
      const kq = await taoHoaDonNapTien(Math.floor(amount))
      if (!kq.thanhCong) throw new Error(kq.loiMessage || 'Không tạo được hóa đơn')
      setHoaDon(kq.data)
      setDemGiay(0)
    } catch (e) {
      toast.error(e.message || 'Không thể tạo hóa đơn')
    } finally {
      setDangTaoHoaDon(false)
    }
  }

  const triggerAutoCreate = useRef(false)
  useEffect(() => {
    if (initAmount >= 10000 && !triggerAutoCreate.current) {
      triggerAutoCreate.current = true
      xuLyTaoHoaDon(initAmount)
    }
  }, [initAmount])

  const xuLyXacNhanThuCongDev = async () => {
    if (!hoaDon?.payment_id) return
    setDangXacNhanThuCong(true)
    try {
      const kq = await xacNhanHoaDonThuCongDev(hoaDon.payment_id)
      if (!kq.thanhCong) throw new Error(kq.loiMessage || 'Không xác nhận được')
      await lamMoiThongTinNguoiDung({ imLang: true })
      toast.success('Đã xác nhận nạp tiền (dev)')
      setThanhToanThanhCong(true)
    } catch (e) {
      toast.error(e.message || 'Xác nhận thủ công thất bại')
    } finally {
      setDangXacNhanThuCong(false)
    }
  }

  const dieuChinhSoTien = (delta) => {
    setSoTien((prev) => Math.max(10000, Number(prev || 0) + delta))
  }

  const saoChep = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Đã sao chép')
    } catch {
      toast.error('Không thể sao chép')
    }
  }

  if (thanhToanThanhCong) {
    return (
      <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4 flex items-center justify-center">
        <div className="max-w-lg w-full bg-white/5 border border-emerald-500/30 rounded-3xl p-8 text-center glass-card shadow-2xl shadow-emerald-500/20 backdrop-blur-2xl">
          <div className="w-24 h-24 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6 relative">
            <div className="absolute inset-0 bg-emerald-500 animate-ping rounded-full opacity-20"></div>
            <CheckCircle2 className="w-12 h-12 text-emerald-400" />
          </div>
          <h2 className="text-3xl font-extrabold text-white mb-2">Thanh toán Thành Công!</h2>
          <p className="text-emerald-200 mb-8 max-w-sm mx-auto leading-relaxed">
            Hệ thống đã xác nhận giao dịch. {planName !== 'Premium Package' ? 'Gói cước Premium của bạn đã được kích hoạt!' : 'Bạn đã nạp token thành công để sử dụng mọi chức năng!'}
          </p>
          <button
            onClick={() => navigate('/chuyen-doi')}
            className="w-full rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 p-4 font-bold text-white shadow-lg hover:from-emerald-400 hover:to-green-500 transition-all active:scale-95"
          >
            Quay Về Workspace Chuyển Đổi
          </button>
          <button
            onClick={() => navigate('/premium')}
            className="mt-4 w-full rounded-xl border border-white/20 bg-white/5 p-4 font-semibold text-white/80 hover:bg-white/10 hover:text-white transition-all"
          >
            Về trang thông tin gói
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Thanh toán Premium bằng QR Code</h1>
          <button
            type="button"
            onClick={() => navigate('/premium')}
            className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-white hover:bg-white/10"
          >
            <ArrowLeft className="w-4 h-4" />
            Quay lại gói
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section className="rounded-2xl border border-white/10 bg-white/5 p-6 flex flex-col">
            <h2 className="text-2xl font-bold text-white mb-5 flex items-center gap-2">
               <QrCode className="w-6 h-6 text-primary-400" />
               Quét mã để thanh toán tự động
            </h2>

            {hoaDon ? (
              <div className="flex-1 flex flex-col items-center justify-center bg-black/20 rounded-2xl p-6 border border-white/5 text-center">
                <p className="text-white/80 font-medium mb-5">Hệ thống sẽ tự động đối soát và cộng Token sau khi quét mã này</p>
                
                <div className="bg-white p-4 rounded-[2rem] shadow-2xl shadow-primary-500/20 inline-flex flex-col items-center relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-tr from-primary-500/10 to-transparent pointer-events-none" />
                  <img
                    src={`https://img.vietqr.io/image/${bankBin}-${bankAccount}-compact2.png?amount=${hoaDon.amount_vnd}&addInfo=${encodeURIComponent(hoaDon.noidung_ck)}&accountName=${encodeURIComponent(bankName)}`}
                    alt="QR thanh toán"
                    className="w-72 h-72 sm:w-80 sm:h-80 rounded-2xl object-contain drop-shadow-sm transition-transform duration-500 group-hover:scale-[1.02]"
                  />
                </div>

                <div className="mt-8 bg-white/5 border border-white/10 rounded-xl p-4 w-full max-w-sm flex flex-col items-center">
                  <p className="text-white/50 text-sm mb-1 uppercase tracking-wider font-semibold">Nội dung chuyển khoản bắt buộc</p>
                  <p className="font-mono text-cyan-300 text-2xl font-bold mb-3">{hoaDon.noidung_ck}</p>
                  <button 
                    type="button" 
                    onClick={() => saoChep(hoaDon.noidung_ck)} 
                    className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 border border-cyan-500/30 py-2 px-4 rounded-lg inline-flex items-center gap-2 font-medium transition"
                  >
                    <Copy className="w-4 h-4" /> Sao chép mã này
                  </button>
                </div>

                <div className="mt-6 flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 text-amber-300 animate-spin" />
                  <p className="text-sm text-amber-200/90 font-medium">Đang chờ tiền về tài khoản... ({demGiay}s)</p>
                </div>

                {chuaCauHinhNganHang && (
                  <button
                    type="button"
                    onClick={xuLyXacNhanThuCongDev}
                    disabled={dangXacNhanThuCong}
                    className="mt-6 w-full max-w-sm rounded-xl border border-amber-400/40 bg-amber-500/20 px-4 py-3 font-bold text-amber-100 hover:bg-amber-500/30 disabled:opacity-50"
                  >
                    {dangXacNhanThuCong ? 'Đang xác nhận...' : 'Xác nhận nạp thủ công'}
                  </button>
                )}
              </div>
            ) : (
              <div className="flex-1 flex flex-col justify-center">
                <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                  <label className="text-white/70 text-base font-semibold">Bạn muốn nạp bao nhiêu?</label>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {[10000, 25000, 50000, 100000].map((moc) => (
                      <button
                        key={moc}
                        type="button"
                        onClick={() => setSoTien(moc)}
                        className="rounded-lg border border-white/15 bg-slate-900/50 px-4 py-2 font-semibold text-white hover:bg-primary-500/30"
                      >
                        {new Intl.NumberFormat('vi-VN').format(moc)} ₫
                      </button>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => dieuChinhSoTien(-10000)}
                      className="h-12 w-12 rounded-xl border border-white/15 bg-slate-900/60 text-white/80 hover:bg-slate-900 flex items-center justify-center text-xl font-bold"
                    >
                      -
                    </button>
                    <input
                      type="number"
                      min={10000}
                      step={10000}
                      value={soTien}
                      onChange={(e) => setSoTien(Number(e.target.value || 0))}
                      className="w-full text-center rounded-xl border border-white/15 bg-slate-900/70 p-3 text-xl font-bold text-white focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    />
                    <button
                      type="button"
                      onClick={() => dieuChinhSoTien(10000)}
                      className="h-12 w-12 rounded-xl border border-white/15 bg-slate-900/60 text-white/80 hover:bg-slate-900 flex items-center justify-center text-xl font-bold"
                    >
                      +
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={() => xuLyTaoHoaDon()}
                    disabled={dangTaoHoaDon || Number(soTien) < 10000}
                    className="mt-6 w-full rounded-xl bg-primary-600 p-4 text-lg font-extrabold text-white hover:bg-primary-500 disabled:opacity-60 inline-flex items-center justify-center gap-2 shadow-xl shadow-primary-500/20"
                  >
                    {dangTaoHoaDon ? <Loader2 className="w-5 h-5 animate-spin" /> : <QrCode className="w-5 h-5" />}
                    Tạo mã thanh toán QR
                  </button>
                </div>
              </div>
            )}
          </section>

          <section className="space-y-6">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
              <h2 className="text-2xl font-bold text-white mb-4">Gói của bạn</h2>
              <div className="rounded-xl border border-white/10 bg-slate-900/45 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-white/60 text-sm">Package</p>
                    <p className="text-xl font-bold text-white">{planName}</p>
                    <p className="text-white/60">Sử dụng trong {planDays >= 300 ? '1 năm' : `${planDays} ngày`}</p>
                  </div>
                  <div className="rounded-lg bg-amber-500/20 px-3 py-2 text-amber-200 font-bold text-lg">
                    {new Intl.NumberFormat('vi-VN').format(planCost || soTien)} ₫
                  </div>
                </div>

                <div className="mt-4 space-y-2 text-white/80">
                  <div className="inline-flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-300" /> Hệ thống tự động kích hoạt Premium sau 5-10s</div>
                  <div className="inline-flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-300" /> Hỗ trợ nạp 24/7 không cần chờ</div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-6">
              <h3 className="text-3xl font-bold text-white mb-3">An toàn & Tiện lợi</h3>
              <div className="rounded-xl border border-emerald-400/40 bg-emerald-500/15 p-4 text-white">
                <div className="inline-flex items-center gap-2 font-bold mb-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-300" />
                  Giao dịch được bảo vệ
                </div>
                <p className="text-white/80 text-sm leading-relaxed text-justify">
                  Mọi giao dịch đều được mã hoá và xác minh tự động. Bạn chỉ cần mở app ngân hàng, quét mã QR bên cạnh — hệ thống sẽ tự động xác nhận và kích hoạt tài khoản trong vài giây.
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-white/70">
              <p className="inline-flex items-center gap-2 text-white/90 font-bold mb-2 uppercase tracking-wider"><CheckCircle2 className="w-4 h-4 text-primary-400" /> Lưu ý quan trọng</p>
              <ul className="list-disc pl-5 space-y-2">
                <li>Vui lòng giữ nguyên cửa sổ này cho đến khi nhận được thông báo nạp thành công (thường mất 5–10 giây).</li>
                <li>Khi chuyển khoản, hãy giữ nguyên <strong className="text-cyan-300">nội dung chuyển khoản</strong> để hệ thống có thể xác nhận giao dịch của bạn.</li>
              </ul>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

export default TrangThanhToanPremium
