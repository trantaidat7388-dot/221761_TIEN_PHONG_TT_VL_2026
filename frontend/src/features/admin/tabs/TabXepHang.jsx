import { Trophy } from 'lucide-react';
import { useMemo } from 'react';
import { avatarChars } from '../utils/formatters';

const TabXepHang = ({ danhSachNguoiDung }) => {
  const topUsers = useMemo(() => {
    return [...danhSachNguoiDung]
      .sort((a, b) => (b.so_lan_chuyen_doi || 0) - (a.so_lan_chuyen_doi || 0))
      .slice(0, 50);
  }, [danhSachNguoiDung]);

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2 text-lg">
          <Trophy className="h-5 w-5 text-amber-400" /> Bảng Xếp Hạng Người Dùng Tích Cực
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm text-white/90 table-fixed">
          <thead>
            <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-slate-400">
              <th className="w-[10%] py-3">Hạng</th>
              <th className="w-[30%] py-3">Tài khoản</th>
              <th className="w-[20%] py-3">Loại Gói</th>
              <th className="w-[20%] py-3">Số dư (Token)</th>
              <th className="w-[20%] py-3 text-right">Tài liệu đã chuyển</th>
            </tr>
          </thead>
          <tbody>
            {topUsers.map((u, idx) => (
              <tr key={u.id} className="border-b border-white/[0.03] hover:bg-white/[0.01] transition-colors">
                <td className="py-3 font-semibold text-slate-300">
                  {idx === 0 && <span className="flex items-center gap-1.5 text-amber-400"><Trophy className="h-4 w-4" /> 1</span>}
                  {idx === 1 && <span className="flex items-center gap-1.5 text-slate-300"><Trophy className="h-4 w-4" /> 2</span>}
                  {idx === 2 && <span className="flex items-center gap-1.5 text-amber-700"><Trophy className="h-4 w-4" /> 3</span>}
                  {idx > 2 && <span className="pl-6 text-slate-500">#{idx + 1}</span>}
                </td>
                <td className="py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-[10px] font-bold text-white shadow-inner">
                      {avatarChars(u)}
                    </div>
                    <div>
                      <p className="font-medium text-slate-200">{u.username}</p>
                      <p className="text-[11px] text-slate-500">{u.email}</p>
                    </div>
                  </div>
                </td>
                <td className="py-3">
                    {u.plan_type === 'premium' 
                      ? <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-400">Premium</span> 
                      : <span className="rounded-full bg-slate-500/10 px-2 py-0.5 text-[11px] font-semibold text-slate-400">Miễn phí</span>}
                </td>
                <td className="py-3 font-mono text-cyan-200">{new Intl.NumberFormat('vi-VN').format(u.token_balance || 0)}</td>
                <td className="py-3 text-right text-lg font-bold text-white">{u.so_lan_chuyen_doi}</td>
              </tr>
            ))}
            {!topUsers.length && (
              <tr><td className="py-6 text-center text-slate-500" colSpan={5}>Chưa có đủ dữ liệu người dùng</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TabXepHang;
