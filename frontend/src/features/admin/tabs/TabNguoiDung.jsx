import { useState, useMemo } from 'react';
import { Search, Trash2, Crown, Shield, Coins, Users, Filter, ChevronRight, X, Plus, Minus, Mail, Calendar, Hash, Activity, Download, RefreshCw, Lock, Unlock, Clipboard, ArrowUpDown } from 'lucide-react';
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
  thucHienBulkUserActionAdmin,
} from '../../../services/api';

const FILTERS = [
  { key: 'all', label: 'Tất cả', icon: Users },
  { key: 'premium', label: 'Premium', icon: Crown },
  { key: 'free', label: 'Miễn phí', icon: Users },
  { key: 'admin', label: 'Admin', icon: Shield },
];

const STATUS_FILTERS = [
  { key: 'all', label: 'Mọi trạng thái' },
  { key: 'active', label: 'Đang hoạt động' },
  { key: 'locked', label: 'Đã khóa' },
];

const SORT_OPTIONS = [
  { key: 'newest', label: 'Mới nhất' },
  { key: 'tokens_desc', label: 'Token cao nhất' },
  { key: 'tokens_asc', label: 'Token thấp nhất' },
  { key: 'name_asc', label: 'Tên A-Z' },
  { key: 'name_desc', label: 'Tên Z-A' },
];

