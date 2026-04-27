import { useMemo, useState } from 'react';
import { CheckCircle2, Clock, Coins, CreditCard, XCircle, Filter } from 'lucide-react';
import toast from 'react-hot-toast';
import { xacNhanPaymentThuCongAdmin } from '../../../services/api';
import { StatCard } from '../components';
import StatusBadge from '../components/StatusBadge';
import { fmtVND, fmtDate } from '../utils/formatters';

const PLAN_LABELS = {
  week_20k: 'Gói Tuần 20K',
  month_50k: 'Gói Tháng 50K',
  month_100k: 'Gói Tháng 100K',
  year_500k: 'Gói Năm 500K',
};

const STATUS_FILTERS = [
  { key: 'all', label: 'Tất cả' },
  { key: 'pending', label: 'Đang chờ' },
  { key: 'completed', label: 'Thành công' },
  { key: 'failed', label: 'Thất bại' },
];

const TabThanhToan = ({ danhSachPayments, taiDuLieu }) => {
  const [statusFilter, setStatusFilter] = useState('all');

  const paymentStats = useMemo(() => {
    const completed = danhSachPayments.filter(p => p.status === 'completed');
    const pending = danhSachPayments.filter(p => p.status === 'pending');
    const failed = danhSachPayments.filter(p => p.status === 'failed');
    const totalRevenue = completed.reduce((sum, p) => sum + (p.amount_vnd || 0), 0);
    return { completed: completed.length, pending: pending.length, failed: failed.length, totalRevenue };
  }, [danhSachPayments]);

  const danhSachDaLoc = useMemo(() => {
    if (statusFilter === 'all') return danhSachPayments;
    return danhSachPayments.filter(p => p.status === statusFilter);
  }, [danhSachPayments, statusFilter]);

  const xuLyXacNhanPayment = async (paymentId) => {
    if (!window.confirm('Xác nhận thanh toán thủ công cho hóa đơn này?')) return;
    const kq = await xacNhanPaymentThuCongAdmin(paymentId);
    if (!kq.thanhCong) { toast.error(kq.loiMessage || 'Lỗi xác nhận'); return; }
    toast.success('Đã xác nhận thanh toán');
    if (taiDuLieu) taiDuLieu();
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={CheckCircle2} label="Thành công" value={paymentStats.completed} color="text-emerald-300 bg-emerald-500/10" />
        <StatCard icon={Clock} label="Đang chờ" value={paymentStats.pending} color="text-amber-300 bg-amber-500/10" />
        <StatCard icon={XCircle} label="Thất bại" value={paymentStats.failed} color="text-red-300 bg-red-500/10" />
        <StatCard icon={Coins} label="Tổng doanh thu" value={fmtVND(paymentStats.totalRevenue)} color="text-sky-300 bg-sky-500/10" />
      </div>

      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-cyan-400" /> Tất cả hóa đơn
            <span className="text-xs text-slate-500 font-normal">({danhSachDaLoc.length}/{danhSachPayments.length})</span>
          </h3>
          {/* Filter Tabs */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-white/5 border border-white/5">
            <Filter className="w-3 h-3 text-slate-500 ml-1" />
            {STATUS_FILTERS.map(f => (
              <button
                key={f.key}
                onClick={() => setStatusFilter(f.key)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                  statusFilter === f.key
                    ? 'bg-primary-600 text-white shadow'
                    : 'text-white/40 hover:text-white hover:bg-white/5'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-sm text-white/90">
            <thead>
              <tr className="border-b border-white/5 text-left text-[11px] uppercase tracking-wider text-slate-500">
                <th className="py-2.5 pr-3 font-medium">ID</th>
                <th className="py-2.5 pr-3 font-medium">Người dùng</th>
                <th className="py-2.5 pr-3 font-medium">Loại gói</th>
                <th className="py-2.5 pr-3 font-medium">Số tiền</th>
                <th className="py-2.5 pr-3 font-medium">Token</th>
                <th className="py-2.5 pr-3 font-medium">Trạng thái</th>
                <th className="py-2.5 pr-3 font-medium">Thời gian</th>
                <th className="py-2.5 font-medium">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {danhSachDaLoc.map(p => (
                <tr key={p.id} className="border-b border-white/[0.03] hover:bg-white/[0.015] transition">
                  <td className="py-2.5 pr-3 font-mono text-xs text-slate-400">#{p.id}</td>
                  <td className="py-2.5 pr-3">
                    <p className="text-sm font-medium">{p.username || '—'}</p>
                    <p className="text-xs text-slate-500">{p.email}</p>
                  </td>
                  <td className="py-2.5 pr-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                      p.plan_key
                        ? 'bg-violet-500/15 text-violet-300 border border-violet-500/20'
                        : 'bg-white/5 text-slate-500 border border-white/5'
                    }`}>
                      {p.plan_key ? (PLAN_LABELS[p.plan_key] || p.plan_key) : 'Nạp lẻ'}
                    </span>
                  </td>
                  <td className="py-2.5 pr-3 font-semibold text-white">{fmtVND(p.amount_vnd)}</td>
                  <td className="py-2.5 pr-3 text-amber-300 font-mono font-semibold">
                    {new Intl.NumberFormat('vi-VN').format(p.token_amount)}
                  </td>
                  <td className="py-2.5 pr-3">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="py-2.5 pr-3 text-xs text-slate-500">
                    {p.created_at ? fmtDate(new Date(p.created_at)) : (p.createdAt ? fmtDate(p.createdAt) : '—')}
                  </td>
                  <td className="py-2.5">
                    {p.status !== 'completed' && (
                      <button
                        onClick={() => xuLyXacNhanPayment(p.id)}
                        className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-300 hover:bg-emerald-500/20 transition whitespace-nowrap"
                      >
                        Xác nhận
                      </button>
                    )}
                    {p.status === 'completed' && <span className="text-xs text-slate-600">—</span>}
                  </td>
                </tr>
              ))}
              {!danhSachDaLoc.length && (
                <tr>
                  <td className="py-8 text-center text-slate-600" colSpan={8}>
                    {statusFilter === 'all' ? 'Chưa có hóa đơn nào' : `Không có hóa đơn "${STATUS_FILTERS.find(f => f.key === statusFilter)?.label}"`}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TabThanhToan;
