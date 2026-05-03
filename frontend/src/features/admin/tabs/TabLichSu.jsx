import { useMemo, useState } from 'react';
import { History, Trash2, Shield, FileText, Filter, Download, Search, ArrowUpDown } from 'lucide-react';
import toast from 'react-hot-toast';
import { xoaBanGhiLichSuAdmin } from '../../../services/api';
import StatusBadge from '../components/StatusBadge';
import { fmtDate } from '../utils/formatters';

const SUB_TABS = [
  { key: 'chuyen-doi', label: 'Lịch sử Chuyển đổi', icon: FileText },
  { key: 'audit', label: 'Nhật ký Quản trị', icon: Shield },
];

const TabLichSu = ({ danhSachLichSu, setDanhSachLichSu, danhSachAuditLogs }) => {
  const [subTab, setSubTab] = useState('chuyen-doi');
  const [tuKhoaLichSu, setTuKhoaLichSu] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [tuNgay, setTuNgay] = useState('');
  const [denNgay, setDenNgay] = useState('');
  const [auditKeyword, setAuditKeyword] = useState('');
  const [auditAction, setAuditAction] = useState('all');

  const xuLyXoaLichSu = async (recordId) => {
    const kq = await xoaBanGhiLichSuAdmin(recordId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Lỗi'); return; }
    setDanhSachLichSu(prev => prev.filter(x => x.id !== recordId));
    toast.success('Đã xóa bản ghi lịch sử');
  };

  const danhSachDaLoc = useMemo(() => {
    const kw = (tuKhoaLichSu || '').trim().toLowerCase();
    const fromDate = tuNgay ? new Date(`${tuNgay}T00:00:00`) : null;
    const toDate = denNgay ? new Date(`${denNgay}T23:59:59`) : null;

    return (danhSachLichSu || []).filter(item => {
      const text = `${item.username || ''} ${item.email || ''} ${item.file_name || ''} ${item.template_name || ''}`.toLowerCase();
      if (kw && !text.includes(kw)) return false;
      if (statusFilter !== 'all' && (item.status || '').toLowerCase() !== statusFilter) return false;
      const createdAt = item.createdAt ? new Date(item.createdAt) : (item.created_at ? new Date(item.created_at) : null);
      if (fromDate && createdAt && createdAt < fromDate) return false;
      if (toDate && createdAt && createdAt > toDate) return false;
      return true;
    });
  }, [danhSachLichSu, tuKhoaLichSu, statusFilter, tuNgay, denNgay]);

  const auditDaLoc = useMemo(() => {
    const kw = (auditKeyword || '').trim().toLowerCase();
    return (danhSachAuditLogs || []).filter(item => {
      const text = `${item.actor_user_id || ''} ${item.action || ''} ${item.target_user_id || ''} ${item.detail || ''} ${item.request_id || ''} ${item.ip_address || ''}`.toLowerCase();
      if (kw && !text.includes(kw)) return false;
      if (auditAction !== 'all' && item.action !== auditAction) return false;
      return true;
    });
  }, [danhSachAuditLogs, auditKeyword, auditAction]);

  const lichSuStats = useMemo(() => {
    const total = danhSachDaLoc.length;
    const success = danhSachDaLoc.filter(item => /success|done|completed/i.test(item.status || '')).length;
    const totalToken = danhSachDaLoc.reduce((sum, item) => sum + (item.token_cost || 0), 0);
    const refunded = danhSachDaLoc.filter(item => item.token_refunded).reduce((sum, item) => sum + (item.token_cost || 0), 0);
    return { total, success, totalToken, refunded };
  }, [danhSachDaLoc]);

  const xuatCsvLichSu = () => {
    const headers = ['ID', 'User', 'Email', 'File', 'Template', 'Status', 'Pages', 'Token', 'Refunded', 'Created At'];
    const rows = danhSachDaLoc.map(item => [
      item.id,
      item.username || '',
      item.email || '',
      item.file_name || '',
      item.template_name || '',
      item.status || '',
      item.pages_count || 0,
      item.token_cost || 0,
      item.token_refunded ? 'yes' : 'no',
      item.createdAt || item.created_at || '',
    ]);
    const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `lich_su_chuyen_doi_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Đã xuất CSV lịch sử');
  };

  const xuatCsvAudit = () => {
    const headers = ['ID', 'Time', 'Actor', 'Action', 'Target User', 'Detail', 'Request ID', 'IP'];
    const rows = auditDaLoc.map(item => [
      item.id,
      item.createdAt || item.created_at || '',
      item.actor_user_id || '',
      item.action || '',
      item.target_user_id ?? '',
      item.detail || '',
      item.request_id || '',
      item.ip_address || '',
    ]);
    const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `audit_logs_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Đã xuất CSV audit');
  };

  return (
    <div className="space-y-4">
      {/* Sub-tab navigation */}
      <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-white/5 w-fit">
        {SUB_TABS.map(st => (
          <button
            key={st.key}
            onClick={() => setSubTab(st.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
              subTab === st.key
                ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/20'
                : 'text-white/50 hover:text-white hover:bg-white/5'
            }`}
          >
            <st.icon className="w-4 h-4" />
            {st.label}
          </button>
        ))}
      </div>

      {/* Conversion History */}
      {subTab === 'chuyen-doi' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
            <StatMini label="Bản ghi" value={lichSuStats.total} color="text-cyan-300 bg-cyan-500/10" />
            <StatMini label="Tỉ lệ thành công" value={`${lichSuStats.total ? Math.round((lichSuStats.success / lichSuStats.total) * 100) : 0}%`} color="text-emerald-300 bg-emerald-500/10" />
            <StatMini label="Tổng token" value={new Intl.NumberFormat('vi-VN').format(lichSuStats.totalToken)} color="text-amber-300 bg-amber-500/10" />
            <StatMini label="Hoàn token" value={lichSuStats.refunded} color="text-purple-300 bg-purple-500/10" />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[260px] flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 bg-white/[0.02] focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/15 transition-all">
              <Search className="w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={tuKhoaLichSu}
                onChange={e => setTuKhoaLichSu(e.target.value)}
                placeholder="Tìm theo user, file, template..."
                className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
              />
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/5 px-3 py-2">
              <Filter className="w-4 h-4 text-slate-500" />
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="bg-transparent text-xs text-white/70 outline-none [&>option]:bg-slate-900 [&>option]:text-white"
              >
                <option value="all">Tất cả trạng thái</option>
                <option value="success">success</option>
                <option value="done">done</option>
                <option value="failed">failed</option>
                <option value="error">error</option>
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
              onClick={xuatCsvLichSu}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 transition-all"
            >
              <Download className="w-4 h-4" />
              Xuất CSV
            </button>
          </div>

          <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5 flex items-center gap-2">
            <History className="h-4 w-4 text-cyan-400" />
            <span className="font-semibold text-white text-sm">Lịch sử chuyển đổi toàn hệ thống</span>
            <span className="text-xs text-slate-500 ml-auto">{danhSachDaLoc.length} bản ghi</span>
          </div>
          <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
            <table className="w-full text-sm text-white/90">
              <thead className="sticky top-0 bg-slate-950/95 backdrop-blur-sm">
                <tr className="border-b border-white/5 text-left text-[11px] uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-4 font-medium">User</th>
                  <th className="py-3 px-3 font-medium">File</th>
                  <th className="py-3 px-3 font-medium">Template</th>
                  <th className="py-3 px-3 font-medium text-center">Trạng thái</th>
                  <th className="py-3 px-3 font-medium text-right">Trang</th>
                  <th className="py-3 px-3 font-medium text-right">Token</th>
                  <th className="py-3 px-3 font-medium">Thời gian</th>
                  <th className="py-3 px-3 font-medium text-center">Xóa</th>
                </tr>
              </thead>
              <tbody>
                {danhSachDaLoc.map(item => (
                  <tr key={item.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition">
                    <td className="py-2.5 px-4 text-xs font-medium">{item.username || '-'}</td>
                    <td className="py-2.5 px-3 max-w-[220px] truncate" title={item.file_name}>{item.file_name || '-'}</td>
                    <td className="py-2.5 px-3 text-xs text-slate-500">{item.template_name || '-'}</td>
                    <td className="py-2.5 px-3 text-center"><StatusBadge status={item.status} /></td>
                    <td className="py-2.5 px-3 text-right">{item.pages_count || 0}</td>
                    <td className="py-2.5 px-3 text-right text-amber-300 font-semibold">{item.token_cost || 0}</td>
                    <td className="py-2.5 px-3 text-xs text-slate-500">{fmtDate(item.createdAt)}</td>
                    <td className="py-2.5 px-3 text-center">
                      <button onClick={() => xuLyXoaLichSu(item.id)} className="text-red-400/40 hover:text-red-300 transition">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {!danhSachDaLoc.length && (
                  <tr><td className="py-8 text-center text-slate-600" colSpan={8}>Chưa có dữ liệu</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        </div>
      )}

      {/* Audit Log */}
      {subTab === 'audit' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[260px] flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 bg-white/[0.02] focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/15 transition-all">
              <Search className="w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={auditKeyword}
                onChange={e => setAuditKeyword(e.target.value)}
                placeholder="Tìm theo actor, action, detail..."
                className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
              />
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-white/5 border border-white/5 px-3 py-2">
              <ArrowUpDown className="w-4 h-4 text-slate-500" />
              <select
                value={auditAction}
                onChange={e => setAuditAction(e.target.value)}
                className="bg-transparent text-xs text-white/70 outline-none [&>option]:bg-slate-900 [&>option]:text-white"
              >
                <option value="all">Tất cả action</option>
                {[...new Set((danhSachAuditLogs || []).map(item => item.action).filter(Boolean))].slice(0, 20).map(action => (
                  <option key={action} value={action}>{action}</option>
                ))}
              </select>
            </div>
            <button
              onClick={xuatCsvAudit}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 transition-all"
            >
              <Download className="w-4 h-4" />
              Xuất CSV
            </button>
          </div>

          <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5 flex items-center gap-2">
            <Shield className="h-4 w-4 text-emerald-400" />
            <span className="font-semibold text-white text-sm">Nhật ký thao tác quản trị</span>
            <span className="text-xs text-slate-500 ml-auto">{auditDaLoc.length} bản ghi</span>
          </div>
          <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
            <table className="w-full text-sm text-white/90">
              <thead className="sticky top-0 bg-slate-950/95 backdrop-blur-sm">
                <tr className="border-b border-white/5 text-left text-[11px] uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-4 font-medium">Thời gian</th>
                  <th className="py-3 px-3 font-medium">Actor</th>
                  <th className="py-3 px-3 font-medium">Action</th>
                  <th className="py-3 px-3 font-medium">Target user</th>
                  <th className="py-3 px-3 font-medium">Detail</th>
                  <th className="py-3 px-3 font-medium">Request ID</th>
                </tr>
              </thead>
              <tbody>
                {auditDaLoc.slice(0, 200).map(item => (
                  <tr key={item.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition">
                    <td className="py-2.5 px-4 text-xs text-slate-500">{fmtDate(item.createdAt)}</td>
                    <td className="py-2.5 px-3 font-medium">{item.actor_user_id}</td>
                    <td className="py-2.5 px-3">
                      <span className="rounded-lg bg-white/5 px-2 py-1 text-xs font-mono tracking-tight">{item.action}</span>
                    </td>
                    <td className="py-2.5 px-3">{item.target_user_id ?? '-'}</td>
                    <td className="py-2.5 px-3 max-w-[300px] truncate text-xs text-slate-400" title={item.detail || ''}>{item.detail || '-'}</td>
                    <td className="py-2.5 px-3 text-xs font-mono text-slate-600">{item.request_id || '-'}</td>
                  </tr>
                ))}
                {!auditDaLoc.length && (
                  <tr><td className="py-8 text-center text-slate-600" colSpan={6}>Chưa có nhật ký quản trị</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        </div>
      )}
    </div>
  );
};

export default TabLichSu;

const StatMini = ({ label, value, color }) => (
  <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex items-center justify-between">
    <div>
      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">{label}</p>
      <p className="text-xl font-black text-white">{value}</p>
    </div>
    <div className={`h-9 w-9 rounded-xl ${color} flex items-center justify-center`}>
      <History className="w-4 h-4" />
    </div>
  </div>
);
