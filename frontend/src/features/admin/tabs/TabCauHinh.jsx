import { useState } from 'react';
import { Settings, Crown, Coins } from 'lucide-react';
import toast from 'react-hot-toast';
import { capNhatCauHinhHeThongAdmin } from '../../../services/api';

// Danh sách gói premium — đồng bộ với backend/app/config.py PREMIUM_PACKAGES
const PREMIUM_PACKAGES_DISPLAY = [
  { key: 'week_20k', label: 'Gói Tuần', gia: '20.000₫', so_ngay: 7, token: 500, mo_ta: 'Phù hợp dùng thử' },
  { key: 'month_50k', label: 'Gói Tháng Bạc', gia: '50.000₫', so_ngay: 30, token: 1500, mo_ta: 'Phổ biến nhất' },
  { key: 'month_100k', label: 'Gói Tháng Vàng', gia: '100.000₫', so_ngay: 30, token: 3500, mo_ta: 'Hiệu quả cao' },
  { key: 'year_500k', label: 'Gói Năm', gia: '500.000₫', so_ngay: 365, token: 20000, mo_ta: 'Tiết kiệm nhất' },
];

const TOPUP_TIERS_DISPLAY = [
  { nguong: '20.000₫', thuong: '+10%', mo_ta: 'Thưởng nhỏ' },
  { nguong: '50.000₫', thuong: '+20%', mo_ta: 'Thưởng vừa' },
  { nguong: '100.000₫', thuong: '+30%', mo_ta: 'Thưởng lớn' },
];

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
      toast.error(kq.loiMessage || 'Không thể lưu cấu hình hệ thống');
      return;
    }

    setCauHinhHeThong({
      token_min_cost_vnd: Number(kq.data?.settings?.token_min_cost_vnd || payload.token_min_cost_vnd),
      free_plan_max_pages: Number(kq.data?.settings?.free_plan_max_pages || payload.free_plan_max_pages),
      max_doc_upload_mb: Number(kq.data?.settings?.max_doc_upload_mb || payload.max_doc_upload_mb),
      rate_limit_admin_per_minute: Number(kq.data?.settings?.rate_limit_admin_per_minute || payload.rate_limit_admin_per_minute),
    });
    if (setCauHinhMeta) setCauHinhMeta(kq.data?.meta || null);
    toast.success('Đã lưu cấu hình. Khởi động lại backend để áp dụng cho luồng xử lý chính.');
  };

  return (
    <div className="max-w-4xl space-y-6">
      {/* ── SYSTEM CONFIG ─────────────────────────────────────────── */}
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm">
        <h3 className="mb-1 text-lg font-semibold text-white flex items-center gap-2">
          <Settings className="h-5 w-5 text-cyan-400" /> Tham Số Hệ Thống
        </h3>
        <p className="mb-6 text-sm text-slate-400">Dữ liệu đọc/ghi trực tiếp qua API backend /api/admin/system-config.</p>

        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Giá Token tối thiểu (VNĐ)</label>
              <input type="number" value={cauHinhHeThong.token_min_cost_vnd} onChange={(e) => capNhatGiaTriCauHinh('token_min_cost_vnd', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
              <p className="text-xs text-slate-500">Tỉ giá gốc quy đổi ra VNĐ cho tính toán dịch vụ.</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Số trang miễn phí (Gói Free)</label>
              <input type="number" value={cauHinhHeThong.free_plan_max_pages} onChange={(e) => capNhatGiaTriCauHinh('free_plan_max_pages', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
              <p className="text-xs text-slate-500">Số trang tài liệu được chuyển đổi miễn phí mỗi tài khoản.</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Trạng thái SePay API Key</label>
              <input type="text" value={cauHinhMeta?.sepay_api_key_configured ? 'Đã cấu hình' : 'Chưa cấu hình'} disabled className="w-full rounded-lg border border-white/5 bg-slate-900/50 px-4 py-2 text-slate-400 cursor-not-allowed" />
              <p className="text-xs text-slate-500">Khóa SePay được quản lý trong backend/.env.</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Giới hạn file Upload lớn nhất (MB)</label>
              <input type="number" value={cauHinhHeThong.max_doc_upload_mb} onChange={(e) => capNhatGiaTriCauHinh('max_doc_upload_mb', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
              <p className="text-xs text-slate-500">Ngăn người dùng lợi dụng tài nguyên máy chủ.</p>
            </div>
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-sm font-medium text-slate-300">Rate limit nhóm Admin (request/phút)</label>
              <input type="number" value={cauHinhHeThong.rate_limit_admin_per_minute} onChange={(e) => capNhatGiaTriCauHinh('rate_limit_admin_per_minute', e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
              <p className="text-xs text-slate-500">Khóa request API sau thời gian định nghĩa. Restart backend để áp dụng.</p>
            </div>
          </div>

          <div className="pt-4 border-t border-white/10 flex justify-end">
            <button disabled={dangLuuCauHinh} className="rounded-lg bg-cyan-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-500/20 disabled:opacity-60" onClick={xuLyLuuCauHinhHeThong}>
              {dangLuuCauHinh ? 'Đang lưu...' : 'Cập nhật Toàn hệ thống'}
            </button>
          </div>
        </div>
      </div>

      {/* ── PREMIUM PACKAGES DISPLAY ──────────────────────────────── */}
      <div className="rounded-xl border border-amber-500/10 bg-amber-500/[0.03] p-5">
        <h3 className="mb-1 text-lg font-semibold text-white flex items-center gap-2">
          <Crown className="h-5 w-5 text-amber-400" /> Cấu Hình Gói Premium
        </h3>
        <p className="mb-4 text-sm text-slate-400">
          Các giá trị này được định nghĩa trong <code className="text-amber-300 text-xs bg-amber-500/10 px-1 rounded">backend/app/config.py</code>.
          Để thay đổi giá gói, chỉnh sửa file đó và khởi động lại server.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {PREMIUM_PACKAGES_DISPLAY.map(pkg => (
            <div key={pkg.key} className="rounded-xl border border-amber-500/15 bg-amber-500/5 p-4">
              <p className="text-xs font-bold text-amber-300 uppercase tracking-wider mb-1">{pkg.label}</p>
              <p className="text-2xl font-black text-white">{pkg.gia}</p>
              <div className="mt-2 space-y-1 text-xs text-slate-400">
                <p>{pkg.so_ngay} ngày Premium</p>
                <p className="text-amber-300 font-semibold">{new Intl.NumberFormat('vi-VN').format(pkg.token)} token</p>
                <p className="text-slate-500 italic">{pkg.mo_ta}</p>
              </div>
              <p className="mt-2 text-[10px] text-slate-600 font-mono">{pkg.key}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── TOPUP BONUS TIERS ─────────────────────────────────────── */}
      <div className="rounded-xl border border-violet-500/10 bg-violet-500/[0.03] p-5">
        <h3 className="mb-1 text-lg font-semibold text-white flex items-center gap-2">
          <Coins className="h-5 w-5 text-violet-400" /> Bảng Thưởng Nạp Lẻ
        </h3>
        <p className="mb-4 text-sm text-slate-400">
          Khi người dùng nạp lẻ (không chọn gói combo), hệ thống tự động thưởng token theo mức sau.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-left text-[11px] uppercase tracking-wider text-slate-500">
                <th className="pb-2 font-medium">Mức nạp tối thiểu</th>
                <th className="pb-2 font-medium">Thưởng</th>
                <th className="pb-2 font-medium">Mô tả</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03]">
              {TOPUP_TIERS_DISPLAY.map((tier, i) => (
                <tr key={i}>
                  <td className="py-2 font-bold text-white">{tier.nguong}</td>
                  <td className="py-2">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/20">
                      {tier.thuong}
                    </span>
                  </td>
                  <td className="py-2 text-slate-400">{tier.mo_ta}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-slate-600">
          Cấu hình trong <code className="text-violet-300 bg-violet-500/10 px-1 rounded">TOPUP_BONUS_TIERS</code> tại backend/app/config.py
        </p>
      </div>
    </div>
  );
};

export default TabCauHinh;
