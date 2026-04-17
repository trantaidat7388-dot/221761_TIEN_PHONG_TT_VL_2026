import { Home, LogOut, ChevronRight } from 'lucide-react';

const AdminSidebar = ({ sidebarOpen, activeTab, setActiveTab, TABS, navigate, xuLyDangXuatAdmin }) => {
  return (
    <aside className={`${sidebarOpen ? 'w-56' : 'w-16'} flex flex-col border-r border-white/5 bg-slate-950/90 transition-all duration-300`}>
      {/* Logo */}
      <div className="flex items-center gap-2 border-b border-white/5 px-4 py-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-blue-500 text-xs font-black text-white">
          W2L
        </div>
        {sidebarOpen && <span className="text-sm font-bold text-white">Admin Panel</span>}
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
                  ? 'bg-cyan-500/15 text-cyan-300 shadow-lg shadow-cyan-500/5'
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
      <div className="border-t border-white/5 px-2 py-3 space-y-1">
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
