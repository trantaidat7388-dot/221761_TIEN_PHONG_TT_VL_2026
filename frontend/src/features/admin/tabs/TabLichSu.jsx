import { History, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { xoaBanGhiLichSuAdmin } from '../../../services/api';
import StatusBadge from '../components/StatusBadge';
import { fmtDate } from '../utils/formatters';

const TabLichSu = ({ danhSachLichSu, setDanhSachLichSu }) => {
  const xuLyXoaLichSu = async (recordId) => {
    const kq = await xoaBanGhiLichSuAdmin(recordId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Lỗi'); return; }
    setDanhSachLichSu(prev => prev.filter(x => x.id !== recordId));
    toast.success('Da xoa ban ghi lich su');
  };

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <h3 className="mb-4 font-semibold text-white flex items-center gap-2">
        <History className="h-4 w-4 text-cyan-400" /> Lich su chuyen doi toan he thong
      </h3>
      <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
        <table className="min-w-full text-sm text-white/90">
          <thead className="sticky top-0 bg-slate-950">
            <tr className="border-b border-white/5 text-left text-xs text-slate-500">
              <th className="py-2 pr-2">User</th>
              <th className="py-2 pr-2">File</th>
              <th className="py-2 pr-2">Template</th>
              <th className="py-2 pr-2">Trang thai</th>
              <th className="py-2 pr-2">Trang</th>
              <th className="py-2 pr-2">Token</th>
              <th className="py-2 pr-2">Thoi gian</th>
              <th className="py-2">Xoa</th>
            </tr>
          </thead>
          <tbody>
            {danhSachLichSu.map(item => (
              <tr key={item.id} className="border-b border-white/[0.03]">
                <td className="py-2 pr-2 text-xs">{item.username || '-'}</td>
                <td className="py-2 pr-2 max-w-[200px] truncate">{item.file_name || '-'}</td>
                <td className="py-2 pr-2 text-xs text-slate-500">{item.template_name || '-'}</td>
                <td className="py-2 pr-2"><StatusBadge status={item.status} /></td>
                <td className="py-2 pr-2">{item.pages_count || 0}</td>
                <td className="py-2 pr-2 text-amber-300">{item.token_cost || 0}</td>
                <td className="py-2 pr-2 text-xs text-slate-500">{fmtDate(item.createdAt)}</td>
                <td className="py-2">
                  <button onClick={() => xuLyXoaLichSu(item.id)} className="text-red-400/50 hover:text-red-300">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
            {!danhSachLichSu.length && (
              <tr><td className="py-4 text-slate-600" colSpan={8}>Chua co du lieu</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TabLichSu;
