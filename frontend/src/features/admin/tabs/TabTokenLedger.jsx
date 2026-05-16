import { useMemo, useState } from 'react';
import { Coins, Download, Filter, Search } from 'lucide-react';
import toast from 'react-hot-toast';
import { avatarChars, fmtDate } from '../utils/formatters';

const TabTokenLedger = ({ danhSachTokenLedger }) => {
  const [tuKhoa, setTuKhoa] = useState('');
  const [lyDo, setLyDo] = useState('all');
  const [tuNgay, setTuNgay] = useState('');
  const [denNgay, setDenNgay] = useState('');

  const ledgerDaLoc = useMemo(() => {
    const kw = (tuKhoa || '').trim().toLowerCase();
    const fromDate = tuNgay ? new Date(`${tuNgay}T00:00:00`) : null;
    const toDate = denNgay ? new Date(`${denNgay}T23:59:59`) : null;

    return (danhSachTokenLedger || []).filter(item => {
      const text = `${item.username || ''} ${item.email || ''} ${item.reason || ''} ${item.meta_json || ''} ${item.job_id || ''}`.toLowerCase();
      if (kw && !text.includes(kw)) return false;
      if (lyDo !== 'all' && item.reason !== lyDo) return false;
      const createdAt = item.createdAt ? new Date(item.createdAt) : (item.created_at ? new Date(item.created_at) : null);
      if (fromDate && createdAt && createdAt < fromDate) return false;
      if (toDate && createdAt && createdAt > toDate) return false;
      return true;
    });
  }, [danhSachTokenLedger, tuKhoa, lyDo, tuNgay, denNgay]);

  const thongKe = useMemo(() => {
    const total = ledgerDaLoc.length;
    const tongCong = ledgerDaLoc.filter(i => i.delta_token > 0).reduce((sum, i) => sum + i.delta_token, 0);
    const tongTru = ledgerDaLoc.filter(i => i.delta_token < 0).reduce((sum, i) => sum + Math.abs(i.delta_token), 0);
    const nguoiDung = new Set(ledgerDaLoc.map(i => i.user_id)).size;
    return { total, tongCong, tongTru, nguoiDung };
  }, [ledgerDaLoc]);

  const danhSachLyDo = useMemo(() => {
    return ['all', ...new Set((danhSachTokenLedger || []).map(item => item.reason).filter(Boolean))];
  }, [danhSachTokenLedger]);

  const xuatCsv = () => {
    const headers = ['ID', 'User', 'Email', 'Delta', 'Balance', 'Reason', 'Meta', 'Job ID', 'Created At'];
    const rows = ledgerDaLoc.map(item => [
      item.id,
      item.username || '',
      item.email || '',
      item.delta_token || 0,
      item.balance_after || 0,
      item.reason || '',
      item.meta_json || '',
      item.job_id || '',
      item.createdAt || item.created_at || '',
    ]);
    const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `token_ledger_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Đã xuất CSV nhật ký phát sinh token.');
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
        <StatMini label="Bản ghi" value={thongKe.total} color="text-violet-300 bg-violet-500/10" />
        <StatMini label="Tổng cộng" value={new Intl.NumberFormat('vi-VN').format(thongKe.tongCong)} color="text-emerald-300 bg-emerald-500/10" />
        <StatMini label="Tổng trừ" value={new Intl.NumberFormat('vi-VN').format(thongKe.tongTru)} color="text-red-300 bg-red-500/10" />
        <StatMini label="Người dùng" value={thongKe.nguoiDung} color="text-cyan-300 bg-cyan-500/10" />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[260px] flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 bg-white/[0.02] focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/15 transition-all">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={tuKhoa}
            onChange={e => setTuKhoa(e.target.value)}
            placeholder="Tìm theo người dùng, lý do, job..."
            className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
          />
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/5 px-3 py-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={lyDo}
            onChange={e => setLyDo(e.target.value)}
            className="bg-transparent text-xs text-white/70 outline-none [&>option]:bg-slate-900 [&>option]:text-white"
          >
            {danhSachLyDo.map(item => (
              <option key={item} value={item}>{item === 'all' ? 'Tất cả lý do' : item}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/5 px-3 py-2">
          <span className="text-[11px] text-slate-500">Từ</span>
          <input type="date" value={tuNgay} onChange={e => setTuNgay(e.target.value)} className="bg-transparent text-xs text-white/70 outline-none" />
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/5 px-3 py-2">
          <span className="text-[11px] text-slate-500">Đến</span>
          <input type="date" value={denNgay} onChange={e => setDenNgay(e.target.value)} className="bg-transparent text-xs text-white/70 outline-none" />
        </div>
        <button
          onClick={xuatCsv}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 transition-all"
        >
          <Download className="w-4 h-4" />
          Xuất CSV
        </button>
      </div>

      <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5 flex items-center gap-2">
          <Coins className="h-4 w-4 text-violet-400" />
          <span className="font-semibold text-white text-sm">Nhật ký phát sinh Token toàn hệ thống</span>
          <span className="text-xs text-slate-500 ml-auto">{ledgerDaLoc.length} bản ghi</span>
        </div>
        <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
          <table className="w-full text-sm text-white/90">
            <thead className="sticky top-0 bg-slate-950/95 backdrop-blur-sm">
              <tr className="border-b border-white/5 text-left text-[11px] uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4 font-medium">Người dùng</th>
                <th className="py-3 px-3 font-medium">Email</th>
                <th className="py-3 px-3 font-medium text-right">Delta</th>
                <th className="py-3 px-3 font-medium text-right">Số dư</th>
                <th className="py-3 px-3 font-medium">Lý do</th>
                <th className="py-3 px-3 font-medium">Meta</th>
                <th className="py-3 px-3 font-medium">Job ID</th>
                <th className="py-3 px-3 font-medium">Thời gian</th>
              </tr>
            </thead>
            <tbody>
              {ledgerDaLoc.map(item => (
                <tr key={item.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition">
                  <td className="py-2.5 px-4">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary-500/20 to-violet-500/20 border border-primary-500/20 text-[10px] font-bold text-primary-300">
                        {avatarChars(item)}
                      </div>
                      <span className="text-xs font-medium text-white">{item.username || item.user_id}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-xs text-slate-400 truncate max-w-[200px]" title={item.email}>{item.email || '-'}</td>
                  <td className={`py-2.5 px-3 text-right font-semibold ${item.delta_token >= 0 ? 'text-emerald-300' : 'text-red-300'}`}>
                    {item.delta_token >= 0 ? '+' : ''}{item.delta_token}
                  </td>
                  <td className="py-2.5 px-3 text-right text-amber-300 font-semibold">{item.balance_after}</td>
                  <td className="py-2.5 px-3 text-xs text-slate-400">{item.reason || '-'}</td>
                  <td className="py-2.5 px-3 text-xs text-slate-500 max-w-[220px] truncate" title={item.meta_json || ''}>{item.meta_json || '-'}</td>
                  <td className="py-2.5 px-3 text-xs text-slate-500 max-w-[160px] truncate" title={item.job_id || ''}>{item.job_id || '-'}</td>
                  <td className="py-2.5 px-3 text-xs text-slate-500">{fmtDate(item.createdAt)}</td>
                </tr>
              ))}
              {!ledgerDaLoc.length && (
                <tr><td className="py-8 text-center text-slate-600" colSpan={8}>Chưa có dữ liệu</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const StatMini = ({ label, value, color }) => (
  <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex items-center justify-between">
    <div>
      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">{label}</p>
      <p className="text-xl font-black text-white">{value}</p>
    </div>
    <div className={`h-9 w-9 rounded-xl ${color} flex items-center justify-center`}>
      <Coins className="w-4 h-4" />
    </div>
  </div>
);

export default TabTokenLedger;
