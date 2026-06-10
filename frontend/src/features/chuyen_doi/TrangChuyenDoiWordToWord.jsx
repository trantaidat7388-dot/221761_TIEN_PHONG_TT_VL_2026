import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRightLeft, Download, FileCheck2, Sparkles, AlertCircle, FileText, Repeat, FileDown, Loader2, CheckCircle2, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import KhuVucKeoTha from './KhuVucKeoTha'
import { NutBam } from '../../components'
import { chuyenDoiWordIEEE, chuyenDoiWordSpringer, taiFileWordTheoJob, bienDichPDFTuWordJob, taiFilePDF } from '../../services/api'
import { dungXacThuc } from '../../context/AuthContext'

const CHE_DO = {
  SPRINGER_TO_IEEE: 'springer-to-ieee',
  IEEE_TO_SPRINGER: 'ieee-to-springer'
}

const TrangChuyenDoiWordToWord = () => {
  const { lamMoiThongTinNguoiDung } = dungXacThuc()
  const [cheDo, setCheDo] = useState(CHE_DO.SPRINGER_TO_IEEE)
  const [fileNguon, setFileNguon] = useState(null)
  const [suDungTemplateRieng, setSuDungTemplateRieng] = useState(false)
  const [fileTemplate, setFileTemplate] = useState(null)
  const [loiValidationNguon, setLoiValidationNguon] = useState(null)
  const [loiValidationTemplate, setLoiValidationTemplate] = useState(null)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [loi, setLoi] = useState('')
  const [ketQua, setKetQua] = useState(null)
  const [dangBienDichPDF, setDangBienDichPDF] = useState(false)
  const [ketQuaPDF, setKetQuaPDF] = useState(null) // { soTrang, tenFilePDF, pdfUrl }

  const laSpringerToIEEE = cheDo === CHE_DO.SPRINGER_TO_IEEE

  const metadataRows = useMemo(() => {
    if (!ketQua?.metadata) return []
    const md = ketQua.metadata
    const rows = [
      { nhan: 'Sections', giaTri: md.so_section ?? 0 },
      { nhan: 'Paragraphs', giaTri: md.so_paragraph ?? 0 },
      { nhan: 'Tables', giaTri: md.so_bang ?? 0 },
      { nhan: 'References', giaTri: md.so_tai_lieu_tham_khao ?? 0 },
    ]

    if (laSpringerToIEEE && md.bao_cao_dinh_dang_ieee) {
      const qr = md.bao_cao_dinh_dang_ieee
      rows.push(
        { nhan: 'Tables Full-Width', giaTri: qr.table_span_full_width ?? 0 },
        { nhan: 'Tables Landscape', giaTri: qr.table_span_landscape ?? 0 },
        { nhan: 'Normalized Table Captions', giaTri: qr.table_caption_normalized ?? 0 },
        { nhan: 'Normalized Figure Captions', giaTri: qr.figure_caption_normalized ?? 0 },
      )
    }
    return rows
  }, [ketQua, laSpringerToIEEE])

  const hoanDoiCheDo = () => {
    setCheDo(prev => prev === CHE_DO.SPRINGER_TO_IEEE ? CHE_DO.IEEE_TO_SPRINGER : CHE_DO.SPRINGER_TO_IEEE)
    // Clear state when switching modes
    setFileNguon(null)
    setFileTemplate(null)
    setKetQua(null)
    setLoi('')
    setLoiValidationNguon(null)
    setLoiValidationTemplate(null)
    setKetQuaPDF(null)
  }

  const xuLyChonFileNguon = (file, loi) => {
    if (loi) {
      setLoiValidationNguon(loi)
      setFileNguon(null)
      return
    }
    setLoiValidationNguon(null)
    setFileNguon(file)
    setLoi('')
    setKetQua(null)
  }

  const xuLyXoaFileNguon = () => {
    setFileNguon(null)
    setLoiValidationNguon(null)
  }

  const xuLyChonFileTemplate = (file, loi) => {
    if (loi) {
      setLoiValidationTemplate(loi)
      setFileTemplate(null)
      return
    }
    setLoiValidationTemplate(null)
    setFileTemplate(file)
    setLoi('')
    setKetQua(null)
  }

  const xuLyXoaFileTemplate = () => {
    setFileTemplate(null)
    setLoiValidationTemplate(null)
  }

  const xuLyDoiCheDoTemplate = (coUploadTemplateRieng) => {
    setSuDungTemplateRieng(coUploadTemplateRieng)
    setLoi('')
    setKetQua(null)
    if (!coUploadTemplateRieng) {
      setFileTemplate(null)
      setLoiValidationTemplate(null)
    }
  }

  const xuLyChuyenDoi = async () => {
    const tenFileNguon = laSpringerToIEEE ? 'Springer Word' : 'IEEE Word'
    const tenFileHienThi = laSpringerToIEEE ? 'IEEE Word' : 'Springer Word'

    if (!fileNguon) {
      toast.error(`Vui lòng chọn file ${tenFileNguon}`)
      return
    }
    if (suDungTemplateRieng && !fileTemplate) {
      toast.error(`Vui lòng chọn file template ${tenFileHienThi} riêng`)
      return
    }

    setDangXuLy(true)
    setLoi('')
    setKetQua(null)

    let kq
    if (laSpringerToIEEE) {
      kq = await chuyenDoiWordIEEE(fileNguon, suDungTemplateRieng ? fileTemplate : null)
    } else {
      kq = await chuyenDoiWordSpringer(fileNguon, suDungTemplateRieng ? fileTemplate : null)
    }

    setDangXuLy(false)

    if (!kq.thanhCong) {
      const loiText = kq.loiMessage || 'Chuyển đổi thất bại'
      setLoi(loiText)
      toast.error(loiText)
      return
    }

    setKetQua(kq.data)
    setKetQuaPDF(null)
    toast.success(`Đã chuyển đổi sang ${tenFileHienThi} thành công`)
    if (lamMoiThongTinNguoiDung) {
      try { await lamMoiThongTinNguoiDung({ imLang: true }) } catch (e) { console.error('Failed to sync token', e) }
    }
  }

  const xuLyTaiFile = async () => {
    if (!ketQua?.jobId) return
    const kq = await taiFileWordTheoJob(ketQua.jobId, ketQua.tenFileWord)
    if (!kq.thanhCong) {
      toast.error(kq.loiMessage || 'Không thể tải file Word')
      return
    }
    toast.success(`Đã tải file ${laSpringerToIEEE ? 'IEEE Word' : 'Springer Word'}`)
  }

  const xuLyBienDichPDF = async () => {
    if (!ketQua?.jobId) return
    setDangBienDichPDF(true)
    setKetQuaPDF(null)
    toast.loading('Đang xuất PDF (Word → PDF)...', { id: 'compile-pdf-w2w' })
    const kq = await bienDichPDFTuWordJob(ketQua.jobId)
    setDangBienDichPDF(false)
    toast.dismiss('compile-pdf-w2w')
    if (!kq.thanhCong) {
      toast.error(kq.loiMessage || 'Xuất PDF thất bại')
      return
    }
    setKetQuaPDF(kq)
    toast.success(`Xuất PDF thành công${kq.soTrang ? ` (${kq.soTrang} trang)` : ''}`)
  }

  const xuLyTaiPDF = async () => {
    if (!ketQua?.jobId) return
    const kq = await taiFilePDF(ketQua.jobId)
    if (!kq.thanhCong) {
      toast.error(kq.loiMessage || 'Không thể tải file PDF')
      return
    }
    toast.success('Đã tải file PDF')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 pt-24 pb-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Header Section */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="glass-card p-6 sm:p-8"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl bg-primary-500/20 flex items-center justify-center shrink-0">
                <Repeat className="w-6 h-6 text-primary-300" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-semibold text-white">
                  {laSpringerToIEEE ? 'Springer sang IEEE Word' : 'IEEE sang Springer Word'}
                </h1>
                <p className="text-white/60 mt-2">
                  Chuyển đổi định dạng bài báo giữa Springer và IEEE nhanh chóng.
                </p>
              </div>
            </div>

            <button
              onClick={hoanDoiCheDo}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-all hover:border-primary-500/50 group"
            >
              <ArrowRightLeft className="w-4 h-4 text-primary-400 group-hover:rotate-180 transition-transform duration-500" />
              <span className="text-sm font-medium">Đổi chiều chuyển đổi</span>
            </button>
          </div>
        </motion.div>

        {/* Main Content Card */}
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
          className="glass-card p-6 sm:p-8 space-y-8"
        >
          {/* Mode Description */}
          <div className="flex items-center gap-3 p-4 rounded-xl bg-primary-500/10 border border-primary-500/20">
            <Sparkles className="w-5 h-5 text-primary-300" />
            <span className="text-sm text-primary-100 italic">
              Đang ở chế độ: <span className="font-bold text-white not-italic">{laSpringerToIEEE ? 'Springer → IEEE' : 'IEEE → Springer'}</span>
            </span>
          </div>

          {/* Template Selection */}
          <div className="space-y-4">
            <h3 className="text-white/90 font-medium">Template đích ({laSpringerToIEEE ? 'IEEE' : 'Springer'})</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => xuLyDoiCheDoTemplate(false)}
                className={`rounded-xl border p-4 text-left transition-all ${
                  !suDungTemplateRieng
                    ? 'border-primary-400 bg-primary-500/15 text-white ring-2 ring-primary-500/20'
                    : 'border-white/15 bg-white/5 text-white/80 hover:border-white/30'
                }`}
              >
                <p className="font-medium">Dùng template mặc định</p>
                <p className="text-xs text-white/50 mt-1">Sử dụng định dạng tiêu chuẩn có sẵn</p>
              </button>

              <button
                type="button"
                onClick={() => xuLyDoiCheDoTemplate(true)}
                className={`rounded-xl border p-4 text-left transition-all ${
                  suDungTemplateRieng
                    ? 'border-primary-400 bg-primary-500/15 text-white ring-2 ring-primary-500/20'
                    : 'border-white/15 bg-white/5 text-white/80 hover:border-white/30'
                }`}
              >
                <p className="font-medium">Upload template riêng</p>
                <p className="text-xs text-white/50 mt-1">Dành cho các hội nghị có yêu cầu riêng</p>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input File */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-white/90 font-medium">
                <div className="w-6 h-6 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 text-xs">1</div>
                <h3>File gốc ({laSpringerToIEEE ? 'Springer' : 'IEEE'})</h3>
              </div>
              <KhuVucKeoTha
                onChonFile={xuLyChonFileNguon}
                fileHienTai={fileNguon}
                onXoaFile={xuLyXoaFileNguon}
                loiValidation={loiValidationNguon}
                dangTaiLen={dangXuLy}
              />
            </div>

            {/* Custom Template (Optional) */}
            <AnimatePresence mode="wait">
              {suDungTemplateRieng ? (
                <motion.div
                  key="custom-template"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-3"
                >
                  <div className="flex items-center gap-2 text-white/90 font-medium">
                    <div className="w-6 h-6 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 text-xs">2</div>
                    <h3>Template {laSpringerToIEEE ? 'IEEE' : 'Springer'} riêng</h3>
                  </div>
                  <KhuVucKeoTha
                    onChonFile={xuLyChonFileTemplate}
                    fileHienTai={fileTemplate}
                    onXoaFile={xuLyXoaFileTemplate}
                    loiValidation={loiValidationTemplate}
                    dangTaiLen={dangXuLy}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="hidden lg:flex flex-col items-center justify-center p-8 rounded-2xl border border-dashed border-white/10 bg-white/[0.02] text-white/30 text-center"
                >
                  <FileText className="w-12 h-12 mb-2 opacity-20" />
                  <p className="text-sm">Template mặc định đang được chọn</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Action Buttons */}
          <div className="pt-4 flex flex-wrap gap-4 items-center">
            <NutBam
              onClick={xuLyChuyenDoi}
              dangTai={dangXuLy}
              disabled={!fileNguon}
              icon={FileCheck2}
              className="px-8 shadow-lg shadow-primary-500/20"
            >
              {dangXuLy ? 'Đang chuyển đổi...' : 'Thực hiện chuyển đổi'}
            </NutBam>

            <NutBam
              bienThe="secondary"
              onClick={xuLyTaiFile}
              disabled={!ketQua?.jobId}
              icon={Download}
            >
              Tải kết quả Word
            </NutBam>

            {/* Compile PDF Button */}
            <button
              onClick={xuLyBienDichPDF}
              disabled={!ketQua?.jobId || dangBienDichPDF}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 border
                ${ketQua?.jobId && !dangBienDichPDF
                  ? 'bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 border-violet-500/50 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 hover:-translate-y-0.5'
                  : 'bg-white/5 border-white/10 text-white/30 cursor-not-allowed'
                }`}
            >
              {dangBienDichPDF
                ? <><Loader2 className="w-4 h-4 animate-spin" /><span>Đang xuất PDF...</span></>
                : <><FileDown className="w-4 h-4" /><span>Xuất PDF</span></>
              }
            </button>

            {/* PDF result quick-action buttons — appear after compilation */}
            <AnimatePresence>
              {ketQuaPDF && !dangBienDichPDF && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="flex items-center gap-2"
                >
                  {/* Separator */}
                  <div className="w-px h-8 bg-white/15 mx-1" />

                  {/* Download PDF */}
                  <button
                    onClick={xuLyTaiPDF}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/35 border border-emerald-500/40 text-emerald-300 hover:text-white text-sm font-medium transition-all hover:-translate-y-0.5"
                    title="Tải file PDF về máy"
                  >
                    <Download className="w-4 h-4" />
                    <span>Tải PDF</span>
                  </button>

                  {/* View inline */}
                  <a
                    href={ketQuaPDF.pdfUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/15 text-white/70 hover:text-white text-sm font-medium transition-all hover:-translate-y-0.5"
                    title="Xem PDF trực tiếp"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>Xem PDF</span>
                  </a>

                  {ketQuaPDF.soTrang && (
                    <span className="text-xs text-violet-300/70 font-mono bg-violet-500/10 border border-violet-500/20 px-2 py-1 rounded-lg">
                      {ketQuaPDF.soTrang} trang
                    </span>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {loi && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="rounded-xl border border-red-400/30 bg-red-500/10 p-4 text-red-200 flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-red-400" />
              <div className="text-sm leading-relaxed">{loi}</div>
            </motion.div>
          )}
        </motion.div>

        {/* Results Metadata */}
        <AnimatePresence>
          {ketQua && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="glass-card p-6 sm:p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-2 h-8 bg-emerald-500 rounded-full" />
                <h2 className="text-xl font-bold text-white">Số liệu thống kê sau chuyển đổi</h2>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {metadataRows.map((row) => (
                  <div key={row.nhan} className="p-4 rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 transition-colors">
                    <p className="text-white/50 text-xs mb-1 uppercase tracking-wider">{row.nhan}</p>
                    <p className="text-2xl font-bold text-white">{row.giaTri}</p>
                  </div>
                ))}
              </div>

              <div className="pt-6 border-t border-white/10 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-sm">
                <div className="space-y-1">
                  <p className="text-white/40">Mã tiến trình (Job ID)</p>
                  <p className="text-white/90 font-mono bg-white/5 px-2 py-1 rounded">{ketQua.jobId}</p>
                </div>
                <div className="text-right">
                  <p className="text-white/40">Tên file kết quả</p>
                  <p className="text-white/90 font-medium">{ketQua.tenFileWord || 'output.docx'}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* PDF Compile Result Card */}
        <AnimatePresence>
          {ketQuaPDF && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ type: 'spring', stiffness: 300, damping: 28 }}
              className="glass-card p-6 sm:p-8 border border-violet-500/30 bg-violet-500/5"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-violet-300" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">PDF đã xuất thành công!</h2>
                  {ketQuaPDF.soTrang && (
                    <p className="text-violet-300/80 text-sm mt-0.5">
                      {ketQuaPDF.soTrang} trang · {laSpringerToIEEE ? 'IEEE Format' : 'Springer Format'}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                {/* View PDF */}
                <a
                  href={ketQuaPDF.pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 border border-violet-500/50 text-white text-sm font-medium transition-all hover:-translate-y-0.5 shadow-lg shadow-violet-500/25"
                >
                  <ExternalLink className="w-4 h-4" />
                  Xem PDF
                </a>

                {/* Download PDF */}
                <button
                  onClick={xuLyTaiPDF}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 border border-white/15 text-white text-sm font-medium transition-all hover:-translate-y-0.5"
                >
                  <FileDown className="w-4 h-4" />
                  Tải PDF
                </button>
              </div>

              <div className="mt-4 pt-4 border-t border-white/10">
                <p className="text-white/40 text-xs">
                  Pipeline: Word → PDF direct export
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}


export default TrangChuyenDoiWordToWord
