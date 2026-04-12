import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Shield, Users, History, Trash2, RefreshCw, Files, CreditCard,
  BarChart3, ChevronRight, LogOut, Search, CheckCircle2, XCircle,
  Clock, Home, Coins, ArrowUpDown, Eye, UserCheck, UserX,
  Trophy, Settings
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  layTongQuanAdmin,
  layDanhSachNguoiDungAdmin,
  capNhatVaiTroNguoiDungAdmin,
  capNhatPremiumNguoiDungAdmin,
  congTokenNguoiDungAdmin,
  truTokenNguoiDungAdmin,
  layLichSuTheoNguoiDungAdmin,
  layTokenLedgerTheoNguoiDungAdmin,
  xoaNguoiDungAdmin,
  layLichSuToanHeThongAdmin,
  xoaBanGhiLichSuAdmin,
  layDanhSachTemplateAdmin,
  layAuditLogsAdmin,
  layCauHinhHeThongAdmin,
  capNhatCauHinhHeThongAdmin,
  taiLenTemplate,
  xoaTemplateAdmin,
  layDanhSachPaymentsAdmin,
  xacNhanPaymentThuCongAdmin,
} from '../../services/api'
import { dungXacThuc } from '../../context/AuthContext'
import { NutBam } from '../../components'

// ─── SIDEBAR TABS ───────────────────────────────────────────
const TABS = [
  { key: 'tong-quan', label: 'Tổng quan', icon: BarChart3 },
  { key: 'nguoi-dung', label: 'Người dùng', icon: Users },
  { key: 'xep-hang', label: 'Xếp hạng', icon: Trophy },
  { key: 'thanh-toan', label: 'Thanh toán', icon: CreditCard },
  { key: 'template', label: 'Template', icon: Files },
  { key: 'lich-su', label: 'Lịch sử', icon: History },
  { key: 'audit-log', label: 'Audit Log', icon: Shield },
  { key: 'cau-hinh', label: 'Cấu hình', icon: Settings },
]

