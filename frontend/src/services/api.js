// api.js - Service gọi API backend Python
import { DIA_CHI_API_GOC } from '../config/apiConfig'

const TOKEN_KEY = 'word2latex_token'
const SU_KIEN_PHIEN_HET_HAN = 'xac-thuc:het-han'

export const layToken = () => localStorage.getItem(TOKEN_KEY)

const giaiMaPayloadJWT = (token) => {
  try {
    const payloadBase64 = token.split('.')[1]
    if (!payloadBase64) return null
    const normalized = payloadBase64.replace(/-/g, '+').replace(/_/g, '/')
    const decoded = window.atob(normalized)
    return JSON.parse(decoded)
  } catch {
    return null
  }
}

const tokenDaHetHan = (token) => {
  const payload = giaiMaPayloadJWT(token)
  if (!payload?.exp) return false
  const nowInSeconds = Math.floor(Date.now() / 1000)
  return payload.exp <= nowInSeconds
}

const thongBaoPhienHetHan = () => {
  window.dispatchEvent(new CustomEvent(SU_KIEN_PHIEN_HET_HAN))
}

const chuanHoaNgayGioApi = (rawValue) => {
  if (!rawValue || typeof rawValue !== 'string') return null
  const coTimezone = /[zZ]|[+\-]\d{2}:?\d{2}$/.test(rawValue)
  const normalized = coTimezone ? rawValue : `${rawValue}Z`
  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed
}

const taoHeaderXacThuc = () => {
  const token = layToken()
  if (token && tokenDaHetHan(token)) {
    thongBaoPhienHetHan()
    return {}
  }
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

// ── FILE UTILITIES ────────────────────────────────────────────────────────────

export const luuBlobThanhFile = (blob, tenFile) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = tenFile
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export const docLoiJsonTuResponse = async (response) => {
  try {
    const data = await response.json()
    return data?.error || data?.detail || data?.message || 'Đã xảy ra lỗi khi xử lý'
  } catch {
    return 'Đã xảy ra lỗi khi xử lý'
  }
}

// ── CONVERSION ────────────────────────────────────────────────────────────────

export const chuyenDoiFileStream = (file, templateType = 'onecolumn', onProgress) => {
  return new Promise((resolve) => {
    const formData = new FormData()
    formData.append('file', file)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      controller.abort()
      resolve({ thanhCong: false, loiMessage: 'Xử lý quá lâu (>3 phút). Vui lòng thử lại.' })
    }, 180000)

    const url = `${DIA_CHI_API_GOC}/api/chuyen-doi-stream?template_type=${encodeURIComponent(templateType)}`
    fetch(url, {
      method: 'POST',
      headers: taoHeaderXacThuc(),
      body: formData,
      signal: controller.signal,
    }).then(async (response) => {
      clearTimeout(timeoutId)
      if (!response.ok) {
        const message = await docLoiJsonTuResponse(response)
        resolve({ thanhCong: false, loiMessage: message })
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let daNhanDuLieu = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        daNhanDuLieu = true
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.error) {
              resolve({
                thanhCong: false,
                loiMessage: event.msg || 'Lỗi chuyển đổi',
                errorDetails: event.details || null,
                errorType: event.error_type || null,
              })
              return
            }
            if (onProgress) onProgress(event.step, event.msg)
            if (event.done) {
              resolve({
                thanhCong: true,
                data: {
                  texContent: event.tex_content || '',
                  jobId: event.job_id || '',
                  tenFileZip: event.ten_file_zip || '',
                  tenFileLatex: event.ten_file_latex || '',
                  tenFilePdf: event.ten_file_pdf || '',
                  pdfUrl: event.pdf_url || '',
                  metadata: event.metadata || {},
                }
              })
              return
            }
          } catch { /* skip */ }
        }
      }
      resolve({
        thanhCong: false,
        loiMessage: daNhanDuLieu
          ? 'Kết nối SSE bị gián đoạn trong lúc xử lý. Vui lòng kiểm tra mạng và bấm Thử lại.'
          : 'Không nhận được dữ liệu từ SSE. Vui lòng thử lại sau ít phút.'
      })
    }).catch((loi) => {
      clearTimeout(timeoutId)
      if (loi?.name === 'AbortError') {
        resolve({ thanhCong: false, loiMessage: 'Xử lý quá lâu. Vui lòng thử lại.' })
      } else {
        resolve({ thanhCong: false, loiMessage: loi.message || 'Không thể kết nối đến server' })
      }
    })
  })
}

