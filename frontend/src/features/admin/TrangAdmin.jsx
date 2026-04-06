import { useCallback, useEffect, useMemo, useState } from 'react'
import { Shield, Users, History, Trash2, RefreshCw, Files } from 'lucide-react'
import toast from 'react-hot-toast'
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
  taiLenTemplate,
  xoaTemplateAdmin,
} from '../../services/api'
import { NutBam } from '../../components'

const TrangAdmin = () => {
  const [dangTai, setDangTai] = useState(true)
  const [tuKhoaTimNguoiDung, setTuKhoaTimNguoiDung] = useState('')
  const [tongQuan, setTongQuan] = useState(null)
  const [danhSachNguoiDung, setDanhSachNguoiDung] = useState([])
  const [danhSachLichSu, setDanhSachLichSu] = useState([])
  const [danhSachTemplate, setDanhSachTemplate] = useState([])
  const [danhSachAuditLogs, setDanhSachAuditLogs] = useState([])
  const [selectedUserId, setSelectedUserId] = useState(null)
  const [selectedUserSummary, setSelectedUserSummary] = useState(null)
  const [chiTietLichSuUser, setChiTietLichSuUser] = useState([])
  const [chiTietLedgerUser, setChiTietLedgerUser] = useState([])
  const [dangTaiTemplate, setDangTaiTemplate] = useState(false)

  const taiDuLieu = useCallback(async () => {
    setDangTai(true)
    try {
      const [overviewRes, usersRes, historyRes, auditRes] = await Promise.all([
        layTongQuanAdmin(),
        layDanhSachNguoiDungAdmin(),
        layLichSuToanHeThongAdmin(200),
        layAuditLogsAdmin(200),
      ])
      const templatesRes = await layDanhSachTemplateAdmin()

      if (!overviewRes.thanhCong) throw new Error(overviewRes.loiMessage || 'Không tải được tổng quan')
      if (!usersRes.thanhCong) throw new Error(usersRes.loiMessage || 'Không tải được danh sách người dùng')
      if (!historyRes.thanhCong) throw new Error(historyRes.loiMessage || 'Không tải được lịch sử hệ thống')
      if (!auditRes.thanhCong) throw new Error(auditRes.loiMessage || 'Không tải được nhật ký quản trị')
      if (!templatesRes.thanhCong) throw new Error(templatesRes.loiMessage || 'Không tải được danh sách template')

      setTongQuan(overviewRes.data)
      setDanhSachNguoiDung(usersRes.danhSach)
      setDanhSachLichSu(historyRes.danhSach)
      setDanhSachTemplate(templatesRes.danhSach)
      setDanhSachAuditLogs(auditRes.danhSach)
    } catch (error) {
      toast.error(error.message || 'Không thể tải dữ liệu trang Admin')
    } finally {
      setDangTai(false)
    }
  }, [])

  useEffect(() => {
    taiDuLieu()
  }, [taiDuLieu])

  const xuLyDoiVaiTro = async (userId, role) => {
    const ketQua = await capNhatVaiTroNguoiDungAdmin(userId, role)
    if (!ketQua.thanhCong) {
      toast.error(ketQua.loiMessage || 'Không thể cập nhật quyền')
      return
    }
    toast.success('Đã cập nhật quyền người dùng')
    taiDuLieu()
  }

  const xuLyXoaNguoiDung = async (userId) => {
    if (!window.confirm('Bạn có chắc muốn xóa người dùng này?')) return
    const ketQua = await xoaNguoiDungAdmin(userId)
    if (!ketQua.thanhCong) {
      toast.error(ketQua.loiMessage || 'Không thể xóa người dùng')
      return
    }
    toast.success('Đã xóa người dùng')
    taiDuLieu()
  }

  const taiChiTietNguoiDung = async (userId) => {
    setSelectedUserId(userId)
    const user = danhSachNguoiDung.find((u) => u.id === userId)
    setSelectedUserSummary(user || null)
    const [historyRes, ledgerRes] = await Promise.all([
      layLichSuTheoNguoiDungAdmin(userId, 30),
      layTokenLedgerTheoNguoiDungAdmin(userId, 50),
    ])

    if (!historyRes.thanhCong) {
      toast.error(historyRes.loiMessage || 'Không tải được lịch sử người dùng')
      setChiTietLichSuUser([])
    } else {
      setChiTietLichSuUser(historyRes.danhSach)
    }

    if (!ledgerRes.thanhCong) {
      toast.error(ledgerRes.loiMessage || 'Không tải được ledger token')
      setChiTietLedgerUser([])
    } else {
      setChiTietLedgerUser(ledgerRes.danhSach)
    }
  }

  const xuLyCapNhatPremium = async (userId, enabled) => {
    const soNgayRaw = enabled ? window.prompt('Nhập số ngày premium (mặc định 30):', '30') : '0'
    const soNgay = Number(soNgayRaw || 30)
    const ketQua = await capNhatPremiumNguoiDungAdmin(userId, enabled, Number.isFinite(soNgay) ? soNgay : 30)
    if (!ketQua.thanhCong) {
      toast.error(ketQua.loiMessage || 'Không thể cập nhật premium')
      return
    }
    toast.success('Đã cập nhật trạng thái premium')
    taiDuLieu()
  }

  const xuLyCongToken = async (userId) => {
    const amountRaw = window.prompt('Nhập số token muốn cộng:', '500')
    const amount = Number(amountRaw)
    if (!Number.isFinite(amount) || amount <= 0) return
    const ketQua = await congTokenNguoiDungAdmin(userId, Math.floor(amount), 'Admin grant from dashboard')
    if (!ketQua.thanhCong) {
      toast.error(ketQua.loiMessage || 'Không thể cộng token')
      return
    }
    toast.success('Đã cộng token')
    taiDuLieu()
    if (selectedUserId === userId) taiChiTietNguoiDung(userId)
  }

  const xuLyTruToken = async (userId) => {
    const amountRaw = window.prompt('Nhập số token muốn trừ:', '100')
    const amount = Number(amountRaw)
    if (!Number.isFinite(amount) || amount <= 0) return
    const ketQua = await truTokenNguoiDungAdmin(userId, Math.floor(amount), 'Admin deduct from dashboard')
    if (!ketQua.thanhCong) {
      toast.error(ketQua.loiMessage || 'Không thể trừ token')
      return
    }
    toast.success('Đã trừ token')
    taiDuLieu()
    if (selectedUserId === userId) taiChiTietNguoiDung(userId)
  }

  const xuLyXoaLichSu = async (recordId) => {
    const ketQua = await xoaBanGhiLichSuAdmin(recordId)
    if (!ketQua.thanhCong) {
      toast.error(ketQua.loiMessage || 'Không thể xóa bản ghi lịch sử')
      return
    }
    setDanhSachLichSu((prev) => prev.filter((x) => x.id !== recordId))
    setChiTietLichSuUser((prev) => prev.filter((x) => x.id !== recordId))
    toast.success('Đã xóa bản ghi lịch sử')
  }

  const xuLyXoaTemplate = async (templateId) => {
    if (!window.confirm('Bạn có chắc muốn xóa template này?')) return
    const ketQua = await xoaTemplateAdmin(templateId)
    if (!ketQua.thanhCong) {
      toast.error(ketQua.loiMessage || 'Không thể xóa template')
      return
    }
    setDanhSachTemplate((prev) => prev.filter((x) => x.id !== templateId))
    toast.success('Đã xóa template')
  }

  const xuLyHanhDongNhanhNguoiDung = async (user, action) => {
    if (!action || !user) return
    if (action === 'detail') {
      await taiChiTietNguoiDung(user.id)
      return
    }
    if (action === 'premium') {
      await xuLyCapNhatPremium(user.id, user.plan_type !== 'premium')
      return
    }
    if (action === 'grant') {
      await xuLyCongToken(user.id)
      return
    }
    if (action === 'deduct') {
      await xuLyTruToken(user.id)
      return
    }
    if (action === 'delete') {
      await xuLyXoaNguoiDung(user.id)
    }
  }

  const xuLyTaiLenTemplate = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setDangTaiTemplate(true)
    try {
      const ketQua = await taiLenTemplate(file)
      if (!ketQua.thanhCong) {
        toast.error(ketQua.loiMessage || 'Không thể tải lên template')
        return
      }
      toast.success(ketQua.message || 'Đã tải lên template')
      const dsTemplate = await layDanhSachTemplateAdmin()
      if (dsTemplate.thanhCong) {
        setDanhSachTemplate(dsTemplate.danhSach)
      }
      const dsAudit = await layAuditLogsAdmin(200)
      if (dsAudit.thanhCong) {
        setDanhSachAuditLogs(dsAudit.danhSach)
      }
    } finally {
      setDangTaiTemplate(false)
      e.target.value = ''
    }
  }

  const danhSachNguoiDungDaLoc = useMemo(() => {
    const keyword = (tuKhoaTimNguoiDung || '').trim().toLowerCase()
    if (!keyword) return danhSachNguoiDung
    return danhSachNguoiDung.filter((u) => {
      const username = (u.username || '').toLowerCase()
      const email = (u.email || '').toLowerCase()
      return username.includes(keyword) || email.includes(keyword)
    })
  }, [danhSachNguoiDung, tuKhoaTimNguoiDung])

  const dinhDangNgayGio = (value) => {
    if (!(value instanceof Date)) return '-'
    return value.toLocaleString('vi-VN')
  }

  const dinhDangKichThuoc = (bytes) => {
    if (!Number.isFinite(bytes) || bytes < 0) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const layAvtKyTu = (user) => {
    const nguon = (user?.username || user?.email || '').trim()
    if (!nguon) return 'U'
    const phan = nguon
      .replace(/\s+/g, ' ')
      .split(' ')
      .filter(Boolean)
    if (phan.length >= 2) {
      return (phan[0][0] + phan[phan.length - 1][0]).toUpperCase()
    }
    return (phan[0]?.slice(0, 2) || 'U').toUpperCase()
  }

  return (
    <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary-400" />
              Trang quản trị
            </h1>
            <p className="text-white/60">Quản lý tài khoản và lịch sử chuyển đổi toàn hệ thống</p>
          </div>
          <NutBam onClick={taiDuLieu} bienThe="secondary" icon={RefreshCw} dangTai={dangTai}>
            Làm mới
          </NutBam>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="glass-card p-4 bg-white/10">
            <p className="text-white/60 text-sm">Tổng người dùng</p>
            <p className="text-3xl text-white font-bold">{tongQuan?.tong_nguoi_dung ?? '-'}</p>
          </div>
          <div className="glass-card p-4 bg-emerald-500/10">
            <p className="text-emerald-200 text-sm">Số admin</p>
            <p className="text-3xl text-emerald-300 font-bold">{tongQuan?.tong_admin ?? '-'}</p>
          </div>
          <div className="glass-card p-4 bg-cyan-500/10">
            <p className="text-cyan-200 text-sm">Số tài khoản premium</p>
            <p className="text-3xl text-cyan-300 font-bold">{tongQuan?.tong_premium ?? '-'}</p>
          </div>
        </div>

        <div className="glass-card p-4 mb-6 bg-sky-500/10">
          <p className="text-sky-200 text-sm">Tổng bản ghi lịch sử</p>
          <p className="text-2xl text-sky-300 font-bold">{tongQuan?.tong_ban_ghi_lich_su ?? '-'}</p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <section className="glass-card p-4 h-[72vh] flex flex-col min-h-[520px] overflow-hidden">
            <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-primary-300" />
              Người dùng
            </h2>
            <div className="mb-3">
              <input
                type="text"
                value={tuKhoaTimNguoiDung}
                onChange={(e) => setTuKhoaTimNguoiDung(e.target.value)}
                placeholder="Tìm theo username hoặc email..."
                className="w-full rounded-lg border border-white/15 bg-slate-900/70 px-3 py-2 text-sm text-white placeholder:text-white/40 outline-none focus:border-primary-300"
              />
              <p className="text-xs text-white/50 mt-1">
                Hiển thị {danhSachNguoiDungDaLoc.length}/{danhSachNguoiDung.length} người dùng. Bấm vào dòng để xem lịch sử chuyển đổi.
              </p>
            </div>
            <div className="overflow-auto flex-1 min-h-0">
              <table className="min-w-full table-fixed text-sm text-white/90">
                <thead>
                  <tr className="text-left text-white/60 border-b border-white/10">
                    <th className="py-2 pr-2 w-[26%]">Username</th>
                    <th className="py-2 pr-2 w-[24%]">Email</th>
                    <th className="py-2 pr-2 w-[12%]">Vai trò</th>
                    <th className="py-2 pr-2 w-[10%]">Gói</th>
                    <th className="py-2 pr-2 w-[9%]">Token</th>
                    <th className="py-2 pr-2 w-[8%]">Số lần</th>
                    <th className="py-2 w-[11%] whitespace-nowrap">Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {danhSachNguoiDungDaLoc.map((u) => (
                    <tr
                      key={u.id}
                      className={`border-b border-white/5 cursor-pointer transition-colors ${selectedUserId === u.id ? 'bg-sky-500/10' : 'hover:bg-white/5'}`}
                      onClick={() => taiChiTietNguoiDung(u.id)}
                      title="Bấm để xem lịch sử chuyển đổi"
                    >
                      <td className="py-2 pr-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <div className="w-7 h-7 rounded-full bg-primary-500/25 border border-primary-400/30 text-primary-200 text-[11px] font-semibold flex items-center justify-center shrink-0">
                            {layAvtKyTu(u)}
                          </div>
                          <span className="truncate" title={u.username}>{u.username}</span>
                        </div>
                      </td>
                      <td className="py-2 pr-2 truncate" title={u.email}>{u.email}</td>
                      <td className="py-2 pr-2">
                        <select
                          value={u.role || 'user'}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => xuLyDoiVaiTro(u.id, e.target.value)}
                          className="bg-slate-800 border border-white/20 rounded-lg px-2 py-1"
                        >
                          <option value="user">user</option>
                          <option value="admin">admin</option>
                        </select>
                      </td>
                      <td className="py-2 pr-2">
                        <span className={`px-2 py-1 rounded text-xs ${u.plan_type === 'premium' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-white/10 text-white/70'}`}>
                          {u.plan_type || 'free'}
                        </span>
                      </td>
                      <td className="py-2 pr-2 font-semibold text-amber-300">{u.token_balance ?? 0}</td>
                      <td className="py-2 pr-2">{u.so_lan_chuyen_doi}</td>
                      <td className="py-2">
                        <select
                          defaultValue=""
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => {
                            e.stopPropagation()
                            const action = e.target.value
                            if (action) {
                              xuLyHanhDongNhanhNguoiDung(u, action)
                              e.target.value = ''
                            }
                          }}
                          className="w-full bg-slate-800 border border-white/20 rounded-lg px-2 py-1 text-xs whitespace-nowrap"
                        >
                          <option value="">Tác vụ</option>
                          <option value="detail">Chi tiết</option>
                          <option value="premium">{u.plan_type === 'premium' ? 'Hạ premium' : 'Nâng premium'}</option>
                          <option value="grant">Cộng token</option>
                          <option value="deduct">Trừ token</option>
                          <option value="delete">Xóa người dùng</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                  {!danhSachNguoiDungDaLoc.length && (
                    <tr>
                      <td className="py-3 text-white/60" colSpan={7}>
                        {danhSachNguoiDung.length ? 'Không tìm thấy người dùng phù hợp' : 'Không có dữ liệu người dùng'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="glass-card p-4 h-[72vh] flex flex-col min-h-[520px]">
            <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
              <History className="w-5 h-5 text-primary-300" />
              {selectedUserId ? `Chi tiết tài khoản #${selectedUserId}` : 'Chi tiết tài khoản'}
            </h2>

            {!selectedUserId && (
              <p className="text-sm text-white/60">Chọn một người dùng ở bảng bên trái để xem lịch sử chuyển đổi và token ledger.</p>
            )}

            {selectedUserId && (
              <div className="space-y-4 flex-1 min-h-0 overflow-y-auto pr-1">
                {selectedUserSummary && (
                  <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                    <div className="flex items-center gap-3 mb-1">
                      <div className="w-9 h-9 rounded-full bg-primary-500/25 border border-primary-400/30 text-primary-200 text-sm font-semibold flex items-center justify-center shrink-0">
                        {layAvtKyTu(selectedUserSummary)}
                      </div>
                      <p className="text-white font-medium">{selectedUserSummary.username}</p>
                    </div>
                    <p className="text-xs text-white/60">{selectedUserSummary.email}</p>
                    <p className="text-xs text-white/60 mt-1">Vai trò: {selectedUserSummary.role || 'user'} | Gói: {selectedUserSummary.plan_type || 'free'} | Token: {selectedUserSummary.token_balance ?? 0}</p>
                  </div>
                )}

                <div>
                  <h3 className="text-white/80 font-medium mb-2">Lịch sử chuyển đổi gần nhất</h3>
                  <div className="space-y-2">
                    {chiTietLichSuUser.map((item) => (
                      <div key={item.id} className="p-2 rounded bg-white/5 border border-white/10 flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="text-sm text-white truncate">{item.file_name || 'Không tên file'}</p>
                          <p className="text-xs text-white/60">{item.status} | {item.pages_count || 0} trang | {item.token_cost || 0} token</p>
                        </div>
                        <button
                          onClick={() => xuLyXoaLichSu(item.id)}
                          className="text-red-300 hover:text-red-200"
                          title="Xóa bản ghi"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    {!chiTietLichSuUser.length && <p className="text-sm text-white/60">Chưa có dữ liệu</p>}
                  </div>
                </div>

                <div>
                  <h3 className="text-white/80 font-medium mb-2">Token ledger gần nhất</h3>
                  <div className="space-y-2">
                    {chiTietLedgerUser.map((item) => (
                      <div key={item.id} className="p-2 rounded bg-white/5 border border-white/10">
                        <p className="text-sm text-white">{item.reason}</p>
                        <p className="text-xs text-white/60">delta: {item.delta_token} | balance: {item.balance_after}</p>
                      </div>
                    ))}
                    {!chiTietLedgerUser.length && <p className="text-sm text-white/60">Chưa có dữ liệu</p>}
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>

        <section className="glass-card p-4 mt-6">
          <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
            <Files className="w-5 h-5 text-primary-300" />
            Quản lý template tùy chỉnh
          </h2>
          <div className="overflow-x-auto">
            <div className="mb-3 flex items-center justify-between gap-3">
              <label className="inline-flex items-center gap-2 rounded-lg border border-white/15 bg-slate-900/60 px-3 py-2 text-sm text-white cursor-pointer hover:bg-slate-900/80">
                <input
                  type="file"
                  accept=".tex,.zip,application/zip,application/x-zip-compressed"
                  onChange={xuLyTaiLenTemplate}
                  className="hidden"
                  disabled={dangTaiTemplate}
                />
                {dangTaiTemplate ? 'Đang tải lên...' : 'Tải lên template (.tex / .zip)'}
              </label>
              <p className="text-xs text-white/50">Mục này dành cho quản trị viên hệ thống.</p>
            </div>
            <table className="min-w-full text-sm text-white/90">
              <thead>
                <tr className="text-left text-white/60 border-b border-white/10">
                  <th className="py-2 pr-2">Tên template</th>
                  <th className="py-2 pr-2">Phạm vi</th>
                  <th className="py-2 pr-2">Chủ sở hữu</th>
                  <th className="py-2 pr-2">Loại</th>
                  <th className="py-2 pr-2">Kích thước</th>
                  <th className="py-2">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {danhSachTemplate.map((tpl) => (
                  <tr key={tpl.id} className="border-b border-white/5">
                    <td className="py-2 pr-2">{tpl.ten}</td>
                    <td className="py-2 pr-2">{tpl.scope === 'private' ? 'cá nhân' : 'global'}</td>
                    <td className="py-2 pr-2">{tpl.owner_label || '-'}</td>
                    <td className="py-2 pr-2">{tpl.loai}</td>
                    <td className="py-2 pr-2">{dinhDangKichThuoc(tpl.kich_thuoc)}</td>
                    <td className="py-2">
                      <button
                        onClick={() => xuLyXoaTemplate(tpl.id)}
                        className="inline-flex items-center gap-1 text-red-300 hover:text-red-200"
                      >
                        <Trash2 className="w-4 h-4" /> Xóa
                      </button>
                    </td>
                  </tr>
                ))}
                {!danhSachTemplate.length && (
                  <tr>
                    <td className="py-3 text-white/60" colSpan={6}>Không có template tùy chỉnh</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="glass-card p-4 mt-6">
          <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
            <History className="w-5 h-5 text-primary-300" />
            Nhật ký thao tác quản trị
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-white/90">
              <thead>
                <tr className="text-left text-white/60 border-b border-white/10">
                  <th className="py-2 pr-2">Thời gian</th>
                  <th className="py-2 pr-2">Actor</th>
                  <th className="py-2 pr-2">Action</th>
                  <th className="py-2 pr-2">Target user</th>
                  <th className="py-2 pr-2">Detail</th>
                  <th className="py-2">Request ID</th>
                </tr>
              </thead>
              <tbody>
                {danhSachAuditLogs.slice(0, 50).map((item) => (
                  <tr key={item.id} className="border-b border-white/5">
                    <td className="py-2 pr-2">{dinhDangNgayGio(item.createdAt)}</td>
                    <td className="py-2 pr-2">{item.actor_user_id}</td>
                    <td className="py-2 pr-2">{item.action}</td>
                    <td className="py-2 pr-2">{item.target_user_id ?? '-'}</td>
                    <td className="py-2 pr-2 max-w-[420px] truncate" title={item.detail || ''}>{item.detail || '-'}</td>
                    <td className="py-2 font-mono text-xs text-white/70">{item.request_id || '-'}</td>
                  </tr>
                ))}
                {!danhSachAuditLogs.length && (
                  <tr>
                    <td className="py-3 text-white/60" colSpan={6}>Chưa có nhật ký quản trị</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}

export default TrangAdmin
