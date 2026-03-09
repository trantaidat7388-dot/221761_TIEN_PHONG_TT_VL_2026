// TrangChuyenDoi.jsx - Trang chính chuyển đổi Word sang LaTeX (Split-pane + SSE)

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Download,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Zap,
  Clock,
  FileCode,
  Image,
  Eye,
  Copy,
  Upload,
  Trash2,
  Settings,
  Terminal,
  ChevronRight,
  Table2
} from 'lucide-react'
import toast from 'react-hot-toast'
import KhuVucKeoTha from './KhuVucKeoTha'
import { NutBam } from '../../components'
import { chuyenDoiFileStream, taiFileZip, layDanhSachTemplate, taiLenTemplate, xoaTemplate } from '../../services/api'

// --- Sub-components ---

/** Real-time SSE progress bar with step indicator */
const ThanhTienTrinh = ({ tienTrinh, thongBao, buocHienTai, tongBuoc }) => (
  <div className="space-y-3">
    <div className="flex items-center justify-between text-sm">
      <span className="text-white/70 flex items-center gap-2">
        <motion.div
          className="w-2 h-2 rounded-full bg-primary-400"
          animate={{ scale: [1, 1.4, 1], opacity: [1, 0.5, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
        {thongBao || 'Đang xử lý...'}
      </span>
      <span className="text-primary-400 font-mono text-xs">
        {buocHienTai}/{tongBuoc} &middot; {Math.round(tienTrinh)}%
      </span>
    </div>
    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
      <motion.div
        className="h-full bg-gradient-to-r from-primary-600 via-primary-400 to-purple-400 rounded-full"
        initial={{ width: 0 }}
        animate={{ width: `${tienTrinh}%` }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      />
    </div>
  </div>
)

/** Visual LaTeX Debugger card - supports both legacy (loai_loi) and SSE (errorType+details) formats */
const BoGiLoi = ({ error }) => {
  // Normalize SSE error format → display fields
  const loaiLoi = error.loai_loi || error.errorType || 'UNKNOWN'
  const details = error.details || error
  const dong = details.dong ?? error.dong ?? null
  const thongDiep = details.thong_diep ?? error.thong_diep ?? error.loiMessage ?? 'Lỗi không xác định'
  const nguCanh = details.ngu_canh ?? error.ngu_canh ?? ''

  return (
    <div className="text-left w-full bg-[#1e1e1e] rounded-xl border border-red-500/30 overflow-hidden shadow-2xl">
      <div className="flex items-center justify-between px-4 py-2.5 bg-black/40 border-b border-white/5">
        <span className="text-red-400 font-mono text-xs uppercase tracking-wider flex items-center gap-2">
          <Terminal className="w-4 h-4" />
          LaTeX Compilation Error
        </span>
        {dong && <span className="text-white/40 text-xs font-mono">Line {dong}</span>}
      </div>
      <div className="p-4 space-y-3">
        <p className="text-red-300 font-semibold text-sm">{thongDiep}</p>
        {(nguCanh || dong) && (
          <div className="bg-black/50 p-3 rounded-lg border border-white/5 font-mono text-xs overflow-x-auto">
            <div className="text-white/40">...</div>
            {dong && (
              <div className="text-white/50">
                <span className="text-white/30 mr-3 select-none">{dong - 1} |</span>
                &nbsp;
              </div>
            )}
            <div className="bg-red-500/20 -mx-3 px-3 py-1 border-l-2 border-red-500 text-red-100 flex items-start">
              {dong && <span className="text-white/30 mr-3 select-none shrink-0">{dong} |</span>}
              <span className="break-all">{nguCanh || thongDiep}</span>
            </div>
            {dong && (
              <div className="text-white/50">
                <span className="text-white/30 mr-3 select-none">{dong + 1} |</span>
                ...
              </div>
            )}
          </div>
        )}
        <p className="text-white/50 text-xs italic">
          Mẹo: Lỗi <strong className="text-white/60">{loaiLoi}</strong> thường do file Template không chuẩn, hoặc có ký tự đặc biệt như $, &amp;, %, # chưa được escape trong Word.
        </p>
      </div>
    </div>
  )
}

// --- Main Component ---

const TrangChuyenDoi = ({ nguoiDung }) => {
  // State
  const [fileChon, setFileChon] = useState(null)
  const [loiValidation, setLoiValidation] = useState(null)
  const [trangThaiXuLy, setTrangThaiXuLy] = useState('cho') // 'cho' | 'dang_xu_ly' | 'hoan_thanh' | 'loi'
  const [error, setError] = useState(null)
  const [tienTrinh, setTienTrinh] = useState(0)
  const [buocHienTai, setBuocHienTai] = useState(0)
  const [ketQuaChuyenDoi, setKetQuaChuyenDoi] = useState(null)
  const [thongBaoTienTrinh, setThongBaoTienTrinh] = useState('')
  const [loaiTemplate, setLoaiTemplate] = useState('ieee_conference')
  const [texContent, setTexContent] = useState('')
  const [jobId, setJobId] = useState('')
  const [hienThiMaLatex, setHienThiMaLatex] = useState(false)
  const [danhSachTemplate, setDanhSachTemplate] = useState([])
  const [hienThiQuanLyTemplate, setHienThiQuanLyTemplate] = useState(false)
  const [dangTaiTemplate, setDangTaiTemplate] = useState(false)
  const templateInputRef = useRef(null)

  const TONG_BUOC = 6

  // --- Helpers ---

  const luuLichSuChuyenDoi = async (user, file, jobIdMoi) => {
    if (!user?.uid || !file?.name) return
    try {
      await themLichSuChuyenDoi({
        uid: user.uid,
        tenFileGoc: file.name,
        trangThai: 'Thành công',
        job_id: jobIdMoi || '',
        templateName: loaiTemplate
      })
    } catch {
      // silent — zip still downloadable
    }
  }

  const xuLyCopyMa = async () => {
    try {
      if (!texContent) throw new Error('Không có mã để copy')
      await navigator.clipboard.writeText(texContent)
      toast.success('Đã copy mã LaTeX')
    } catch (loi) {
      toast.error(loi.message || 'Không thể copy')
    }
  }

  const xuLyChonFile = (file, loi) => {
    if (loi) {
      setLoiValidation(loi)
      setFileChon(null)
      return
    }
    setFileChon(file)
    setLoiValidation(null)
    setTrangThaiXuLy('cho')
    setKetQuaChuyenDoi(null)
    setError(null)
    setTexContent('')
    setJobId('')
  }

  // --- Template management ---

  useEffect(() => {
    const taiTemplates = async () => {
      const kq = await layDanhSachTemplate()
      if (kq.thanhCong) setDanhSachTemplate(kq.templates)
    }
    taiTemplates()
  }, [])

  const xuLyTaiLenTemplate = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setDangTaiTemplate(true)
    try {
      const kq = await taiLenTemplate(file)
      if (kq.thanhCong) {
        toast.success(kq.message || 'Đã tải lên template')
        // Refresh danh sách template từ backend NGAY LẬP TỨC
        const dsKq = await layDanhSachTemplate()
        if (dsKq.thanhCong) setDanhSachTemplate(dsKq.templates)
        // Auto-select template mới (guard undefined)
        if (kq.template?.id) setLoaiTemplate(kq.template.id)
      } else {
        toast.error(kq.loiMessage || 'Lỗi tải lên template')
      }
    } catch {
      toast.error('Lỗi tải lên template')
    } finally {
      setDangTaiTemplate(false)
      if (templateInputRef.current) templateInputRef.current.value = ''
    }
  }

  const xuLyXoaTemplate = async (templateId) => {
    const kq = await xoaTemplate(templateId)
    if (kq.thanhCong) {
      toast.success('Đã xóa template')
      if (loaiTemplate === templateId) setLoaiTemplate('ieee_conference')
      const dsKq = await layDanhSachTemplate()
      if (dsKq.thanhCong) setDanhSachTemplate(dsKq.templates)
    } else {
      toast.error(kq.loiMessage || 'Lỗi xóa template')
    }
  }

  // --- Core conversion (SSE) ---

  const xuLyChuyenDoi = async () => {
    if (!fileChon) {
      toast.error('Vui lòng chọn file trước')
      return
    }

    setTrangThaiXuLy('dang_xu_ly')
    setError(null)
    setTienTrinh(0)
    setBuocHienTai(0)
    setThongBaoTienTrinh('Đang kết nối...')
    setKetQuaChuyenDoi(null)
    setTexContent('')
    setJobId('')
    setHienThiMaLatex(false)

    const ketQuaAPI = await chuyenDoiFileStream(
      fileChon,
      loaiTemplate,
      (step, msg) => {
        setBuocHienTai(step)
        setThongBaoTienTrinh(msg)
        setTienTrinh(Math.round((step / TONG_BUOC) * 100))
      }
    )

    if (ketQuaAPI.thanhCong) {
      const apiData = ketQuaAPI.data || {}
      const metadata = apiData.metadata || {}
      setTexContent(apiData.texContent || '')
      setJobId(apiData.jobId || '')
      setKetQuaChuyenDoi({
        jobId: apiData.jobId || '',
        tenFileZip: apiData.tenFileZip || '',
        tenFileLatex: apiData.tenFileLatex || '',
        thoiGianXuLy: `${metadata.thoi_gian_xu_ly_giay ?? 0}s`,
        soTrang: metadata.so_trang ?? '—',
        soCongThuc: metadata.so_cong_thuc ?? 0,
        soHinhAnh: metadata.so_hinh_anh ?? 0,
        soBang: metadata.so_bang ?? 0
      })
      setTrangThaiXuLy('hoan_thanh')
      setTienTrinh(100)
      setBuocHienTai(TONG_BUOC)
      setThongBaoTienTrinh('Hoàn tất!')
      toast.success('Chuyển đổi thành công!')

      const userHienTai = nguoiDung
      await luuLichSuChuyenDoi(userHienTai, fileChon, apiData.jobId || '')
    } else {
      setTrangThaiXuLy('loi')
      // Build error object for Visual Debugger
      if (ketQuaAPI.errorDetails || ketQuaAPI.errorType) {
        setError({
          errorType: ketQuaAPI.errorType,
          details: ketQuaAPI.errorDetails,
          loiMessage: ketQuaAPI.loiMessage,
        })
      } else {
        setError(ketQuaAPI.loiMessage || 'Đã xảy ra lỗi khi chuyển đổi')
      }
      toast.error(ketQuaAPI.loiMessage || 'Lỗi chuyển đổi')
    }
  }

  const xuLyTaiVe = async () => {
    try {
      toast.loading('Đang tải xuống...', { id: 'download' })
      const kq = await taiFileZip(jobId || ketQuaChuyenDoi?.jobId, ketQuaChuyenDoi?.tenFileZip || '')
      if (!kq.thanhCong) throw new Error(kq.loiMessage || 'Không thể tải file')
      toast.success('Tải file thành công!', { id: 'download' })
    } catch (loi) {
      toast.error(loi.message || 'Không thể tải file', { id: 'download' })
    }
  }

  const xuLyChuyenDoiMoi = () => {
    setFileChon(null)
    setTrangThaiXuLy('cho')
    setError(null)
    setTienTrinh(0)
    setBuocHienTai(0)
    setKetQuaChuyenDoi(null)
    setThongBaoTienTrinh('')
    setTexContent('')
    setJobId('')
    setHienThiMaLatex(false)
    setLoiValidation(null)
  }

  const xuLyXoaFile = () => {
    xuLyChuyenDoiMoi()
  }

  // --- Animation variants ---
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.08 } }
  }
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100 } }
  }

  // Helpers for template rendering
  const templateMacDinh = danhSachTemplate.filter(t => t.loai !== 'tuy_chinh')
  const templateTuyChinh = danhSachTemplate.filter(t => t.loai === 'tuy_chinh')

  // Check if we have a structured error (for Visual Debugger)
  const isStructuredError = error && typeof error === 'object' && (error.loai_loi || error.errorType || error.details)

  return (
    <div className="min-h-screen bg-gradient-animated pt-20 pb-12 px-4">
      <motion.div
        className="max-w-7xl mx-auto"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Header */}
        <motion.div className="text-center mb-6" variants={itemVariants}>
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/20 text-primary-300 text-sm mb-3"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <Sparkles className="w-4 h-4" />
            Hỗ trợ OMML &amp; OLE Equation &middot; Real-time SSE
          </motion.div>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
            Chuyển đổi Word sang LaTeX
          </h1>
          <p className="text-white/60 max-w-xl mx-auto text-sm">
            Upload file .docx / .docm và nhận file LaTeX (.tex) chuẩn học thuật
          </p>
        </motion.div>

        {/* ===== SPLIT-PANE LAYOUT ===== */}
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-5 gap-6"
          variants={itemVariants}
        >
          {/* === LEFT PANEL: Config (2/5 on lg) === */}
          <div className="lg:col-span-2 space-y-4">
            {/* Dropzone */}
            <KhuVucKeoTha
              onChonFile={xuLyChonFile}
              fileHienTai={fileChon}
              onXoaFile={xuLyXoaFile}
              loiValidation={loiValidation}
              dangTaiLen={trangThaiXuLy === 'dang_xu_ly'}
            />

            {/* Template Selector */}
            <div className="glass-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-white/70 text-sm font-medium">Template LaTeX</span>
                <button
                  onClick={() => setHienThiQuanLyTemplate(!hienThiQuanLyTemplate)}
                  className="flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
                >
                  <Settings className="w-3.5 h-3.5" />
                  Quản lý
                </button>
              </div>

              {/* All template buttons (default + custom) */}
              <div className="flex flex-wrap gap-2">
                {/* Hardcoded defaults (always available even if API hasn't responded) */}
                {templateMacDinh.length === 0 && (
                  <>
                    <button
                      onClick={() => setLoaiTemplate('ieee_conference')}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all duration-200 text-xs ${loaiTemplate === 'ieee_conference'
                        ? 'bg-primary-500/30 border-primary-500 text-primary-300'
                        : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10'}`}
                    >
                      <FileCode className="w-3.5 h-3.5" />
                      IEEE Conference
                    </button>
                    <button
                      onClick={() => setLoaiTemplate('springer_lncs')}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all duration-200 text-xs ${loaiTemplate === 'springer_lncs'
                        ? 'bg-primary-500/30 border-primary-500 text-primary-300'
                        : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10'}`}
                    >
                      <FileCode className="w-3.5 h-3.5" />
                      Springer LNCS
                    </button>
                  </>
                )}
                {/* Dynamic from API */}
                {templateMacDinh.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setLoaiTemplate(t.id)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all duration-200 text-xs ${loaiTemplate === t.id
                      ? 'bg-primary-500/30 border-primary-500 text-primary-300'
                      : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10'}`}
                  >
                    <FileCode className="w-3.5 h-3.5" />
                    {t.ten}
                  </button>
                ))}
                {templateTuyChinh.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setLoaiTemplate(t.id)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all duration-200 text-xs ${loaiTemplate === t.id
                      ? 'bg-purple-500/30 border-purple-500 text-purple-300'
                      : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10'}`}
                  >
                    <FileCode className="w-3.5 h-3.5" />
                    {t.ten}
                  </button>
                ))}
              </div>

              {/* Template management panel */}
              <AnimatePresence>
                {hienThiQuanLyTemplate && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="border-t border-white/10 pt-3 mt-1 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <input
                          ref={templateInputRef}
                          type="file"
                          accept=".tex,.zip,application/zip,application/x-zip-compressed"
                          onChange={xuLyTaiLenTemplate}
                          className="hidden"
                          id="template-upload"
                        />
                        <button
                          onClick={() => templateInputRef.current?.click()}
                          disabled={dangTaiTemplate}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary-500/20 border border-primary-500/30 text-primary-300 text-xs hover:bg-primary-500/30 transition-all disabled:opacity-50"
                        >
                          <Upload className="w-3.5 h-3.5" />
                          {dangTaiTemplate ? 'Đang tải...' : 'Tải lên (.tex / .zip)'}
                        </button>
                        <span className="text-white/40 text-xs">
                          .tex có \documentclass hoặc .zip đầy đủ
                        </span>
                      </div>
                      {templateTuyChinh.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-white/40 text-xs">Tùy chỉnh:</p>
                          {templateTuyChinh.map(t => (
                            <div key={t.id} className="flex items-center justify-between px-3 py-1.5 rounded bg-white/5">
                              <span className="text-white/70 text-xs truncate">{t.ten} ({(t.kichThuoc / 1024).toFixed(1)}KB)</span>
                              <button
                                onClick={() => xuLyXoaTemplate(t.id)}
                                className="text-red-400/60 hover:text-red-400 transition-colors ml-2"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Convert Button */}
            <NutBam
              onClick={xuLyChuyenDoi}
              icon={Zap}
              kichThuoc="lg"
              className="w-full"
              disabled={!fileChon || trangThaiXuLy === 'dang_xu_ly'}
              dangTai={trangThaiXuLy === 'dang_xu_ly'}
            >
              {trangThaiXuLy === 'dang_xu_ly' ? 'Đang chuyển đổi...' : 'Bắt đầu chuyển đổi'}
            </NutBam>

            {/* Feature badges */}
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                { icon: FileText, label: 'OMML' },
                { icon: Zap, label: 'OLE Eq.' },
                { icon: CheckCircle2, label: 'IEEE/ACM' },
              ].map((f, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 text-white/50 text-xs">
                  <f.icon className="w-3 h-3 text-primary-400" />
                  {f.label}
                </span>
              ))}
            </div>
          </div>

          {/* === RIGHT PANEL: Results (3/5 on lg) === */}
          <div className="lg:col-span-3">
            <AnimatePresence mode="wait">
              {/* Placeholder khi chưa có gì */}
              {trangThaiXuLy === 'cho' && !ketQuaChuyenDoi && (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="glass-card p-12 flex flex-col items-center justify-center text-center min-h-[400px]"
                >
                  <div className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
                    <FileCode className="w-10 h-10 text-white/20" />
                  </div>
                  <h3 className="text-white/40 font-medium mb-2">Kết quả hiển thị tại đây</h3>
                  <p className="text-white/30 text-sm max-w-sm">
                    Chọn file Word và nhấn &ldquo;Bắt đầu chuyển đổi&rdquo; để xem tiến trình real-time và kết quả LaTeX.
                  </p>
                </motion.div>
              )}

              {/* Đang xử lý: Progress bar */}
              {trangThaiXuLy === 'dang_xu_ly' && (
                <motion.div
                  key="processing"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="glass-card p-6 space-y-6 min-h-[400px] flex flex-col justify-center"
                >
                  <div className="text-center">
                    <motion.div
                      className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-500/20 mb-4"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                    >
                      <FileText className="w-8 h-8 text-primary-400" />
                    </motion.div>
                    <h3 className="text-white font-medium mb-1">Đang chuyển đổi</h3>
                    <p className="text-white/50 text-sm">{fileChon?.name}</p>
                  </div>
                  <ThanhTienTrinh
                    tienTrinh={tienTrinh}
                    thongBao={thongBaoTienTrinh}
                    buocHienTai={buocHienTai}
                    tongBuoc={TONG_BUOC}
                  />
                  {/* Step log */}
                  <div className="space-y-1">
                    {Array.from({ length: buocHienTai }, (_, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center gap-2 text-xs text-white/40"
                      >
                        <CheckCircle2 className="w-3 h-3 text-green-400/70" />
                        <span>Bước {i + 1} hoàn thành</span>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Hoàn thành */}
              {trangThaiXuLy === 'hoan_thanh' && ketQuaChuyenDoi && (
                <motion.div
                  key="completed"
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.97 }}
                  className="space-y-4"
                >
                  {/* Success header */}
                  <div className="glass-card p-6">
                    <div className="flex items-center gap-4 mb-5">
                      <motion.div
                        className="w-14 h-14 rounded-xl bg-green-500/20 flex items-center justify-center shrink-0"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', delay: 0.1 }}
                      >
                        <CheckCircle2 className="w-7 h-7 text-green-400" />
                      </motion.div>
                      <div>
                        <h2 className="text-xl font-bold text-white">Chuyển đổi thành công!</h2>
                        <p className="text-white/50 text-sm">File LaTeX đã sẵn sàng</p>
                      </div>
                    </div>

                    {/* Stats grid */}
                    <div className="grid grid-cols-5 gap-3 mb-5">
                      {[
                        { icon: FileCode, value: ketQuaChuyenDoi.soTrang, label: 'Trang', color: 'text-primary-400' },
                        { icon: FileText, value: ketQuaChuyenDoi.soCongThuc, label: 'Công thức', color: 'text-purple-400' },
                        { icon: Table2, value: ketQuaChuyenDoi.soBang, label: 'Bảng', color: 'text-orange-400' },
                        { icon: Image, value: ketQuaChuyenDoi.soHinhAnh, label: 'Hình ảnh', color: 'text-green-400' },
                        { icon: Clock, value: ketQuaChuyenDoi.thoiGianXuLy, label: 'Thời gian', color: 'text-blue-400' },
                      ].map((s, i) => (
                        <div key={i} className="text-center p-3 rounded-xl bg-white/5">
                          <s.icon className={`w-5 h-5 ${s.color} mx-auto mb-1`} />
                          <p className="text-lg font-bold text-white">{s.value}</p>
                          <p className="text-white/50 text-xs">{s.label}</p>
                        </div>
                      ))}
                    </div>

                    {/* File info */}
                    <div className="bg-white/5 rounded-xl p-3 mb-5">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
                          <FileText className="w-5 h-5 text-primary-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-white font-medium text-sm truncate">{ketQuaChuyenDoi.tenFileZip || 'output.zip'}</p>
                          <p className="text-white/50 text-xs">
                            {ketQuaChuyenDoi.tenFileLatex || 'output.tex'} + PDF + images/
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col sm:flex-row gap-2">
                      <NutBam onClick={xuLyTaiVe} icon={Download} className="flex-1" kichThuoc="md">
                        Tải xuống (.zip)
                      </NutBam>
                      <NutBam onClick={() => setHienThiMaLatex(!hienThiMaLatex)} bienThe="secondary" icon={Eye} className="flex-1" kichThuoc="md">
                        {hienThiMaLatex ? 'Ẩn mã LaTeX' : 'Xem mã LaTeX'}
                      </NutBam>
                      <NutBam onClick={xuLyChuyenDoiMoi} bienThe="secondary" icon={RefreshCw} className="flex-1" kichThuoc="md">
                        File khác
                      </NutBam>
                    </div>
                  </div>

                  {/* Inline LaTeX code viewer */}
                  <AnimatePresence>
                    {hienThiMaLatex && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="glass-card p-0 overflow-hidden">
                          <div className="flex items-center justify-between px-4 py-2.5 bg-white/5 border-b border-white/10">
                            <span className="text-white/70 text-sm font-medium flex items-center gap-2">
                              <Terminal className="w-4 h-4 text-primary-400" />
                              Mã LaTeX
                            </span>
                            <button
                              onClick={xuLyCopyMa}
                              className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-primary-500/20 border border-primary-500/30 text-primary-300 text-xs hover:bg-primary-500/30 transition-all"
                            >
                              <Copy className="w-3 h-3" />
                              Copy
                            </button>
                          </div>
                          <pre className="p-4 text-green-300 font-mono text-xs overflow-auto max-h-[60vh] whitespace-pre-wrap">
                            <code>{texContent || 'Không có nội dung LaTeX'}</code>
                          </pre>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}

              {/* Lỗi */}
              {trangThaiXuLy === 'loi' && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.97 }}
                  className="glass-card p-6 space-y-5"
                >
                  <div className="flex items-center gap-4">
                    <motion.div
                      className="w-14 h-14 rounded-xl bg-red-500/20 flex items-center justify-center shrink-0"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                    >
                      <AlertCircle className="w-7 h-7 text-red-400" />
                    </motion.div>
                    <div>
                      <h2 className="text-xl font-bold text-white">Chuyển đổi thất bại</h2>
                      <p className="text-white/50 text-sm">Kiểm tra chi tiết lỗi bên dưới</p>
                    </div>
                  </div>

                  {/* Visual Debugger or plain error */}
                  {isStructuredError ? (
                    <BoGiLoi error={error} />
                  ) : (
                    <p className="text-red-300/80 bg-red-500/10 p-4 rounded-lg break-words text-sm border border-red-500/20">
                      {typeof error === 'string' ? error : 'Không thể chuyển đổi file. Vui lòng thử lại.'}
                    </p>
                  )}

                  <NutBam onClick={xuLyChuyenDoiMoi} icon={RefreshCw}>
                    Thử lại
                  </NutBam>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default TrangChuyenDoi
