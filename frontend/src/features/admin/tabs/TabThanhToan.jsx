import { useMemo } from 'react';
import { CheckCircle2, Clock, Coins, CreditCard, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { xacNhanPaymentThuCongAdmin, dongBoSePayAdmin } from '../../../services/api';
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
    if (!window.confirm('Xác nhận thanh toán thủ công cho hóa đơn này?')) return;
    const kq = await xacNhanPaymentThuCongAdmin(paymentId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Lỗi xác nhận'); return; }
    toast.success('Đã xác nhận thanh toán');
    if (taiDuLieu) taiDuLieu();
  };

  const xuLyDongBoSePay = async () => {
    toast.promise(dongBoSePayAdmin(), {
      loading: 'Đang kết nối SePay và đối soát...',
      success: (res) => {
        if (taiDuLieu) taiDuLieu();
        return `Đã đồng bộ xong. Khớp thành công ${res.count} giao dịch.`;
      },
      error: (err) => err.loiMessage || 'Lỗi khi đồng bộ'
    });
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard icon={CheckCircle2} label="Thanh cong" value={paymentStats.completed} color="text-purple-300 bg-purple-500/10" />
        <StatCard icon={Clock} label="Dang cho" value={paymentStats.pending} color="text-amber-300 bg-amber-500/10" />
        <StatCard icon={Coins} label="Tong doanh thu" value={fmtVND(paymentStats.totalRevenue)} color="text-fuchsia-300 bg-fuchsia-500/10" />
      </div>

      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-purple-400" /> Tất cả hóa đơn
          </h3>
          <button
            onClick={xuLyDongBoSePay}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-xs font-bold shadow-lg shadow-primary-500/20 transition-all active:scale-95"
          >
            <RefreshCw className="w-4 h-4" />
            Đồng bộ SePay
          </button>
        </div>
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
                        className="rounded-lg border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 text-xs font-medium text-purple-300 hover:bg-purple-500/20 transition"
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
