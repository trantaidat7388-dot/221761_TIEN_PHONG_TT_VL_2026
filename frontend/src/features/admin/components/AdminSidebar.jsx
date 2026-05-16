import { Home, LogOut, ChevronRight } from 'lucide-react';

const AdminSidebar = ({ sidebarOpen, activeTab, setActiveTab, TABS, navigate, xuLyDangXuatAdmin }) => {
  return (
    <aside className={`${sidebarOpen ? 'w-56' : 'w-16'} flex h-screen flex-col border-r border-white/5 bg-slate-950/90 transition-all duration-300 sticky top-0`}>
      {/* Logo */}
      <div className={`flex ${sidebarOpen ? 'items-end gap-2 justify-start' : 'items-center justify-center'} border-b border-white/5 px-4 py-4`}>
        <img 
          src="/logo_admin_purple.png" 
          alt="W2L Logo" 
          className="h-9 w-9 shrink-0 rounded-xl object-cover shadow-lg shadow-purple-500/20 ring-1 ring-white/10" 
        />
        {sidebarOpen && <span className="text-sm font-bold text-white leading-none pb-0.5">Admin Panel</span>}
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 px-2 py-3 overflow-y-auto">
        {TABS.map(tab => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-all
                ${isActive
                  ? 'bg-purple-500/15 text-purple-300 shadow-lg shadow-purple-500/5'
                  : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
              title={tab.label}
            >
              <tab.icon className="h-4.5 w-4.5 shrink-0" />
              {sidebarOpen && <span>{tab.label}</span>}
              {isActive && sidebarOpen && <ChevronRight className="ml-auto h-3.5 w-3.5" />}
            </button>
          );
        })}
      </nav>

      {/* Sidebar footer */}
      <div className="mt-auto sticky bottom-0 border-t border-white/5 px-2 py-3 space-y-1 bg-slate-950/95">
        <button
          onClick={() => navigate('/')}
          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/5 hover:text-white transition"
          title="Về trang chủ"
        >
          <Home className="h-4 w-4 shrink-0" />
          {sidebarOpen && <span>Trang chủ</span>}
        </button>
        <button
          onClick={xuLyDangXuatAdmin}
          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-red-400/70 hover:bg-red-500/10 hover:text-red-300 transition"
          title="Đăng xuất"
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {sidebarOpen && <span>Đăng xuất</span>}
        </button>
      </div>
    </aside>
  );
};

export default AdminSidebar;
