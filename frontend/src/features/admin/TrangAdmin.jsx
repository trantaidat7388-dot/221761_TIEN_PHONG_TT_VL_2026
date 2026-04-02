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
  xoaTemplateAdmin,
} from '../../services/api'
import { NutBam } from '../../components'

const TrangAdmin = () => {
  const [dangTai, setDangTai] = useState(true)
  const [tongQuan, setTongQuan] = useState(null)
  const [danhSachNguoiDung, setDanhSachNguoiDung] = useState([])
  const [danhSachLichSu, setDanhSachLichSu] = useState([])
  const [danhSachTemplate, setDanhSachTemplate] = useState([])
  const [selectedUserId, setSelectedUserId] = useState(null)
  const [chiTietLichSuUser, setChiTietLichSuUser] = useState([])
  const [chiTietLedgerUser, setChiTietLedgerUser] = useState([])

  const taiDuLieu = useCallback(async () => {
    setDangTai(true)
    try {
      const [overviewRes, usersRes, historyRes] = await Promise.all([
        layTongQuanAdmin(),
        layDanhSachNguoiDungAdmin(),
        layLichSuToanHeThongAdmin(200),
      ])
      const templatesRes = await layDanhSachTemplateAdmin()

      if (!overviewRes.thanhCong) throw new Error(overviewRes.loiMessage || 'Không tải được tổng quan')
      if (!usersRes.thanhCong) throw new Error(usersRes.loiMessage || 'Không tải được danh sách người dùng')
      if (!historyRes.thanhCong) throw new Error(historyRes.loiMessage || 'Không tải được lịch sử hệ thống')
      if (!templatesRes.thanhCong) throw new Error(templatesRes.loiMessage || 'Không tải được danh sách template')

      setTongQuan(overviewRes.data)
      setDanhSachNguoiDung(usersRes.danhSach)
      setDanhSachLichSu(historyRes.danhSach)
      setDanhSachTemplate(templatesRes.danhSach)
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

  const topRecentHistory = useMemo(() => danhSachLichSu.slice(0, 20), [danhSachLichSu])

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
          <section className="glass-card p-4">
            <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-primary-300" />
              Người dùng
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-white/90">
                <thead>
                  <tr className="text-left text-white/60 border-b border-white/10">
                    <th className="py-2 pr-2">Username</th>
                    <th className="py-2 pr-2">Email</th>
                    <th className="py-2 pr-2">Vai trò</th>
                    <th className="py-2 pr-2">Gói</th>
                    <th className="py-2 pr-2">Token</th>
                    <th className="py-2 pr-2">Số lần</th>
                    <th className="py-2">Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {danhSachNguoiDung.map((u) => (
                    <tr key={u.id} className="border-b border-white/5">
                      <td className="py-2 pr-2">{u.username}</td>
                      <td className="py-2 pr-2">{u.email}</td>
                      <td className="py-2 pr-2">
                        <select
                          value={u.role || 'user'}
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
                      <td className="py-2 space-x-2">
                        <button onClick={() => taiChiTietNguoiDung(u.id)} className="text-sky-300 hover:text-sky-200 text-xs">Chi tiết</button>
                        <button onClick={() => xuLyCapNhatPremium(u.id, u.plan_type !== 'premium')} className="text-emerald-300 hover:text-emerald-200 text-xs">
                          {u.plan_type === 'premium' ? 'Hạ Premium' : 'Nâng Premium'}
                        </button>
                        <button onClick={() => xuLyCongToken(u.id)} className="text-amber-300 hover:text-amber-200 text-xs">+Token</button>
                        <button onClick={() => xuLyTruToken(u.id)} className="text-orange-300 hover:text-orange-200 text-xs">-Token</button>
                        <button
                          onClick={() => xuLyXoaNguoiDung(u.id)}
                          className="inline-flex items-center gap-1 text-red-300 hover:text-red-200 text-xs"
                        >
                          <Trash2 className="w-3.5 h-3.5" /> Xóa
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!danhSachNguoiDung.length && (
                    <tr>
                      <td className="py-3 text-white/60" colSpan={7}>Không có dữ liệu người dùng</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="glass-card p-4">
            <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
              <History className="w-5 h-5 text-primary-300" />
              20 bản ghi lịch sử gần nhất
            </h2>
            <div className="space-y-2 max-h-[520px] overflow-auto pr-1">
              {topRecentHistory.map((item) => (
                <div key={item.id} className="border border-white/10 rounded-xl p-3 bg-white/5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-white text-sm font-medium truncate">{item.file_name || 'Không tên file'}</p>
                      <p className="text-white/60 text-xs truncate">{item.email || item.username || `User #${item.user_id}`}</p>
                      <p className="text-white/50 text-xs mt-1">{dinhDangNgayGio(item.createdAt)}</p>
                    </div>
                    <button
                      onClick={() => xuLyXoaLichSu(item.id)}
                      className="text-red-300 hover:text-red-200"
                      title="Xóa bản ghi"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
              {!topRecentHistory.length && (
                <p className="text-white/60 text-sm">Không có bản ghi lịch sử</p>
              )}
            </div>
          </section>
        </div>

        {selectedUserId && (
          <section className="glass-card p-4 mt-6">
            <h2 className="text-white font-semibold text-lg mb-4">Chi tiết tài khoản #{selectedUserId}</h2>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <div>
                <h3 className="text-white/80 font-medium mb-2">Lịch sử chuyển đổi gần nhất</h3>
                <div className="space-y-2 max-h-72 overflow-auto">
                  {chiTietLichSuUser.map((item) => (
                    <div key={item.id} className="p-2 rounded bg-white/5 border border-white/10">
                      <p className="text-sm text-white truncate">{item.file_name || 'Không tên file'}</p>
                      <p className="text-xs text-white/60">{item.status} | {item.pages_count || 0} trang | {item.token_cost || 0} token</p>
                    </div>
                  ))}
                  {!chiTietLichSuUser.length && <p className="text-sm text-white/60">Chưa có dữ liệu</p>}
                </div>
              </div>
              <div>
                <h3 className="text-white/80 font-medium mb-2">Token ledger gần nhất</h3>
                <div className="space-y-2 max-h-72 overflow-auto">
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
          </section>
        )}

        <section className="glass-card p-4 mt-6">
          <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
            <Files className="w-5 h-5 text-primary-300" />
            Quản lý template tùy chỉnh
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-white/90">
              <thead>
                <tr className="text-left text-white/60 border-b border-white/10">
                  <th className="py-2 pr-2">Tên template</th>
                  <th className="py-2 pr-2">Loại</th>
                  <th className="py-2 pr-2">Kích thước</th>
                  <th className="py-2">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {danhSachTemplate.map((tpl) => (
                  <tr key={tpl.id} className="border-b border-white/5">
                    <td className="py-2 pr-2">{tpl.ten}</td>
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
                    <td className="py-3 text-white/60" colSpan={4}>Không có template tùy chỉnh</td>
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