export const chuyenDoiWordIEEE = async (file, templateFile = null) => {
  try {
    if (!file) throw new Error('Vui lòng chọn file Word')

    const formData = new FormData()
    formData.append('file', file)
    if (templateFile) {
      formData.append('template_file', templateFile)
    }

    const response = await fetch(`${DIA_CHI_API_GOC}/api/chuyen-doi-word-ieee`, {
      method: 'POST',
      headers: taoHeaderXacThuc(),
      body: formData,
    })

    const data = await response.json().catch(() => ({}))
    if (!response.ok || !data?.thanh_cong) {
      return {
        thanhCong: false,
        loiMessage: data?.error || data?.detail || 'Chuyển đổi Word sang IEEE Word thất bại',
      }
    }

    return {
      thanhCong: true,
      data: {
        jobId: data.job_id || '',
        tenFileWord: data.ten_file_word || '',
        wordUrl: data.word_url || '',
        metadata: data.metadata || {},
      }
    }
  } catch (loi) {
    return { thanhCong: false, loiMessage: loi.message || 'Không thể kết nối đến server' }
  }
}

export const chuyenDoiWordSpringer = async (file, templateFile = null) => {
  try {
    if (!file) throw new Error('Vui lòng chọn file Word')

    const formData = new FormData()
    formData.append('file', file)
    if (templateFile) {
      formData.append('template_file', templateFile)
    }

    const response = await fetch(`${DIA_CHI_API_GOC}/api/chuyen-doi-word-springer`, {
      method: 'POST',
      headers: taoHeaderXacThuc(),
      body: formData,
    })

    const data = await response.json().catch(() => ({}))
    if (!response.ok || !data?.thanh_cong) {
      return {
        thanhCong: false,
        loiMessage: data?.error || data?.detail || 'Chuyển đổi Word sang Springer Word thất bại',
      }
    }

    return {
      thanhCong: true,
      data: {
        jobId: data.job_id || '',
        tenFileWord: data.ten_file_word || '',
        wordUrl: data.word_url || '',
        metadata: data.metadata || {},
      }
    }
  } catch (loi) {
    return { thanhCong: false, loiMessage: loi.message || 'Không thể kết nối đến server' }
  }
}

export const taiFileWordTheoJob = async (jobId, tenFileWordFallback = '') => {
  try {
    if (!jobId || typeof jobId !== 'string') throw new Error('Job ID không hợp lệ')

    const response = await fetch(`${DIA_CHI_API_GOC}/api/tai-ve-word/${jobId}`, {
      method: 'GET',
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const message = await docLoiJsonTuResponse(response)
      throw new Error(message)
    }

    const blob = await response.blob()
    const contentDisposition = response.headers.get('content-disposition') || ''
    const match = contentDisposition.match(/filename=([^;]+)/i)
    const tenFileTuHeader = match?.[1]?.replace(/"/g, '') || ''
    const tenFileWord = tenFileTuHeader || tenFileWordFallback || `${jobId}_ieee.docx`
    luuBlobThanhFile(blob, tenFileWord)
    return { thanhCong: true }
  } catch (loi) {
    return { thanhCong: false, loiMessage: loi.message || 'Không thể tải file Word' }
  }
}

export const taiFile = async (duongDan, tenFile) => {
  try {
    const response = await fetch(duongDan, { headers: taoHeaderXacThuc() })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) throw new Error('Không thể tải file')
    const blob = await response.blob()
    luuBlobThanhFile(blob, tenFile)
    return { thanhCong: true }
  } catch (loi) {
    return { thanhCong: false, loiMessage: loi.message || 'Không thể tải file' }
  }
}

export const taiFileZip = async (jobId, tenFileZipFallback = '') => {
  try {
    if (!jobId || typeof jobId !== 'string') throw new Error('Job ID không hợp lệ')

    // Thử endpoint mới /api/download/{job_id} trước (yêu cầu auth)
    const downloadUrl = `${DIA_CHI_API_GOC}/api/download/${jobId}`
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: taoHeaderXacThuc()
    })
    if (response.status === 401) thongBaoPhienHetHan()

    // Fallback sang endpoint cũ nếu chưa đăng nhập
    const finalResponse = response.ok ? response : await fetch(`${DIA_CHI_API_GOC}/api/tai-ve-zip/${jobId}`)
    if (!finalResponse.ok) {
      const message = await docLoiJsonTuResponse(finalResponse)
      throw new Error(message)
    }

    const blob = await finalResponse.blob()
    const contentDisposition = finalResponse.headers.get('content-disposition') || ''
    const match = contentDisposition.match(/filename=([^;]+)/i)
    const tenFileTuHeader = match?.[1]?.replace(/"/g, '') || ''
    const tenFileZip = tenFileTuHeader || tenFileZipFallback || `${jobId}.zip`
    luuBlobThanhFile(blob, tenFileZip)
    return { thanhCong: true }
  } catch (loi) {
    return { thanhCong: false, loiMessage: loi.message || 'Không thể tải file ZIP' }
  }
}

