import { RefreshCw } from 'lucide-react';
import { NutBam } from '../../../components';

const AdminTopBar = ({ sidebarOpen, setSidebarOpen, activeTabLabel, nguoiDung, taiDuLieu, dangTai }) => {
  return (
    <div className="sticky top-0 z-30 flex items-center justify-between border-b border-white/5 bg-slate-950/80 px-6 py-3 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="rounded-lg p-1.5 text-slate-400 hover:bg-white/5 hover:text-white transition">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
        <h1 className="text-lg font-bold text-white">{activeTabLabel || 'Admin'}</h1>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-500">{nguoiDung?.email}</span>
        <NutBam onClick={taiDuLieu} bienThe="secondary" icon={RefreshCw} dangTai={dangTai}>
          Làm mới
        </NutBam>
      </div>
    </div>
  );
};

export default AdminTopBar;
