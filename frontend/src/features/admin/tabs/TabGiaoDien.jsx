import { Palette } from 'lucide-react';
import { dungTheme } from '../context/AdminThemeContext';

const TabGiaoDien = () => {
  const { theme, doiTheme } = dungTheme();

  const themes = [
    { id: 'dark-indigo', name: 'Dark Indigo', description: 'Mặc định, sang trọng với tông màu xanh đen' },
    { id: 'midnight-cyan', name: 'Midnight Cyan', description: 'Tông màu đen tuyền kết hợp cyan neon' },
    { id: 'warm-slate', name: 'Warm Slate', description: 'Trầm ấm với màu xám đá và viền vàng' },
    { id: 'light-pro', name: 'Light Pro (Beta)', description: 'Chế độ nền sáng chuyên nghiệp' }
  ];

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm space-y-6">
      <h3 className="mb-1 text-lg font-semibold text-white flex items-center gap-2">
        <Palette className="h-5 w-5 text-cyan-400" /> Quản lý Giao diện Toàn hệ thống
      </h3>
      <p className="text-sm text-slate-400">Thay đổi theme cho tất cả các trang, bao gồm cả trang Admin và Landing Page.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {themes.map(t => (
          <div 
            key={t.id}
            onClick={() => doiTheme(t.id)}
            className={`cursor-pointer rounded-xl border p-4 transition-all duration-300 ${theme === t.id ? 'bg-cyan-500/10 border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.2)]' : 'border-white/10 bg-slate-900/50 hover:bg-slate-800'}`}
          >
            <div className="h-24 w-full rounded-md mb-4 flex divide-x divide-white/10 overflow-hidden shadow-inner uppercase font-bold text-[10px] text-white/50 tracking-wider">
              {t.id === 'dark-indigo' && <><div className="flex-1 bg-slate-950 p-2">Bg</div><div className="flex-1 bg-indigo-500 p-2">Accent</div></>}
              {t.id === 'midnight-cyan' && <><div className="flex-1 bg-black p-2">Bg</div><div className="flex-1 bg-cyan-400 p-2 text-black">Accent</div></>}
              {t.id === 'warm-slate' && <><div className="flex-1 bg-stone-900 p-2">Bg</div><div className="flex-1 bg-amber-500 p-2">Accent</div></>}
              {t.id === 'light-pro' && <><div className="flex-1 bg-slate-50 text-slate-900 p-2">Bg</div><div className="flex-1 bg-blue-600 p-2">Accent</div></>}
            </div>
            <h4 className="font-semibold text-white text-sm">{t.name}</h4>
            <p className="text-xs text-slate-500 mt-1 h-10">{t.description}</p>
            
            <div className="mt-4 flex items-center justify-between">
              <span className={`text-xs font-medium px-2 py-1 rounded-md ${theme === t.id ? 'bg-cyan-400 text-slate-900' : 'bg-white/5 text-slate-400'}`}>
                {theme === t.id ? 'Đang dùng' : 'Chọn Theme'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TabGiaoDien;
