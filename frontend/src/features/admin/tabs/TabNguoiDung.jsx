import { useState, useMemo } from 'react';
import { Search, Eye, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { avatarChars } from '../utils/formatters';
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

const TabNguoiDung = ({ danhSachNguoiDung, taiDuLieu, setDanhSachLichSu }) => {
  const [tuKhoaTimNguoiDung, setTuKhoaTimNguoiDung] = useState('');
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedUserSummary, setSelectedUserSummary] = useState(null);
  const [chiTietLichSuUser, setChiTietLichSuUser] = useState([]);
  const [chiTietLedgerUser, setChiTietLedgerUser] = useState([]);

  const danhSachNguoiDungDaLoc = useMemo(() => {
    const kw = (tuKhoaTimNguoiDung || '').trim().toLowerCase();
    if (!kw) return danhSachNguoiDung;
    return danhSachNguoiDung.filter(u =>
      (u.username || '').toLowerCase().includes(kw) || (u.email || '').toLowerCase().includes(kw)
    );
  }, [danhSachNguoiDung, tuKhoaTimNguoiDung]);

  const taiChiTietNguoiDung = async (userId) => {
    setSelectedUserId(userId);
    const user = danhSachNguoiDung.find(u => u.id === userId);
    setSelectedUserSummary(user || null);
    const [hRes, lRes] = await Promise.all([
      layLichSuTheoNguoiDungAdmin(userId, 30),
      layTokenLedgerTheoNguoiDungAdmin(userId, 50),
    ]);
    setChiTietLichSuUser(hRes.thanhCong ? hRes.danhSach : []);
    setChiTietLedgerUser(lRes.thanhCong ? lRes.danhSach : []);
  };

  const xuLyDoiVaiTro = async (userId, role) => {
    const kq = await capNhatVaiTroNguoiDungAdmin(userId, role);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Khong the cap nhat quyen'); return; }
    toast.success('Da cap nhat quyen nguoi dung');
    taiDuLieu();
  };

  const xuLyCapNhatPremium = async (userId, enabled) => {
    const soNgayRaw = enabled ? window.prompt('Nhap so ngay premium (mac dinh 30):', '30') : '0';
    if (enabled && soNgayRaw === null) return;
    const soNgay = Number(soNgayRaw || 30);
    const kq = await capNhatPremiumNguoiDungAdmin(userId, enabled, Number.isFinite(soNgay) ? soNgay : 30);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success('Da cap nhat premium');
    taiDuLieu();
  };

  const xuLyCongToken = async (userId) => {
    const raw = window.prompt('Nhap so token muon cong:', '500');
    if (raw === null) return;
    const amount = Number(raw);
    if (!Number.isFinite(amount) || amount <= 0) return;
    const kq = await congTokenNguoiDungAdmin(userId, Math.floor(amount), 'Admin grant from dashboard');
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success('Da cong token');
    taiDuLieu();
    if (selectedUserId === userId) taiChiTietNguoiDung(userId);
  };

  const xuLyTruToken = async (userId) => {
    const raw = window.prompt('Nhap so token muon tru:', '100');
    if (raw === null) return;
    const amount = Number(raw);
    if (!Number.isFinite(amount) || amount <= 0) return;
    const kq = await truTokenNguoiDungAdmin(userId, Math.floor(amount), 'Admin deduct from dashboard');
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success('Da tru token');
    taiDuLieu();
    if (selectedUserId === userId) taiChiTietNguoiDung(userId);
  };

  const xuLyXoaNguoiDung = async (userId) => {
    if (!window.confirm('Ban co chac muon xoa nguoi dung nay?')) return;
    const kq = await xoaNguoiDungAdmin(userId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    toast.success('Da xoa nguoi dung');
    taiDuLieu();
  };

  const xuLyXoaLichSu = async (recordId) => {
    const kq = await xoaBanGhiLichSuAdmin(recordId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage); return; }
    setChiTietLichSuUser(prev => prev.filter(x => x.id !== recordId));
    if (setDanhSachLichSu) setDanhSachLichSu(prev => prev.filter(x => x.id !== recordId));
    toast.success('Da xoa ban ghi lich su');
  };

  const xuLyHanhDong = async (user, action) => {
    if (!action || !user) return;
    if (action === 'detail') { await taiChiTietNguoiDung(user.id); return; }
    if (action === 'premium') { await xuLyCapNhatPremium(user.id, user.plan_type !== 'premium'); return; }
    if (action === 'grant') { await xuLyCongToken(user.id); return; }
    if (action === 'deduct') { await xuLyTruToken(user.id); return; }
    if (action === 'delete') { await xuLyXoaNguoiDung(user.id); }
  };

  return (
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
                      onChange={e => { const v = e.target.value; if (v) { xuLyHanhDong(u, v); e.target.value = ''; } }}
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
  );
};

export default TabNguoiDung;