// ── COMPILE PDF (Step 2) ──────────────────────────────────────────────────────

export const bienDichPDF = async (jobId, signal = null) => {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60000) // ⏱️ Frontend timeout: 60s

  try {
    if (!jobId || typeof jobId !== 'string') throw new Error('Job ID không hợp lệ')
    const response = await fetch(`${DIA_CHI_API_GOC}/api/compile-pdf/${jobId}`, {
      method: 'POST',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({}), // Gửi body rỗng để tránh 422 trên một số cấu hình server/proxy
      signal: signal || controller.signal // 🧊 Support external cancellation
    })
    if (response.status === 401) thongBaoPhienHetHan()
    clearTimeout(timeoutId)
    const data = await response.json()
    if (!response.ok || !data.thanh_cong) {
      return {
        thanhCong: false,
        loiMessage: data.loi || 'Biên dịch PDF thất bại',
        chiTiet: data.chi_tiet || null,
      }
    }
    return {
      thanhCong: true,
      soTrang: data.so_trang,
      tenFilePDF: data.ten_file_pdf,
      pdfUrl: `${DIA_CHI_API_GOC}${data.pdf_url}`,
    }
  } catch (loi) {
    clearTimeout(timeoutId)
    if (loi.name === 'AbortError') {
      return { thanhCong: false, loiMessage: 'Biên dịch PDF quá lâu (>35s). Vui lòng kiểm tra lại mã LaTeX.' }
    }
    return { thanhCong: false, loiMessage: loi.message || 'Không thể kết nối server để biên dịch' }
  }
}

export const taiFilePDF = async (jobId) => {
  try {
    if (!jobId || typeof jobId !== 'string') throw new Error('Job ID không hợp lệ')
    const response = await fetch(`${DIA_CHI_API_GOC}/api/tai-ve-pdf/${jobId}`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) throw new Error('Không thể tải file PDF')
    const blob = await response.blob()
    const contentDisposition = response.headers.get('content-disposition') || ''
    const match = contentDisposition.match(/filename=([^;]+)/i)
    const tenFile = match?.[1]?.replace(/"/g, '') || `${jobId}.pdf`
    luuBlobThanhFile(blob, tenFile)
    return { thanhCong: true }
  } catch (loi) {
    return { thanhCong: false, loiMessage: loi.message || 'Không thể tải file PDF' }
  }
}

// ── TEMPLATES ─────────────────────────────────────────────────────────────────

export const layDanhSachTemplate = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/templates`, {
      cache: 'no-store',
      headers: taoHeaderXacThuc(),
    })
    if (!response.ok) throw new Error('Không thể tải danh sách template')
    const data = await response.json()
    return { thanhCong: true, templates: data.templates || [] }
  } catch (loi) {
    return { thanhCong: false, templates: [], loiMessage: loi.message }
  }
}

export const taiLenTemplate = async (file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(`${DIA_CHI_API_GOC}/api/templates/upload`, {
      method: 'POST',
      headers: taoHeaderXacThuc(),
      body: formData,
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || 'Không thể tải lên template')
    }
    const data = await response.json()
    return { thanhCong: true, template: data.template, message: data.message }
  } catch (loi) {
    return { thanhCong: false, loiMessage: loi.message }
  }
}

export const xoaTemplate = async (templateId) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/templates/${templateId}`, {
      method: 'DELETE',
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || 'Không thể xóa template')
    }
    return { thanhCong: true }
  } catch (loi) {
    return { thanhCong: false, loiMessage: loi.message }
  }
}

