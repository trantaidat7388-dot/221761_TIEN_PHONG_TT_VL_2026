import { useState, useEffect, useMemo } from 'react';
import {
  Palette, Eye, EyeOff, GripVertical, Save, RotateCcw, Monitor, Smartphone,
  Type, Image, Sparkles, ChevronRight, Check, Sun, Moon, Paintbrush,
  LayoutGrid, Megaphone, HelpCircle, ArrowUpDown, Layers, Zap,
  CreditCard, BarChart, Star, Quote, X, Edit3, Globe
} from 'lucide-react';
import toast from 'react-hot-toast';
import { layNoiDungLandingAdmin, capNhatNoiDungLandingAdmin, resetNoiDungLandingAdmin } from '../../../services/api';
import { dungTheme } from '../context/AdminThemeContext';

// ── ICON MAP ──────────────────────────────────────────────────────────────────
const SECTION_META = {
  hero:         { label: 'Hero Banner',      icon: Megaphone,   color: 'from-violet-500 to-purple-600',  desc: 'Tiêu đề chính & lời kêu gọi hành động' },
  tinh_nang:    { label: 'Tính Năng',        icon: Zap,         color: 'from-blue-500 to-cyan-500',      desc: 'Danh sách tính năng nổi bật' },
  buoc_su_dung: { label: 'Hướng Dẫn',        icon: BarChart,    color: 'from-emerald-500 to-green-500',  desc: 'Quy trình sử dụng từng bước' },
  mau_template: { label: 'Template',         icon: Layers,      color: 'from-pink-500 to-rose-500',      desc: 'Mẫu LaTeX hỗ trợ' },
  goi_premium:  { label: 'Bảng Giá',         icon: CreditCard,  color: 'from-amber-500 to-yellow-500',   desc: 'Gói Premium & Token' },
  thanh_toan:   { label: 'Thanh Toán',       icon: CreditCard,  color: 'from-teal-500 to-emerald-500',   desc: 'Module thanh toán (tự động)' },
  so_sanh:      { label: 'So Sánh',          icon: ArrowUpDown, color: 'from-orange-500 to-red-500',     desc: 'Trước/Sau khi dùng' },
  faq:          { label: 'FAQ',              icon: HelpCircle,  color: 'from-cyan-500 to-blue-500',      desc: 'Câu hỏi thường gặp' },
  cta_bottom:   { label: 'Kêu Gọi Cuối',    icon: Star,        color: 'from-indigo-500 to-violet-500',  desc: 'Nút đăng ký cuối trang' },
};

