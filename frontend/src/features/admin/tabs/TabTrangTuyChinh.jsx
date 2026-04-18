import { useState, useEffect } from 'react'
import { Plus, Trash2, Edit, Save, X, Globe, EyeOff, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import { layDanhSachTrangAdmin, taoTrangAdmin, capNhatTrangAdmin, xoaTrangAdmin } from '../../../services/api'
import { NutBam } from '../../../components'

const TabTrangTuyChinh = () => {
  const [pages, setPages] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingPage, setEditingPage] = useState(null)
  
  // Form State
  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [contentHtml, setContentHtml] = useState('')
  const [cssVariables, setCssVariables] = useState('{}')
  const [isPublished, setIsPublished] = useState(false)

  const loadThemePages = async () => {
    setLoading(true)
    const res = await layDanhSachTrangAdmin()
    if (res.thanhCong) {
      setPages(res.danhSach)
    } else {
      toast.error(res.loiMessage || 'Không thể tải danh sách trang')
    }
    setLoading(false)
  }

  useEffect(() => {
    loadThemePages()
  }, [])

  const resetForm = () => {
    setEditingPage(null)
    setSlug('')
    setTitle('')
    setContentHtml('')
    setCssVariables('{\n  "primary-500": "#10b981",\n  "bg-color": "#020617"\n}')
    setIsPublished(false)
  }

  const handleCreateOrEdit = async () => {
    if (!slug || !title) {
        toast.error('Slug và Title là bắt buộc')
        return
    }

    // Validate Json
    try {
        JSON.parse(cssVariables)
    } catch {
        toast.error('Cấu hình CSS Variables phải là JSON hợp lệ')
        return
    }

    const payload = {
        title,
        content_html: contentHtml,
        css_variables: cssVariables,
        is_published: isPublished
    }

    if (editingPage) {
        // Edit
        const res = await capNhatTrangAdmin(slug, payload)
        if (res.thanhCong) {
            toast.success('Đã cập nhật trang')
            resetForm()
            loadThemePages()
        } else toast.error(res.loiMessage || 'Lỗi cập nhật')
    } else {
        // Create
        payload.slug = slug
        const res = await taoTrangAdmin(payload)
        if (res.thanhCong) {
            toast.success('Đã tạo trang mới')
            resetForm()
            loadThemePages()
        } else toast.error(res.loiMessage || 'Lỗi tạo trang')
    }
  }

  const handleDelete = async (slugToDelete) => {
    if (!window.confirm(`Bạn có chắc muốn xóa trang ${slugToDelete}?`)) return
    const res = await xoaTrangAdmin(slugToDelete)
    if (res.thanhCong) {
        toast.success('Đã xóa')
        loadThemePages()
    } else {
        toast.error(res.loiMessage || 'Lỗi xóa trang')
    }
  }

  const startEdit = (page) => {
      setEditingPage(page)
      setSlug(page.slug)
      setTitle(page.title)
      setContentHtml(page.content_html || '')
      setCssVariables(page.css_variables || '{}')
      setIsPublished(page.is_published || false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Quản lý Trang (CMS/Page Builder)</h2>
          <p className="text-white/50 text-sm">Tạo các trang phụ động với HTML tự do.</p>
        </div>
        {!editingPage && (
          <NutBam onClick={() => setEditingPage('NEW')} icon={Plus}>
            Thêm Trang Mới
          </NutBam>
        )}
      </div>

      {editingPage ? (
          <div className="glass-card p-6 border border-primary-500/30">
              <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-bold text-white">
                      {editingPage === 'NEW' ? 'Tạo Trang Mới' : `Sửa Trang: ${slug}`}
                  </h3>
                  <button onClick={resetForm} className="text-white/40 hover:text-white"><X className="w-5 h-5"/></button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-white/50 mb-1">Đường dẫn URL (Slug)</label>
                        <input 
                            readOnly={editingPage !== 'NEW'}
                            className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-white text-sm outline-none focus:border-primary-500 disabled:opacity-50"
                            placeholder="vd: huong-dan-su-dung"
                            value={slug}
                            onChange={(e) => setSlug(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-white/50 mb-1">Tiêu đề (Title)</label>
                        <input 
                            className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-white text-sm outline-none focus:border-primary-500"
                            placeholder="vd: Hướng dẫn sử dụng"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-3 bg-slate-900/50 p-3 rounded-xl border border-white/5">
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" checked={isPublished} onChange={(e) => setIsPublished(e.target.checked)} />
                            <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                        </label>
                        <span className="text-sm font-medium text-white">Công khai (Publish)</span>
                    </div>
                </div>

                <div>
                    <label className="block text-xs font-medium text-white/50 mb-1">Cấu hình CSS Variables (JSON)</label>
                    <textarea 
                        className="w-full h-32 font-mono bg-slate-900 border border-white/10 rounded-lg p-2 text-white text-sm outline-none focus:border-primary-500"
                        value={cssVariables}
                        onChange={(e) => setCssVariables(e.target.value)}
                    />
                </div>
              </div>

              <div className="mb-6">
                  <label className="flex justify-between items-end mb-1">
                      <span className="text-xs font-medium text-white/50">Nội dung HTML (Tailwind Classes allowed)</span>
                      <a href="https://play.tailwindcss.com/" target="_blank" rel="noreferrer" className="text-xs text-primary-400 hover:underline flex items-center gap-1">
                          Thử nghiệm UI <ExternalLink className="w-3 h-3"/>
                      </a>
                  </label>
                  <textarea 
                        className="w-full h-80 font-mono bg-slate-900 border border-white/10 rounded-lg p-3 text-white text-sm outline-none focus:border-primary-500"
                        placeholder="<div><h1>Nội dung</h1></div>"
                        value={contentHtml}
                        onChange={(e) => setContentHtml(e.target.value)}
                  />
              </div>

              <div className="flex justify-end gap-3">
                  <NutBam onClick={resetForm} bienThe="secondary">Hủy</NutBam>
                  <NutBam onClick={handleCreateOrEdit} icon={Save}>Lưu Cài Đặt</NutBam>
              </div>
          </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-white/10 glass-card">
            <table className="w-full text-left text-sm text-white/70">
            <thead className="bg-white/5 text-xs text-white/40 uppercase">
                <tr>
                <th className="px-6 py-4 font-medium">Slug / Tiêu đề</th>
                <th className="px-6 py-4 font-medium text-center">Trạng Thái</th>
                <th className="px-6 py-4 font-medium text-right">Thao Tác</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
                {pages.length === 0 && !loading && (
                    <tr><td colSpan="3" className="px-6 py-8 text-center text-white/30 italic">Chưa có trang nào</td></tr>
                )}
                {pages.map((p) => (
                <tr key={p.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-6 py-4">
                        <div className="flex flex-col">
                            <span className="font-bold text-white flex items-center gap-2">
                                {p.title}
                                <a href={`/p/${p.slug}`} target="_blank" rel="noreferrer" className="text-primary-400 hover:text-primary-300">
                                    <ExternalLink className="w-3 h-3" />
                                </a>
                            </span>
                            <span className="text-xs text-white/40 font-mono">/p/{p.slug}</span>
                        </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                        {p.is_published ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs">
                                <Globe className="w-3.5 h-3.5" /> Public
                            </span>
                        ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 text-white/40 text-xs">
                                <EyeOff className="w-3.5 h-3.5" /> Bản nháp
                            </span>
                        )}
                    </td>
                    <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2">
                            <button onClick={() => startEdit(p)} className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-primary-400 transition" title="Sửa">
                                <Edit className="w-4 h-4" />
                            </button>
                            <button onClick={() => handleDelete(p.slug)} className="p-2 bg-red-500/10 hover:bg-red-500/20 rounded-lg text-red-400 transition" title="Xóa">
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    </td>
                </tr>
                ))}
            </tbody>
            </table>
        </div>
      )}
    </div>
  )
}

export default TabTrangTuyChinh
