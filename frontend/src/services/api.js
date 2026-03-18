// api.js - Service gọi API backend Python
import { API_BASE_URL } from '../config/apiConfig'

const TOKEN_KEY = 'word2latex_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)

const authHeaders = () => {
  const token = getToken()
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

    const url = `${API_BASE_URL}/api/chuyen-doi-stream?template_type=${encodeURIComponent(templateType)}`
    fetch(url, {
      method: 'POST',
      headers: authHeaders(),   // 🔑 Tự động đính Bearer token
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

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
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
                  metadata: event.metadata || {},
                }
              })
              return
            }
          } catch { /* skip */ }
        }
      }
      resolve({ thanhCong: false, loiMessage: 'Kết nối bị gián đoạn' })
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

export const taiFile = async (duongDan, tenFile) => {
  try {
    const response = await fetch(duongDan, { headers: authHeaders() })
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
    const downloadUrl = `${API_BASE_URL}/api/download/${jobId}`
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: authHeaders()
    })

    // Fallback sang endpoint cũ nếu chưa đăng nhập
    const finalResponse = response.ok ? response : await fetch(`${API_BASE_URL}/api/tai-ve-zip/${jobId}`)
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
    const response = await fetch(`${API_BASE_URL}/api/compile-pdf/${jobId}`, {
      method: 'POST',
      headers: {
        ...authHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({}), // Gửi body rỗng để tránh 422 trên một số cấu hình server/proxy
      signal: signal || controller.signal // 🧊 Support external cancellation
    })
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
      pdfUrl: `${API_BASE_URL}${data.pdf_url}`,
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
    const response = await fetch(`${API_BASE_URL}/api/tai-ve-pdf/${jobId}`, {
      headers: authHeaders(),
    })
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
    const response = await fetch(`${API_BASE_URL}/api/templates`, { cache: 'no-store' })
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
    const response = await fetch(`${API_BASE_URL}/api/templates/upload`, {
      method: 'POST',
      headers: authHeaders(),
      body: formData,
    })
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
    const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
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
    const response = await fetch(`${API_BASE_URL}/health`, { method: 'GET' })
    return response.ok
  } catch {
    return false
  }
}

// ── LỊCH SỬ CHUYỂN ĐỔI (SQLite - JWT) ───────────────────────────────────────

export const layLichSuChuyenDoi = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/history`, {
      headers: authHeaders()
    })
    if (!response.ok) throw new Error('Không thể lấy lịch sử')
    const data = await response.json()
    const danhSach = (data.danhSach || []).map(item => ({
      ...item,
      thoiGian: item.thoiGian ? new Date(item.thoiGian) : new Date()
    }))
    return { thanhCong: true, danhSach }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message, danhSach: [] }
  }
}

export const xoaLichSuChuyenDoi = async (recordId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/history/${recordId}`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (!response.ok) throw new Error('Không thể xóa lịch sử')
    return { thanhCong: true }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

// ── AUTH (JWT - no Firebase) ──────────────────────────────────────────────────
// Auth functions are now managed by AuthContext.jsx
// These are kept for backward-compat imports in components

export const dangNhapVoiEmail = async (email, password) => {
  const resp = await fetch(`${API_BASE_URL}/api/auth/login`, {
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
  const resp = await fetch(`${API_BASE_URL}/api/auth/register`, {
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
  dangNhapVoiEmail,
  dangKyVoiEmail,
  dangXuat,
  theoDoiTrangThaiXacThuc
}
