import { useState } from 'react';
import { History, Trash2, Shield, FileText, Filter } from 'lucide-react';
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

  const xuLyXoaLichSu = async (recordId) => {
    const kq = await xoaBanGhiLichSuAdmin(recordId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Lỗi'); return; }
    setDanhSachLichSu(prev => prev.filter(x => x.id !== recordId));
    toast.success('Đã xóa bản ghi lịch sử');
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
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5 flex items-center gap-2">
            <History className="h-4 w-4 text-cyan-400" />
            <span className="font-semibold text-white text-sm">Lịch sử chuyển đổi toàn hệ thống</span>
            <span className="text-xs text-slate-500 ml-auto">{danhSachLichSu.length} bản ghi</span>
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
                {danhSachLichSu.map(item => (
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
                {!danhSachLichSu.length && (
                  <tr><td className="py-8 text-center text-slate-600" colSpan={8}>Chưa có dữ liệu</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Audit Log */}
      {subTab === 'audit' && (
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5 flex items-center gap-2">
            <Shield className="h-4 w-4 text-emerald-400" />
            <span className="font-semibold text-white text-sm">Nhật ký thao tác quản trị</span>
            <span className="text-xs text-slate-500 ml-auto">{(danhSachAuditLogs || []).length} bản ghi</span>
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
                {(danhSachAuditLogs || []).slice(0, 100).map(item => (
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
                {!(danhSachAuditLogs || []).length && (
                  <tr><td className="py-8 text-center text-slate-600" colSpan={6}>Chưa có nhật ký quản trị</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default TabLichSu;