const TrangAdmin = () => {
  const navigate = useNavigate()
  const { nguoiDung, dangXuat: xuLyDangXuat } = dungXacThuc()
  const [activeTab, setActiveTab] = useState('tong-quan')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [dangTai, setDangTai] = useState(true)
  const [tuKhoaTimNguoiDung, setTuKhoaTimNguoiDung] = useState('')

  // Data states
  const [tongQuan, setTongQuan] = useState(null)
  const [danhSachNguoiDung, setDanhSachNguoiDung] = useState([])
  const [danhSachLichSu, setDanhSachLichSu] = useState([])
  const [danhSachTemplate, setDanhSachTemplate] = useState([])
  const [danhSachAuditLogs, setDanhSachAuditLogs] = useState([])
  const [danhSachPayments, setDanhSachPayments] = useState([])
  const [selectedUserId, setSelectedUserId] = useState(null)
  const [selectedUserSummary, setSelectedUserSummary] = useState(null)
  const [chiTietLichSuUser, setChiTietLichSuUser] = useState([])
  const [chiTietLedgerUser, setChiTietLedgerUser] = useState([])
  const [dangTaiTemplate, setDangTaiTemplate] = useState(false)
  const [dangLuuCauHinh, setDangLuuCauHinh] = useState(false)
  const [cauHinhMeta, setCauHinhMeta] = useState(null)
  const [cauHinhHeThong, setCauHinhHeThong] = useState({
    token_min_cost_vnd: 1,
    free_plan_max_pages: 60,
    max_doc_upload_mb: 10,
    rate_limit_admin_per_minute: 120,
  })

  const taiDuLieu = useCallback(async () => {
    setDangTai(true)
    try {
      const [overviewRes, usersRes, historyRes, auditRes, paymentsRes, systemConfigRes] = await Promise.all([
        layTongQuanAdmin(),
        layDanhSachNguoiDungAdmin(),
        layLichSuToanHeThongAdmin(200),
        layAuditLogsAdmin(200),
        layDanhSachPaymentsAdmin(200),
        layCauHinhHeThongAdmin(),
      ])
      const templatesRes = await layDanhSachTemplateAdmin()

      if (overviewRes.thanhCong) setTongQuan(overviewRes.data)
      if (usersRes.thanhCong) setDanhSachNguoiDung(usersRes.danhSach)
      if (historyRes.thanhCong) setDanhSachLichSu(historyRes.danhSach)
      if (auditRes.thanhCong) setDanhSachAuditLogs(auditRes.danhSach)
      if (templatesRes.thanhCong) setDanhSachTemplate(templatesRes.danhSach)
      if (paymentsRes.thanhCong) setDanhSachPayments(paymentsRes.danhSach)
      if (systemConfigRes.thanhCong && systemConfigRes.data?.settings) {
        setCauHinhHeThong({
          token_min_cost_vnd: Number(systemConfigRes.data.settings.token_min_cost_vnd || 1),
          free_plan_max_pages: Number(systemConfigRes.data.settings.free_plan_max_pages || 60),
          max_doc_upload_mb: Number(systemConfigRes.data.settings.max_doc_upload_mb || 10),
          rate_limit_admin_per_minute: Number(systemConfigRes.data.settings.rate_limit_admin_per_minute || 120),
        })
        setCauHinhMeta(systemConfigRes.data.meta || null)
      }
    } catch (error) {
      toast.error(error.message || 'Khong the tai du lieu trang Admin')
    } finally {
      setDangTai(false)
    }
  }, [])

  useEffect(() => { taiDuLieu() }, [taiDuLieu])

  // ─── USER ACTIONS ─────────────────────────────────────────
  const xuLyDoiVaiTro = async (userId, role) => {
    const kq = await capNhatVaiTroNguoiDungAdmin(userId, role)
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Khong the cap nhat quyen'); return }
    toast.success('Da cap nhat quyen nguoi dung')
    taiDuLieu()
  }

  const xuLyXoaNguoiDung = async (userId) => {
    if (!window.confirm('Ban co chac muon xoa nguoi dung nay?')) return
    const kq = await xoaNguoiDungAdmin(userId)
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return }
    toast.success('Da xoa nguoi dung')
    taiDuLieu()
  }

  const taiChiTietNguoiDung = async (userId) => {
    setSelectedUserId(userId)
    const user = danhSachNguoiDung.find(u => u.id === userId)
    setSelectedUserSummary(user || null)
    const [hRes, lRes] = await Promise.all([
      layLichSuTheoNguoiDungAdmin(userId, 30),
      layTokenLedgerTheoNguoiDungAdmin(userId, 50),
    ])
    setChiTietLichSuUser(hRes.thanhCong ? hRes.danhSach : [])
    setChiTietLedgerUser(lRes.thanhCong ? lRes.danhSach : [])
  }

  const xuLyCapNhatPremium = async (userId, enabled) => {
    const soNgayRaw = enabled ? window.prompt('Nhap so ngay premium (mac dinh 30):', '30') : '0'
    const soNgay = Number(soNgayRaw || 30)
    const kq = await capNhatPremiumNguoiDungAdmin(userId, enabled, Number.isFinite(soNgay) ? soNgay : 30)
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return }
    toast.success('Da cap nhat premium')
    taiDuLieu()
  }

  const xuLyCongToken = async (userId) => {
    const raw = window.prompt('Nhap so token muon cong:', '500')
    const amount = Number(raw)
    if (!Number.isFinite(amount) || amount <= 0) return
    const kq = await congTokenNguoiDungAdmin(userId, Math.floor(amount), 'Admin grant from dashboard')
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return }
    toast.success('Da cong token')
    taiDuLieu()
    if (selectedUserId === userId) taiChiTietNguoiDung(userId)
  }

  const xuLyTruToken = async (userId) => {
    const raw = window.prompt('Nhap so token muon tru:', '100')
    const amount = Number(raw)
    if (!Number.isFinite(amount) || amount <= 0) return
    const kq = await truTokenNguoiDungAdmin(userId, Math.floor(amount), 'Admin deduct from dashboard')
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return }
    toast.success('Da tru token')
    taiDuLieu()
    if (selectedUserId === userId) taiChiTietNguoiDung(userId)
  }

  const xuLyXoaLichSu = async (recordId) => {
    const kq = await xoaBanGhiLichSuAdmin(recordId)
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return }
    setDanhSachLichSu(prev => prev.filter(x => x.id !== recordId))
    setChiTietLichSuUser(prev => prev.filter(x => x.id !== recordId))
    toast.success('Da xoa ban ghi lich su')
  }

  const xuLyXoaTemplate = async (templateId) => {
    if (!window.confirm('Ban co chac muon xoa template nay?')) return
    const kq = await xoaTemplateAdmin(templateId)
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return }
    setDanhSachTemplate(prev => prev.filter(x => x.id !== templateId))
    toast.success('Da xoa template')
  }

  const xuLyTaiLenTemplate = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setDangTaiTemplate(true)
    try {
      const kq = await taiLenTemplate(file)
      if (!kq.thanhCong) { toast.error(kq.loiMessage); return }
      toast.success(kq.message || 'Da tai len template')
      const dsTemplate = await layDanhSachTemplateAdmin()
      if (dsTemplate.thanhCong) setDanhSachTemplate(dsTemplate.danhSach)
    } finally {
      setDangTaiTemplate(false)
      e.target.value = ''
    }
  }

  const xuLyXacNhanPayment = async (paymentId) => {
    if (!window.confirm('Xac nhan thanh toan thu cong cho hoa don nay?')) return
    const kq = await xacNhanPaymentThuCongAdmin(paymentId)
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return }
    toast.success('Da xac nhan thanh toan')
    taiDuLieu()
  }

  const capNhatGiaTriCauHinh = (key, value) => {
    const num = Number(value)
    setCauHinhHeThong(prev => ({
      ...prev,
      [key]: Number.isFinite(num) ? num : 0,
    }))
  }

  const xuLyLuuCauHinhHeThong = async () => {
    const payload = {
      token_min_cost_vnd: Math.max(1, Math.floor(Number(cauHinhHeThong.token_min_cost_vnd || 1))),
      free_plan_max_pages: Math.max(1, Math.floor(Number(cauHinhHeThong.free_plan_max_pages || 60))),
      max_doc_upload_mb: Math.max(1, Math.floor(Number(cauHinhHeThong.max_doc_upload_mb || 10))),
      rate_limit_admin_per_minute: Math.max(10, Math.floor(Number(cauHinhHeThong.rate_limit_admin_per_minute || 120))),
    }

    setDangLuuCauHinh(true)
    const kq = await capNhatCauHinhHeThongAdmin(payload)
    setDangLuuCauHinh(false)

    if (!kq.thanhCong) {
      toast.error(kq.loiMessage || 'Khong the luu cau hinh he thong')
      return
    }

    setCauHinhHeThong({
      token_min_cost_vnd: Number(kq.data?.settings?.token_min_cost_vnd || payload.token_min_cost_vnd),
      free_plan_max_pages: Number(kq.data?.settings?.free_plan_max_pages || payload.free_plan_max_pages),
      max_doc_upload_mb: Number(kq.data?.settings?.max_doc_upload_mb || payload.max_doc_upload_mb),
      rate_limit_admin_per_minute: Number(kq.data?.settings?.rate_limit_admin_per_minute || payload.rate_limit_admin_per_minute),
    })
    setCauHinhMeta(kq.data?.meta || null)
    toast.success('Da luu cau hinh. Restart backend de ap dung cho luong xu ly chinh.')
  }

  const xuLyHanhDong = async (user, action) => {
    if (!action || !user) return
    if (action === 'detail') { await taiChiTietNguoiDung(user.id); return }
    if (action === 'premium') { await xuLyCapNhatPremium(user.id, user.plan_type !== 'premium'); return }
    if (action === 'grant') { await xuLyCongToken(user.id); return }
    if (action === 'deduct') { await xuLyTruToken(user.id); return }
    if (action === 'delete') { await xuLyXoaNguoiDung(user.id) }
  }

  // ─── COMPUTED ─────────────────────────────────────────────
  const danhSachNguoiDungDaLoc = useMemo(() => {
    const kw = (tuKhoaTimNguoiDung || '').trim().toLowerCase()
    if (!kw) return danhSachNguoiDung
    return danhSachNguoiDung.filter(u =>
      (u.username || '').toLowerCase().includes(kw) || (u.email || '').toLowerCase().includes(kw)
    )
  }, [danhSachNguoiDung, tuKhoaTimNguoiDung])

  const fmtDate = (v) => (v instanceof Date ? v.toLocaleString('vi-VN') : '-')
  const fmtSize = (b) => {
    if (!Number.isFinite(b) || b < 0) return '-'
    if (b < 1024) return `${b} B`
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
    return `${(b / (1024 * 1024)).toFixed(1)} MB`
  }
  const fmtVND = (n) => `${new Intl.NumberFormat('vi-VN').format(n)} VND`
  const avatarChars = (u) => {
    const s = (u?.username || u?.email || '').trim()
    if (!s) return 'U'
    const parts = s.replace(/\s+/g, ' ').split(' ').filter(Boolean)
    return parts.length >= 2 ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() : (parts[0]?.slice(0, 2) || 'U').toUpperCase()
  }

  const paymentStats = useMemo(() => {
    const completed = danhSachPayments.filter(p => p.status === 'completed')
    const pending = danhSachPayments.filter(p => p.status === 'pending')
    const totalRevenue = completed.reduce((sum, p) => sum + (p.amount_vnd || 0), 0)
    return { completed: completed.length, pending: pending.length, totalRevenue }
  }, [danhSachPayments])

  // --- CHART DATA GENERATION ---
  const { chartDataUsers, pieDataPlanType, chartDataRevenue, topUsers } = useMemo(() => {
    // 1. Tăng trưởng người dùng (Theo ngày tạo)
    const userGroups = {}
    let freeCount = 0
    let premiumCount = 0

    danhSachNguoiDung.forEach(u => {
      if (u.plan_type === 'premium') premiumCount++
      else freeCount++

      if (u.created_at) {
        const dateRaw = new Date(u.created_at)
        if (!isNaN(dateRaw)) {
          const dateStr = dateRaw.toISOString().split('T')[0] // YYYY-MM-DD
          userGroups[dateStr] = (userGroups[dateStr] || 0) + 1
        }
      }
    })

    const chartDataUsersObj = Object.keys(userGroups).sort().map(date => ({
      date,
      users: userGroups[date]
    }))

    // 2. Pie Chart: Free vs Premium
    const pieDataPlanTypeObj = [
      { name: 'Kế hoạch Miễn phí', value: freeCount, color: '#94a3b8' },
      { name: 'Khách hàng Premium', value: premiumCount, color: '#2dd4bf' }
    ]

    // 3. Doanh thu theo thời gian
    const revenueGroups = {}
    danhSachPayments.filter(p => p.status === 'completed').forEach(p => {
      if (p.createdAt) {
          const d = p.createdAt instanceof Date ? p.createdAt : new Date(p.createdAt)
          if (!isNaN(d)) {
            const dateStr = d.toISOString().split('T')[0]
            revenueGroups[dateStr] = (revenueGroups[dateStr] || 0) + (p.amount_vnd || 0)
          }
      }
    })
    const chartDataRevenueObj = Object.keys(revenueGroups).sort().map(date => ({
      date,
      revenue: revenueGroups[date]
    }))

    // 4. Xếp hạng người dùng tích cực (Top Conversions)
    const topUsersObj = [...danhSachNguoiDung].sort((a, b) => (b.so_lan_chuyen_doi || 0) - (a.so_lan_chuyen_doi || 0)).slice(0, 50)

    return {
      chartDataUsers: chartDataUsersObj,
      pieDataPlanType: pieDataPlanTypeObj,
      chartDataRevenue: chartDataRevenueObj,
      topUsers: topUsersObj
    }
  }, [danhSachNguoiDung, danhSachPayments])

  const xuLyDangXuatAdmin = () => {
    navigate('/', { replace: true })
    setTimeout(() => {
      xuLyDangXuat()
      toast.success('Đã đăng xuất')
    }, 50)
  }

  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════
  return (
    <div className="flex min-h-screen bg-slate-950">
      {/* ─── SIDEBAR ─── */}
      <aside className={`${sidebarOpen ? 'w-56' : 'w-16'} flex flex-col border-r border-white/5 bg-slate-950/90 transition-all duration-300`}>
        {/* Logo */}
        <div className="flex items-center gap-2 border-b border-white/5 px-4 py-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-blue-500 text-xs font-black text-white">
            W2L
          </div>
          {sidebarOpen && <span className="text-sm font-bold text-white">Admin Panel</span>}
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-0.5 px-2 py-3">
          {TABS.map(tab => {
            const isActive = activeTab === tab.key
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-all
                  ${isActive
                    ? 'bg-cyan-500/15 text-cyan-300 shadow-lg shadow-cyan-500/5'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                  }`}
                title={tab.label}
              >
                <tab.icon className="h-4.5 w-4.5 shrink-0" />
                {sidebarOpen && <span>{tab.label}</span>}
                {isActive && sidebarOpen && <ChevronRight className="ml-auto h-3.5 w-3.5" />}
              </button>
            )
          })}
        </nav>

        {/* Sidebar footer */}
        <div className="border-t border-white/5 px-2 py-3 space-y-1">
          <button
            onClick={() => navigate('/')}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/5 hover:text-white transition"
            title="Ve trang chu"
          >
            <Home className="h-4 w-4 shrink-0" />
            {sidebarOpen && <span>Trang chu</span>}
          </button>
          <button
            onClick={xuLyDangXuatAdmin}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-red-400/70 hover:bg-red-500/10 hover:text-red-300 transition"
            title="Dang xuat"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {sidebarOpen && <span>Dang xuat</span>}
          </button>
        </div>
      </aside>

      {/* ─── MAIN CONTENT ─── */}
      <main className="flex-1 overflow-auto">
        {/* Top bar */}
        <div className="sticky top-0 z-30 flex items-center justify-between border-b border-white/5 bg-slate-950/80 px-6 py-3 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="rounded-lg p-1.5 text-slate-400 hover:bg-white/5 hover:text-white transition">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
            <h1 className="text-lg font-bold text-white">{TABS.find(t => t.key === activeTab)?.label || 'Admin'}</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">{nguoiDung?.email}</span>
            <NutBam onClick={taiDuLieu} bienThe="secondary" icon={RefreshCw} dangTai={dangTai}>
              Lam moi
            </NutBam>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* ════════════ TAB: TONG QUAN ════════════ */}
          {activeTab === 'tong-quan' && (
            <div className="space-y-6">
              {/* Thống kê nhanh */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard icon={Users} label="Tổng người dùng" value={tongQuan?.tong_nguoi_dung ?? '-'} color="text-cyan-300 bg-cyan-500/10" />
                <StatCard icon={Shield} label="Quản trị viên" value={tongQuan?.tong_admin ?? '-'} color="text-emerald-300 bg-emerald-500/10" />
                <StatCard icon={Coins} label="Khách hàng Premium" value={tongQuan?.tong_premium ?? '-'} color="text-violet-300 bg-violet-500/10" />
                <StatCard icon={History} label="Tài liệu đã chuyển đổi" value={tongQuan?.tong_ban_ghi_lich_su ?? '-'} color="text-amber-300 bg-amber-500/10" />
              </div>

              {/* Bảng điều khiển biểu đồ */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 xl:grid-cols-4">
                {/* Tăng trưởng người dùng (Line Chart) */}
                <div className="col-span-1 lg:col-span-2 xl:col-span-2 rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm">
                  <h3 className="mb-4 text-sm font-semibold text-slate-300 uppercase tracking-wider">Tăng trưởng Người Dùng (Mới)</h3>
                  <div className="h-[250px] w-full">
                    {chartDataUsers.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartDataUsers}>
                          <XAxis dataKey="date" stroke="#cbd5e1" fontSize={11} tickMargin={8} />
                          <YAxis stroke="#cbd5e1" fontSize={11} tickMargin={8} allowDecimals={false} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                            itemStyle={{ color: '#bae6fd' }}
                          />
                          <Line type="monotone" dataKey="users" name="Tài khoản mới" stroke="#38bdf8" strokeWidth={3} dot={{ strokeWidth: 2, r: 4, fill: '#0f172a' }} />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-sm text-slate-500">Chưa đủ dữ liệu thống kê</div>
                    )}
                  </div>
                </div>

                {/* Tỷ trọng gói (Pie Chart) */}
                <div className="col-span-1 xl:col-span-1 border border-white/5 bg-white/[0.02] p-5 shadow-sm rounded-xl">
                  <h3 className="mb-4 text-sm font-semibold text-slate-300 uppercase tracking-wider text-center">Tỷ trọng Khách Hàng</h3>
                  <div className="h-[250px] w-full">
                    {pieDataPlanType.some(d => d.value > 0) ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={pieDataPlanType}
                            cx="50%" cy="50%"
                            innerRadius={60} outerRadius={85}
                            paddingAngle={5}
                            dataKey="value" stroke="none"
                          >
                            {pieDataPlanType.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff' }} />
                          <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px' }} />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-sm text-slate-500">Chưa đủ dữ liệu thống kê</div>
                    )}
                  </div>
                </div>

                {/* Doanh thu (Bar Chart) */}
                <div className="col-span-1 lg:col-span-3 xl:col-span-1 border border-white/5 bg-white/[0.02] p-5 shadow-sm rounded-xl">
                  <h3 className="mb-4 text-sm font-semibold text-slate-300 uppercase tracking-wider">Doanh thu SePay (VNĐ)</h3>
                  <div className="mb-2 text-2xl font-black text-emerald-400">{fmtVND(paymentStats.totalRevenue)}</div>
                  <div className="text-xs text-slate-400 mb-4">{paymentStats.completed} hóa đơn hoàn tất, {paymentStats.pending} chưa xác nhận.</div>
                  <div className="h-[170px] w-full">
                    {chartDataRevenue.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartDataRevenue}>
                          <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickMargin={5} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                            itemStyle={{ color: '#34d399' }}
                            formatter={(value) => new Intl.NumberFormat('vi-VN').format(value) + ' VNĐ'}
                          />
                          <Bar dataKey="revenue" name="Doanh thu" fill="#34d399" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-sm text-slate-500 border border-dashed border-white/10 rounded-xl">Chưa phát sinh doanh thu</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ════════════ TAB: XEP HANG KHACH HANG ════════════ */}
          {activeTab === 'xep-hang' && (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm">
              <div className="mb-6 flex items-center justify-between">
                <h3 className="font-semibold text-white flex items-center gap-2 text-lg">
                  <Trophy className="h-5 w-5 text-amber-400" /> Bảng Xếp Hạng Người Dùng Tích Cực
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm text-white/90 table-fixed">
                  <thead>
                    <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-slate-400">
                      <th className="w-[10%] py-3">Hạng</th>
                      <th className="w-[30%] py-3">Tài khoản</th>
                      <th className="w-[20%] py-3">Loại Gói</th>
                      <th className="w-[20%] py-3">Số dư (Token)</th>
                      <th className="w-[20%] py-3 text-right">Tài liệu đã chuyển</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topUsers.map((u, idx) => (
                      <tr key={u.id} className="border-b border-white/[0.03] hover:bg-white/[0.01] transition-colors">
                        <td className="py-3 font-semibold text-slate-300">
                          {idx === 0 && <span className="flex items-center gap-1.5 text-amber-400"><Trophy className="h-4 w-4" /> 1</span>}
                          {idx === 1 && <span className="flex items-center gap-1.5 text-slate-300"><Trophy className="h-4 w-4" /> 2</span>}
                          {idx === 2 && <span className="flex items-center gap-1.5 text-amber-700"><Trophy className="h-4 w-4" /> 3</span>}
                          {idx > 2 && <span className="pl-6 text-slate-500">#{idx + 1}</span>}
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-[10px] font-bold text-white shadow-inner">
                              {avatarChars(u)}
                            </div>
                            <div>
                              <p className="font-medium text-slate-200">{u.username}</p>
                              <p className="text-[11px] text-slate-500">{u.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3">
                           {u.plan_type === 'premium' 
                             ? <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-400">Premium</span> 
                             : <span className="rounded-full bg-slate-500/10 px-2 py-0.5 text-[11px] font-semibold text-slate-400">Miễn phí</span>}
                        </td>
                        <td className="py-3 font-mono text-cyan-200">{new Intl.NumberFormat('vi-VN').format(u.token_balance || 0)}</td>
                        <td className="py-3 text-right text-lg font-bold text-white">{u.so_lan_chuyen_doi}</td>
                      </tr>
                    ))}
                    {!topUsers.length && (
                      <tr><td className="py-6 text-center text-slate-500" colSpan={5}>Chưa có đủ dữ liệu người dùng</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ════════════ TAB: CAU HINH HE THONG ════════════ */}
          {activeTab === 'cau-hinh' && (
            <div className="max-w-4xl space-y-6">
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm">
                <h3 className="mb-1 text-lg font-semibold text-white flex items-center gap-2">
                  <Settings className="h-5 w-5 text-cyan-400" /> Tham Số Hệ Thống cơ bản
                </h3>
                <p className="mb-6 text-sm text-slate-400">Du lieu dang doc/ghi truc tiep qua API backend /api/admin/system-config.</p>
                
                <div className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div className="space-y-1.5">
                      <label className="text-sm font-medium text-slate-300">Giá Token tối thiểu (VNĐ)</label>
                      <input type="number" value={cauHinhHeThong.token_min_cost_vnd} onChange={(e) => capNhatGiaTriCauHinh('token_min_cost_vnd', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
                      <p className="text-xs text-slate-500">Tỉ giá gốc quy đổi ra VNĐ cho tính toán dịch vụ.</p>
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-medium text-slate-300">Token đăng ký (Mặc định)</label>
                      <input type="number" value={cauHinhHeThong.free_plan_max_pages} onChange={(e) => capNhatGiaTriCauHinh('free_plan_max_pages', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
                      <p className="text-xs text-slate-500">Số lượng Token tương đương số trang được dùng miễn phí.</p>
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-medium text-slate-300">Trang thai SePay API Key</label>
                      <input type="text" value={cauHinhMeta?.sepay_api_key_configured ? 'Da cau hinh' : 'Chua cau hinh'} disabled className="w-full rounded-lg border border-white/5 bg-slate-900/50 px-4 py-2 text-slate-400 cursor-not-allowed" />
                      <p className="text-xs text-slate-500">Thong tin khoa SePay duoc quan ly trong backend/.env.</p>
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-medium text-slate-300">Giới hạn file Upload lớn nhất (MB)</label>
                      <input type="number" value={cauHinhHeThong.max_doc_upload_mb} onChange={(e) => capNhatGiaTriCauHinh('max_doc_upload_mb', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
                      <p className="text-xs text-slate-500">Ngăn người dùng lợi dụng tài nguyên máy chủ.</p>
                    </div>
                    <div className="space-y-1.5 md:col-span-2">
                      <label className="text-sm font-medium text-slate-300">Rate limit nhom Admin (request/phut)</label>
                      <input type="number" value={cauHinhHeThong.rate_limit_admin_per_minute} onChange={(e) => capNhatGiaTriCauHinh('rate_limit_admin_per_minute', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
                      <p className="text-xs text-slate-500">Khuyen nghi restart backend sau khi cap nhat de ap dung cho middleware rate-limit.</p>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-white/10 flex justify-end">
                    <button disabled={dangLuuCauHinh} className="rounded-lg bg-cyan-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-500/20 disabled:opacity-60" onClick={xuLyLuuCauHinhHeThong}>
                      {dangLuuCauHinh ? 'Dang luu...' : 'Cập nhật Toàn hệ thống'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ════════════ TAB: NGUOI DUNG ════════════ */}
          {activeTab === 'nguoi-dung' && (
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
              {/* Users table */}
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Search className="h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    value={tuKhoaTimNguoiDung}
                    onChange={e => setTuKhoaTimNguoiDung(e.target.value)}
                    placeholder="Tim theo username hoac email..."
                    className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
                  />
                </div>
                <p className="mb-2 text-xs text-slate-600">
                  {danhSachNguoiDungDaLoc.length}/{danhSachNguoiDung.length} nguoi dung. Bam vao dong de xem chi tiet.
                </p>
                <div className="max-h-[65vh] overflow-auto">
                  <table className="min-w-full table-fixed text-sm text-white/90">
                    <thead>
                      <tr className="border-b border-white/5 text-left text-xs text-slate-500">
                        <th className="w-[24%] py-2 pr-2">Username</th>
                        <th className="w-[22%] py-2 pr-2">Email</th>
                        <th className="w-[10%] py-2 pr-2">Vai tro</th>
                        <th className="w-[9%] py-2 pr-2">Goi</th>
                        <th className="w-[9%] py-2 pr-2">Token</th>
                        <th className="w-[8%] py-2 pr-2">So lan</th>
                        <th className="w-[11%] py-2">Hanh dong</th>
                      </tr>
                    </thead>
                    <tbody>
                      {danhSachNguoiDungDaLoc.map(u => (
                        <tr
                          key={u.id}
                          className={`cursor-pointer border-b border-white/[0.03] transition ${selectedUserId === u.id ? 'bg-cyan-500/5' : 'hover:bg-white/[0.02]'}`}
                          onClick={() => taiChiTietNguoiDung(u.id)}
                        >
                          <td className="py-2 pr-2">
                            <div className="flex items-center gap-2 min-w-0">
                              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-cyan-500/20 bg-cyan-500/10 text-[10px] font-bold text-cyan-300">
                                {avatarChars(u)}
                              </div>
                              <span className="truncate">{u.username}</span>
                            </div>
                          </td>
                          <td className="truncate py-2 pr-2 text-slate-400" title={u.email}>{u.email}</td>
                          <td className="py-2 pr-2">
                            <select
                              value={u.role || 'user'}
                              onClick={e => e.stopPropagation()}
                              onChange={e => xuLyDoiVaiTro(u.id, e.target.value)}
                              className="rounded-md border border-white/10 bg-slate-900 px-1.5 py-0.5 text-xs"
                            >
                              <option value="user">user</option>
                              <option value="admin">admin</option>
                            </select>
                          </td>
                          <td className="py-2 pr-2">
                            <span className={`rounded-md px-1.5 py-0.5 text-xs ${u.plan_type === 'premium' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-white/5 text-slate-500'}`}>
                              {u.plan_type || 'free'}
                            </span>
                          </td>
                          <td className="py-2 pr-2 font-semibold text-amber-300">{u.token_balance ?? 0}</td>
                          <td className="py-2 pr-2">{u.so_lan_chuyen_doi}</td>
                          <td className="py-2">
                            <select
                              defaultValue=""
                              onClick={e => e.stopPropagation()}
                              onChange={e => { const v = e.target.value; if (v) { xuLyHanhDong(u, v); e.target.value = '' } }}
                              className="w-full rounded-md border border-white/10 bg-slate-900 px-1 py-0.5 text-xs"
                            >
                              <option value="">Tac vu</option>
                              <option value="detail">Chi tiet</option>
                              <option value="premium">{u.plan_type === 'premium' ? 'Ha premium' : 'Nang premium'}</option>
                              <option value="grant">Cong token</option>
                              <option value="deduct">Tru token</option>
                              <option value="delete">Xoa</option>
                            </select>
                          </td>
                        </tr>
                      ))}
                      {!danhSachNguoiDungDaLoc.length && (
                        <tr><td className="py-4 text-slate-600" colSpan={7}>Khong co du lieu</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* User detail panel */}
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <h3 className="mb-4 font-semibold text-white flex items-center gap-2">
                  <Eye className="h-4 w-4 text-cyan-400" />
                  {selectedUserId ? `Chi tiet tai khoan #${selectedUserId}` : 'Chi tiet tai khoan'}
                </h3>
                {!selectedUserId && <p className="text-sm text-slate-600">Chon nguoi dung o bang ben trai.</p>}
                {selectedUserId && (
                  <div className="max-h-[60vh] space-y-4 overflow-y-auto pr-1">
                    {selectedUserSummary && (
                      <div className="rounded-lg border border-white/5 bg-white/[0.03] p-3">
                        <div className="flex items-center gap-3 mb-1">
                          <div className="flex h-9 w-9 items-center justify-center rounded-full border border-cyan-500/20 bg-cyan-500/10 text-sm font-bold text-cyan-300">{avatarChars(selectedUserSummary)}</div>
                          <p className="font-medium text-white">{selectedUserSummary.username}</p>
                        </div>
                        <p className="text-xs text-slate-500">{selectedUserSummary.email}</p>
                        <p className="mt-1 text-xs text-slate-500">Vai tro: {selectedUserSummary.role || 'user'} | Goi: {selectedUserSummary.plan_type || 'free'} | Token: {selectedUserSummary.token_balance ?? 0}</p>
                      </div>
                    )}

                    <div>
                      <h4 className="mb-2 text-sm font-medium text-slate-300">Lich su chuyen doi</h4>
                      <div className="space-y-1.5">
                        {chiTietLichSuUser.map(item => (
                          <div key={item.id} className="flex items-start justify-between gap-2 rounded-lg bg-white/[0.03] p-2 border border-white/[0.03]">
                            <div className="min-w-0">
                              <p className="truncate text-sm text-white">{item.file_name || 'Khong ten'}</p>
                              <p className="text-xs text-slate-500">{item.status} | {item.pages_count || 0} trang | {item.token_cost || 0} token</p>
                            </div>
                            <button onClick={() => xuLyXoaLichSu(item.id)} className="text-red-400/50 hover:text-red-300"><Trash2 className="h-3.5 w-3.5" /></button>
                          </div>
                        ))}
                        {!chiTietLichSuUser.length && <p className="text-xs text-slate-600">Chua co du lieu</p>}
                      </div>
                    </div>

                    <div>
                      <h4 className="mb-2 text-sm font-medium text-slate-300">Token ledger</h4>
                      <div className="space-y-1.5">
                        {chiTietLedgerUser.map(item => (
                          <div key={item.id} className="rounded-lg bg-white/[0.03] p-2 border border-white/[0.03]">
                            <p className="text-sm text-white">{item.reason}</p>
                            <p className="text-xs text-slate-500">delta: {item.delta_token} | balance: {item.balance_after}</p>
                          </div>
                        ))}
                        {!chiTietLedgerUser.length && <p className="text-xs text-slate-600">Chua co du lieu</p>}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ════════════ TAB: THANH TOAN ════════════ */}
          {activeTab === 'thanh-toan' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <StatCard icon={CheckCircle2} label="Thanh cong" value={paymentStats.completed} color="text-emerald-300 bg-emerald-500/10" />
                <StatCard icon={Clock} label="Dang cho" value={paymentStats.pending} color="text-amber-300 bg-amber-500/10" />
                <StatCard icon={Coins} label="Tong doanh thu" value={fmtVND(paymentStats.totalRevenue)} color="text-sky-300 bg-sky-500/10" />
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <h3 className="mb-4 font-semibold text-white flex items-center gap-2">
                  <CreditCard className="h-4 w-4 text-cyan-400" /> Tat ca hoa don
                </h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm text-white/90">
                    <thead>
                      <tr className="border-b border-white/5 text-left text-xs text-slate-500">
                        <th className="py-2 pr-2">ID</th>
                        <th className="py-2 pr-2">User</th>
                        <th className="py-2 pr-2">So tien</th>
                        <th className="py-2 pr-2">Token</th>
                        <th className="py-2 pr-2">Trang thai</th>
                        <th className="py-2 pr-2">Thoi gian</th>
                        <th className="py-2">Hanh dong</th>
                      </tr>
                    </thead>
                    <tbody>
                      {danhSachPayments.map(p => (
                        <tr key={p.id} className="border-b border-white/[0.03]">
                          <td className="py-2 pr-2 font-mono text-xs">#{p.id}</td>
                          <td className="py-2 pr-2">
                            <p className="text-sm">{p.username || '-'}</p>
                            <p className="text-xs text-slate-500">{p.email}</p>
                          </td>
                          <td className="py-2 pr-2 font-semibold">{fmtVND(p.amount_vnd)}</td>
                          <td className="py-2 pr-2 text-amber-300">{new Intl.NumberFormat('vi-VN').format(p.token_amount)}</td>
                          <td className="py-2 pr-2">
                            <StatusBadge status={p.status} />
                          </td>
                          <td className="py-2 pr-2 text-xs text-slate-500">{fmtDate(p.createdAt)}</td>
                          <td className="py-2">
                            {p.status !== 'completed' && (
                              <button
                                onClick={() => xuLyXacNhanPayment(p.id)}
                                className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-300 hover:bg-emerald-500/20 transition"
                              >
                                Xac nhan
                              </button>
                            )}
                            {p.status === 'completed' && <span className="text-xs text-slate-600">—</span>}
                          </td>
                        </tr>
                      ))}
                      {!danhSachPayments.length && (
                        <tr><td className="py-4 text-slate-600" colSpan={7}>Chua co hoa don nao</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ════════════ TAB: TEMPLATE ════════════ */}
          {activeTab === 'template' && (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <div className="mb-4 flex items-center justify-between gap-3">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <Files className="h-4 w-4 text-cyan-400" /> Quan ly template tuy chinh
                </h3>
                <label className="cursor-pointer rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white hover:bg-white/10 transition">
                  <input type="file" accept=".tex,.zip" onChange={xuLyTaiLenTemplate} className="hidden" disabled={dangTaiTemplate} />
                  {dangTaiTemplate ? 'Dang tai len...' : 'Tai len (.tex / .zip)'}
                </label>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm text-white/90">
                  <thead>
                    <tr className="border-b border-white/5 text-left text-xs text-slate-500">
                      <th className="py-2 pr-2">Ten template</th>
                      <th className="py-2 pr-2">Pham vi</th>
                      <th className="py-2 pr-2">Chu so huu</th>
                      <th className="py-2 pr-2">Loai</th>
                      <th className="py-2 pr-2">Kich thuoc</th>
                      <th className="py-2">Hanh dong</th>
                    </tr>
                  </thead>
                  <tbody>
                    {danhSachTemplate.map(tpl => (
                      <tr key={tpl.id} className="border-b border-white/[0.03]">
                        <td className="py-2 pr-2">{tpl.ten}</td>
                        <td className="py-2 pr-2">{tpl.scope === 'private' ? 'ca nhan' : 'global'}</td>
                        <td className="py-2 pr-2">{tpl.owner_label || '-'}</td>
                        <td className="py-2 pr-2">{tpl.loai}</td>
                        <td className="py-2 pr-2">{fmtSize(tpl.kich_thuoc)}</td>
                        <td className="py-2">
                          <button onClick={() => xuLyXoaTemplate(tpl.id)} className="inline-flex items-center gap-1 text-red-400/60 hover:text-red-300">
                            <Trash2 className="h-3.5 w-3.5" /> Xoa
                          </button>
                        </td>
                      </tr>
                    ))}
                    {!danhSachTemplate.length && (
                      <tr><td className="py-4 text-slate-600" colSpan={6}>Khong co template tuy chinh</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ════════════ TAB: LICH SU ════════════ */}
          {activeTab === 'lich-su' && (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <h3 className="mb-4 font-semibold text-white flex items-center gap-2">
                <History className="h-4 w-4 text-cyan-400" /> Lich su chuyen doi toan he thong
              </h3>
              <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
                <table className="min-w-full text-sm text-white/90">
                  <thead className="sticky top-0 bg-slate-950">
                    <tr className="border-b border-white/5 text-left text-xs text-slate-500">
                      <th className="py-2 pr-2">User</th>
                      <th className="py-2 pr-2">File</th>
                      <th className="py-2 pr-2">Template</th>
                      <th className="py-2 pr-2">Trang thai</th>
                      <th className="py-2 pr-2">Trang</th>
                      <th className="py-2 pr-2">Token</th>
                      <th className="py-2 pr-2">Thoi gian</th>
                      <th className="py-2">Xoa</th>
                    </tr>
                  </thead>
                  <tbody>
                    {danhSachLichSu.map(item => (
                      <tr key={item.id} className="border-b border-white/[0.03]">
                        <td className="py-2 pr-2 text-xs">{item.username || '-'}</td>
                        <td className="py-2 pr-2 max-w-[200px] truncate">{item.file_name || '-'}</td>
                        <td className="py-2 pr-2 text-xs text-slate-500">{item.template_name || '-'}</td>
                        <td className="py-2 pr-2"><StatusBadge status={item.status} /></td>
                        <td className="py-2 pr-2">{item.pages_count || 0}</td>
                        <td className="py-2 pr-2 text-amber-300">{item.token_cost || 0}</td>
                        <td className="py-2 pr-2 text-xs text-slate-500">{fmtDate(item.createdAt)}</td>
                        <td className="py-2">
                          <button onClick={() => xuLyXoaLichSu(item.id)} className="text-red-400/50 hover:text-red-300"><Trash2 className="h-3.5 w-3.5" /></button>
                        </td>
                      </tr>
                    ))}
                    {!danhSachLichSu.length && (
                      <tr><td className="py-4 text-slate-600" colSpan={8}>Chua co du lieu</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ════════════ TAB: AUDIT LOG ════════════ */}
          {activeTab === 'audit-log' && (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <h3 className="mb-4 font-semibold text-white flex items-center gap-2">
                <Shield className="h-4 w-4 text-cyan-400" /> Nhat ky thao tac quan tri
              </h3>
              <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
                <table className="min-w-full text-sm text-white/90">
                  <thead className="sticky top-0 bg-slate-950">
                    <tr className="border-b border-white/5 text-left text-xs text-slate-500">
                      <th className="py-2 pr-2">Thoi gian</th>
                      <th className="py-2 pr-2">Actor</th>
                      <th className="py-2 pr-2">Action</th>
                      <th className="py-2 pr-2">Target user</th>
                      <th className="py-2 pr-2">Detail</th>
                      <th className="py-2">Request ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {danhSachAuditLogs.slice(0, 100).map(item => (
                      <tr key={item.id} className="border-b border-white/[0.03]">
                        <td className="py-2 pr-2 text-xs text-slate-500">{fmtDate(item.createdAt)}</td>
                        <td className="py-2 pr-2">{item.actor_user_id}</td>
                        <td className="py-2 pr-2"><span className="rounded bg-white/5 px-1.5 py-0.5 text-xs font-mono">{item.action}</span></td>
                        <td className="py-2 pr-2">{item.target_user_id ?? '-'}</td>
                        <td className="py-2 pr-2 max-w-[350px] truncate text-xs" title={item.detail || ''}>{item.detail || '-'}</td>
                        <td className="py-2 text-xs font-mono text-slate-600">{item.request_id || '-'}</td>
                      </tr>
                    ))}
                    {!danhSachAuditLogs.length && (
                      <tr><td className="py-4 text-slate-600" colSpan={6}>Chua co nhat ky quan tri</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

// ─── SUB-COMPONENTS ─────────────────────────────────────────

const StatCard = ({ icon: Icon, label, value, color }) => (
  <div className={`rounded-xl border border-white/5 p-4 ${color.split(' ').pop()}`}>
    <div className="flex items-center gap-3">
      <div className={`rounded-lg p-2 ${color.split(' ').pop()}`}>
        <Icon className={`h-5 w-5 ${color.split(' ')[0]}`} />
      </div>
      <div>
        <p className="text-xs text-slate-400">{label}</p>
        <p className={`text-xl font-bold ${color.split(' ')[0]}`}>{value}</p>
      </div>
    </div>
  </div>
)

const StatusBadge = ({ status }) => {
  const configMap = {
    completed: { icon: CheckCircle2, cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' },
    pending: { icon: Clock, cls: 'bg-amber-500/10 text-amber-300 border-amber-500/20' },
    failed: { icon: XCircle, cls: 'bg-red-500/10 text-red-300 border-red-500/20' },
    success: { icon: CheckCircle2, cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' },
  }
  const cfg = configMap[status] || configMap.pending
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-xs ${cfg.cls}`}>
      <Icon className="h-3 w-3" /> {status || 'unknown'}
    </span>
  )
}

export default TrangAdmin
