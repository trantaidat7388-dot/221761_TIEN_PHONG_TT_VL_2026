import { useState } from 'react';
import { Files, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { taiLenTemplate, xoaTemplateAdmin, layDanhSachTemplateAdmin } from '../../../services/api';
import { fmtSize } from '../utils/formatters';

const TabTemplate = ({ danhSachTemplate, setDanhSachTemplate }) => {
  const [dangTaiTemplate, setDangTaiTemplate] = useState(false);

  const xuLyXoaTemplate = async (templateId) => {
    if (!window.confirm('Ban co chac muon xoa template nay?')) return;
    const kq = await xoaTemplateAdmin(templateId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Xóa thất bại'); return; }
    setDanhSachTemplate(prev => prev.filter(x => x.id !== templateId));
    toast.success('Da xoa template');
  };

  const xuLyTaiLenTemplate = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setDangTaiTemplate(true);
    try {
      const kq = await taiLenTemplate(file);
      if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Tải lên thất bại'); return; }
      toast.success(kq.message || 'Da tai len template');
      const dsTemplate = await layDanhSachTemplateAdmin();
      if (dsTemplate.thanhCong) setDanhSachTemplate(dsTemplate.danhSach);
    } catch (error) {
       toast.error(error.message || 'Lỗi hệ thống');
    } finally {
      setDangTaiTemplate(false);
      e.target.value = '';
    }
  };

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Files className="h-4 w-4 text-cyan-400" /> Quan ly template tuy chinh
        </h3>
        <label className={`cursor-pointer rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white hover:bg-white/10 transition ${dangTaiTemplate ? 'opacity-50 cursor-not-allowed' : ''}`}>
          <input type="file" accept=".tex,.zip" onChange={xuLyTaiLenTemplate} className="hidden" disabled={dangTaiTemplate} />
          {dangTaiTemplate ? 'Dang tai len...' : 'Tai len (.tex / .zip)'}
        </label>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm text-white/90">
          <thead>
            <tr className="border-b border-white/5 text-left text-xs text-slate-500">
              <th className="py-2 pr-2">Ten template</th>
              <th className="py-2 pr-2">Pham vi</th>
              <th className="py-2 pr-2">Chu so huu</th>
              <th className="py-2 pr-2">Loai</th>
              <th className="py-2 pr-2">Kich thuoc</th>
              <th className="py-2">Hanh dong</th>
            </tr>
          </thead>
          <tbody>
            {danhSachTemplate.map(tpl => (
              <tr key={tpl.id} className="border-b border-white/[0.03]">
                <td className="py-2 pr-2">{tpl.ten}</td>
                <td className="py-2 pr-2">{tpl.scope === 'private' ? 'ca nhan' : 'global'}</td>
                <td className="py-2 pr-2">{tpl.owner_label || '-'}</td>
                <td className="py-2 pr-2">{tpl.loai}</td>
                <td className="py-2 pr-2">{fmtSize(tpl.kich_thuoc)}</td>
                <td className="py-2">
                  <button onClick={() => xuLyXoaTemplate(tpl.id)} className="inline-flex items-center gap-1 text-red-400/60 hover:text-red-300">
                    <Trash2 className="h-3.5 w-3.5" /> Xoa
                  </button>
                </td>
              </tr>
            ))}
            {!danhSachTemplate.length && (
              <tr><td className="py-4 text-slate-600" colSpan={6}>Khong co template tuy chinh</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TabTemplate;
