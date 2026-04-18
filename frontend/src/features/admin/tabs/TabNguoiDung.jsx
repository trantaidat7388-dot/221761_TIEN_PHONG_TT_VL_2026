import { useState, useMemo } from 'react';
import { Search, Eye, Trash2, UserPlus, Crown, Shield, Coins, Users, Filter, ChevronRight, X, Plus, Minus, Star, Mail, Calendar, Hash, Activity } from 'lucide-react';
import toast from 'react-hot-toast';
import { avatarChars, fmtDate } from '../utils/formatters';
import {
  capNhatVaiTroNguoiDungAdmin,
  capNhatPremiumNguoiDungAdmin,
  congTokenNguoiDungAdmin,
  truTokenNguoiDungAdmin,
  xoaNguoiDungAdmin,
  layLichSuTheoNguoiDungAdmin,
  layTokenLedgerTheoNguoiDungAdmin,
  xoaBanGhiLichSuAdmin,
} from '../../../services/api';

const FILTERS = [
  { key: 'all', label: 'Tất cả', icon: Users },
  { key: 'premium', label: 'Premium', icon: Crown },
  { key: 'free', label: 'Miễn phí', icon: Users },
  { key: 'admin', label: 'Admin', icon: Shield },
];

const TabNguoiDung = ({ danhSachNguoiDung, taiDuLieu, setDanhSachLichSu }) => {
  const [tuKhoaTimNguoiDung, setTuKhoaTimNguoiDung] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [chiTietLichSuUser, setChiTietLichSuUser] = useState([]);
  const [chiTietLedgerUser, setChiTietLedgerUser] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // ── STATS ─────────────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    const total = danhSachNguoiDung.length;
    const premium = danhSachNguoiDung.filter(u => u.plan_type === 'premium').length;
    const admin = danhSachNguoiDung.filter(u => u.role === 'admin').length;
    const totalTokens = danhSachNguoiDung.reduce((sum, u) => sum + (u.token_balance || 0), 0);
    return { total, premium, free: total - premium, admin, totalTokens };
  }, [danhSachNguoiDung]);

  // ── FILTERED LIST ─────────────────────────────────────────────────────────
  const danhSachDaLoc = useMemo(() => {
    let list = [...danhSachNguoiDung];
    const kw = (tuKhoaTimNguoiDung || '').trim().toLowerCase();
    if (kw) list = list.filter(u => (u.username || '').toLowerCase().includes(kw) || (u.email || '').toLowerCase().includes(kw));
    if (filterType === 'premium') list = list.filter(u => u.plan_type === 'premium');
    if (filterType === 'free') list = list.filter(u => u.plan_type !== 'premium');
    if (filterType === 'admin') list = list.filter(u => u.role === 'admin');
    return list;
  }, [danhSachNguoiDung, tuKhoaTimNguoiDung, filterType]);

  // ── DETAIL LOADER ─────────────────────────────────────────────────────────
  const moChiTiet = async (user) => {
    setSelectedUser(user);
    setDrawerOpen(true);
    const [hRes, lRes] = await Promise.all([
      layLichSuTheoNguoiDungAdmin(user.id, 30),
      layTokenLedgerTheoNguoiDungAdmin(user.id, 50),
    ]);
    setChiTietLichSuUser(hRes.thanhCong ? hRes.danhSach : []);
    setChiTietLedgerUser(lRes.thanhCong ? lRes.danhSach : []);
  };

  const dongDrawer = () => {
    setDrawerOpen(false);
    setTimeout(() => setSelectedUser(null), 300);
  };

  // ── ACTIONS ───────────────────────────────────────────────────────────────
  const xuLyDoiVaiTro = async (userId, role) => {
    const kq = await capNhatVaiTroNguoiDungAdmin(userId, role);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Không thể cập nhật quyền'); return; }
    toast.success('Đã cập nhật quyền người dùng');
    taiDuLieu();
  };

  const xuLyCapNhatPremium = async (userId, enabled) => {
    const soNgayRaw = enabled ? window.prompt('Nhập số ngày premium (mặc định 30):', '30') : '0';
    if (enabled && soNgayRaw === null) return;
    const soNgay = Number(soNgayRaw || 30);
    const kq = await capNhatPremiumNguoiDungAdmin(userId, enabled, Number.isFinite(soNgay) ? soNgay : 30);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success('Đã cập nhật premium');
    taiDuLieu();
  };

  const xuLyCongToken = async (userId) => {
    const raw = window.prompt('Nhập số token muốn cộng:', '500');
    if (raw === null) return;
    const amount = Number(raw);
    if (!Number.isFinite(amount) || amount <= 0) return;
    const kq = await congTokenNguoiDungAdmin(userId, Math.floor(amount), 'Admin grant from dashboard');
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success('Đã cộng token');
    taiDuLieu();
    if (selectedUser?.id === userId) moChiTiet(selectedUser);
  };

  const xuLyTruToken = async (userId) => {
    const raw = window.prompt('Nhập số token muốn trừ:', '100');
    if (raw === null) return;
    const amount = Number(raw);
    if (!Number.isFinite(amount) || amount <= 0) return;
    const kq = await truTokenNguoiDungAdmin(userId, Math.floor(amount), 'Admin deduct from dashboard');
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success('Đã trừ token');
    taiDuLieu();
    if (selectedUser?.id === userId) moChiTiet(selectedUser);
  };

  const xuLyXoaNguoiDung = async (userId) => {
    if (!window.confirm('Bạn có chắc muốn xóa người dùng này? Hành động không thể hoàn tác.')) return;
    const kq = await xoaNguoiDungAdmin(userId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success('Đã xóa người dùng');
    if (selectedUser?.id === userId) dongDrawer();
    taiDuLieu();
  };

  const xuLyXoaLichSu = async (recordId) => {
    const kq = await xoaBanGhiLichSuAdmin(recordId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    setChiTietLichSuUser(prev => prev.filter(x => x.id !== recordId));
    if (setDanhSachLichSu) setDanhSachLichSu(prev => prev.filter(x => x.id !== recordId));
    toast.success('Đã xóa bản ghi');
  };

  return (
    <div className="space-y-6 relative">

      {/* ── STAT CARDS ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatMini icon={Users} label="Tổng người dùng" value={stats.total} color="text-cyan-400 bg-cyan-500/10" />
        <StatMini icon={Crown} label="Premium" value={stats.premium} color="text-amber-400 bg-amber-500/10" />
        <StatMini icon={Shield} label="Quản trị viên" value={stats.admin} color="text-emerald-400 bg-emerald-500/10" />
        <StatMini icon={Coins} label="Tổng Token" value={new Intl.NumberFormat('vi-VN').format(stats.totalTokens)} color="text-violet-400 bg-violet-500/10" />
      </div>

      {/* ── SEARCH & FILTER BAR ────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[280px] flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 bg-white/[0.02] focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/15 transition-all">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={tuKhoaTimNguoiDung}
            onChange={e => setTuKhoaTimNguoiDung(e.target.value)}
            placeholder="Tìm theo tên hoặc email..."
            className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
          />
          {tuKhoaTimNguoiDung && (
            <button onClick={() => setTuKhoaTimNguoiDung('')} className="text-slate-500 hover:text-white"><X className="w-4 h-4" /></button>
          )}
        </div>
        <div className="flex gap-1 p-1 rounded-xl bg-white/5 border border-white/5">
          {FILTERS.map(f => (
            <button
              key={f.key}
              onClick={() => setFilterType(f.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                filterType === f.key ? 'bg-primary-600 text-white shadow' : 'text-white/40 hover:text-white hover:bg-white/5'
              }`}
            >
              <f.icon className="w-3 h-3" />
              {f.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-500">{danhSachDaLoc.length}/{danhSachNguoiDung.length}</span>
      </div>

      {/* ── USERS TABLE (Full-width) ───────────────────────────────────────── */}
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
        <div className="overflow-x-auto max-h-[65vh] overflow-y-auto">
          <table className="w-full text-sm text-white/90">
            <thead className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur-sm">
              <tr className="border-b border-white/5 text-left text-[11px] uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4 font-medium">Người dùng</th>
                <th className="py-3 px-3 font-medium">Email</th>
                <th className="py-3 px-3 font-medium text-center">Vai trò</th>
                <th className="py-3 px-3 font-medium text-center">Gói</th>
                <th className="py-3 px-3 font-medium text-right">Token</th>
                <th className="py-3 px-3 font-medium text-right">Lượt dùng</th>
                <th className="py-3 px-4 font-medium text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {danhSachDaLoc.map(u => (
                <tr
                  key={u.id}
                  className={`border-b border-white/[0.03] transition-colors cursor-pointer ${
                    selectedUser?.id === u.id ? 'bg-primary-500/5' : 'hover:bg-white/[0.02]'
                  }`}
                  onClick={() => moChiTiet(u)}
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-primary-500/20 to-violet-500/20 border border-primary-500/20 text-xs font-bold text-primary-300 shrink-0">
                        {avatarChars(u)}
                      </div>
                      <span className="font-medium truncate max-w-[180px]">{u.username}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-slate-400 truncate max-w-[200px]" title={u.email}>{u.email}</td>
                  <td className="py-3 px-3 text-center">
                    <select
                      value={u.role || 'user'}
                      onClick={e => e.stopPropagation()}
                      onChange={e => xuLyDoiVaiTro(u.id, e.target.value)}
                      className="rounded-lg border border-white/10 bg-slate-900 px-2 py-1 text-xs font-medium text-white/80 cursor-pointer hover:border-white/20 transition"
                    >
                      <option value="user">user</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
                      u.plan_type === 'premium'
                        ? 'bg-amber-500/15 text-amber-300 border border-amber-500/20'
                        : 'bg-white/5 text-slate-500 border border-white/5'
                    }`}>
                      {u.plan_type === 'premium' && <Crown className="w-3 h-3" />}
                      {u.plan_type || 'free'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right font-mono font-semibold text-amber-300">{new Intl.NumberFormat('vi-VN').format(u.token_balance ?? 0)}</td>
                  <td className="py-3 px-3 text-right text-white/60">{u.so_lan_chuyen_doi || 0}</td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1" onClick={e => e.stopPropagation()}>
                      <ActionBtn icon={Plus} title="Cộng token" color="text-emerald-400 hover:bg-emerald-500/10" onClick={() => xuLyCongToken(u.id)} />
                      <ActionBtn icon={Minus} title="Trừ token" color="text-amber-400 hover:bg-amber-500/10" onClick={() => xuLyTruToken(u.id)} />
                      <ActionBtn
                        icon={Crown}
                        title={u.plan_type === 'premium' ? 'Hạ Premium' : 'Nâng Premium'}
                        color={u.plan_type === 'premium' ? 'text-amber-400 hover:bg-amber-500/10' : 'text-slate-400 hover:bg-white/5'}
                        onClick={() => xuLyCapNhatPremium(u.id, u.plan_type !== 'premium')}
                      />
                      <ActionBtn icon={Trash2} title="Xóa" color="text-red-400/60 hover:bg-red-500/10 hover:text-red-400" onClick={() => xuLyXoaNguoiDung(u.id)} />
                    </div>
                  </td>
                </tr>
              ))}
              {!danhSachDaLoc.length && (
                <tr><td className="py-12 text-center text-slate-600" colSpan={7}>Không tìm thấy người dùng</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── USER DETAIL DRAWER ─────────────────────────────────────────────── */}
      {/* Backdrop */}
      {drawerOpen && <div className="fixed inset-0 bg-black/50 z-40 transition-opacity" onClick={dongDrawer} />}

      {/* Drawer */}
      <div className={`fixed top-0 right-0 h-full w-full max-w-lg bg-slate-950 border-l border-white/10 shadow-2xl z-50 transform transition-transform duration-300 ease-out ${
        drawerOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        {selectedUser && (
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-primary-500/30 to-violet-500/30 border border-primary-500/20 text-sm font-bold text-primary-300">
                  {avatarChars(selectedUser)}
                </div>
                <div>
                  <p className="font-bold text-white text-lg">{selectedUser.username}</p>
                  <p className="text-xs text-slate-400 flex items-center gap-1"><Mail className="w-3 h-3" />{selectedUser.email}</p>
                </div>
              </div>
              <button onClick={dongDrawer} className="p-2 rounded-lg text-slate-500 hover:bg-white/5 hover:text-white transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* User Info Cards */}
            <div className="px-6 py-4 grid grid-cols-3 gap-3">
              <InfoCard label="Vai trò" value={selectedUser.role || 'user'} icon={Shield} />
              <InfoCard label="Gói" value={selectedUser.plan_type || 'free'} icon={Crown} highlight={selectedUser.plan_type === 'premium'} />
              <InfoCard label="Token" value={selectedUser.token_balance ?? 0} icon={Coins} />
            </div>

            {/* Quick Actions */}
            <div className="px-6 pb-4 flex flex-wrap gap-2">
              <QuickAction label="Cộng token" icon={Plus} color="bg-emerald-500/10 text-emerald-400 border-emerald-500/20" onClick={() => xuLyCongToken(selectedUser.id)} />
              <QuickAction label="Trừ token" icon={Minus} color="bg-red-500/10 text-red-400 border-red-500/20" onClick={() => xuLyTruToken(selectedUser.id)} />
              <QuickAction
                label={selectedUser.plan_type === 'premium' ? 'Hạ Premium' : 'Nâng Premium'}
                icon={Crown}
                color="bg-amber-500/10 text-amber-400 border-amber-500/20"
                onClick={() => xuLyCapNhatPremium(selectedUser.id, selectedUser.plan_type !== 'premium')}
              />
              <QuickAction label="Xóa tài khoản" icon={Trash2} color="bg-red-500/10 text-red-400 border-red-500/20" onClick={() => xuLyXoaNguoiDung(selectedUser.id)} />
            </div>

            {/* Tabs: History & Ledger */}
            <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-5">
              <DetailSection title="Lịch sử chuyển đổi" icon={Activity} items={chiTietLichSuUser} renderItem={(item) => (
                <div key={item.id} className="flex items-start justify-between gap-2 rounded-xl bg-white/[0.03] p-3 border border-white/[0.03]">
                  <div className="min-w-0">
                    <p className="truncate text-sm text-white font-medium">{item.file_name || 'Không tên'}</p>
                    <p className="text-[11px] text-slate-500">{item.status} · {item.pages_count || 0} trang · {item.token_cost || 0} token</p>
                  </div>
                  <button onClick={() => xuLyXoaLichSu(item.id)} className="text-red-400/40 hover:text-red-300 shrink-0 mt-1"><Trash2 className="h-3.5 w-3.5" /></button>
                </div>
              )} />

              <DetailSection title="Token Ledger" icon={Coins} items={chiTietLedgerUser} renderItem={(item) => (
                <div key={item.id} className="rounded-xl bg-white/[0.03] p-3 border border-white/[0.03]">
                  <p className="text-sm text-white font-medium">{item.reason}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`text-xs font-bold ${item.delta_token >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {item.delta_token >= 0 ? '+' : ''}{item.delta_token}
                    </span>
                    <span className="text-[11px] text-slate-500">→ Số dư: {item.balance_after}</span>
                  </div>
                </div>
              )} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ── SUB-COMPONENTS ──────────────────────────────────────────────────────────
const StatMini = ({ icon: Icon, label, value, color }) => (
  <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex items-center gap-4">
    <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center shrink-0`}>
      <Icon className="w-5 h-5" />
    </div>
    <div>
      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">{label}</p>
      <p className="text-xl font-black text-white">{value}</p>
    </div>
  </div>
);

const ActionBtn = ({ icon: Icon, title, color, onClick }) => (
  <button onClick={onClick} className={`p-1.5 rounded-lg transition ${color}`} title={title}>
    <Icon className="w-3.5 h-3.5" />
  </button>
);

const InfoCard = ({ label, value, icon: Icon, highlight = false }) => (
  <div className={`rounded-xl border p-3 text-center ${highlight ? 'border-amber-500/20 bg-amber-500/5' : 'border-white/5 bg-white/[0.02]'}`}>
    <Icon className={`w-4 h-4 mx-auto mb-1.5 ${highlight ? 'text-amber-400' : 'text-slate-500'}`} />
    <p className="text-[10px] text-slate-500 uppercase mb-0.5">{label}</p>
    <p className={`text-sm font-bold ${highlight ? 'text-amber-300' : 'text-white'}`}>{value}</p>
  </div>
);

const QuickAction = ({ label, icon: Icon, color, onClick }) => (
  <button onClick={onClick} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition hover:opacity-80 ${color}`}>
    <Icon className="w-3 h-3" /> {label}
  </button>
);

const DetailSection = ({ title, icon: Icon, items, renderItem }) => (
  <div>
    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
      <Icon className="w-3.5 h-3.5 text-primary-400" /> {title}
    </h4>
    <div className="space-y-2">
      {items.map(renderItem)}
      {!items.length && <p className="text-xs text-slate-600 italic">Chưa có dữ liệu</p>}
    </div>
  </div>
);

export default TabNguoiDung;