const THEMES_DATA = [
  { id: 'dark-indigo',    name: 'Dark Indigo',    bg: '#0f172a', accent: '#6366f1', light: false },
  { id: 'midnight-cyan',  name: 'Midnight Cyan',  bg: '#000000', accent: '#22d3ee', light: false },
  { id: 'warm-slate',     name: 'Warm Slate',     bg: '#1c1917', accent: '#f59e0b', light: false },
  { id: 'light-pro',      name: 'Light Pro',      bg: '#f8fafc', accent: '#2563eb', light: true },
];

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MAIN COMPONENT
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const TabQuanTriGiaoDien = () => {
  const { theme, doiTheme } = dungTheme();

  // Landing content state
  const [content, setContent] = useState(null);
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // UI state
  const [editingSection, setEditingSection] = useState(null);
  const [previewMode, setPreviewMode] = useState('desktop'); // desktop | mobile
  const [draggedIdx, setDraggedIdx] = useState(null);

  // Disabled sections (local toggle for visibility)
  const [disabledSections, setDisabledSections] = useState(new Set());

  // ── DATA LOADING ──────────────────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      setLoading(true);
      const res = await layNoiDungLandingAdmin();
      if (res.thanhCong) {
        setContent(res.content);
        setDraft(res.content);
      } else {
        toast.error('Lỗi tải dữ liệu: ' + res.loiMessage);
      }
      setLoading(false);
    })();
  }, []);

  const isDirty = useMemo(() => JSON.stringify(content) !== JSON.stringify(draft), [content, draft]);

  // ── HANDLERS ──────────────────────────────────────────────────────────────
  const xuLyLuu = async () => {
    setSaving(true);
    const res = await capNhatNoiDungLandingAdmin(draft);
    if (res.thanhCong) {
      toast.success('Đã xuất bản giao diện thành công!');
      setContent(res.content);
      setDraft(res.content);
    } else toast.error('Lỗi: ' + res.loiMessage);
    setSaving(false);
  };

  const xuLyReset = async () => {
    if (!window.confirm('Khôi phục về giao diện mặc định? Mọi tuỳ chỉnh sẽ bị xoá.')) return;
    setSaving(true);
    const res = await resetNoiDungLandingAdmin();
    if (res.thanhCong) {
      toast.success('Đã khôi phục thành công!');
      setContent(res.content);
      setDraft(res.content);
      setEditingSection(null);
    } else toast.error('Lỗi: ' + res.loiMessage);
    setSaving(false);
  };

  const updateField = (path, value) => {
    setDraft(prev => {
      const d = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let cur = d;
      for (let i = 0; i < keys.length - 1; i++) {
        if (!cur[keys[i]]) cur[keys[i]] = {};
        cur = cur[keys[i]];
      }
      cur[keys[keys.length - 1]] = value;
      return d;
    });
  };

  const updateArray = (arrayPath, index, field, value) => {
    setDraft(prev => {
      const d = JSON.parse(JSON.stringify(prev));
      if (field) d[arrayPath][index][field] = value;
      else d[arrayPath][index] = value;
      return d;
    });
  };

  const addToArray = (arrayPath, obj) => {
    setDraft(prev => {
      const d = JSON.parse(JSON.stringify(prev));
      if (!d[arrayPath]) d[arrayPath] = [];
      d[arrayPath].push(obj);
      return d;
    });
  };

  const removeFromArray = (arrayPath, index) => {
    setDraft(prev => {
      const d = JSON.parse(JSON.stringify(prev));
      d[arrayPath].splice(index, 1);
      return d;
    });
  };

  const toggleSection = (secId) => {
    setDisabledSections(prev => {
      const next = new Set(prev);
      next.has(secId) ? next.delete(secId) : next.add(secId);
      return next;
    });
  };

  // ── DRAG & DROP ───────────────────────────────────────────────────────────
  const onDragStart = (e, idx) => { setDraggedIdx(idx); e.dataTransfer.effectAllowed = 'move'; };
  const onDragOver = (e) => e.preventDefault();
  const onDrop = (e, dropIdx) => {
    e.preventDefault();
    if (draggedIdx === null || draggedIdx === dropIdx) return;
    const newOrder = [...(draft.section_order || [])];
    const [moved] = newOrder.splice(draggedIdx, 1);
    newOrder.splice(dropIdx, 0, moved);
    updateField('section_order', newOrder);
    setDraggedIdx(null);
  };

  // ── LOADING / ERROR ───────────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-400 text-sm">Đang tải Quản trị giao diện...</p>
      </div>
    </div>
  );
  if (!draft) return <div className="p-10 text-center text-red-400">Không thể kết nối đến hệ thống nội dung</div>;

  const sections = draft.section_order || [];

  return (
    <div className="space-y-6">

      {/* ── TOP BAR ─────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-white flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-primary-500 to-violet-600">
              <Paintbrush className="w-6 h-6 text-white" />
            </div>
            Quản Trị Giao Diện
          </h2>
          <p className="text-sm text-slate-400 mt-1">Tuỳ chỉnh giao diện Landing Page, quản lý bố cục, màu sắc và nội dung.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-white/5 rounded-lg p-0.5 border border-white/5">
            <button onClick={() => setPreviewMode('desktop')} className={`p-2 rounded-md transition ${previewMode === 'desktop' ? 'bg-primary-600 text-white' : 'text-white/40 hover:text-white'}`}>
              <Monitor className="w-4 h-4" />
            </button>
            <button onClick={() => setPreviewMode('mobile')} className={`p-2 rounded-md transition ${previewMode === 'mobile' ? 'bg-primary-600 text-white' : 'text-white/40 hover:text-white'}`}>
              <Smartphone className="w-4 h-4" />
            </button>
          </div>
          <button onClick={xuLyReset} disabled={saving} className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-white/70 hover:bg-white/10 text-sm font-medium transition disabled:opacity-50">
            <RotateCcw className="w-4 h-4" /> Khôi phục
          </button>
          <button onClick={xuLyLuu} disabled={saving || !isDirty} className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-bold transition shadow-lg ${isDirty ? 'bg-primary-600 hover:bg-primary-500 text-white shadow-primary-500/25' : 'bg-white/5 text-white/30 shadow-none cursor-not-allowed'}`}>
            <Save className="w-4 h-4" />
            {saving ? 'Đang lưu...' : isDirty ? 'Xuất bản thay đổi' : 'Đã đồng bộ'}
          </button>
        </div>
      </div>

      {/* ── MAIN GRID ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-12 gap-6">

        {/* ─── LEFT: CONTROLS ─────────────────────────────────────── (5 cols) */}
        <div className="col-span-12 xl:col-span-5 space-y-5">

          {/* THEME CARDS */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
              <Palette className="w-4 h-4 text-primary-400" /> Chọn Theme Hệ Thống
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {THEMES_DATA.map(t => (
                <button
                  key={t.id}
                  onClick={() => doiTheme(t.id)}
                  className={`relative rounded-xl border p-3 transition-all duration-300 text-left group ${
                    theme === t.id
                      ? 'border-primary-400 bg-primary-500/10 ring-2 ring-primary-500/30 shadow-lg shadow-primary-500/10'
                      : 'border-white/10 bg-white/[0.02] hover:bg-white/5 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="flex gap-1.5">
                      <div className="w-5 h-5 rounded-full border border-white/20 shadow-inner" style={{ backgroundColor: t.bg }} />
                      <div className="w-5 h-5 rounded-full border border-white/20 shadow-inner" style={{ backgroundColor: t.accent }} />
                    </div>
                    {theme === t.id && (
                      <div className="ml-auto w-5 h-5 rounded-full bg-primary-500 flex items-center justify-center">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                    )}
                  </div>
                  <p className={`text-xs font-semibold ${theme === t.id ? 'text-white' : 'text-white/60'}`}>{t.name}</p>
                  <div className="flex items-center gap-1 mt-1">
                    {t.light ? <Sun className="w-3 h-3 text-amber-400" /> : <Moon className="w-3 h-3 text-indigo-400" />}
                    <span className="text-[10px] text-white/30">{t.light ? 'Sáng' : 'Tối'}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* SECTION MANAGER */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1 flex items-center gap-2">
              <LayoutGrid className="w-4 h-4 text-primary-400" /> Quản lý bố cục
            </h3>
            <p className="text-xs text-slate-500 mb-4">Kéo thả để sắp xếp. Bật/tắt hiển thị từng khối.</p>

            <div className="space-y-2">
              {sections.map((secId, idx) => {
                const meta = SECTION_META[secId] || { label: secId, icon: Layers, color: 'from-slate-500 to-slate-600', desc: '' };
                const Icon = meta.icon;
                const isDisabled = disabledSections.has(secId);
                const isEditing = editingSection === secId;
                const isDragging = draggedIdx === idx;

                return (
                  <div
                    key={secId}
                    draggable
                    onDragStart={(e) => onDragStart(e, idx)}
                    onDragOver={onDragOver}
                    onDrop={(e) => onDrop(e, idx)}
                    className={`group flex items-center gap-3 p-3 rounded-xl border transition-all duration-200 ${
                      isDragging ? 'opacity-30 scale-95' :
                      isEditing ? 'border-primary-500 bg-primary-500/10 shadow-lg shadow-primary-500/10' :
                      isDisabled ? 'border-white/5 bg-white/[0.01] opacity-50' :
                      'border-white/5 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/10'
                    }`}
                  >
                    {/* Drag Handle */}
                    <div className="cursor-grab active:cursor-grabbing text-slate-600 group-hover:text-slate-400 touch-none">
                      <GripVertical className="w-4 h-4" />
                    </div>

                    {/* Icon */}
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${meta.color} flex items-center justify-center shrink-0 shadow-sm`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>

                    {/* Label */}
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-semibold truncate ${isDisabled ? 'text-white/30' : 'text-white/90'}`}>{meta.label}</p>
                      <p className="text-[10px] text-slate-500 truncate">{meta.desc}</p>
                    </div>

                    {/* Toggle */}
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleSection(secId); }}
                      className={`p-1.5 rounded-lg transition ${isDisabled ? 'text-slate-600 hover:text-slate-400' : 'text-emerald-400 hover:text-emerald-300'}`}
                      title={isDisabled ? 'Hiển thị' : 'Ẩn'}
                    >
                      {isDisabled ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>

                    {/* Edit */}
                    <button
                      onClick={() => setEditingSection(isEditing ? null : secId)}
                      className={`p-1.5 rounded-lg transition ${isEditing ? 'bg-primary-500 text-white' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ─── RIGHT: EDITOR / PREVIEW ──────────────────────────── (7 cols) */}
        <div className="col-span-12 xl:col-span-7">
          {editingSection ? (
            <SectionEditor
              sectionId={editingSection}
              draft={draft}
              updateField={updateField}
              updateArray={updateArray}
              addToArray={addToArray}
              removeFromArray={removeFromArray}
              onClose={() => setEditingSection(null)}
            />
          ) : (
            <LandingPreview draft={draft} previewMode={previewMode} disabledSections={disabledSections} />
          )}
        </div>
      </div>
    </div>
  );
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// SECTION EDITOR - Full-featured form editor for each section
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const SectionEditor = ({ sectionId, draft, updateField, updateArray, addToArray, removeFromArray, onClose }) => {
  const meta = SECTION_META[sectionId] || { label: sectionId, icon: Layers, color: 'from-slate-500 to-slate-600', desc: '' };
  const Icon = meta.icon;

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
      {/* Editor Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${meta.color} flex items-center justify-center shadow-lg`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{meta.label}</h3>
            <p className="text-xs text-slate-400">{meta.desc}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 rounded-lg text-slate-500 hover:bg-white/5 hover:text-white transition">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Editor Body */}
      <div className="p-6 max-h-[70vh] overflow-y-auto custom-scrollbar space-y-5">
        {sectionId === 'hero' && <HeroEditor draft={draft} updateField={updateField} />}
        {sectionId === 'tinh_nang' && <ArrayEditor draft={draft} arrayKey="tinh_nang" fields={[{key:'icon',label:'Icon',w:'w-24'},{key:'title',label:'Tiêu đề'},{key:'desc',label:'Mô tả',type:'area'}]} defaultItem={{icon:'Check',title:'Tính năng mới',desc:''}} updateArray={updateArray} addToArray={addToArray} removeFromArray={removeFromArray} />}
        {sectionId === 'buoc_su_dung' && <ArrayEditor draft={draft} arrayKey="buoc_su_dung" fields={[{key:'step',label:'Bước',type:'number',w:'w-16'},{key:'icon',label:'Icon',w:'w-24'},{key:'title',label:'Tiêu đề'},{key:'desc',label:'Mô tả',type:'area'}]} defaultItem={{step:(draft.buoc_su_dung?.length||0)+1,icon:'Circle',title:'Bước mới',desc:''}} updateArray={updateArray} addToArray={addToArray} removeFromArray={removeFromArray} />}
        {sectionId === 'mau_template' && <ArrayEditor draft={draft} arrayKey="mau_template" fields={[{key:'name',label:'Tên Template'},{key:'cls',label:'Định dạng (.cls)'}]} defaultItem={{name:'Nhà xuất bản',cls:'example.cls'}} updateArray={updateArray} addToArray={addToArray} removeFromArray={removeFromArray} cols={3} />}
        {sectionId === 'goi_premium' && <ArrayEditor draft={draft} arrayKey="goi_premium" fields={[{key:'name',label:'Tên Gói'},{key:'days',label:'Ngày',type:'number',w:'w-20'},{key:'price',label:'Giá'},{key:'badge',label:'Badge'}]} defaultItem={{name:'Gói mới',days:30,price:'100.000',badge:''}} updateArray={updateArray} addToArray={addToArray} removeFromArray={removeFromArray} />}
        {sectionId === 'thanh_toan' && <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm"><Zap className="w-5 h-5 shrink-0" /> Module thanh toán được hệ thống tự động tạo. Bạn chỉ có thể thay đổi vị trí hiển thị bằng cách kéo thả ở bảng bố cục.</div>}
        {sectionId === 'so_sanh' && <CompareEditor draft={draft} updateField={updateField} />}
        {sectionId === 'faq' && <ArrayEditor draft={draft} arrayKey="faq" fields={[{key:'q',label:'Câu Hỏi'},{key:'a',label:'Câu Trả Lời',type:'area'}]} defaultItem={{q:'Câu hỏi mới?',a:'Trả lời...'}} updateArray={updateArray} addToArray={addToArray} removeFromArray={removeFromArray} />}
        {sectionId === 'cta_bottom' && <CTAEditor draft={draft} updateField={updateField} />}
      </div>
    </div>
  );
};

// ── HERO EDITOR ─────────────────────────────────────────────────────────────
const HeroEditor = ({ draft, updateField }) => (
  <div className="space-y-4">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Field label="Nhãn (Badge)" value={draft.hero?.badge} onChange={v => updateField('hero.badge', v)} placeholder="VD: #1 Nền tảng" />
      <Field label="Nút chính (CTA)" value={draft.hero?.cta_primary} onChange={v => updateField('hero.cta_primary', v)} placeholder="VD: Bắt đầu miễn phí" />
    </div>
    <Field label="Tiêu đề chính" value={draft.hero?.title} onChange={v => updateField('hero.title', v)} placeholder="Tiêu đề lớn..." />
    <Field label="Phần in đậm (highlight)" value={draft.hero?.title_highlight} onChange={v => updateField('hero.title_highlight', v)} placeholder="Từ khoá nổi bật" />
    <Field label="Mô tả" value={draft.hero?.description} onChange={v => updateField('hero.description', v)} type="area" rows={3} placeholder="Giới thiệu ngắn gọn..." />
    <Field label="Nút phụ (CTA)" value={draft.hero?.cta_secondary} onChange={v => updateField('hero.cta_secondary', v)} placeholder="VD: Xem hướng dẫn" />
  </div>
);

// ── COMPARE EDITOR ──────────────────────────────────────────────────────────
const CompareEditor = ({ draft, updateField }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
    <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-5 space-y-4">
      <h4 className="text-base font-bold text-red-400">❌ Trước (Thủ công)</h4>
      <Field label="Tiêu đề" value={draft.so_sanh?.truoc?.title} onChange={v => updateField('so_sanh.truoc.title', v)} />
      <Field label="Nhược điểm (mỗi dòng 1 mục)" value={draft.so_sanh?.truoc?.items?.join('\n')} onChange={v => updateField('so_sanh.truoc.items', v.split('\n'))} type="area" rows={5} />
    </div>
    <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 space-y-4">
      <h4 className="text-base font-bold text-emerald-400">✅ Sau (Nền tảng)</h4>
      <Field label="Tiêu đề" value={draft.so_sanh?.sau?.title} onChange={v => updateField('so_sanh.sau.title', v)} />
      <Field label="Ưu điểm (mỗi dòng 1 mục)" value={draft.so_sanh?.sau?.items?.join('\n')} onChange={v => updateField('so_sanh.sau.items', v.split('\n'))} type="area" rows={5} />
    </div>
  </div>
);

// ── CTA EDITOR ──────────────────────────────────────────────────────────────
const CTAEditor = ({ draft, updateField }) => (
  <div className="space-y-4 max-w-xl">
    <Field label="Tiêu đề Kêu Gọi" value={draft.cta_bottom?.title} onChange={v => updateField('cta_bottom.title', v)} placeholder="Bắt đầu ngay hôm nay!" />
    <Field label="Mô tả" value={draft.cta_bottom?.description} onChange={v => updateField('cta_bottom.description', v)} type="area" rows={3} />
  </div>
);

// ── GENERIC ARRAY EDITOR ────────────────────────────────────────────────────
const ArrayEditor = ({ draft, arrayKey, fields, defaultItem, updateArray, addToArray, removeFromArray, cols = 1 }) => {
  const items = draft[arrayKey] || [];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-400">{items.length} mục</p>
        <button
          onClick={() => addToArray(arrayKey, defaultItem)}
          className="flex items-center gap-1.5 text-xs bg-primary-500/15 hover:bg-primary-500/25 text-primary-300 border border-primary-500/20 px-3 py-1.5 rounded-lg transition font-medium"
        >
          + Thêm mới
        </button>
      </div>

      <div className={`grid gap-3 ${cols === 3 ? 'grid-cols-1 md:grid-cols-3' : cols === 2 ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
        {items.map((item, idx) => (
          <div key={idx} className="relative group rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:border-white/10 transition">
            <button
              onClick={() => removeFromArray(arrayKey, idx)}
              className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-red-500/80 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100 shadow-lg"
            >
              <X className="w-3 h-3" />
            </button>
            <div className="space-y-3">
              {fields.map(f => (
                <div key={f.key} className={f.w || ''}>
                  <Field
                    label={f.label}
                    value={item[f.key]}
                    onChange={v => updateArray(arrayKey, idx, f.key, f.type === 'number' ? Number(v) : v)}
                    type={f.type || 'text'}
                    rows={f.rows}
                    small
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// LANDING PREVIEW (Mini visual preview)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const LandingPreview = ({ draft, previewMode, disabledSections }) => {
  const sections = (draft.section_order || []).filter(s => !disabledSections.has(s));

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 bg-white/[0.02]">
        <div className="flex items-center gap-2.5">
          <Globe className="w-4 h-4 text-primary-400" />
          <span className="text-sm font-semibold text-white">Xem trước Landing Page</span>
        </div>
        <span className="text-[10px] text-white/30 uppercase font-bold tracking-widest">{previewMode}</span>
      </div>

      <div className={`overflow-y-auto bg-[#0a0c10] transition-all duration-500 ${
        previewMode === 'mobile' ? 'max-w-[375px] mx-auto rounded-b-2xl' : 'w-full'
      }`} style={{ height: '70vh' }}>
        <div className="p-4 space-y-3">
          {sections.map(secId => {
            const meta = SECTION_META[secId] || { label: secId, icon: Layers, color: 'from-slate-500 to-slate-600' };
            const Icon = meta.icon;
            return (
              <PreviewBlock key={secId} secId={secId} meta={meta} Icon={Icon} draft={draft} previewMode={previewMode} />
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ── PREVIEW BLOCK ───────────────────────────────────────────────────────────
const PreviewBlock = ({ secId, meta, Icon, draft, previewMode }) => {
  const isMobile = previewMode === 'mobile';

  if (secId === 'hero') {
    return (
      <div className="rounded-xl bg-gradient-to-br from-primary-600/20 via-violet-600/10 to-transparent border border-primary-500/10 p-6 text-center">
        {draft.hero?.badge && <span className="inline-block px-2 py-0.5 rounded-full bg-primary-500/20 text-primary-300 text-[10px] font-bold mb-3">{draft.hero.badge}</span>}
        <h2 className={`font-black text-white mb-2 leading-tight ${isMobile ? 'text-lg' : 'text-2xl'}`}>
          {draft.hero?.title || 'Tiêu đề'} <span className="text-primary-400">{draft.hero?.title_highlight || ''}</span>
        </h2>
        <p className={`text-white/50 mb-4 ${isMobile ? 'text-xs' : 'text-sm'}`}>{draft.hero?.description || 'Mô tả...'}</p>
        <div className="flex gap-2 justify-center flex-wrap">
          {draft.hero?.cta_primary && <span className="px-3 py-1.5 rounded-lg bg-primary-600 text-white text-xs font-bold">{draft.hero.cta_primary}</span>}
          {draft.hero?.cta_secondary && <span className="px-3 py-1.5 rounded-lg border border-white/20 text-white/70 text-xs">{draft.hero.cta_secondary}</span>}
        </div>
      </div>
    );
  }

  if (secId === 'tinh_nang') {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <p className="text-xs font-bold text-white/60 uppercase mb-3">Tính năng</p>
        <div className={`grid gap-2 ${isMobile ? 'grid-cols-1' : 'grid-cols-2'}`}>
          {(draft.tinh_nang || []).slice(0, 4).map((f, i) => (
            <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-white/[0.03]">
              <div className="w-6 h-6 rounded-md bg-blue-500/20 flex items-center justify-center shrink-0"><Zap className="w-3 h-3 text-blue-400" /></div>
              <div><p className="text-xs font-semibold text-white/80">{f.title}</p><p className="text-[10px] text-white/30 line-clamp-1">{f.desc}</p></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (secId === 'goi_premium') {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <p className="text-xs font-bold text-white/60 uppercase mb-3">Bảng giá</p>
        <div className={`grid gap-2 ${isMobile ? 'grid-cols-1' : 'grid-cols-3'}`}>
          {(draft.goi_premium || []).slice(0, 3).map((g, i) => (
            <div key={i} className="p-3 rounded-lg bg-white/[0.03] border border-white/5 text-center">
              <p className="text-xs font-bold text-white/80">{g.name}</p>
              <p className="text-sm font-black text-primary-400 mt-1">{g.price}₫</p>
              <p className="text-[10px] text-white/30">{g.days} ngày</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (secId === 'faq') {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <p className="text-xs font-bold text-white/60 uppercase mb-3">FAQ</p>
        <div className="space-y-1.5">
          {(draft.faq || []).slice(0, 3).map((f, i) => (
            <div key={i} className="p-2 rounded-lg bg-white/[0.03]">
              <p className="text-xs font-semibold text-white/70">{f.q}</p>
              <p className="text-[10px] text-white/30 line-clamp-1 mt-0.5">{f.a}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Default section block
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex items-center gap-3">
      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${meta.color} flex items-center justify-center`}>
        <Icon className="w-4 h-4 text-white" />
      </div>
      <div>
        <p className="text-xs font-semibold text-white/70">{meta.label}</p>
        <p className="text-[10px] text-white/30">{meta.desc}</p>
      </div>
    </div>
  );
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// FIELD COMPONENT (Modern input)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const Field = ({ label, value, onChange, type = 'text', rows = 3, placeholder = '', small = false }) => {
  const baseClass = `w-full bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder:text-white/20 focus:bg-white/[0.05] focus:border-primary-500 focus:ring-2 focus:ring-primary-500/15 transition-all outline-none ${
    small ? 'px-3 py-2 text-xs' : 'px-4 py-2.5 text-sm'
  }`;

  return (
    <div>
      <label className={`block font-semibold text-slate-400 uppercase tracking-widest mb-1.5 ${small ? 'text-[9px]' : 'text-[10px]'}`}>{label}</label>
      {type === 'area' ? (
        <textarea rows={rows} className={baseClass} value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder} />
      ) : (
        <input type={type} className={baseClass} value={value === null || value === undefined ? '' : value} onChange={e => onChange(e.target.value)} placeholder={placeholder} />
      )}
    </div>
  );
};

export default TabQuanTriGiaoDien;