const TabNguoiDung = ({ danhSachNguoiDung, taiDuLieu, setDanhSachLichSu, danhSachAuditLogs }) => {
  const [tuKhoaTimNguoiDung, setTuKhoaTimNguoiDung] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortKey, setSortKey] = useState('newest');
  const [selectedUser, setSelectedUser] = useState(null);
  const [chiTietLichSuUser, setChiTietLichSuUser] = useState([]);
  const [chiTietLedgerUser, setChiTietLedgerUser] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());

  // ── STATS ─────────────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    const total = danhSachNguoiDung.length;
    const premium = danhSachNguoiDung.filter(u => u.plan_type === 'premium').length;
    const admin = danhSachNguoiDung.filter(u => u.role === 'admin').length;
    const locked = danhSachNguoiDung.filter(u => u.is_active === false).length;
    const totalTokens = danhSachNguoiDung.reduce((sum, u) => sum + (u.token_balance || 0), 0);
    return { total, premium, free: total - premium, admin, locked, totalTokens };
  }, [danhSachNguoiDung]);

  // ── FILTERED LIST ─────────────────────────────────────────────────────────
  const danhSachDaLoc = useMemo(() => {
    let list = [...danhSachNguoiDung];
    const kw = (tuKhoaTimNguoiDung || '').trim().toLowerCase();
    if (kw) list = list.filter(u => (u.username || '').toLowerCase().includes(kw) || (u.email || '').toLowerCase().includes(kw));
    if (filterType === 'premium') list = list.filter(u => u.plan_type === 'premium');
    if (filterType === 'free') list = list.filter(u => u.plan_type !== 'premium');
    if (filterType === 'admin') list = list.filter(u => u.role === 'admin');
    if (statusFilter === 'active') list = list.filter(u => u.is_active !== false);
    if (statusFilter === 'locked') list = list.filter(u => u.is_active === false);

    switch (sortKey) {
      case 'tokens_desc':
        list.sort((a, b) => (b.token_balance || 0) - (a.token_balance || 0));
        break;
      case 'tokens_asc':
        list.sort((a, b) => (a.token_balance || 0) - (b.token_balance || 0));
        break;
      case 'name_asc':
        list.sort((a, b) => (a.username || '').localeCompare(b.username || ''));
        break;
      case 'name_desc':
        list.sort((a, b) => (b.username || '').localeCompare(a.username || ''));
        break;
      default:
        list.sort((a, b) => new Date(b.createdAt || b.created_at || 0) - new Date(a.createdAt || a.created_at || 0));
        break;
    }
    return list;
  }, [danhSachNguoiDung, tuKhoaTimNguoiDung, filterType, statusFilter, sortKey]);

  const auditTheoNguoiDung = useMemo(() => {
    if (!selectedUser?.id) return [];
    return (danhSachAuditLogs || [])
      .filter(log => Number(log.target_user_id) === Number(selectedUser.id))
      .slice(0, 50);
  }, [danhSachAuditLogs, selectedUser]);

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
  const [bulkTokenModal, setBulkTokenModal] = useState({ open: false, mode: 'grant', amount: '', reason: '' });
  const [bulkPremiumModal, setBulkPremiumModal] = useState({ open: false, soNgay: '30' });
  const [bulkRoleModal, setBulkRoleModal] = useState({ open: false, role: 'user' });

  const moTokenModal = (user, mode) => setTokenModal({ open: true, user, mode, amount: '', reason: '' });
  const moPremiumModal = (user) => setPremiumModal({ open: true, user, soNgay: '30' });
  const moBulkTokenModal = (mode) => setBulkTokenModal({ open: true, mode, amount: '', reason: '' });
  const moBulkPremiumModal = () => setBulkPremiumModal({ open: true, soNgay: '30' });
  const moBulkRoleModal = () => setBulkRoleModal({ open: true, role: 'user' });

  const toggleSelect = (userId) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(userId)) next.delete(userId);
      else next.add(userId);
      return next;
    });
  };

  const toggleSelectAll = () => {
    setSelectedIds(prev => {
      if (prev.size === danhSachDaLoc.length) return new Set();
      return new Set(danhSachDaLoc.map(u => u.id));
    });
  };

  const clearSelection = () => setSelectedIds(new Set());

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

  const thucHienBulk = async (payload, successLabel) => {
    const kq = await thucHienBulkUserActionAdmin(payload);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Không thể thực hiện thao tác'); return; }
    const { success_count, fail_count } = kq.data || { success_count: 0, fail_count: 0 };
    toast.success(`${successLabel} · Thành công ${success_count}, thất bại ${fail_count}`);
    if (fail_count > 0) toast.error(`Có ${fail_count} người dùng thất bại`);
    clearSelection();
    taiDuLieu();
  };

  const xuLyBulkKhoa = async (isUnlock) => {
    if (!selectedIds.size) return;
    if (!window.confirm(`${isUnlock ? 'Mở khóa' : 'Khóa'} ${selectedIds.size} tài khoản?`)) return;
    await thucHienBulk({ user_ids: Array.from(selectedIds), action: isUnlock ? 'unlock' : 'lock' }, isUnlock ? 'Đã mở khóa' : 'Đã khóa');
  };

  const xuLyBulkToken = async () => {
    const amount = Math.floor(Number(bulkTokenModal.amount));
    if (!Number.isFinite(amount) || amount <= 0) { toast.error('Số token phải > 0'); return; }
    await thucHienBulk({
      user_ids: Array.from(selectedIds),
      action: bulkTokenModal.mode === 'grant' ? 'grant_token' : 'deduct_token',
      amount,
      reason: bulkTokenModal.reason || '',
    }, bulkTokenModal.mode === 'grant' ? 'Đã cộng token' : 'Đã trừ token');
    setBulkTokenModal(p => ({ ...p, open: false }));
  };

  const xuLyBulkPremium = async (enabled) => {
    if (!selectedIds.size) return;
    if (!enabled && !window.confirm(`Hủy Premium cho ${selectedIds.size} tài khoản?`)) return;
    const soNgay = Number(bulkPremiumModal.soNgay || 30);
    if (enabled && (!Number.isFinite(soNgay) || soNgay < 1)) { toast.error('Số ngày >= 1'); return; }
    await thucHienBulk({
      user_ids: Array.from(selectedIds),
      action: 'set_premium',
      premium_enabled: enabled,
      premium_days: enabled ? soNgay : 0,
    }, enabled ? 'Đã gán Premium' : 'Đã hủy Premium');
    setBulkPremiumModal(p => ({ ...p, open: false }));
  };

  const xuLyBulkRole = async () => {
    if (!selectedIds.size) return;
    const role = bulkRoleModal.role;
    await thucHienBulk({ user_ids: Array.from(selectedIds), action: 'set_role', role }, `Đã đổi role sang ${role}`);
    setBulkRoleModal(p => ({ ...p, open: false }));
  };

  const saoChepEmail = async (email) => {
    if (!email) return;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(email);
      } else {
        const input = document.createElement('input');
        input.value = email;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
      }
      toast.success('Đã sao chép email');
    } catch {
      toast.error('Không thể sao chép email');
    }
  };

  return (
    <div className="space-y-6 relative">

      {/* ── STAT CARDS ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatMini icon={Users} label="Tổng người dùng" value={stats.total} color="text-purple-400 bg-purple-500/10" />
        <StatMini icon={Crown} label="Premium" value={stats.premium} color="text-amber-400 bg-amber-500/10" />
        <StatMini icon={Shield} label="Quản trị viên" value={stats.admin} color="text-fuchsia-400 bg-fuchsia-500/10" />
        <StatMini icon={Lock} label="Tài khoản khóa" value={stats.locked} color="text-red-400 bg-red-500/10" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex items-center justify-between">
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Tổng token đang giữ</p>
            <p className="text-2xl font-black text-white">{new Intl.NumberFormat('vi-VN').format(stats.totalTokens)}</p>
          </div>
          <div className="h-10 w-10 rounded-xl bg-violet-500/10 text-violet-300 flex items-center justify-center">
            <Coins className="w-5 h-5" />
          </div>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex items-center justify-between">
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Tỷ lệ Premium</p>
            <p className="text-2xl font-black text-white">{stats.total ? Math.round((stats.premium / stats.total) * 100) : 0}%</p>
          </div>
          <div className="h-10 w-10 rounded-xl bg-amber-500/10 text-amber-300 flex items-center justify-center">
            <Crown className="w-5 h-5" />
          </div>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex items-center justify-between">
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Đang hoạt động</p>
            <p className="text-2xl font-black text-white">{stats.total - stats.locked}</p>
          </div>
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-300 flex items-center justify-center">
            <Unlock className="w-5 h-5" />
          </div>
        </div>
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
        <div className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/5 px-3 py-1.5">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="bg-transparent text-xs text-white/70 outline-none [&>option]:bg-slate-900 [&>option]:text-white"
          >
            {STATUS_FILTERS.map(f => (
              <option key={f.key} value={f.key}>{f.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/5 px-3 py-1.5">
          <ArrowUpDown className="w-4 h-4 text-slate-500" />
          <select
            value={sortKey}
            onChange={e => setSortKey(e.target.value)}
            className="bg-transparent text-xs text-white/70 outline-none [&>option]:bg-slate-900 [&>option]:text-white"
          >
            {SORT_OPTIONS.map(opt => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
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

      {selectedIds.size > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
          <span className="text-xs text-slate-400">Đã chọn <strong className="text-white">{selectedIds.size}</strong> người dùng</span>
          <button onClick={clearSelection} className="text-xs text-slate-400 hover:text-white">Bỏ chọn</button>
          <div className="h-4 w-px bg-white/10" />
          <button onClick={() => xuLyBulkKhoa(false)} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-500/10 text-red-300 border border-red-500/20 hover:bg-red-500/20">Khóa</button>
          <button onClick={() => xuLyBulkKhoa(true)} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 hover:bg-emerald-500/20">Mở khóa</button>
          <button onClick={() => moBulkTokenModal('grant')} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20 hover:bg-purple-500/20">Cộng token</button>
          <button onClick={() => moBulkTokenModal('deduct')} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20 hover:bg-amber-500/20">Trừ token</button>
          <button onClick={moBulkPremiumModal} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20 hover:bg-amber-500/20">Gán Premium</button>
          <button onClick={() => xuLyBulkPremium(false)} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-500/10 text-slate-300 border border-white/10 hover:bg-white/10">Hủy Premium</button>
          <button onClick={moBulkRoleModal} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-fuchsia-500/10 text-fuchsia-300 border border-fuchsia-500/20 hover:bg-fuchsia-500/20">Đổi role</button>
        </div>
      )}

      {/* ── USERS TABLE (Full-width) ───────────────────────────────────────── */}
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
        <div className="overflow-x-auto max-h-[65vh] overflow-y-auto">
          <table className="w-full text-sm text-white/90">
            <thead className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur-sm">
              <tr className="border-b border-white/5 text-left text-[11px] uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4 font-medium">
                  <input
                    type="checkbox"
                    checked={danhSachDaLoc.length > 0 && selectedIds.size === danhSachDaLoc.length}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 rounded border-white/10 bg-slate-900"
                  />
                </th>
                <th className="py-3 px-4 font-medium">Người dùng</th>
                <th className="py-3 px-3 font-medium">Email</th>
                <th className="py-3 px-3 font-medium text-center">Vai trò</th>
                <th className="py-3 px-3 font-medium text-center">Gói</th>
                <th className="py-3 px-3 font-medium text-right">Token</th>
                <th className="py-3 px-3 font-medium text-right">Lượt dùng</th>
                <th className="py-3 px-3 font-medium">Tạo lúc</th>
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
                  <td className="py-3 px-4" onClick={e => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(u.id)}
                      onChange={() => toggleSelect(u.id)}
                      className="h-4 w-4 rounded border-white/10 bg-slate-900"
                    />
                  </td>
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
                      className="rounded-lg border border-white/10 bg-slate-900 px-2 py-1 text-xs font-medium text-white/80 cursor-pointer hover:border-white/20 transition [&>option]:bg-slate-900 [&>option]:text-white"
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
                  <td className="py-3 px-3 text-xs text-slate-500">{fmtDate(u.createdAt || u.created_at)}</td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1" onClick={e => e.stopPropagation()}>
                      <ActionBtn icon={Clipboard} title="Sao chép email" color="text-cyan-400/70 hover:bg-cyan-500/10 hover:text-cyan-300" onClick={() => saoChepEmail(u.email)} />
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
                <tr><td className="py-12 text-center text-slate-600" colSpan={9}>Không tìm thấy người dùng</td></tr>
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
              <InfoCard label="Trạng thái" value={selectedUser.is_active !== false ? 'Hoạt động' : 'Đã khóa'} icon={selectedUser.is_active !== false ? Unlock : Lock} tone={selectedUser.is_active !== false ? 'emerald' : 'red'} />
              <InfoCard label="Tham gia" value={fmtDate(selectedUser.createdAt || selectedUser.created_at)} icon={Calendar} />
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
                    <p className="text-[11px] text-slate-600">{fmtDate(item.createdAt)}</p>
                  </div>
                  <button onClick={() => xuLyXoaLichSu(item.id)} className="text-red-400/40 hover:text-red-300 shrink-0 mt-1"><Trash2 className="h-3.5 w-3.5" /></button>
                </div>
              )} />

              <DetailSection title="Nhật ký phát sinh Token" icon={Coins} items={chiTietLedgerUser} renderItem={(item) => (
                <div key={item.id} className="rounded-xl bg-white/[0.03] p-3 border border-white/[0.03]">
                  <p className="text-sm text-white font-medium">{item.reason}</p>
                  {item.meta_json && <p className="text-[11px] text-slate-500 mt-0.5">{item.meta_json}</p>}
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`text-xs font-bold ${item.delta_token >= 0 ? 'text-purple-400' : 'text-red-400'}`}>
                      {item.delta_token >= 0 ? '+' : ''}{item.delta_token}
                    </span>
                    <span className="text-[11px] text-slate-500">→ Số dư: {item.balance_after}</span>
                    <span className="text-[11px] text-slate-600 ml-auto">{fmtDate(item.createdAt)}</span>
                  </div>
                </div>
              )} />

              <DetailSection title="Nhật ký admin liên quan" icon={Shield} items={auditTheoNguoiDung} renderItem={(item) => (
                <div key={item.id} className="rounded-xl bg-white/[0.03] p-3 border border-white/[0.03]">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-mono text-slate-400">{item.action}</span>
                    <span className="text-[11px] text-slate-600">{fmtDate(item.createdAt)}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">Actor: {item.actor_user_id} · Request: {item.request_id || '-'}</p>
                  {item.detail && <p className="text-[11px] text-slate-500 mt-1">{item.detail}</p>}
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
                {tokenModal.user?.photo_url ? (
                  <img
                    src={tokenModal.user.photo_url}
                    alt={tokenModal.user?.username || 'Avatar'}
                    referrerPolicy="no-referrer"
                    className="h-10 w-10 rounded-full object-cover border border-white/10 shadow-sm"
                    onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                  />
                ) : null}
                <div className={`h-10 w-10 rounded-full bg-primary-500/20 flex items-center justify-center text-primary-300 font-bold text-xs ${tokenModal.user?.photo_url ? 'hidden' : 'flex'}`}>
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
                  <div className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-500 font-bold text-sm">Token</div>
                </div>
                {tokenModal.user && tokenModal.amount && Number(tokenModal.amount) > 0 && (
                  <p className="text-[11px] text-slate-500 mt-2">
                    Số dư sau: <span className="text-white">{Number(tokenModal.user?.token_balance || 0) + (tokenModal.mode === 'grant' ? 1 : -1) * Number(tokenModal.amount || 0)}</span>
                  </p>
                )}
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

      {/* ── BULK TOKEN MODAL ───────────────────────────────────────────── */}
      <AnimatePresence>
        {bulkTokenModal.open && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/80 backdrop-blur-sm"
              onClick={() => setBulkTokenModal(p => ({ ...p, open: false }))}
            />
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative w-full max-w-sm bg-slate-900 border border-white/10 rounded-3xl shadow-2xl p-6 space-y-5"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-white font-bold text-lg leading-tight">
                    {bulkTokenModal.mode === 'grant' ? 'Cộng Token hàng loạt' : 'Trừ Token hàng loạt'}
                  </h3>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">{selectedIds.size} người dùng</p>
                </div>
                <button onClick={() => setBulkTokenModal(p => ({ ...p, open: false }))} className="p-2 rounded-full text-slate-500 hover:bg-white/5 hover:text-white transition">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div>
                <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-2 block">Số lượng Token</label>
                <div className="relative">
                  <input
                    type="number"
                    min="1"
                    value={bulkTokenModal.amount}
                    onChange={e => setBulkTokenModal(p => ({ ...p, amount: e.target.value }))}
                    placeholder="0"
                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white text-2xl font-black focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 focus:outline-none transition-all placeholder:text-white/10"
                  />
                  <div className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-500 font-bold text-sm">TK</div>
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-2 block">Lý do điều chỉnh</label>
                <input
                  type="text"
                  value={bulkTokenModal.reason}
                  onChange={e => setBulkTokenModal(p => ({ ...p, reason: e.target.value }))}
                  placeholder="VD: Ưu đãi chiến dịch..."
                  className="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-sm text-white focus:border-primary-500 focus:outline-none transition-all"
                />
              </div>

              <button
                onClick={xuLyBulkToken}
                className={`w-full py-4 rounded-2xl font-black text-xs uppercase tracking-widest text-white shadow-xl transition-all active:scale-[0.98] ${
                  bulkTokenModal.mode === 'grant'
                    ? 'bg-gradient-to-r from-purple-600 to-purple-500 shadow-purple-500/20 hover:from-purple-500 hover:to-purple-400'
                    : 'bg-gradient-to-r from-red-600 to-red-500 shadow-red-500/20 hover:from-red-500 hover:to-red-400'
                }`}
              >
                Xác nhận
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── BULK PREMIUM MODAL ─────────────────────────────────────────── */}
      {bulkPremiumModal.open && (
        <>
          <div className="fixed inset-0 bg-black/60 z-[60]" onClick={() => setBulkPremiumModal(p => ({ ...p, open: false }))} />
          <div className="fixed inset-0 z-[61] flex items-center justify-center p-4">
            <div className="w-full max-w-sm bg-slate-950 border border-white/10 rounded-2xl shadow-2xl p-6 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-white font-bold text-lg flex items-center gap-2">
                  <Crown className="w-5 h-5 text-amber-400" /> Gán Premium hàng loạt
                </h3>
                <button onClick={() => setBulkPremiumModal(p => ({ ...p, open: false }))} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
              </div>
              <p className="text-xs text-slate-400">Áp dụng cho <strong className="text-white">{selectedIds.size}</strong> người dùng</p>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Số ngày Premium</label>
                <input type="number" min="1" value={bulkPremiumModal.soNgay} onChange={e => setBulkPremiumModal(p => ({ ...p, soNgay: e.target.value }))} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-lg font-bold focus:border-amber-500 focus:outline-none" />
                <div className="flex gap-2 mt-2">
                  {[7, 30, 90, 365].map(d => (
                    <button key={d} onClick={() => setBulkPremiumModal(p => ({ ...p, soNgay: String(d) }))} className={`px-4 py-2 rounded-lg border text-xs font-semibold transition ${bulkPremiumModal.soNgay === String(d) ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10'}`}>{d} ngày</button>
                  ))}
                </div>
              </div>
              <button onClick={() => xuLyBulkPremium(true)} className="w-full py-3 rounded-xl bg-amber-600 hover:bg-amber-500 font-bold text-white transition">
                Kích hoạt Premium
              </button>
            </div>
          </div>
        </>
      )}

      {/* ── BULK ROLE MODAL ────────────────────────────────────────────── */}
      {bulkRoleModal.open && (
        <>
          <div className="fixed inset-0 bg-black/60 z-[60]" onClick={() => setBulkRoleModal(p => ({ ...p, open: false }))} />
          <div className="fixed inset-0 z-[61] flex items-center justify-center p-4">
            <div className="w-full max-w-sm bg-slate-950 border border-white/10 rounded-2xl shadow-2xl p-6 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-white font-bold text-lg flex items-center gap-2">
                  <Shield className="w-5 h-5 text-fuchsia-400" /> Đổi role hàng loạt
                </h3>
                <button onClick={() => setBulkRoleModal(p => ({ ...p, open: false }))} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
              </div>
              <p className="text-xs text-slate-400">Áp dụng cho <strong className="text-white">{selectedIds.size}</strong> người dùng</p>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Role</label>
                <select value={bulkRoleModal.role} onChange={e => setBulkRoleModal(p => ({ ...p, role: e.target.value }))} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-semibold focus:border-fuchsia-500 focus:outline-none [&>option]:bg-slate-900 [&>option]:text-white">
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <button onClick={xuLyBulkRole} className="w-full py-3 rounded-xl bg-fuchsia-600 hover:bg-fuchsia-500 font-bold text-white transition">
                Cập nhật role
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

const InfoCard = ({ label, value, icon: Icon, highlight = false, tone = '' }) => {
  const toneMap = {
    emerald: {
      wrap: 'border-emerald-500/20 bg-emerald-500/5',
      icon: 'text-emerald-400',
      text: 'text-emerald-300',
    },
    red: {
      wrap: 'border-red-500/20 bg-red-500/5',
      icon: 'text-red-400',
      text: 'text-red-300',
    },
  };
  const toneStyle = toneMap[tone] || null;
  const wrapClass = toneStyle ? toneStyle.wrap : (highlight ? 'border-amber-500/20 bg-amber-500/5' : 'border-white/5 bg-white/[0.02]');
  const iconClass = toneStyle ? toneStyle.icon : (highlight ? 'text-amber-400' : 'text-slate-500');
  const textClass = toneStyle ? toneStyle.text : (highlight ? 'text-amber-300' : 'text-white');

  return (
    <div className={`rounded-xl border p-3 text-center ${wrapClass}`}>
      <Icon className={`w-4 h-4 mx-auto mb-1.5 ${iconClass}`} />
      <p className="text-[10px] text-slate-500 uppercase mb-0.5">{label}</p>
      <p className={`text-sm font-bold ${textClass}`}>{value}</p>
    </div>
  );
};

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
