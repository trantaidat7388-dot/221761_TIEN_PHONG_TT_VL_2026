import { Shield } from 'lucide-react';
import { fmtDate } from '../utils/formatters';

const TabAuditLog = ({ danhSachAuditLogs }) => {
  return (
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
  );
};

export default TabAuditLog;
