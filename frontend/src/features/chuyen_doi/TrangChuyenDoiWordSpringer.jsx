import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRightLeft, Download, FileCheck2, Sparkles, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import KhuVucKeoTha from './KhuVucKeoTha'
import { NutBam } from '../../components'
import { chuyenDoiWordSpringer, taiFileWordTheoJob } from '../../services/api'

const TrangChuyenDoiWordSpringer = () => {
  const [fileIEEE, setFileIEEE] = useState(null)
  const [suDungTemplateRieng, setSuDungTemplateRieng] = useState(false)
  const [fileTemplateSpringer, setFileTemplateSpringer] = useState(null)
  const [loiValidationIEEE, setLoiValidationIEEE] = useState(null)
  const [loiValidationSpringer, setLoiValidationSpringer] = useState(null)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [loi, setLoi] = useState('')
  const [ketQua, setKetQua] = useState(null)

  const metadataRows = useMemo(() => {
    if (!ketQua?.metadata) return []
    const md = ketQua.metadata
    return [
      { nhan: 'Sections', giaTri: md.so_section ?? 0 },
      { nhan: 'Paragraphs', giaTri: md.so_paragraph ?? 0 },
      { nhan: 'Tables', giaTri: md.so_bang ?? 0 },
      { nhan: 'References', giaTri: md.so_tai_lieu_tham_khao ?? 0 },
    ]
  }, [ketQua])

  const xuLyChonFileIEEE = (file, loi) => {
    if (loi) {
      setLoiValidationIEEE(loi)
      setFileIEEE(null)
      return
    }
    setLoiValidationIEEE(null)
    setFileIEEE(file)
    setLoi('')
    setKetQua(null)
  }

  const xuLyXoaFileIEEE = () => {
    setFileIEEE(null)
    setLoiValidationIEEE(null)
  }

  const xuLyChonFileTemplateSpringer = (file, loi) => {
    if (loi) {
      setLoiValidationSpringer(loi)
      setFileTemplateSpringer(null)
      return
    }
    setLoiValidationSpringer(null)
    setFileTemplateSpringer(file)
    setLoi('')
    setKetQua(null)
  }

  const xuLyXoaFileTemplateSpringer = () => {
    setFileTemplateSpringer(null)
    setLoiValidationSpringer(null)
  }

  const xuLyDoiCheDoTemplate = (coUploadTemplateRieng) => {
    setSuDungTemplateRieng(coUploadTemplateRieng)
    setLoi('')
    setKetQua(null)
    if (!coUploadTemplateRieng) {
      setFileTemplateSpringer(null)
      setLoiValidationSpringer(null)
    }
  }

  const xuLyChuyenDoi = async () => {
    if (!fileIEEE) {
      toast.error('Vui lòng chọn file IEEE Word')
      return
    }
    if (suDungTemplateRieng && !fileTemplateSpringer) {
      toast.error('Vui lòng chọn file template Springer riêng')
      return
    }

    setDangXuLy(true)
    setLoi('')
    setKetQua(null)

    const kq = await chuyenDoiWordSpringer(fileIEEE, suDungTemplateRieng ? fileTemplateSpringer : null)
    setDangXuLy(false)

    if (!kq.thanhCong) {
      const loiText = kq.loiMessage || 'Chuyển đổi thất bại'
      setLoi(loiText)
      toast.error(loiText)
      return
    }

    setKetQua(kq.data)
    toast.success('Đã chuyển đổi sang Springer Word thành công')
  }

  const xuLyTaiFile = async () => {
    if (!ketQua?.jobId) return
    const kq = await taiFileWordTheoJob(ketQua.jobId, ketQua.tenFileWord)
    if (!kq.thanhCong) {
      toast.error(kq.loiMessage || 'Không thể tải file Word')
      return
    }
    toast.success('Đã tải file Springer Word')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 pt-24 pb-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="glass-card p-6 sm:p-8"
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-primary-500/20 flex items-center justify-center shrink-0">
              <ArrowRightLeft className="w-6 h-6 text-primary-300" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-semibold text-white">IEEE Word sang Springer Word</h1>
              <p className="text-white/60 mt-2">
                Chọn template Springer mặc định hoặc tải lên template riêng, sau đó chuyển đổi từ IEEE Word.
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
          className="glass-card p-6 sm:p-8 space-y-6"
        >
          <div className="flex items-center gap-2 text-white/80">
            <Sparkles className="w-4 h-4 text-primary-300" />
            <span className="text-sm">Hỗ trợ 2 chế độ: template mặc định hoặc template Springer riêng (.docx/.docm)</span>
          </div>

          <div className="space-y-3">
            <h3 className="text-white/90 font-medium">Template Springer (đích)</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => xuLyDoiCheDoTemplate(false)}
                className={`rounded-xl border px-4 py-3 text-left transition-all ${
                  !suDungTemplateRieng
                    ? 'border-primary-400 bg-primary-500/15 text-white'
                    : 'border-white/15 bg-white/5 text-white/80 hover:border-white/30'
                }`}
              >
                <p className="font-medium">Dùng template mặc định</p>
                <p className="text-sm text-white/60 mt-1">Nhanh gọn, không cần upload thêm file</p>
              </button>

              <button
                type="button"
                onClick={() => xuLyDoiCheDoTemplate(true)}
                className={`rounded-xl border px-4 py-3 text-left transition-all ${
                  suDungTemplateRieng
                    ? 'border-primary-400 bg-primary-500/15 text-white'
                    : 'border-white/15 bg-white/5 text-white/80 hover:border-white/30'
                }`}
              >
                <p className="font-medium">Upload template riêng</p>
                <p className="text-sm text-white/60 mt-1">Dùng khi bạn có chuẩn Springer nội bộ</p>
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-white/90 font-medium">1) Tài liệu IEEE Word (nguồn)</h3>
            <KhuVucKeoTha
              onChonFile={xuLyChonFileIEEE}
              fileHienTai={fileIEEE}
              onXoaFile={xuLyXoaFileIEEE}
              loiValidation={loiValidationIEEE}
              dangTaiLen={dangXuLy}
            />
          </div>

          {suDungTemplateRieng && (
            <div className="space-y-2">
              <h3 className="text-white/90 font-medium">2) Template Springer Word (riêng)</h3>
              <KhuVucKeoTha
                onChonFile={xuLyChonFileTemplateSpringer}
                fileHienTai={fileTemplateSpringer}
                onXoaFile={xuLyXoaFileTemplateSpringer}
                loiValidation={loiValidationSpringer}
                dangTaiLen={dangXuLy}
              />
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <NutBam
              onClick={xuLyChuyenDoi}
              dangTai={dangXuLy}
              disabled={!fileIEEE}
              icon={FileCheck2}
            >
              {dangXuLy ? 'Đang chuyển đổi...' : 'Bắt đầu chuyển đổi'}
            </NutBam>

            <NutBam
              bienThe="secondary"
              onClick={xuLyTaiFile}
              disabled={!ketQua?.jobId}
              icon={Download}
            >
              Tải Springer Word
            </NutBam>
          </div>

          {loi && (
            <div className="rounded-xl border border-red-400/30 bg-red-500/10 p-4 text-red-200 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{loi}</span>
            </div>
          )}
        </motion.div>

        {ketQua && (
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="glass-card p-6 sm:p-8"
          >
            <h2 className="text-xl font-semibold text-white mb-4">Kết quả</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              {metadataRows.map((row) => (
                <div key={row.nhan} className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 flex justify-between">
                  <span className="text-white/70">{row.nhan}</span>
                  <span className="text-white font-semibold">{row.giaTri}</span>
                </div>
              ))}
            </div>

            <div className="text-sm text-white/70 space-y-1">
              <p>Job ID: <span className="text-white/90 font-mono">{ketQua.jobId}</span></p>
              <p>Tên file: <span className="text-white/90">{ketQua.tenFileWord || 'springer_output.docx'}</span></p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default TrangChuyenDoiWordSpringer
