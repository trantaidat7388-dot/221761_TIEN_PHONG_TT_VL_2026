import { useState, useEffect } from 'react';
import { Layout, Save, RotateCcw, AlertTriangle, Plus, Trash2, GripVertical, Settings2, FileJson } from 'lucide-react';
import toast from 'react-hot-toast';
import { layNoiDungLandingAdmin, capNhatNoiDungLandingAdmin, resetNoiDungLandingAdmin } from '../../../services/api';
import { NutBam } from '../../../components';

const SECTION_DEFS = {
  hero: { label: 'Phần Đầu (Hero)', desc: 'Tiêu đề lớn & Kêu gọi hành động', color: 'border-purple-500/30 bg-purple-500/10 text-purple-300' },
  tinh_nang: { label: 'Các Tính Năng', desc: 'Danh sách tính năng nổi bật', color: 'border-blue-500/30 bg-blue-500/10 text-blue-300' },
  buoc_su_dung: { label: 'Bước Sử Dụng', desc: 'Quy trình hoạt động', color: 'border-green-500/30 bg-green-500/10 text-green-300' },
  mau_template: { label: 'Mẫu Template', desc: 'Các template LaTeX hỗ trợ', color: 'border-pink-500/30 bg-pink-500/10 text-pink-300' },
  goi_premium: { label: 'Gói Premium', desc: 'Bảng giá / Gói nạp', color: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-300' },
  thanh_toan: { label: 'Thanh Toán', desc: 'Module hướng dẫn chuyển khoản', color: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300', isReadOnly: true },
  so_sanh: { label: 'So Sánh (Trước/Sau)', desc: 'Sự khác biệt khi dùng', color: 'border-orange-500/30 bg-orange-500/10 text-orange-300' },
  faq: { label: 'FAQ (Hỏi Đáp)', desc: 'Câu hỏi thường gặp', color: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300' },
  cta_bottom: { label: 'Kêu Gọi (Cuối Trang)', desc: 'Nút đăng ký / Bắt đầu ngay', color: 'border-indigo-500/30 bg-indigo-500/10 text-indigo-300' }
};

const TabLandingEditor = () => {
  const [content, setContent] = useState(null);
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [activeSection, setActiveSection] = useState('hero');
  const [draggedIdx, setDraggedIdx] = useState(null);

  const taiDuLieu = async () => {
    setLoading(true);
    const res = await layNoiDungLandingAdmin();
    if (res.thanhCong) {
      setContent(res.content);
      setDraft(res.content);
    } else {
      toast.error('Lỗi tải dữ liệu landing: ' + res.loiMessage);
    }
    setLoading(false);
  };

  useEffect(() => {
    taiDuLieu();
  }, []);

  const xuLyLuu = async () => {
    setSaving(true);
    const res = await capNhatNoiDungLandingAdmin(draft);
    if (res.thanhCong) {
      toast.success('Đã xuất bản giao diện mới!');
      setContent(res.content);
      setDraft(res.content);
    } else {
      toast.error('Lỗi khi lưu: ' + res.loiMessage);
    }
    setSaving(false);
  };

  const xuLyReset = async () => {
    if (!window.confirm('Bạn có chắc muốn khôi phục về giao diện gốc?')) return;
    setSaving(true);
    const res = await resetNoiDungLandingAdmin();
    if (res.thanhCong) {
      toast.success('Đã khôi phục thành công!');
      setContent(res.content);
      setDraft(res.content);
    } else {
      toast.error('Lỗi khi khôi phục: ' + res.loiMessage);
    }
    setSaving(false);
  };

  const handleChange = (path, value) => {
    setDraft(prev => {
      const newData = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let current = newData;
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {};
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      return newData;
    });
  };

  const handleArrayChange = (arrayPath, index, field, value) => {
    setDraft(prev => {
      const newData = JSON.parse(JSON.stringify(prev));
      if (field) {
        newData[arrayPath][index][field] = value;
      } else {
        newData[arrayPath][index] = value;
      }
      return newData;
    });
  };

  const addArrayElement = (arrayPath, defaultObj) => {
    setDraft(prev => {
      const newData = JSON.parse(JSON.stringify(prev));
      if (!newData[arrayPath]) newData[arrayPath] = [];
      newData[arrayPath].push(defaultObj);
      return newData;
    });
  };

  const removeArrayElement = (arrayPath, index) => {
    setDraft(prev => {
      const newData = JSON.parse(JSON.stringify(prev));
      newData[arrayPath].splice(index, 1);
      return newData;
    });
  };

  // --- HTML5 Drag & Drop Logic ---
  const onDragStart = (e, index) => {
    setDraggedIdx(index);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/html", index); // Required for Firefox
  };

  const onDragOver = (e, index) => {
    e.preventDefault(); // Necessary to allow dropping
  };

  const onDrop = (e, dropIndex) => {
    e.preventDefault();
    if (draggedIdx === null || draggedIdx === dropIndex) return;

    const newOrder = [...(draft.section_order || [])];
    const [movedItem] = newOrder.splice(draggedIdx, 1);
    newOrder.splice(dropIndex, 0, movedItem);

    handleChange('section_order', newOrder);
    setDraggedIdx(null);
  };

  if (loading) return <div className="p-10 text-center text-slate-400">Đang tải dữ liệu trình dựng trang...</div>;
  if (!draft) return <div className="p-10 text-center text-red-400">Không thể kết nối đến hệ thống</div>;

  const isDirty = JSON.stringify(content) !== JSON.stringify(draft);
  const currentSections = draft.section_order || [];

  return (
    <div className="rounded-xl border border-white/5 bg-slate-900 shadow-xl overflow-hidden flex flex-col h-[85vh] min-h-[600px]">
      
      {/* HEADERBAR */}
      <div className="flex items-center justify-between border-b border-white/10 px-6 py-4 bg-slate-950">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Layout className="h-6 w-6 text-primary-400" /> Trình Dựng Trang (Page Builder)
          </h3>
          <p className="text-sm text-slate-400 mt-1">Kéo thả để sắp xếp bố cục. Chỉnh sửa chữ và thuộc tính ngay tại form.</p>
        </div>
        <div className="flex gap-3">
          <NutBam onClick={() => setActiveSection('json_raw')} bienThe={activeSection === 'json_raw' ? 'primary' : 'outline'} icon={FileJson}>Mã JSON</NutBam>
          <NutBam onClick={xuLyReset} bienThe="secondary" icon={RotateCcw} dangTai={saving}>Khôi phục gốc</NutBam>
          <NutBam onClick={xuLyLuu} icon={Save} dangTai={saving} disabled={!isDirty}>
            {isDirty ? 'Xuất bản giao diện' : 'Đã đồng bộ'}
          </NutBam>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        
        {/* CANVAS LEFT PANE (KÉO THẢ) */}
        <div className="w-[300px] shrink-0 border-r border-white/10 bg-slate-950/50 flex flex-col">
          <div className="p-4 border-b border-white/5 bg-slate-900/80 sticky top-0 z-10 shadow-sm">
            <div className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Cấu trúc hiển thị</div>
            <div className="text-xs text-slate-500 mt-1">Kéo khối lệnh để đổi thứ tự trên trang</div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            {currentSections.map((secId, idx) => {
              const def = SECTION_DEFS[secId] || { label: secId, desc: 'Khối tùy chỉnh', color: 'border-slate-500/30 bg-slate-500/10 text-slate-300' };
              const isDragging = draggedIdx === idx;
              const isActive = activeSection === secId;

              return (
                <div
                  key={secId}
                  draggable
                  onDragStart={(e) => onDragStart(e, idx)}
                  onDragOver={(e) => onDragOver(e, idx)}
                  onDrop={(e) => onDrop(e, idx)}
                  onClick={() => setActiveSection(secId)}
                  className={`
                    group relative flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200
                    ${isDragging ? 'opacity-30 scale-95' : 'hover:scale-[1.02]'}
                    ${isActive ? 'border-primary-500 bg-primary-500/10 shadow-[0_0_15px_rgba(99,102,241,0.15)] ring-1 ring-primary-500' : 'border-white/10 bg-white/5 hover:bg-white/10'}
                  `}
                >
                  <div className="cursor-grab active:cursor-grabbing text-slate-500 group-hover:text-slate-300 touch-none py-2 px-1">
                    <GripVertical className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0 pr-2">
                    <div className={`font-semibold text-sm truncate ${isActive ? 'text-white' : def.color.split(' ')[2]}`}>{def.label}</div>
                    <div className="text-xs text-slate-400 truncate">{def.desc}</div>
                  </div>
                  {isActive && <Settings2 className="w-5 h-5 text-primary-400 opacity-80" />}
                </div>
              );
            })}
          </div>
        </div>

        {/* EDITOR RIGHT PANE (INSPECTOR FORMS) */}
        <div className="flex-1 overflow-y-auto relative bg-slate-900 custom-scrollbar">
          
          <div className="max-w-4xl mx-auto p-8 pb-32 space-y-6">
             {activeSection !== 'json_raw' && SECTION_DEFS[activeSection] && (
               <div className="mb-8">
                 <h2 className="text-2xl font-bold text-white tracking-tight">{SECTION_DEFS[activeSection].label}</h2>
                 <p className="text-slate-400 mt-1">{SECTION_DEFS[activeSection].desc}</p>
                 {SECTION_DEFS[activeSection].isReadOnly && (
                    <div className="mt-4 inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm px-4 py-2 rounded-lg">
                      Khối này điều khiển hiển thị module hệ thống. Bạn chỉ có thể kéo thả để thay đổi vị trí, nội dung tự động tạo.
                    </div>
                 )}
               </div>
             )}

             {/* HERO */}
             {activeSection === 'hero' && (
                <div className="space-y-6 animate-in fade-in">
                  <div className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-5">
                    <InputRow label="Nhãn (Badge)" val={draft.hero?.badge} onChange={v => handleChange('hero.badge', v)} />
                    <InputRow label="Tiêu đề thứ nhất" val={draft.hero?.title} onChange={v => handleChange('hero.title', v)} />
                    <InputRow label="Tiêu đề bôi đậm" val={draft.hero?.title_highlight} onChange={v => handleChange('hero.title_highlight', v)} />
                    <AreaRow label="Đoạn văn giới thiệu" val={draft.hero?.description} onChange={v => handleChange('hero.description', v)} rows={3} />
                  </div>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-5">
                      <InputRow label="Text Nút Chính" val={draft.hero?.cta_primary} onChange={v => handleChange('hero.cta_primary', v)} />
                    </div>
                    <div className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-5">
                      <InputRow label="Text Nút Phụ" val={draft.hero?.cta_secondary} onChange={v => handleChange('hero.cta_secondary', v)} />
                    </div>
                  </div>
                </div>
             )}

             {/* TÍNH NĂNG */}
             {activeSection === 'tinh_nang' && (
                <div className="space-y-4 animate-in fade-in">
                  <div className="flex justify-between items-center mb-6">
                    <h4 className="text-lg font-bold text-slate-200">Danh sách các Block Tính năng</h4>
                    <button onClick={() => addArrayElement('tinh_nang', {icon: 'Check', title: 'Tính năng mới', desc: ''})} className="flex items-center gap-1 text-sm bg-primary-500/20 hover:bg-primary-500/30 text-primary-300 border border-primary-500/30 px-4 py-2 rounded-lg transition shadow-sm"><Plus className="w-4 h-4"/> Thêm ô tính năng</button>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    {draft.tinh_nang?.map((item, idx) => (
                      <div key={idx} className="bg-white/5 border border-white/10 p-5 rounded-2xl relative group focus-within:ring-1 focus-within:ring-primary-500/50">
                        <button onClick={() => removeArrayElement('tinh_nang', idx)} className="absolute top-4 right-4 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-5 h-5"/></button>
                        <div className="space-y-4 pr-6">
                          <div className="flex gap-4">
                            <div className="w-24">
                              <InputRow label="Icon" val={item.icon} onChange={v => handleArrayChange('tinh_nang', idx, 'icon', v)} />
                            </div>
                            <div className="flex-1">
                              <InputRow label="Tiêu đề" val={item.title} onChange={v => handleArrayChange('tinh_nang', idx, 'title', v)} />
                            </div>
                          </div>
                          <AreaRow label="Mô tả" val={item.desc} onChange={v => handleArrayChange('tinh_nang', idx, 'desc', v)} rows={2} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
             )}

             {/* BƯỚC SỬ DỤNG */}
             {activeSection === 'buoc_su_dung' && (
                <div className="space-y-4 animate-in fade-in">
                  <div className="flex justify-between items-center mb-6">
                    <h4 className="text-lg font-bold text-slate-200">Các Bước Thực Hiện</h4>
                    <button onClick={() => addArrayElement('buoc_su_dung', {step: draft.buoc_su_dung?.length + 1 || 1, icon: 'Circle', title: 'Bước mới', desc: ''})} className="flex items-center gap-1 text-sm bg-primary-500/20 hover:bg-primary-500/30 text-primary-300 border border-primary-500/30 px-4 py-2 rounded-lg transition shadow-sm"><Plus className="w-4 h-4"/> Thêm Bước</button>
                  </div>
                  <div className="space-y-4">
                    {draft.buoc_su_dung?.map((item, idx) => (
                      <div key={idx} className="bg-white/5 border border-white/10 p-5 rounded-2xl relative group focus-within:ring-1 focus-within:ring-primary-500/50 flex gap-5">
                        <button onClick={() => removeArrayElement('buoc_su_dung', idx)} className="absolute top-1/2 -translate-y-1/2 right-4 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-6 h-6"/></button>
                        <div className="flex-none pt-7">
                           <input type="number" value={item.step} onChange={e => handleArrayChange('buoc_su_dung', idx, 'step', Number(e.target.value))} className="w-16 h-16 rounded-full bg-slate-900 border border-white/10 text-center text-xl font-bold text-white focus:outline-none focus:border-primary-500" />
                        </div>
                        <div className="flex-1 grid grid-cols-1 gap-4 pr-10">
                          <div className="flex gap-4">
                            <div className="w-48"><InputRow label="Tên Biểu tượng (Lucide)" val={item.icon} onChange={v => handleArrayChange('buoc_su_dung', idx, 'icon', v)} /></div>
                            <div className="flex-1"><InputRow label="Tiêu đề Buớc" val={item.title} onChange={v => handleArrayChange('buoc_su_dung', idx, 'title', v)} /></div>
                          </div>
                          <AreaRow label="Nội dung diễn giải" val={item.desc} onChange={v => handleArrayChange('buoc_su_dung', idx, 'desc', v)} rows={2} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
             )}

             {/* MẪU TEMPLATE, GOI PREMIUM, FAQ omitted for brevity just mapping similarly - Wait, I'll copy my previous implementation */}
             {activeSection === 'mau_template' && (
               <div className="space-y-4 animate-in fade-in">
                 <div className="flex justify-between items-center mb-6">
                   <h4 className="text-lg font-bold text-slate-200">Danh sách Template Demo hiển thị</h4>
                   <button onClick={() => addArrayElement('mau_template', {name: 'Tên nhà xuất bản', cls: 'examle.cls'})} className="flex items-center gap-1 text-sm bg-primary-500/20 hover:bg-primary-500/30 text-primary-300 border border-primary-500/30 px-4 py-2 rounded-lg transition shadow-sm"><Plus className="w-4 h-4"/> Thêm Mẫu</button>
                 </div>
                 <div className="grid grid-cols-3 gap-4">
                   {draft.mau_template?.map((item, idx) => (
                     <div key={idx} className="bg-white/5 border border-white/10 p-5 rounded-2xl relative group focus-within:ring-1 focus-within:ring-primary-500/50">
                       <button onClick={() => removeArrayElement('mau_template', idx)} className="absolute top-2 right-2 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-4 h-4"/></button>
                       <div className="space-y-3 pt-3">
                         <InputRow label="Tên Template" val={item.name} onChange={v => handleArrayChange('mau_template', idx, 'name', v)} />
                         <InputRow label="Chuỗi định dạng" val={item.cls} onChange={v => handleArrayChange('mau_template', idx, 'cls', v)} />
                       </div>
                     </div>
                   ))}
                 </div>
               </div>
             )}

             {/* GÓI PREMIUM */}
             {activeSection === 'goi_premium' && (
                <div className="space-y-4 animate-in fade-in">
                  <div className="flex justify-between items-center mb-6">
                    <h4 className="text-lg font-bold text-slate-200">Khu vực khai báo Bảng giá (Demo)</h4>
                    <button onClick={() => addArrayElement('goi_premium', {name: 'Gói mới', days: 30, price: '100.000', badge: null})} className="flex items-center gap-1 text-sm bg-primary-500/20 hover:bg-primary-500/30 text-primary-300 border border-primary-500/30 px-4 py-2 rounded-lg transition"><Plus className="w-4 h-4"/> Thêm Gói</button>
                  </div>
                  <div className="space-y-4">
                    {draft.goi_premium?.map((item, idx) => (
                      <div key={idx} className="bg-white/5 border border-white/10 p-5 rounded-2xl relative group grid grid-cols-4 gap-4 pr-10 focus-within:ring-1 focus-within:ring-primary-500/50">
                        <button onClick={() => removeArrayElement('goi_premium', idx)} className="absolute top-1/2 -translate-y-1/2 right-4 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-5 h-5"/></button>
                        <InputRow label="Tên Gói" val={item.name} onChange={v => handleArrayChange('goi_premium', idx, 'name', v)} />
                        <InputRow label="Thời hạn (Ngày)" type="number" val={item.days} onChange={v => handleArrayChange('goi_premium', idx, 'days', Number(v))} />
                        <InputRow label="Giá hiển thị" val={item.price} onChange={v => handleArrayChange('goi_premium', idx, 'price', v)} />
                        <InputRow label="Badge (VD: Phổ biến)" val={item.badge || ''} onChange={v => handleArrayChange('goi_premium', idx, 'badge', v)} />
                      </div>
                    ))}
                  </div>
                </div>
             )}

             {/* SO_SANH */}
             {activeSection === 'so_sanh' && (
               <div className="grid grid-cols-2 gap-6 animate-in fade-in">
                  <div className="space-y-5 bg-red-500/5 border border-red-500/20 shadow-[inset_0_0_30px_rgba(239,68,68,0.02)] p-6 rounded-3xl">
                    <h4 className="text-xl font-bold text-red-400 flex items-center justify-between border-b border-red-500/20 pb-4">Cũ (Thủ công)</h4>
                    <InputRow label="Tiêu đề" val={draft.so_sanh?.truoc?.title} onChange={v => handleChange('so_sanh.truoc.title', v)} />
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Các nhược điểm (1 dòng/mục)</label>
                        <textarea 
                          className="w-full bg-slate-950 border border-white/10 p-4 rounded-xl text-sm text-white focus:border-red-500 transition outline-none"
                          rows={6}
                          value={draft.so_sanh?.truoc?.items?.join('\n')}
                          onChange={e => handleChange('so_sanh.truoc.items', e.target.value.split('\n'))}
                        />
                    </div>
                  </div>
                  <div className="space-y-5 bg-emerald-500/5 border border-emerald-500/20 shadow-[inset_0_0_30px_rgba(16,185,129,0.02)] p-6 rounded-3xl">
                    <h4 className="text-xl font-bold text-emerald-400 flex items-center justify-between border-b border-emerald-500/20 pb-4">Hiện tại (Dùng nền tảng)</h4>
                    <InputRow label="Tiêu đề" val={draft.so_sanh?.sau?.title} onChange={v => handleChange('so_sanh.sau.title', v)} />
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Lời ích mang lại (1 dòng/mục)</label>
                        <textarea 
                          className="w-full bg-slate-950 border border-white/10 p-4 rounded-xl text-sm text-white focus:border-emerald-500 transition outline-none"
                          rows={6}
                          value={draft.so_sanh?.sau?.items?.join('\n')}
                          onChange={e => handleChange('so_sanh.sau.items', e.target.value.split('\n'))}
                        />
                    </div>
                  </div>
               </div>
             )}
             
             {/* FAQ */}
             {activeSection === 'faq' && (
                <div className="space-y-4 animate-in fade-in">
                  <div className="flex justify-between items-center mb-6">
                    <h4 className="text-lg font-bold text-slate-200">Câu hỏi thường gặp (Q&A)</h4>
                    <button onClick={() => addArrayElement('faq', {q: 'Câu hỏi mới?', a: 'Trả lời'})} className="flex items-center gap-1 text-sm bg-primary-500/20 hover:bg-primary-500/30 text-primary-300 border border-primary-500/30 px-4 py-2 rounded-lg transition"><Plus className="w-4 h-4"/> Thêm FAQ</button>
                  </div>
                  {draft.faq?.map((item, idx) => (
                    <div key={idx} className="bg-white/5 border border-white/10 p-6 rounded-2xl relative group pr-8 focus-within:ring-1 focus-within:ring-primary-500/50">
                      <button onClick={() => removeArrayElement('faq', idx)} className="absolute top-1/2 -translate-y-1/2 right-4 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-5 h-5"/></button>
                      <div className="space-y-4">
                        <InputRow label="Câu Hỏi" val={item.q} onChange={v => handleArrayChange('faq', idx, 'q', v)} />
                        <AreaRow label="Câu Trả Lời (Hỗ trợ xuống dòng)" val={item.a} onChange={v => handleArrayChange('faq', idx, 'a', v)} rows={2} />
                      </div>
                    </div>
                  ))}
                </div>
             )}

             {/* CTA BOTTOM */}
             {activeSection === 'cta_bottom' && (
                <div className="p-8 bg-indigo-500/5 border border-indigo-500/20 rounded-3xl space-y-6 animate-in fade-in max-w-2xl shadow-[inset_0_0_50px_rgba(99,102,241,0.03)]">
                  <InputRow label="Tiêu đề Kêu Gọi Khép Lại" val={draft.cta_bottom?.title} onChange={v => handleChange('cta_bottom.title', v)} />
                  <AreaRow label="Mô tả Kêu Gọi" val={draft.cta_bottom?.description} onChange={v => handleChange('cta_bottom.description', v)} rows={3} />
                </div>
             )}

             {/* JSON RAW */}
             {activeSection === 'json_raw' && (
                <div className="space-y-4 animate-in fade-in flex flex-col h-full max-h-[800px]">
                  <div className="flex items-center gap-3 p-4 bg-amber-500/10 border border-amber-500/20 text-amber-200 text-sm rounded-xl">
                    <AlertTriangle className="w-6 h-6 shrink-0" />
                    <div>
                      <strong>Cảnh báo (Chế độ chuyên gia):</strong> Bạn đang trình sửa bản ghi JSON gốc lưu tại CSDL.
                      <div className="text-amber-400/80 mt-1">Cẩn thận với mã nguồn vì một lỗi phẩy nhỏ cũng có thể làm lỗi hiển thị giao diện.</div>
                    </div>
                  </div>
                  <textarea 
                    className="flex-1 w-full font-mono text-sm bg-[#0d1117] border border-white/10 p-5 rounded-2xl text-green-400 focus:border-primary-500 transition outline-none custom-scrollbar shadow-inner min-h-[500px]"
                    value={JSON.stringify(draft, null, 2)}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value);
                        setDraft(parsed);
                      } catch(e) { } // Ignore parse errors while typing
                    }}
                  />
                </div>
             )}

          </div>
        </div>
      </div>
    </div>
  );
};

// --- Helper Components ---
const InputRow = ({ label, type = "text", val, onChange }) => (
  <div>
    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">{label}</label>
    <input 
      type={type} 
      className="w-full bg-slate-950/50 border border-white/10 px-4 py-3 rounded-xl text-sm text-white focus:bg-slate-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all outline-none"
      value={val === null || val === undefined ? '' : val} 
      onChange={e => onChange(e.target.value)} 
    />
  </div>
);

const AreaRow = ({ label, val, onChange, rows=3 }) => (
  <div>
    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">{label}</label>
    <textarea 
      rows={rows}
      className="w-full bg-slate-950/50 border border-white/10 px-4 py-3 rounded-xl text-sm text-white focus:bg-slate-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all outline-none"
      value={val || ''} 
      onChange={e => onChange(e.target.value)} 
    />
  </div>
);

export default TabLandingEditor;
