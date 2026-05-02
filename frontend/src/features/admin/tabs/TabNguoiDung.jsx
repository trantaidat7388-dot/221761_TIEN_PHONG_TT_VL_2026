import { useState, useMemo, useCallback } from 'react';
import { Search, Eye, Trash2, UserPlus, Crown, Shield, Coins, Users, Filter, ChevronRight, X, Plus, Minus, Star, Mail, Calendar, Hash, Activity, Download, RefreshCw, AlertCircle, Lock, Unlock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
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
  capNhatTrangThaiNguoiDungAdmin,
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

  // ── MODAL STATES ──────────────────────────────────────────────────────────
  const [tokenModal, setTokenModal] = useState({ open: false, user: null, mode: 'grant', amount: '', reason: '' });
  const [premiumModal, setPremiumModal] = useState({ open: false, user: null, soNgay: '30' });

  const moTokenModal = (user, mode) => setTokenModal({ open: true, user, mode, amount: '', reason: '' });
  const moPremiumModal = (user) => setPremiumModal({ open: true, user, soNgay: '30' });

  // ── ACTIONS ───────────────────────────────────────────────────────────────
  const xuLyDoiVaiTro = async (userId, role) => {
    const kq = await capNhatVaiTroNguoiDungAdmin(userId, role);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Không thể cập nhật quyền'); return; }
    toast.success('Đã cập nhật quyền người dùng');
    taiDuLieu();
  };

  const xuLyTokenModal = async () => {
    const { user, mode, amount: rawAmt, reason } = tokenModal;
    const amount = Math.floor(Number(rawAmt));
    if (!Number.isFinite(amount) || amount <= 0) { toast.error('Số token phải > 0'); return; }
    const ly_do = reason || (mode === 'grant' ? 'Admin cộng token' : 'Admin trừ token');
    const fn = mode === 'grant' ? congTokenNguoiDungAdmin : truTokenNguoiDungAdmin;
    const kq = await fn(user.id, amount, ly_do);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success(mode === 'grant' ? `+${amount} token` : `-${amount} token`);
    setTokenModal(p => ({ ...p, open: false }));
    taiDuLieu();
    if (selectedUser?.id === user.id) moChiTiet(selectedUser);
  };

  const xuLyPremiumModal = async (enabled, overrideUser = null) => {
    const user = overrideUser || premiumModal.user;
    if (!user) return;
    const { soNgay: raw } = premiumModal;
    const soNgay = Number(raw || 30);
    if (enabled && (!Number.isFinite(soNgay) || soNgay < 1)) { toast.error('Số ngày >= 1'); return; }
    if (!enabled && !window.confirm(`Hạ Premium cho người dùng ${user.username}?`)) return;
    const kq = await capNhatPremiumNguoiDungAdmin(user.id, enabled, enabled ? soNgay : 0);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success(enabled ? `Premium ${soNgay} ngày cho ${user.username}` : `Đã hạ Premium cho ${user.username}`);
    setPremiumModal(p => ({ ...p, open: false }));
    taiDuLieu();
    if (selectedUser?.id === user.id) setSelectedUser({ ...selectedUser, plan_type: enabled ? 'premium' : 'free' });
  };

  const xuLyDoiTrangThai = async (user) => {
    const newStatus = !user.is_active;
    if (!window.confirm(`Bạn có chắc muốn ${newStatus ? 'Mở khóa' : 'Khóa'} tài khoản ${user.username}?`)) return;
    const kq = await capNhatTrangThaiNguoiDungAdmin(user.id, newStatus);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success(`${newStatus ? 'Đã mở khóa' : 'Đã khóa'} tài khoản`);
    taiDuLieu();
    if (selectedUser?.id === user.id) setSelectedUser({ ...selectedUser, is_active: newStatus });
  };

  const xuLyXoaNguoiDung = async (userId) => {
    if (!window.confirm('Bạn có chắc muốn xóa người dùng này?')) return;
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
        <StatMini icon={Users} label="Tổng người dùng" value={stats.total} color="text-purple-400 bg-purple-500/10" />
        <StatMini icon={Crown} label="Premium" value={stats.premium} color="text-amber-400 bg-amber-500/10" />
        <StatMini icon={Shield} label="Quản trị viên" value={stats.admin} color="text-fuchsia-400 bg-fuchsia-500/10" />
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
        
        <button
          onClick={() => {
            const headers = ['ID', 'Username', 'Email', 'Role', 'Plan', 'Tokens', 'Conversions', 'Created At'];
            const rows = danhSachDaLoc.map(u => [
              u.id,
              u.username,
              u.email,
              u.role,
              u.plan_type,
              u.token_balance,
              u.so_lan_chuyen_doi,
              u.created_at
            ]);
            const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', `danh_sach_nguoi_dung_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            toast.success('Đã xuất danh sách CSV');
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 transition-all"
        >
          <Download className="w-4 h-4" />
          Xuất CSV
        </button>

        <button
          onClick={() => {
            toast.promise(taiDuLieu(), {
              loading: 'Đang làm mới dữ liệu...',
              success: 'Đã cập nhật dữ liệu mới nhất',
              error: 'Lỗi khi làm mới dữ liệu'
            });
          }}
          className="p-2 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all"
          title="Làm mới toàn bộ"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
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
                      {u.photo_url ? (
                        <img 
                          src={u.photo_url} 
                          alt={u.username} 
                          referrerPolicy="no-referrer"
                          className="h-9 w-9 rounded-full object-cover border border-white/10 shadow-sm"
                          onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                        />
                      ) : null}
                      <div className={`flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-primary-500/20 to-violet-500/20 border border-primary-500/20 text-xs font-bold text-primary-300 shrink-0 ${u.photo_url ? 'hidden' : 'flex'}`}>
                        {avatarChars(u)}
                      </div>
                      <span className={`font-medium truncate max-w-[180px] ${u.is_active === false ? 'text-white/40 line-through' : ''}`}>{u.username}</span>
                      {u.is_active === false && (
                        <span className="flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-[9px] font-black uppercase tracking-widest text-red-400 border border-red-500/20">
                          <Lock className="w-2.5 h-2.5" /> Khóa
                        </span>
                      )}
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
                      <ActionBtn icon={Plus} title="Cộng token" color="text-purple-400 hover:bg-purple-500/10" onClick={() => moTokenModal(u, 'grant')} />
                      <ActionBtn icon={Minus} title="Trừ token" color="text-amber-400 hover:bg-amber-500/10" onClick={() => moTokenModal(u, 'deduct')} />
                      <ActionBtn
                        icon={Crown}
                        title={u.plan_type === 'premium' ? 'Hạ Premium' : 'Nâng Premium'}
                        color={u.plan_type === 'premium' ? 'text-amber-400 hover:bg-amber-500/10' : 'text-slate-400 hover:bg-white/5'}
                        onClick={() => u.plan_type === 'premium' ? xuLyPremiumModal(false, u) : moPremiumModal(u)}
                      />
                      <ActionBtn 
                        icon={u.is_active !== false ? Lock : Unlock} 
                        title={u.is_active !== false ? 'Khóa tài khoản' : 'Mở khóa tài khoản'} 
                        color={u.is_active !== false ? 'text-slate-400 hover:bg-red-500/10 hover:text-red-400' : 'text-red-400 hover:bg-emerald-500/10 hover:text-emerald-400'} 
                        onClick={() => xuLyDoiTrangThai(u)} 
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
                {selectedUser.photo_url ? (
                  <img 
                    src={selectedUser.photo_url} 
                    alt={selectedUser.username} 
                    referrerPolicy="no-referrer"
                    className="h-12 w-12 rounded-full object-cover border border-primary-500/20 shadow-lg"
                  />
                ) : (
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-primary-500/30 to-violet-500/30 border border-primary-500/20 text-sm font-bold text-primary-300">
                    {avatarChars(selectedUser)}
                  </div>
                )}
                <div>
                  <p className="font-bold text-white text-lg leading-tight">{selectedUser.username}</p>
                  <p className="text-xs text-slate-400 flex items-center gap-1 mt-1"><Mail className="w-3 h-3" />{selectedUser.email}</p>
                </div>
              </div>
              <button onClick={dongDrawer} className="p-2 rounded-lg text-slate-500 hover:bg-white/5 hover:text-white transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* User Info Cards */}
            <div className="px-6 py-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <InfoCard label="Vai trò" value={selectedUser.role || 'user'} icon={Shield} />
              <InfoCard 
                label="Gói" 
                value={selectedUser.plan_type === 'premium' ? (selectedUser.premium_expires_at ? `Premium (${fmtDate(selectedUser.premium_expires_at)})` : 'Premium') : 'Free'} 
                icon={Crown} 
                highlight={selectedUser.plan_type === 'premium'} 
              />
              <InfoCard label="Token" value={selectedUser.token_balance ?? 0} icon={Coins} />
              <InfoCard label="Sức chứa" value={`~${((selectedUser.token_balance || 0) * 1000).toLocaleString()} từ`} icon={Hash} />
            </div>

            {/* Quick Actions */}
            <div className="px-6 pb-4 flex flex-wrap gap-2">
              <QuickAction label="Cộng token" icon={Plus} color="bg-purple-500/10 text-purple-400 border-purple-500/20" onClick={() => moTokenModal(selectedUser, 'grant')} />
              <QuickAction label="Trừ token" icon={Minus} color="bg-red-500/10 text-red-400 border-red-500/20" onClick={() => moTokenModal(selectedUser, 'deduct')} />
              <QuickAction
                label={selectedUser.plan_type === 'premium' ? 'Hạ Premium' : 'Nâng Premium'}
                icon={Crown}
                color="bg-amber-500/10 text-amber-400 border-amber-500/20"
                onClick={() => selectedUser.plan_type === 'premium' ? xuLyPremiumModal(false, selectedUser) : moPremiumModal(selectedUser)}
              />
              <QuickAction 
                label={selectedUser.is_active !== false ? 'Khóa tài khoản' : 'Mở khóa'} 
                icon={selectedUser.is_active !== false ? Lock : Unlock} 
                color={selectedUser.is_active !== false ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-purple-500/10 text-purple-400 border-purple-500/20'} 
                onClick={() => xuLyDoiTrangThai(selectedUser)} 
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
                    <span className={`text-xs font-bold ${item.delta_token >= 0 ? 'text-purple-400' : 'text-red-400'}`}>
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

      {/* ── TOKEN MODAL ────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {tokenModal.open && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/80 backdrop-blur-sm"
              onClick={() => setTokenModal(p => ({ ...p, open: false }))}
            />
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative w-full max-w-sm bg-slate-900 border border-white/10 rounded-3xl shadow-2xl p-6 space-y-5"
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl ${tokenModal.mode === 'grant' ? 'bg-purple-500/10' : 'bg-red-500/10'}`}>
                    {tokenModal.mode === 'grant' ? <Plus className="w-5 h-5 text-purple-400" /> : <Minus className="w-5 h-5 text-red-400" />}
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-lg leading-tight">
                      {tokenModal.mode === 'grant' ? 'Cộng Token' : 'Trừ Token'}
                    </h3>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Quản lý số dư</p>
                  </div>
                </div>
                <button onClick={() => setTokenModal(p => ({ ...p, open: false }))} className="p-2 rounded-full text-slate-500 hover:bg-white/5 hover:text-white transition">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex items-center gap-3 p-4 rounded-2xl bg-white/[0.03] border border-white/5">
                <div className="h-10 w-10 rounded-full bg-primary-500/20 flex items-center justify-center text-primary-300 font-bold text-xs">
                  {avatarChars(tokenModal.user)}
                </div>
                <div>
                  <p className="text-xs text-slate-400">Người nhận</p>
                  <p className="text-sm font-bold text-white">{tokenModal.user?.username}</p>
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-2 block">Số lượng Token</label>
                <div className="relative">
                  <input 
                    type="number" 
                    min="1" 
                    value={tokenModal.amount} 
                    onChange={e => setTokenModal(p => ({ ...p, amount: e.target.value }))} 
                    placeholder="0" 
                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white text-2xl font-black focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 focus:outline-none transition-all placeholder:text-white/10" 
                  />
                  <div className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-500 font-bold text-sm">TK</div>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {[100, 500, 1000, 5000].map(v => (
                    <button key={v} onClick={() => setTokenModal(p => ({ ...p, amount: String(v) }))} className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white/60 hover:bg-white/10 hover:text-white transition-all">+{v}</button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-2 block">Lý do điều chỉnh</label>
                <input 
                  type="text" 
                  value={tokenModal.reason} 
                  onChange={e => setTokenModal(p => ({ ...p, reason: e.target.value }))} 
                  placeholder="VD: Khuyến mãi thành viên mới..." 
                  className="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-sm text-white focus:border-primary-500 focus:outline-none transition-all" 
                />
              </div>

              <button 
                onClick={xuLyTokenModal} 
                className={`w-full py-4 rounded-2xl font-black text-xs uppercase tracking-widest text-white shadow-xl transition-all active:scale-[0.98] ${
                  tokenModal.mode === 'grant' 
                    ? 'bg-gradient-to-r from-purple-600 to-purple-500 shadow-purple-500/20 hover:from-purple-500 hover:to-purple-400' 
                    : 'bg-gradient-to-r from-red-600 to-red-500 shadow-red-500/20 hover:from-red-500 hover:to-red-400'
                }`}
              >
                Xác nhận {tokenModal.mode === 'grant' ? 'cộng' : 'trừ'} ngay
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── PREMIUM MODAL ──────────────────────────────────────────────────── */}
      {premiumModal.open && (
        <>
          <div className="fixed inset-0 bg-black/60 z-[60]" onClick={() => setPremiumModal(p => ({ ...p, open: false }))} />
          <div className="fixed inset-0 z-[61] flex items-center justify-center p-4">
            <div className="w-full max-w-sm bg-slate-950 border border-white/10 rounded-2xl shadow-2xl p-6 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-white font-bold text-lg flex items-center gap-2">
                  <Crown className="w-5 h-5 text-amber-400" /> Nâng Premium
                </h3>
                <button onClick={() => setPremiumModal(p => ({ ...p, open: false }))} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
              </div>
              <p className="text-xs text-slate-400">Cho: <strong className="text-white">{premiumModal.user?.username}</strong></p>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Số ngày Premium</label>
                <input type="number" min="1" value={premiumModal.soNgay} onChange={e => setPremiumModal(p => ({ ...p, soNgay: e.target.value }))} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-lg font-bold focus:border-amber-500 focus:outline-none" />
                <div className="flex gap-2 mt-2">
                  {[7, 30, 90, 365].map(d => (
                    <button key={d} onClick={() => setPremiumModal(p => ({ ...p, soNgay: String(d) }))} className={`px-4 py-2 rounded-lg border text-xs font-semibold transition ${premiumModal.soNgay === String(d) ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10'}`}>{d} ngày</button>
                  ))}
                </div>
              </div>
              <button onClick={() => xuLyPremiumModal(true)} className="w-full py-3 rounded-xl bg-amber-600 hover:bg-amber-500 font-bold text-white transition">
                Kích hoạt Premium
              </button>
            </div>
          </div>
        </>
      )}
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
