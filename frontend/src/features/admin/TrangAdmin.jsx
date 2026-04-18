import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, Users, Trophy, CreditCard, Files, History, Settings, Paintbrush, FileText } from 'lucide-react';
import { dungXacThuc } from '../../context/AuthContext';
import { useAdminData } from './hooks/useAdminData';
import { AdminSidebar, AdminTopBar } from './components';
import {
  TabTongQuan, TabNguoiDung, TabXepHang, TabThanhToan,
  TabTemplate, TabLichSu, TabCauHinh,
  TabQuanTriGiaoDien, TabChuyenDoiAdmin
} from './tabs';

const TABS = [
  { key: 'tong-quan', label: 'Tổng quan', icon: BarChart3 },
  { key: 'chuyen-doi', label: 'Chuyển Đổi', icon: FileText },
  { key: 'nguoi-dung', label: 'Người dùng', icon: Users },
  { key: 'xep-hang', label: 'Xếp hạng', icon: Trophy },
  { key: 'thanh-toan', label: 'Thanh toán', icon: CreditCard },
  { key: 'template', label: 'Template', icon: Files },
  { key: 'lich-su', label: 'Lịch sử', icon: History },
  { key: 'cau-hinh', label: 'Cấu hình', icon: Settings },
  { key: 'quan-tri-giao-dien', label: 'Quản trị Giao diện', icon: Paintbrush },
];

const TrangAdmin = () => {
  const navigate = useNavigate();
  const { token, nguoiDung, dangXuat } = dungXacThuc();
  const [activeTab, setActiveTab] = useState('tong-quan');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const adminData = useAdminData();

  useEffect(() => {
    adminData.taiDuLieu();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!token) {
      navigate('/', { replace: true });
    }
  }, [token, navigate]);

  return (
    <div className="flex min-h-screen bg-slate-950">
      <AdminSidebar 
        TABS={TABS} 
        navigate={navigate}
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        sidebarOpen={sidebarOpen} 
        xuLyDangXuatAdmin={dangXuat} 
      />

      <main className="flex-1 overflow-auto bg-slate-950">
        <AdminTopBar 
          activeTabLabel={TABS.find(t => t.key === activeTab)?.label}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          nguoiDung={nguoiDung}
          taiDuLieu={adminData.taiDuLieu}
          dangTai={adminData.dangTai}
        />

        <div className="p-6">
          {activeTab === 'tong-quan' && <TabTongQuan {...adminData} />}
          {activeTab === 'nguoi-dung' && <TabNguoiDung {...adminData} />}
          {activeTab === 'xep-hang' && <TabXepHang {...adminData} />}
          {activeTab === 'thanh-toan' && <TabThanhToan {...adminData} />}
          {activeTab === 'template' && <TabTemplate {...adminData} />}
          {activeTab === 'lich-su' && <TabLichSu {...adminData} />}
          {activeTab === 'cau-hinh' && <TabCauHinh {...adminData} />}
          {activeTab === 'quan-tri-giao-dien' && <TabQuanTriGiaoDien />}
          {activeTab === 'chuyen-doi' && <TabChuyenDoiAdmin />}
        </div>
      </main>
    </div>
  );
};

export default TrangAdmin;
