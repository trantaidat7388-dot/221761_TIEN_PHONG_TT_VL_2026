import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { layNoiDungTrangPublic } from '../../services/api'
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react'

const CustomPageViewer = () => {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [page, setPage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadPage = async () => {
      setLoading(true)
      const res = await layNoiDungTrangPublic(slug)
      if (res.thanhCong && res.data) {
        setPage(res.data)
        document.title = `${res.data.title} - Word2LaTeX`
        
        // Cài đặt CSS Variables tuỳ chỉnh (nếu có)
        try {
            const vars = JSON.parse(res.data.css_variables || '{}')
            const root = document.documentElement
            Object.keys(vars).forEach(key => {
                root.style.setProperty(`--${key}`, vars[key])
            })
        } catch (e) {
            console.error("Invalid CSS Variables JSON")
        }
      } else {
        setError(res.loiMessage || 'Không thể tải nội dung trang')
      }
      setLoading(false)
    }
    if (slug) loadPage()

    // Cleanup: Remove inline styles when unmounting
    return () => {
        if (page && page.css_variables) {
            try {
                const vars = JSON.parse(page.css_variables)
                const root = document.documentElement
                Object.keys(vars).forEach(key => {
                    root.style.removeProperty(`--${key}`)
                })
            } catch(e) {}
        }
    }
  }, [slug])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (error || !page) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 p-6 text-center">
        <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h1 className="text-2xl font-bold text-white mb-2">Lỗi Tải Trang</h1>
        <p className="text-white/60 mb-6">{error || 'Trang không tồn tại.'}</p>
        <button onClick={() => navigate('/')} className="px-6 py-2 bg-primary-600 rounded-lg text-white font-medium hover:bg-primary-500 transition">
          <ArrowLeft className="w-4 h-4 inline mr-2" /> Về Tên Miền Gốc
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 pt-20 pb-12 text-white">
      <div className="max-w-4xl mx-auto px-4">
        {/* Dynamic HTML Content Injection */}
        <div 
          className="wysiwyg-content prose prose-invert prose-emerald max-w-none"
          dangerouslySetInnerHTML={{ __html: page.content_html }}
        />
      </div>
    </div>
  )
}

export default CustomPageViewer
