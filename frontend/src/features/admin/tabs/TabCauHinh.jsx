import { useState } from 'react';
import { Settings } from 'lucide-react';
import toast from 'react-hot-toast';
import { capNhatCauHinhHeThongAdmin } from '../../../services/api';

const TabCauHinh = ({ cauHinhHeThong, setCauHinhHeThong, cauHinhMeta, setCauHinhMeta }) => {
  const [dangLuuCauHinh, setDangLuuCauHinh] = useState(false);

  const capNhatGiaTriCauHinh = (key, value) => {
    const num = Number(value);
    setCauHinhHeThong(prev => ({
      ...prev,
      [key]: Number.isFinite(num) ? num : 0,
    }));
  };

  const xuLyLuuCauHinhHeThong = async () => {
    const payload = {
      token_min_cost_vnd: Math.max(1, Math.floor(Number(cauHinhHeThong.token_min_cost_vnd || 1))),
      free_plan_max_pages: Math.max(1, Math.floor(Number(cauHinhHeThong.free_plan_max_pages || 60))),
      max_doc_upload_mb: Math.max(1, Math.floor(Number(cauHinhHeThong.max_doc_upload_mb || 10))),
      rate_limit_admin_per_minute: Math.max(10, Math.floor(Number(cauHinhHeThong.rate_limit_admin_per_minute || 120))),
    };

    setDangLuuCauHinh(true);
    const kq = await capNhatCauHinhHeThongAdmin(payload);
    setDangLuuCauHinh(false);

    if (!kq.thanhCong) {
      toast.error(kq.loiMessage || 'Khong the luu cau hinh he thong');
      return;
    }

    setCauHinhHeThong({
      token_min_cost_vnd: Number(kq.data?.settings?.token_min_cost_vnd || payload.token_min_cost_vnd),
      free_plan_max_pages: Number(kq.data?.settings?.free_plan_max_pages || payload.free_plan_max_pages),
      max_doc_upload_mb: Number(kq.data?.settings?.max_doc_upload_mb || payload.max_doc_upload_mb),
      rate_limit_admin_per_minute: Number(kq.data?.settings?.rate_limit_admin_per_minute || payload.rate_limit_admin_per_minute),
    });
    if (setCauHinhMeta) setCauHinhMeta(kq.data?.meta || null);
    toast.success('Da luu cau hinh. Restart backend de ap dung cho luong xu ly chinh.');
  };

  return (
    <div className="max-w-4xl space-y-6">
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm">
        <h3 className="mb-1 text-lg font-semibold text-white flex items-center gap-2">
          <Settings className="h-5 w-5 text-cyan-400" /> Tham Số Hệ Thống cơ bản
        </h3>
        <p className="mb-6 text-sm text-slate-400">Du lieu dang doc/ghi truc tiep qua API backend /api/admin/system-config.</p>
        
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Giá Token tối thiểu (VNĐ)</label>
              <input type="number" value={cauHinhHeThong.token_min_cost_vnd} onChange={(e) => capNhatGiaTriCauHinh('token_min_cost_vnd', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
              <p className="text-xs text-slate-500">Tỉ giá gốc quy đổi ra VNĐ cho tính toán dịch vụ.</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Token đăng ký (Mặc định)</label>
              <input type="number" value={cauHinhHeThong.free_plan_max_pages} onChange={(e) => capNhatGiaTriCauHinh('free_plan_max_pages', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
              <p className="text-xs text-slate-500">Số lượng Token tương đương số trang được dùng miễn phí.</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Trang thai SePay API Key</label>
              <input type="text" value={cauHinhMeta?.sepay_api_key_configured ? 'Da cau hinh' : 'Chua cau hinh'} disabled className="w-full rounded-lg border border-white/5 bg-slate-900/50 px-4 py-2 text-slate-400 cursor-not-allowed" />
              <p className="text-xs text-slate-500">Thong tin khoa SePay duoc quan ly trong backend/.env.</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Giới hạn file Upload lớn nhất (MB)</label>
              <input type="number" value={cauHinhHeThong.max_doc_upload_mb} onChange={(e) => capNhatGiaTriCauHinh('max_doc_upload_mb', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
              <p className="text-xs text-slate-500">Ngăn người dùng lợi dụng tài nguyên máy chủ.</p>
            </div>
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-sm font-medium text-slate-300">Rate limit nhom Admin (request/phut)</label>
              <input type="number" value={cauHinhHeThong.rate_limit_admin_per_minute} onChange={(e) => capNhatGiaTriCauHinh('rate_limit_admin_per_minute', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
              <p className="text-xs text-slate-500">Khuyen nghi restart backend sau khi cap nhat de ap dung cho middleware rate-limit.</p>
            </div>
          </div>
          
          <div className="pt-4 border-t border-white/10 flex justify-end">
            <button disabled={dangLuuCauHinh} className="rounded-lg bg-cyan-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-500/20 disabled:opacity-60" onClick={xuLyLuuCauHinhHeThong}>
              {dangLuuCauHinh ? 'Dang luu...' : 'Cập nhật Toàn hệ thống'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TabCauHinh;
