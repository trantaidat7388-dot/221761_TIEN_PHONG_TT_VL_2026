import { useState, useEffect } from 'react';
import { Layout, Save, RotateCcw, AlertTriangle, Plus, Trash2, ChevronRight, FileJson } from 'lucide-react';
import toast from 'react-hot-toast';
import { layNoiDungLandingAdmin, capNhatNoiDungLandingAdmin, resetNoiDungLandingAdmin } from '../../../services/api';
import { NutBam } from '../../../components';

const SECTION_LABELS = {
  hero: 'Hero & CTA',
  tinh_nang: 'Tính năng',
  buoc_su_dung: 'Bước sử dụng',
  mau_template: 'Mẫu Template',
  goi_premium: 'Gói Premium',
  faq: 'FAQ',
  so_sanh: 'So sánh (Trước/Sau)',
  cta_bottom: 'CTA Cuối trang',
  json_raw: 'Chỉnh sửa JSON'
};

const TabLandingEditor = () => {
  const [content, setContent] = useState(null);
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeSection, setActiveSection] = useState('hero');

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
      toast.success('Đã lưu nội dung Landing Page!');
      setContent(res.content);
      setDraft(res.content);
    } else {
      toast.error('Lỗi khi lưu: ' + res.loiMessage);
    }
    setSaving(false);
  };

  const xuLyReset = async () => {
    if (!window.confirm('Bạn có chắc muốn khôi phục về nội dung mặc định? Mọi thay đổi sẽ bị mất.')) return;
    setSaving(true);
    const res = await resetNoiDungLandingAdmin();
    if (res.thanhCong) {
      toast.success('Đã khôi phục nội dung mặc định!');
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
      // Sometimes field is undefined if we're directly replacing the array item (like strings)
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

  if (loading) return <div className="p-10 text-center text-slate-400">Đang tải dữ liệu...</div>;
  if (!draft) return <div className="p-10 text-center text-red-400">Không thể tải dữ liệu</div>;

  const isDirty = JSON.stringify(content) !== JSON.stringify(draft);

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 shadow-sm space-y-4">
      {/* HEADER */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h3 className="mb-1 text-xl font-bold text-white flex items-center gap-2">
            <Layout className="h-6 w-6 text-purple-400" /> Quản lý Nội dung Landing
          </h3>
          <p className="text-sm text-slate-400">Sửa nội dung và text trực tiếp trên landing page.</p>
        </div>
        <div className="flex gap-3">
          <NutBam onClick={xuLyReset} bienThe="secondary" icon={RotateCcw} dangTai={saving}>Khôi phục</NutBam>
          <NutBam onClick={xuLyLuu} icon={Save} dangTai={saving} disabled={!isDirty}>
            {isDirty ? 'Lưu thay đổi' : 'Đã lưu'}
          </NutBam>
        </div>
      </div>

      <div className="flex gap-6 h-[calc(100vh-250px)] min-h-[500px]">
        {/* SIDEBAR TABS */}
        <div className="w-[15rem] shrink-0 flex flex-col gap-1 overflow-y-auto pr-2 border-r border-white/5">
          {Object.keys(SECTION_LABELS).map(key => (
            <button
              key={key}
              onClick={() => setActiveSection(key)}
              className={`text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                activeSection === key 
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
                  : 'text-slate-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  {key === 'json_raw' && <FileJson className="w-4 h-4" />}
                  {SECTION_LABELS[key]}
                </span>
                {activeSection === key && <ChevronRight className="w-4 h-4" />}
              </div>
            </button>
          ))}
        </div>

        {/* EDITOR AREA */}
        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar pb-10">
          
          {/* HERO SECTION */}
          {activeSection === 'hero' && (
            <div className="space-y-5 animate-in fade-in">
              <h4 className="text-lg font-bold text-white mb-4">Phần mở đầu (Hero)</h4>
              <InputRow label="Badge (Nhãn nổ bật)" val={draft.hero?.badge} onChange={v => handleChange('hero.badge', v)} />
              <InputRow label="Tiêu đề chính" val={draft.hero?.title} onChange={v => handleChange('hero.title', v)} />
              <InputRow label="Tiêu đề làm nổi bật (Highlight)" val={draft.hero?.title_highlight} onChange={v => handleChange('hero.title_highlight', v)} />
              <AreaRow label="Mô tả" val={draft.hero?.description} onChange={v => handleChange('hero.description', v)} rows={3} />
              <div className="grid grid-cols-2 gap-4">
                <InputRow label="Nút hành động chính" val={draft.hero?.cta_primary} onChange={v => handleChange('hero.cta_primary', v)} />
                <InputRow label="Nút hành động phụ" val={draft.hero?.cta_secondary} onChange={v => handleChange('hero.cta_secondary', v)} />
              </div>
            </div>
          )}

          {/* TÍNH NĂNG */}
          {activeSection === 'tinh_nang' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-bold text-white">Danh sách tính năng</h4>
                <button onClick={() => addArrayElement('tinh_nang', {icon: 'Settings', title: 'Tính năng mới', desc: 'Mô tả'})} className="flex items-center gap-1 text-sm bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded-lg transition"><Plus className="w-4 h-4"/> Thêm tính năng</button>
              </div>
              {draft.tinh_nang?.map((item, idx) => (
                <div key={idx} className="bg-slate-900/50 border border-white/10 p-4 rounded-xl relative group">
                  <button onClick={() => removeArrayElement('tinh_nang', idx)} className="absolute top-4 right-4 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-5 h-5"/></button>
                  <div className="grid grid-cols-12 gap-4 pr-8">
                    <div className="col-span-3">
                      <InputRow label="Icon (Lucide)" val={item.icon} onChange={v => handleArrayChange('tinh_nang', idx, 'icon', v)} />
                    </div>
                    <div className="col-span-9">
                      <InputRow label="Tiêu đề" val={item.title} onChange={v => handleArrayChange('tinh_nang', idx, 'title', v)} />
                    </div>
                    <div className="col-span-12">
                      <AreaRow label="Mô tả chi tiết" val={item.desc} onChange={v => handleArrayChange('tinh_nang', idx, 'desc', v)} rows={2} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* BƯỚC SỬ DỤNG */}
          {activeSection === 'buoc_su_dung' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-bold text-white">Hướng dẫn sử dụng</h4>
                <button onClick={() => addArrayElement('buoc_su_dung', {step: draft.buoc_su_dung?.length + 1 || 1, icon: 'Circle', title: 'Bước mới', desc: ''})} className="flex items-center gap-1 text-sm bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded-lg transition"><Plus className="w-4 h-4"/> Thêm bước</button>
              </div>
              {draft.buoc_su_dung?.map((item, idx) => (
                <div key={idx} className="bg-slate-900/50 border border-white/10 p-4 rounded-xl relative group">
                  <button onClick={() => removeArrayElement('buoc_su_dung', idx)} className="absolute top-4 right-4 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-5 h-5"/></button>
                  <div className="grid grid-cols-12 gap-4 pr-8">
                    <div className="col-span-2">
                       <InputRow label="S.TT" type="number" val={item.step} onChange={v => handleArrayChange('buoc_su_dung', idx, 'step', Number(v))} />
                    </div>
                    <div className="col-span-3">
                      <InputRow label="Icon" val={item.icon} onChange={v => handleArrayChange('buoc_su_dung', idx, 'icon', v)} />
                    </div>
                    <div className="col-span-7">
                      <InputRow label="Tiêu đề" val={item.title} onChange={v => handleArrayChange('buoc_su_dung', idx, 'title', v)} />
                    </div>
                    <div className="col-span-12">
                      <AreaRow label="Mô tả" val={item.desc} onChange={v => handleArrayChange('buoc_su_dung', idx, 'desc', v)} rows={2} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* MẪU TEMPLATE */}
          {activeSection === 'mau_template' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-bold text-white">Mẫu Template nổi bật</h4>
                <p className="text-sm text-slate-400 ml-4 flex-1">Danh sách này chỉ để hiển thị trên Landing page.</p>
                <button onClick={() => addArrayElement('mau_template', {name: 'Tên nhà xuất bản', cls: 'examle.cls'})} className="flex items-center gap-1 text-sm bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded-lg transition"><Plus className="w-4 h-4"/> Thêm mẫu</button>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {draft.mau_template?.map((item, idx) => (
                  <div key={idx} className="bg-slate-900/50 border border-white/10 p-4 rounded-xl relative group flex flex-col gap-2">
                    <button onClick={() => removeArrayElement('mau_template', idx)} className="absolute top-2 right-2 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-4 h-4"/></button>
                    <InputRow label="Tên nhà xuất bản" val={item.name} onChange={v => handleArrayChange('mau_template', idx, 'name', v)} />
                    <InputRow label="File Class (.cls)" val={item.cls} onChange={v => handleArrayChange('mau_template', idx, 'cls', v)} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* GÓI PREMIUM */}
          {activeSection === 'goi_premium' && (
             <div className="space-y-4 animate-in fade-in">
             <div className="flex justify-between items-center mb-4">
               <h4 className="text-lg font-bold text-white">Các gói Premium</h4>
               <button onClick={() => addArrayElement('goi_premium', {name: 'Gói mới', days: 30, price: '100.000', badge: null})} className="flex items-center gap-1 text-sm bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded-lg transition"><Plus className="w-4 h-4"/> Thêm gói</button>
             </div>
             <div className="grid grid-cols-1 gap-4">
               {draft.goi_premium?.map((item, idx) => (
                 <div key={idx} className="bg-slate-900/50 border border-white/10 p-4 rounded-xl relative group grid grid-cols-4 gap-4 pr-10">
                   <button onClick={() => removeArrayElement('goi_premium', idx)} className="absolute top-4 right-4 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-5 h-5"/></button>
                   <InputRow label="Tên gói" val={item.name} onChange={v => handleArrayChange('goi_premium', idx, 'name', v)} />
                   <InputRow label="Số ngày hạn" type="number" val={item.days} onChange={v => handleArrayChange('goi_premium', idx, 'days', Number(v))} />
                   <InputRow label="Giá hiển thị (VD: 50.000)" val={item.price} onChange={v => handleArrayChange('goi_premium', idx, 'price', v)} />
                   <InputRow label="Nhãn nổi bật (Badge)" val={item.badge || ''} onChange={v => handleArrayChange('goi_premium', idx, 'badge', v)} />
                 </div>
               ))}
             </div>
           </div>
          )}

          {/* FAQ */}
          {activeSection === 'faq' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-bold text-white">Câu hỏi thường gặp (FAQ)</h4>
                <button onClick={() => addArrayElement('faq', {q: 'Câu hỏi mới?', a: 'Trả lời'})} className="flex items-center gap-1 text-sm bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded-lg transition"><Plus className="w-4 h-4"/> Thêm FAQ</button>
              </div>
              {draft.faq?.map((item, idx) => (
                <div key={idx} className="bg-slate-900/50 border border-white/10 p-4 rounded-xl relative group pr-8">
                  <button onClick={() => removeArrayElement('faq', idx)} className="absolute top-4 right-4 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition"><Trash2 className="w-5 h-5"/></button>
                  <div className="space-y-3">
                    <InputRow label="Câu hỏi" val={item.q} onChange={v => handleArrayChange('faq', idx, 'q', v)} />
                    <AreaRow label="Câu trả lời" val={item.a} onChange={v => handleArrayChange('faq', idx, 'a', v)} rows={2} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* SO_SANH */}
          {activeSection === 'so_sanh' && (
            <div className="grid grid-cols-2 gap-6 animate-in fade-in">
               <div className="space-y-4 bg-red-500/5 border border-red-500/10 p-5 rounded-xl">
                 <h4 className="text-lg font-bold text-red-400 mb-2">Trạng thái Trước (Thủ công)</h4>
                 <InputRow label="Tiêu đề cột trước" val={draft.so_sanh?.truoc?.title} onChange={v => handleChange('so_sanh.truoc.title', v)} />
                 <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Các vấn đề (1 dòng = 1 mục)</label>
                    <textarea 
                      className="w-full bg-slate-950 border border-white/10 p-3 rounded-lg text-sm text-white focus:border-purple-500 transition outline-none"
                      rows={5}
                      value={draft.so_sanh?.truoc?.items?.join('\n')}
                      onChange={e => handleChange('so_sanh.truoc.items', e.target.value.split('\n'))}
                    />
                 </div>
               </div>
               <div className="space-y-4 bg-emerald-500/5 border border-emerald-500/10 p-5 rounded-xl">
                 <h4 className="text-lg font-bold text-emerald-400 mb-2">Trạng thái Sau (Word2LaTeX)</h4>
                 <InputRow label="Tiêu đề cột sau" val={draft.so_sanh?.sau?.title} onChange={v => handleChange('so_sanh.sau.title', v)} />
                 <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Lợi ích mang lại (1 dòng = 1 mục)</label>
                    <textarea 
                      className="w-full bg-slate-950 border border-white/10 p-3 rounded-lg text-sm text-white focus:border-purple-500 transition outline-none"
                      rows={5}
                      value={draft.so_sanh?.sau?.items?.join('\n')}
                      onChange={e => handleChange('so_sanh.sau.items', e.target.value.split('\n'))}
                    />
                 </div>
               </div>
            </div>
          )}

          {/* CTA BOTTOM */}
          {activeSection === 'cta_bottom' && (
            <div className="space-y-5 animate-in fade-in max-w-2xl">
              <h4 className="text-lg font-bold text-white mb-4">Màn hình kêu gọi cuối trang</h4>
              <InputRow label="Tiêu đề" val={draft.cta_bottom?.title} onChange={v => handleChange('cta_bottom.title', v)} />
              <AreaRow label="Mô tả" val={draft.cta_bottom?.description} onChange={v => handleChange('cta_bottom.description', v)} rows={3} />
            </div>
          )}

          {/* JSON RAW */}
          {activeSection === 'json_raw' && (
            <div className="space-y-4 animate-in fade-in h-full flex flex-col">
              <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/20 text-amber-200 text-sm rounded-lg">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <span><strong>Chế độ nâng cao:</strong> Chỉnh sửa toàn bộ dữ liệu cấu hình Landing page dưới dạng JSON. Cẩn thận tránh lỗi cú pháp.</span>
              </div>
              <textarea 
                className="flex-1 w-full font-mono text-sm bg-slate-950 border border-white/10 p-4 rounded-xl text-green-400 focus:border-purple-500 transition outline-none custom-scrollbar"
                value={JSON.stringify(draft, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    setDraft(parsed);
                  } catch(e) {
                    // Ignore parse errors while typing
                  }
                }}
              />
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

// --- Helper Components ---
const InputRow = ({ label, type = "text", val, onChange }) => (
  <div>
    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">{label}</label>
    <input 
      type={type} 
      className="w-full bg-slate-950/50 border border-white/10 p-2.5 rounded-lg text-sm text-white focus:border-purple-500 transition outline-none"
      value={val === null || val === undefined ? '' : val} 
      onChange={e => onChange(e.target.value)} 
    />
  </div>
);

const AreaRow = ({ label, val, onChange, rows=3 }) => (
  <div>
    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">{label}</label>
    <textarea 
      rows={rows}
      className="w-full bg-slate-950/50 border border-white/10 p-2.5 rounded-lg text-sm text-white focus:border-purple-500 transition outline-none"
      value={val || ''} 
      onChange={e => onChange(e.target.value)} 
    />
  </div>
);

export default TabLandingEditor;