export const kiemTraServer = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/health`, { method: 'GET' })
    return response.ok
  } catch {
    return false
  }
}

// ── LỊCH SỬ CHUYỂN ĐỔI (SQLite - JWT) ───────────────────────────────────────

export const layLichSuChuyenDoi = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/history`, {
      headers: taoHeaderXacThuc()
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) throw new Error('Không thể lấy lịch sử')
    const data = await response.json()
    const danhSach = (data.danhSach || []).map(item => ({
      ...item,
      jobId: item.job_id || '',
      duongDanTaiVe: item.file_path || '',
      thoiGian: chuanHoaNgayGioApi(item.thoiGian) || new Date()
    }))
    return { thanhCong: true, danhSach }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const capNhatThongTinTaiKhoan = async (payload) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/auth/me`, {
      method: 'PATCH',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, user: data.user }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const layThongTinGoiPremium = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/premium/options`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const taoHoaDonNapTien = async (amount_vnd) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/payment/create`, {
      method: 'POST',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ amount_vnd })
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const kiemTraTrangThaiHoaDon = async (paymentId) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/payment/status/${paymentId}`, {
      headers: taoHeaderXacThuc()
    })
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const xacNhanHoaDonThuCongDev = async (paymentId) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/payment/dev/complete/${paymentId}`, {
      method: 'POST',
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const dangKyGoiPremium = async (planKey) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/premium/subscribe`, {
      method: 'POST',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ plan_key: planKey })
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const xoaLichSuChuyenDoi = async (recordId) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/history/${recordId}`, {
      method: 'DELETE',
      headers: taoHeaderXacThuc()
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) throw new Error('Không thể xóa lịch sử')
    return { thanhCong: true }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

// ── ADMIN APIs ───────────────────────────────────────────────────────────────

export const layTongQuanAdmin = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/overview`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const layDanhSachNguoiDungAdmin = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/users`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return {
      thanhCong: true,
      danhSach: (data.danh_sach || []).map(item => ({
        ...item,
        createdAt: chuanHoaNgayGioApi(item.created_at),
      })),
    }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const capNhatVaiTroNguoiDungAdmin = async (userId, role) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/users/${userId}/role`, {
      method: 'PATCH',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ role }),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, user: data.user }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const capNhatPremiumNguoiDungAdmin = async (userId, enabled, soNgay = 30) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/users/${userId}/premium`, {
      method: 'PATCH',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ enabled, so_ngay: soNgay }),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, user: data.user }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const congTokenNguoiDungAdmin = async (userId, amount, reason = '') => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/users/${userId}/token/grant`, {
      method: 'POST',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ amount, reason }),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, tokenBalance: data.token_balance }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const truTokenNguoiDungAdmin = async (userId, amount, reason = '') => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/users/${userId}/token/deduct`, {
      method: 'POST',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ amount, reason }),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, tokenBalance: data.token_balance }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const layLichSuTheoNguoiDungAdmin = async (userId, limit = 100) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/users/${userId}/history?limit=${limit}`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return {
      thanhCong: true,
      danhSach: (data.danh_sach || []).map(item => ({
        ...item,
        createdAt: chuanHoaNgayGioApi(item.created_at),
      })),
    }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const layTokenLedgerTheoNguoiDungAdmin = async (userId, limit = 200) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/users/${userId}/token-ledger?limit=${limit}`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return {
      thanhCong: true,
      danhSach: (data.danh_sach || []).map(item => ({
        ...item,
        createdAt: chuanHoaNgayGioApi(item.created_at),
      })),
    }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const xoaNguoiDungAdmin = async (userId) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/users/${userId}`, {
      method: 'DELETE',
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    return { thanhCong: true }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const layLichSuToanHeThongAdmin = async (limit = 200) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/history?limit=${limit}`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return {
      thanhCong: true,
      danhSach: (data.danh_sach || []).map(item => ({
        ...item,
        createdAt: chuanHoaNgayGioApi(item.created_at),
      })),
    }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const xoaBanGhiLichSuAdmin = async (recordId) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/history/${recordId}`, {
      method: 'DELETE',
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    return { thanhCong: true }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const layDanhSachTemplateAdmin = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/templates`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, danhSach: data.danh_sach || [] }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const layAuditLogsAdmin = async (limit = 200) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/audit-logs?limit=${limit}`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return {
      thanhCong: true,
      danhSach: (data.danh_sach || []).map(item => ({
        ...item,
        createdAt: chuanHoaNgayGioApi(item.created_at),
      })),
    }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const xoaTemplateAdmin = async (templateId) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/templates/${templateId}`, {
      method: 'DELETE',
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    return { thanhCong: true }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

// ── ADMIN PAYMENT APIs ────────────────────────────────────────────────────────

export const layDanhSachPaymentsAdmin = async (limit = 200) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/payments?limit=${limit}`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return {
      thanhCong: true,
      danhSach: (data.danh_sach || []).map(item => ({
        ...item,
        createdAt: chuanHoaNgayGioApi(item.created_at),
        updatedAt: chuanHoaNgayGioApi(item.updated_at),
      })),
    }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const xacNhanPaymentThuCongAdmin = async (paymentId) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/payments/${paymentId}/complete`, {
      method: 'PATCH',
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

// ── AUTH (JWT - no Firebase) ──────────────────────────────────────────────────
// Auth functions are now managed by AuthContext.jsx
// These are kept for backward-compat imports in components

export const dangNhapVoiEmail = async (email, password) => {
  const resp = await fetch(`${DIA_CHI_API_GOC}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  const data = await resp.json()
  if (!resp.ok) return { thanhCong: false, loiMessage: data.detail || 'Đăng nhập thất bại' }
  localStorage.setItem('word2latex_token', data.access_token)
  localStorage.setItem('word2latex_user', JSON.stringify(data.user))
  return { thanhCong: true, nguoiDung: data.user }
}

export const dangKyVoiEmail = async (username, email, password) => {
  const resp = await fetch(`${DIA_CHI_API_GOC}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  })
  const data = await resp.json()
  if (!resp.ok) return { thanhCong: false, loiMessage: data.detail || 'Đăng ký thất bại' }
  localStorage.setItem('word2latex_token', data.access_token)
  localStorage.setItem('word2latex_user', JSON.stringify(data.user))
  return { thanhCong: true, nguoiDung: data.user }
}

export const dangXuat = async () => {
  localStorage.removeItem('word2latex_token')
  localStorage.removeItem('word2latex_user')
  return { thanhCong: true }
}

export const theoDoiTrangThaiXacThuc = (callback) => {
  setTimeout(() => {
    try {
      const raw = localStorage.getItem('word2latex_user')
      callback(raw ? JSON.parse(raw) : null)
    } catch {
      callback(null)
    }
  }, 50)
  return () => { }
}

export default {
  luuBlobThanhFile,
  taiFile,
  taiFileZip,
  bienDichPDF,
  taiFilePDF,
  layDanhSachTemplate,
  taiLenTemplate,
  xoaTemplate,
  kiemTraServer,
  layLichSuChuyenDoi,
  xoaLichSuChuyenDoi,
  capNhatThongTinTaiKhoan,
  layThongTinGoiPremium,
  xacNhanHoaDonThuCongDev,
  dangKyGoiPremium,
  taoHoaDonNapTien,
  kiemTraTrangThaiHoaDon,
  layTongQuanAdmin,
  layDanhSachNguoiDungAdmin,
  capNhatVaiTroNguoiDungAdmin,
  capNhatPremiumNguoiDungAdmin,
  congTokenNguoiDungAdmin,
  truTokenNguoiDungAdmin,
  layLichSuTheoNguoiDungAdmin,
  layTokenLedgerTheoNguoiDungAdmin,
  xoaNguoiDungAdmin,
  layLichSuToanHeThongAdmin,
  xoaBanGhiLichSuAdmin,
  layDanhSachTemplateAdmin,
  layAuditLogsAdmin,
  xoaTemplateAdmin,
  layDanhSachPaymentsAdmin,
  xacNhanPaymentThuCongAdmin,
  dangNhapVoiEmail,
  dangKyVoiEmail,
  dangXuat,
  theoDoiTrangThaiXacThuc
}
