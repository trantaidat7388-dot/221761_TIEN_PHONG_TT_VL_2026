import { useMemo } from 'react';
import { CheckCircle2, Clock, Coins, CreditCard } from 'lucide-react';
import toast from 'react-hot-toast';
import { xacNhanPaymentThuCongAdmin } from '../../../services/api';
import { StatCard } from '../components';
import StatusBadge from '../components/StatusBadge';
import { fmtVND, fmtDate } from '../utils/formatters';

const TabThanhToan = ({ danhSachPayments, taiDuLieu }) => {
  const paymentStats = useMemo(() => {
    const completed = danhSachPayments.filter(p => p.status === 'completed');
    const pending = danhSachPayments.filter(p => p.status === 'pending');
    const totalRevenue = completed.reduce((sum, p) => sum + (p.amount_vnd || 0), 0);
    return { completed: completed.length, pending: pending.length, totalRevenue };
  }, [danhSachPayments]);

  const xuLyXacNhanPayment = async (paymentId) => {
    if (!window.confirm('Xac nhan thanh toan thu cong cho hoa don nay?')) return;
    const kq = await xacNhanPaymentThuCongAdmin(paymentId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Lỗi xác nhận'); return; }
    toast.success('Da xac nhan thanh toan');
    if (taiDuLieu) taiDuLieu();
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard icon={CheckCircle2} label="Thanh cong" value={paymentStats.completed} color="text-emerald-300 bg-emerald-500/10" />
        <StatCard icon={Clock} label="Dang cho" value={paymentStats.pending} color="text-amber-300 bg-amber-500/10" />
        <StatCard icon={Coins} label="Tong doanh thu" value={fmtVND(paymentStats.totalRevenue)} color="text-sky-300 bg-sky-500/10" />
      </div>

      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <h3 className="mb-4 font-semibold text-white flex items-center gap-2">
          <CreditCard className="h-4 w-4 text-cyan-400" /> Tat ca hoa don
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm text-white/90">
            <thead>
              <tr className="border-b border-white/5 text-left text-xs text-slate-500">
                <th className="py-2 pr-2">ID</th>
                <th className="py-2 pr-2">User</th>
                <th className="py-2 pr-2">So tien</th>
                <th className="py-2 pr-2">Token</th>
                <th className="py-2 pr-2">Trang thai</th>
                <th className="py-2 pr-2">Thoi gian</th>
                <th className="py-2">Hanh dong</th>
              </tr>
            </thead>
            <tbody>
              {danhSachPayments.map(p => (
                <tr key={p.id} className="border-b border-white/[0.03]">
                  <td className="py-2 pr-2 font-mono text-xs">#{p.id}</td>
                  <td className="py-2 pr-2">
                    <p className="text-sm">{p.username || '-'}</p>
                    <p className="text-xs text-slate-500">{p.email}</p>
                  </td>
                  <td className="py-2 pr-2 font-semibold">{fmtVND(p.amount_vnd)}</td>
                  <td className="py-2 pr-2 text-amber-300">{new Intl.NumberFormat('vi-VN').format(p.token_amount)}</td>
                  <td className="py-2 pr-2">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="py-2 pr-2 text-xs text-slate-500">{fmtDate(p.createdAt)}</td>
                  <td className="py-2">
                    {p.status !== 'completed' && (
                      <button
                        onClick={() => xuLyXacNhanPayment(p.id)}
                        className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-300 hover:bg-emerald-500/20 transition"
                      >
                        Xac nhan
                      </button>
                    )}
                    {p.status === 'completed' && <span className="text-xs text-slate-600">—</span>}
                  </td>
                </tr>
              ))}
              {!danhSachPayments.length && (
                <tr><td className="py-4 text-slate-600" colSpan={7}>Chua co hoa don nao</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TabThanhToan;
