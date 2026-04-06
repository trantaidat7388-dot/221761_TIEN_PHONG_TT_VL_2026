import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { CheckCircle2, Copy, CreditCard, ShieldCheck, ArrowLeft, Loader2, QrCode } from 'lucide-react'
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
  const [soThe, setSoThe] = useState('')
  const [ngayHetHan, setNgayHetHan] = useState('')
  const [cvc, setCvc] = useState('')
  const [quocGia, setQuocGia] = useState('Việt Nam')

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
    try {
      const raw = localStorage.getItem('w2l_checkout_card_draft')
      if (!raw) return
      const draft = JSON.parse(raw)
      setSoThe(String(draft.soThe || ''))
      setNgayHetHan(String(draft.ngayHetHan || ''))
      setCvc(String(draft.cvc || ''))
      setQuocGia(String(draft.quocGia || 'Việt Nam'))
    } catch {
      // ignore invalid local draft
    }
  }, [])

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
        navigate('/premium', { replace: true })
      }
    }, 5000)

    return () => {
      clearInterval(tickId)
      clearInterval(pollId)
    }
  }, [hoaDon?.payment_id, lamMoiThongTinNguoiDung, navigate])

  const xuLyTaoHoaDon = async () => {
    const amount = Number(soTien)
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

  const xuLyXacNhanThuCongDev = async () => {
    if (!hoaDon?.payment_id) return
    setDangXacNhanThuCong(true)
    try {
      const kq = await xacNhanHoaDonThuCongDev(hoaDon.payment_id)
      if (!kq.thanhCong) throw new Error(kq.loiMessage || 'Không xác nhận được')
      await lamMoiThongTinNguoiDung({ imLang: true })
      toast.success('Đã xác nhận nạp tiền (dev)')
      navigate('/premium', { replace: true })
    } catch (e) {
      toast.error(e.message || 'Xác nhận thủ công thất bại')
    } finally {
      setDangXacNhanThuCong(false)
    }
  }

  const xuLyLuuThongTinThe = () => {
    const payload = { soThe, ngayHetHan, cvc, quocGia }
    localStorage.setItem('w2l_checkout_card_draft', JSON.stringify(payload))
    toast.success('Đã lưu thông tin thẻ (local)')
  }

  const xuLyNhapSoThe = (value) => {
    const onlyDigits = value.replace(/\D/g, '').slice(0, 19)
    const grouped = onlyDigits.replace(/(.{4})/g, '$1 ').trim()
    setSoThe(grouped)
  }

  const xuLyNhapNgayHetHan = (value) => {
    const onlyDigits = value.replace(/\D/g, '').slice(0, 4)
    if (onlyDigits.length <= 2) {
      setNgayHetHan(onlyDigits)
      return
    }
    setNgayHetHan(`${onlyDigits.slice(0, 2)}/${onlyDigits.slice(2)}`)
  }

  const xuLyNhapCvc = (value) => {
    setCvc(value.replace(/\D/g, '').slice(0, 4))
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

  return (
    <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Thanh toán Premium</h1>
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
          <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
            <h2 className="text-2xl font-bold text-white mb-5">Chọn phương thức thanh toán</h2>

            <div className="rounded-xl border border-white/10 bg-slate-900/45 p-4">
              <div className="mb-4 inline-flex items-center gap-2 text-primary-300 font-semibold">
                <CreditCard className="w-4 h-4" />
                Thẻ
              </div>
              <div className="space-y-3">
                <input
                  value={soThe}
                  onChange={(e) => xuLyNhapSoThe(e.target.value)}
                  placeholder="1234 1234 1234 1234"
                  className="w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-white"
                />
                <div className="grid grid-cols-2 gap-3">
                  <input
                    value={ngayHetHan}
                    onChange={(e) => xuLyNhapNgayHetHan(e.target.value)}
                    placeholder="MM / YY"
                    className="rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-white"
                  />
                  <input
                    value={cvc}
                    onChange={(e) => xuLyNhapCvc(e.target.value)}
                    placeholder="CVC"
                    className="rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-white"
                  />
                </div>
                <input
                  value={quocGia}
                  onChange={(e) => setQuocGia(e.target.value)}
                  className="w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-white"
                />
                <div className="flex items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={xuLyLuuThongTinThe}
                    className="rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs text-white/90 hover:bg-white/10"
                  >
                    Lưu thông tin thẻ
                  </button>
                  <span className="text-[11px] text-white/50">Lưu trên trình duyệt này</span>
                </div>
              </div>
            </div>

            <div className="mt-5 rounded-xl border border-white/10 bg-white/5 p-4">
              <label className="text-white/70 text-sm">Số tiền nạp để thanh toán</label>
              <div className="mt-2 flex flex-wrap gap-2">
                {[10000, 25000, 50000, 100000].map((moc) => (
                  <button
                    key={moc}
                    type="button"
                    onClick={() => setSoTien(moc)}
                    className="rounded-lg border border-white/15 bg-slate-900/50 px-3 py-1.5 text-xs text-white/80 hover:bg-slate-900/80"
                  >
                    {new Intl.NumberFormat('vi-VN').format(moc)}
                  </button>
                ))}
              </div>
              <div className="mt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => dieuChinhSoTien(-10000)}
                  className="h-10 w-10 rounded-lg border border-white/15 bg-slate-900/60 text-white/80 hover:bg-slate-900"
                >
                  -
                </button>
                <input
                  type="number"
                  min={10000}
                  step={10000}
                  value={soTien}
                  onChange={(e) => setSoTien(Number(e.target.value || 0))}
                  className="w-full rounded-lg border border-white/15 bg-slate-900/70 px-3 py-2 text-white"
                />
                <button
                  type="button"
                  onClick={() => dieuChinhSoTien(10000)}
                  className="h-10 w-10 rounded-lg border border-white/15 bg-slate-900/60 text-white/80 hover:bg-slate-900"
                >
                  +
                </button>
                <span className="text-white/60 text-sm">VND</span>
              </div>

              <div className="mt-4 flex items-center justify-between text-white font-semibold">
                <span>Tổng phải thanh toán:</span>
                <span>{dinhDangVND(soTien)}</span>
              </div>

              <button
                type="button"
                onClick={xuLyTaoHoaDon}
                disabled={dangTaoHoaDon || Number(soTien) < 10000}
                className="mt-4 w-full rounded-xl bg-primary-600 px-4 py-3 text-base font-bold text-white hover:bg-primary-500 disabled:opacity-60 inline-flex items-center justify-center gap-2"
              >
                {dangTaoHoaDon ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                Thanh toán ngay
              </button>
            </div>

            {hoaDon && (
              <div className="mt-5 rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-white font-semibold mb-3">Quét QR để chuyển khoản</p>
                <div className="bg-white p-3 rounded-xl inline-flex">
                  <img
                    src={`https://api.vietqr.io/image/${bankBin}-${bankAccount}-yXwL0O?accountName=${encodeURIComponent(bankName)}&amount=${hoaDon.amount_vnd}&addInfo=${encodeURIComponent(hoaDon.noidung_ck)}`}
                    alt="QR thanh toán"
                    className="w-48 h-48 rounded-lg object-cover"
                  />
                </div>

                <div className="mt-3 text-sm text-white/80 space-y-1">
                  <p>Nội dung CK: <span className="font-mono text-cyan-300">{hoaDon.noidung_ck}</span></p>
                  <button type="button" onClick={() => saoChep(hoaDon.noidung_ck)} className="text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1">
                    <Copy className="w-4 h-4" /> Sao chép nội dung
                  </button>
                </div>

                <p className="mt-3 text-xs text-amber-200/90">Đang chờ xác nhận tự động: {demGiay}s</p>

                {chuaCauHinhNganHang && (
                  <button
                    type="button"
                    onClick={xuLyXacNhanThuCongDev}
                    disabled={dangXacNhanThuCong}
                    className="mt-3 w-full rounded-lg border border-amber-400/40 bg-amber-500/20 px-3 py-2 text-sm font-medium text-amber-100 hover:bg-amber-500/30 disabled:opacity-50"
                  >
                    {dangXacNhanThuCong ? 'Đang xác nhận...' : 'Xác nhận nạp thủ công (Dev)'}
                  </button>
                )}
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
                    <p className="text-white/60">Thanh toán {planDays >= 300 ? 'Yearly' : `${planDays} ngày`}</p>
                  </div>
                  <div className="rounded-lg bg-amber-500/20 px-3 py-2 text-amber-200 font-semibold">
                    {new Intl.NumberFormat('vi-VN').format(planCost || soTien)} credit
                  </div>
                </div>

                <div className="mt-4 space-y-2 text-white/80">
                  <div className="inline-flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-300" /> Hủy bất cứ lúc nào</div>
                  <div className="inline-flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-300" /> Hoàn tiền đầy đủ</div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-6">
              <h3 className="text-3xl font-bold text-white mb-3">Tiết kiệm ngay tới 20%</h3>
              <div className="rounded-xl border border-emerald-400/40 bg-emerald-500/15 p-4 text-white">
                <div className="inline-flex items-center gap-2 font-semibold">
                  <ShieldCheck className="w-4 h-4 text-emerald-300" />
                  Trả theo năm để tiết kiệm
                </div>
                <p className="mt-2 text-white/80">Chọn thanh toán hằng năm để tiết kiệm nhiều hơn và trả ít hơn tổng thể.</p>
                {mucTietKiemUocTinh > 0 && (
                  <span className="mt-3 inline-flex rounded-lg border border-emerald-400/60 bg-emerald-500/20 px-3 py-1 text-emerald-100 font-semibold">
                    Tiết kiệm {dinhDangVND(mucTietKiemUocTinh)}
                  </span>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-white/70">
              <p className="inline-flex items-center gap-2 text-white/90 font-semibold mb-2"><QrCode className="w-4 h-4" /> Lưu ý SePay</p>
              <p>Nếu bạn chưa có tài khoản ngân hàng để kết nối SePay, có thể dùng nút xác nhận thủ công trong môi trường development để test end-to-end.</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

export default TrangThanhToanPremium
