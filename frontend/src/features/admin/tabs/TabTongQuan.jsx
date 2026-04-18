import { useMemo } from 'react';
import { Users, Shield, Coins, History, FileDown, Download } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { xuatBaoCaoAdmin } from '../../../services/api';
import { StatCard } from '../components';

const TabTongQuan = ({ tongQuan, danhSachNguoiDung, danhSachPayments }) => {
  const paymentStats = useMemo(() => {
    const completed = danhSachPayments.filter(p => p.status === 'completed');
    const pending = danhSachPayments.filter(p => p.status === 'pending');
    const totalRevenue = completed.reduce((sum, p) => sum + (p.amount_vnd || 0), 0);
    return { completed: completed.length, pending: pending.length, totalRevenue };
  }, [danhSachPayments]);

  const { chartDataUsers, pieDataPlanType, chartDataRevenue } = useMemo(() => {
    const userGroups = {};
    let freeCount = 0;
    let premiumCount = 0;

    danhSachNguoiDung.forEach(u => {
      if (u.plan_type === 'premium') premiumCount++;
      else freeCount++;

      if (u.created_at) {
        const dateRaw = new Date(u.created_at);
        if (!isNaN(dateRaw)) {
          const dateStr = dateRaw.toISOString().split('T')[0];
          userGroups[dateStr] = (userGroups[dateStr] || 0) + 1;
        }
      }
    });

    const chartDataUsersObj = Object.keys(userGroups).sort().map(date => ({
      date,
      users: userGroups[date]
    }));

    const pieDataPlanTypeObj = [
      { name: 'Kế hoạch Miễn phí', value: freeCount, color: '#94a3b8' },
      { name: 'Khách hàng Premium', value: premiumCount, color: '#2dd4bf' }
    ];

    const revenueGroups = {};
    danhSachPayments.filter(p => p.status === 'completed').forEach(p => {
      if (p.createdAt) {
        const d = p.createdAt instanceof Date ? p.createdAt : new Date(p.createdAt);
        if (!isNaN(d)) {
          const dateStr = d.toISOString().split('T')[0];
          revenueGroups[dateStr] = (revenueGroups[dateStr] || 0) + (p.amount_vnd || 0);
        }
      }
    });
    const chartDataRevenueObj = Object.keys(revenueGroups).sort().map(date => ({
      date,
      revenue: revenueGroups[date]
    }));

    return { chartDataUsers: chartDataUsersObj, pieDataPlanType: pieDataPlanTypeObj, chartDataRevenue: chartDataRevenueObj };
  }, [danhSachNguoiDung, danhSachPayments]);

  const fmtVND = (n) => `${new Intl.NumberFormat('vi-VN').format(n)} VND`;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Users} label="Tổng người dùng" value={tongQuan?.tong_nguoi_dung ?? '-'} color="text-cyan-300 bg-cyan-500/10" />
        <StatCard icon={Shield} label="Quản trị viên" value={tongQuan?.tong_admin ?? '-'} color="text-emerald-300 bg-emerald-500/10" />
        <StatCard icon={Coins} label="Khách hàng Premium" value={tongQuan?.tong_premium ?? '-'} color="text-violet-300 bg-violet-500/10" />
        <StatCard icon={History} label="Tài liệu đã chuyển" value={tongQuan?.tong_ban_ghi_lich_su ?? '-'} color="text-amber-300 bg-amber-500/10" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 xl:grid-cols-4">
        {/* Tăng trưởng người dùng (Line Chart) */}
        <div className="col-span-1 lg:col-span-2 xl:col-span-2 rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-slate-300 uppercase tracking-wider">Tăng trưởng Người Dùng (Mới)</h3>
          <div className="h-[250px] w-full">
            {chartDataUsers.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartDataUsers}>
                  <XAxis dataKey="date" stroke="#cbd5e1" fontSize={11} tickMargin={8} />
                  <YAxis stroke="#cbd5e1" fontSize={11} tickMargin={8} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                    itemStyle={{ color: '#bae6fd' }}
                  />
                  <Line type="monotone" dataKey="users" name="Tài khoản mới" stroke="#38bdf8" strokeWidth={3} dot={{ strokeWidth: 2, r: 4, fill: '#0f172a' }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full w-full items-center justify-center text-sm text-slate-500">Chưa đủ dữ liệu thống kê</div>
            )}
          </div>
        </div>

        {/* Tỷ trọng gói (Pie Chart) */}
        <div className="col-span-1 xl:col-span-1 border border-white/5 bg-white/[0.02] p-5 shadow-sm rounded-xl">
          <h3 className="mb-4 text-sm font-semibold text-slate-300 uppercase tracking-wider text-center">Tỷ trọng Khách Hàng</h3>
          <div className="h-[250px] w-full">
            {pieDataPlanType.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieDataPlanType}
                    cx="50%" cy="50%"
                    innerRadius={60} outerRadius={85}
                    paddingAngle={5}
                    dataKey="value" stroke="none"
                  >
                    {pieDataPlanType.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff' }} />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full w-full items-center justify-center text-sm text-slate-500">Chưa đủ dữ liệu thống kê</div>
            )}
          </div>
        </div>

        {/* Doanh thu (Bar Chart) */}
        <div className="col-span-1 lg:col-span-3 xl:col-span-1 border border-white/5 bg-white/[0.02] p-5 shadow-sm rounded-xl">
          <h3 className="mb-4 text-sm font-semibold text-slate-300 uppercase tracking-wider">Doanh thu SePay (VNĐ)</h3>
          <div className="mb-2 text-2xl font-black text-emerald-400">{fmtVND(paymentStats.totalRevenue)}</div>
          <div className="text-xs text-slate-400 mb-4">{paymentStats.completed} hóa đơn hoàn tất, {paymentStats.pending} chưa xác nhận.</div>
          <div className="h-[170px] w-full">
            {chartDataRevenue.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartDataRevenue}>
                  <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickMargin={5} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                    itemStyle={{ color: '#34d399' }}
                    formatter={(value) => new Intl.NumberFormat('vi-VN').format(value) + ' VNĐ'}
                  />
                  <Bar dataKey="revenue" name="Doanh thu" fill="#34d399" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full w-full items-center justify-center text-sm text-slate-500 border border-dashed border-white/10 rounded-xl">Chưa phát sinh doanh thu</div>
            )}
          </div>
        </div>
        {/* Report Center - Spans all columns */}
        <div className="col-span-1 lg:col-span-3 xl:col-span-4 rounded-2xl border border-white/10 bg-white/5 p-6 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <FileDown className="w-6 h-6 text-primary-400" />
                Trung tâm Xuất Báo cáo
              </h3>
              <p className="text-sm text-white/50 mt-1">Xuất dữ liệu hệ thống ra tệp CSV để theo dõi và đối soát</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => xuatBaoCaoAdmin('payments')}
              className="flex items-center justify-between p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all group gap-3"
            >
              <div className="flex items-center gap-3 text-emerald-300 font-semibold">
                <div className="p-2 bg-emerald-500/20 rounded-lg">
                  <Coins className="w-5 h-5" />
                </div>
                <span className="text-sm">Báo cáo Doanh thu</span>
              </div>
              <Download className="w-4 h-4 text-emerald-400/50 group-hover:text-emerald-400 shrink-0" />
            </button>

            <button
              onClick={() => xuatBaoCaoAdmin('conversions')}
              className="flex items-center justify-between p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20 hover:bg-cyan-500/20 transition-all group gap-3"
            >
              <div className="flex items-center gap-3 text-cyan-300 font-semibold">
                <div className="p-2 bg-cyan-500/20 rounded-lg">
                  <History className="w-5 h-5" />
                </div>
                <span className="text-sm">Báo cáo Chuyển đổi</span>
              </div>
              <Download className="w-4 h-4 text-cyan-400/50 group-hover:text-cyan-400 shrink-0" />
            </button>

            <button
              onClick={() => xuatBaoCaoAdmin('users')}
              className="flex items-center justify-between p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 hover:bg-violet-500/20 transition-all group gap-3"
            >
              <div className="flex items-center gap-3 text-violet-300 font-semibold">
                <div className="p-2 bg-violet-500/20 rounded-lg">
                  <Users className="w-5 h-5" />
                </div>
                <span className="text-sm">Danh sách Người dùng</span>
              </div>
              <Download className="w-4 h-4 text-violet-400/50 group-hover:text-violet-400 shrink-0" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TabTongQuan;
