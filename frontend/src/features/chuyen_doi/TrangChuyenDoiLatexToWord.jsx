import { useCallback, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  ArrowRight,
  FileArchive,
  FileCode2,
  FileText,
  Upload,
  X,
  CheckCircle2,
  AlertCircle,
  Sparkles
} from 'lucide-react'
import toast from 'react-hot-toast'
import { NutBam } from '../../components'
import { chuyenDoiLatexSangWord, taiFileWordTheoJob } from '../../services/api'

const MAU_DAU_RA = [
  {
    id: 'ieee',
    ten: 'IEEE Conference',
    moTa: 'Bố cục 2 cột, tối ưu bài báo hội nghị',
    nhan: 'IEEE',
    mauNhan: 'text-primary-200'
  },
  {
    id: 'springer',
    ten: 'Springer LNCS',
    moTa: 'Bố cục 1 cột, chuẩn LNCS',
    nhan: 'Springer',
    mauNhan: 'text-primary-200'
  }
]

const KhuVucKeoThaLatex = ({ fileHienTai, onChonFile, onXoaFile, loiValidation }) => {
  const [dangKeo, setDangKeo] = useState(false)

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setDangKeo(false)

    if (rejectedFiles.length > 0) {
      const loi = rejectedFiles[0].errors[0]
      if (loi.code === 'file-invalid-type') {
        onChonFile(null, 'Chỉ chấp nhận file .tex hoặc .zip')
      } else if (loi.code === 'file-too-large') {
        onChonFile(null, 'File quá lớn (tối đa 20MB)')
      }
      return
    }

    if (acceptedFiles.length > 0) {
      onChonFile(acceptedFiles[0], null)
    }
  }, [onChonFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/zip': ['.zip'],
      'application/x-zip-compressed': ['.zip'],
      'application/octet-stream': ['.zip'],
      'text/x-tex': ['.tex'],
      'application/x-tex': ['.tex'],
      'text/plain': ['.tex']
    },
    maxSize: 20 * 1024 * 1024,
    multiple: false,
    onDragEnter: () => setDangKeo(true),
    onDragLeave: () => setDangKeo(false)
  })

  const layKichThuocFile = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  return (
    <div className="space-y-3">
      <AnimatePresence mode="wait">
        {!fileHienTai ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.2 }}
            {...getRootProps()}
            className={`
              relative rounded-2xl border-2 border-dashed overflow-hidden cursor-pointer
              transition-all duration-300
              ${isDragActive || dangKeo
                ? 'border-primary-400/70 bg-primary-500/10 shadow-[0_0_40px_rgba(99,102,241,0.35)]'
                : 'border-white/20 bg-white/5 hover:border-primary-500/60 hover:bg-white/10'
              }
            `}
          >
            <input {...getInputProps()} />
            <div className="relative z-10 flex flex-col items-center justify-center py-10 px-6 text-center">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-all ${isDragActive || dangKeo ? 'bg-primary-500/20' : 'bg-white/10'}`}>
                <Upload className={`w-8 h-8 ${isDragActive || dangKeo ? 'text-primary-200' : 'text-white/60'}`} />
              </div>
              <h3 className="text-lg font-semibold text-white">
                {isDragActive || dangKeo ? 'Thả file vào đây' : 'Kéo & thả gói LaTeX'}
              </h3>
              <p className="text-white/60 text-sm mt-2">
                Nhận file .tex hoặc .zip (kèm ảnh, .bib, .cls)
              </p>
              <div className="mt-4 flex items-center gap-3 text-xs text-white/50">
                <span className="flex items-center gap-1"><FileCode2 className="w-4 h-4" />.tex</span>
                <span>•</span>
                <span className="flex items-center gap-1"><FileArchive className="w-4 h-4" />.zip</span>
                <span>•</span>
                <span>Tối đa 20MB</span>
              </div>
            </div>
            {(isDragActive || dangKeo) && (
              <motion.div
                className="absolute inset-0 rounded-2xl pointer-events-none"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0.4, 0.9, 0.4] }}
                transition={{ duration: 1.4, repeat: Infinity }}
                style={{ border: '2px solid rgba(99,102,241,0.6)' }}
              />
            )}
          </motion.div>
        ) : (
          <motion.div
            key="file-selected"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-5"
          >
            <div className="flex items-center gap-4 min-w-0">
              <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center">
                {fileHienTai.name.endsWith('.zip') ? (
                  <FileArchive className="w-6 h-6 text-primary-200" />
                ) : (
                  <FileCode2 className="w-6 h-6 text-primary-200" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-white font-medium truncate" title={fileHienTai.name}>
                  {fileHienTai.name}
                </div>
                <div className="text-xs text-white/50 mt-1 flex items-center gap-3">
                  <span>{layKichThuocFile(fileHienTai.size)}</span>
                  <span className="flex items-center gap-1 text-emerald-300">
                    <CheckCircle2 className="w-4 h-4" />
                    Đã chọn
                  </span>
                </div>
              </div>
              <button
                onClick={onXoaFile}
                className="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-colors shrink-0"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {loiValidation && (
        <div className="flex items-center gap-2 text-sm text-red-300">
          <AlertCircle className="w-4 h-4" />
          {loiValidation}
        </div>
      )}
    </div>
  )
}

const TrangChuyenDoiLatexToWord = () => {
  const [mauChon, setMauChon] = useState(MAU_DAU_RA[0].id)
  const [fileLatex, setFileLatex] = useState(null)
  const [loiValidation, setLoiValidation] = useState(null)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [loi, setLoi] = useState('')
  const [ketQua, setKetQua] = useState(null)

  const mauHienTai = useMemo(() => MAU_DAU_RA.find((item) => item.id === mauChon), [mauChon])

  const xuLyChonFile = (file, loi) => {
    if (loi) {
      setLoiValidation(loi)
      setFileLatex(null)
      return
    }
    setFileLatex(file)
    setLoiValidation(null)
    setLoi('')
    setKetQua(null)
  }

  const xuLyXoaFile = () => {
    setFileLatex(null)
    setLoiValidation(null)
    setLoi('')
    setKetQua(null)
  }

  const xuLyChuyenDoi = async () => {
    if (!fileLatex) {
      toast.error('Vui lòng chọn gói LaTeX trước khi chuyển đổi')
      return
    }
    setDangXuLy(true)
    setLoi('')
    setKetQua(null)

    const kq = await chuyenDoiLatexSangWord(fileLatex, mauChon)
    setDangXuLy(false)

    if (!kq.thanhCong) {
      const loiText = kq.loiMessage || 'Chuyển đổi thất bại'
      setLoi(loiText)
      toast.error(loiText)
      return
    }

    setKetQua(kq.data)
    toast.success('Đã chuyển đổi LaTeX sang Word thành công')
  }

  const xuLyTaiFile = async () => {
    if (!ketQua?.jobId) return
    const kq = await taiFileWordTheoJob(ketQua.jobId, ketQua.tenFileWord)
    if (!kq.thanhCong) {
      toast.error(kq.loiMessage || 'Không thể tải file Word')
      return
    }
    toast.success('Đã tải file Word')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 pt-24 pb-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="glass-card p-6 sm:p-8"
        >
          <div className="flex flex-col lg:flex-row gap-6 lg:items-center lg:justify-between">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl bg-primary-500/20 flex items-center justify-center">
                <FileText className="w-6 h-6 text-primary-200" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-semibold text-white">LaTeX sang Word chuẩn IEEE/Springer</h1>
                <p className="text-white/60 mt-2">
                  Tối ưu giữ format, tập trung đúng chuẩn xuất bản, hỗ trợ gói .tex hoặc .zip.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-2xl px-4 py-3">
              <Sparkles className="w-5 h-5 text-primary-200" />
              <div>
                <p className="text-sm text-white/70">Mục tiêu giữ format</p>
                <p className="text-white font-semibold">Gần 100% cho IEEE & Springer</p>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
          className="glass-card p-6 sm:p-8 space-y-8"
        >
          <div className="space-y-4">
            <h3 className="text-white/90 font-medium">Chọn mẫu đích</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {MAU_DAU_RA.map((mau) => (
                <button
                  key={mau.id}
                  type="button"
                  onClick={() => setMauChon(mau.id)}
                  className={`rounded-2xl border p-5 text-left transition-all ${
                    mauChon === mau.id
                      ? 'border-primary-400/60 bg-primary-500/10 shadow-[0_0_22px_rgba(99,102,241,0.25)]'
                      : 'border-white/10 bg-white/5 hover:border-white/25'
                  }`}
                >
                  <div className={`text-xs font-semibold uppercase tracking-widest ${mau.mauNhan}`}>{mau.nhan}</div>
                  <div className="text-white text-lg font-semibold mt-2">{mau.ten}</div>
                  <div className="text-white/60 text-sm mt-2">{mau.moTa}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-6">
            <div className="space-y-5">
              <div className="flex items-center gap-2 text-white/80">
                <FileCode2 className="w-5 h-5 text-cyan-200" />
                <span className="font-medium">Gói LaTeX đầu vào</span>
              </div>
              <KhuVucKeoThaLatex
                fileHienTai={fileLatex}
                onChonFile={xuLyChonFile}
                onXoaFile={xuLyXoaFile}
                loiValidation={loiValidation}
              />

              <div className="flex flex-col sm:flex-row gap-3">
                <NutBam
                  onClick={xuLyChuyenDoi}
                  icon={ArrowRight}
                  className="flex-1"
                  dangTai={dangXuLy}
                >
                  {dangXuLy ? 'Đang chuyển đổi...' : 'Bắt đầu chuyển đổi'}
                </NutBam>
                <NutBam
                  bienThe="secondary"
                  className="flex-1"
                  onClick={() => toast('Chuẩn bị thêm tùy chọn template Word riêng.', { icon: '🧩' })}
                >
                  Template Word riêng
                </NutBam>
              </div>

              {loi && (
                <div className="flex items-center gap-2 text-sm text-red-300">
                  <AlertCircle className="w-4 h-4" />
                  {loi}
                </div>
              )}

              {ketQua && (
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-emerald-200 font-semibold">Chuyển đổi hoàn tất</div>
                    <div className="text-white/70 text-sm mt-1">
                      <span>Sẵn sàng tải file Word</span>
                      <span
                        className="block max-w-full truncate"
                        title={ketQua.tenFileWord || 'output.docx'}
                      >
                        {ketQua.tenFileWord || 'output.docx'}
                      </span>
                    </div>
                  </div>
                  <NutBam
                    bienThe="secondary"
                    onClick={xuLyTaiFile}
                    icon={FileText}
                    className="w-full sm:w-auto shrink-0"
                  >
                    Tải file Word
                  </NutBam>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-5 space-y-3">
                <div className="text-white font-semibold">Checklist giữ format</div>
                <div className="text-sm text-white/70 space-y-2">
                  <div>• Gói ZIP nên có `main.tex` + thư mục ảnh</div>
                  <div>• Giữ nguyên style IEEE/Springer gốc</div>
                  <div>• Tránh macro tự định nghĩa phức tạp</div>
                  <div>• Ưu tiên ảnh PNG/JPG thay vì EPS</div>
                </div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="text-white/80 text-sm">Mẫu đang chọn</div>
                <div className="text-white text-lg font-semibold mt-1">{mauHienTai?.ten}</div>
                <div className="text-white/60 text-sm mt-2">Kết quả Word sẽ bám sát bố cục {mauHienTai?.nhan}.</div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default TrangChuyenDoiLatexToWord
