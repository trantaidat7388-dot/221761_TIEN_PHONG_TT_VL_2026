
export const layThemeHienTai = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/active-theme`)
    if (!response.ok) return { thanhCong: false, theme: 'dark-indigo' }
    const data = await response.json()
    return { thanhCong: true, theme: data.theme || 'dark-indigo' }
  } catch {
    return { thanhCong: false, theme: 'dark-indigo' }
  }
}

export const layNoiDungLandingAdmin = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/landing-content`, {
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, content: data.content || {} }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const capNhatNoiDungLandingAdmin = async (content) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/landing-content`, {
      method: 'PATCH',
      headers: {
        ...taoHeaderXacThuc(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, content: data.content || {} }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const resetNoiDungLandingAdmin = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/landing-content`, {
      method: 'DELETE',
      headers: taoHeaderXacThuc(),
    })
    if (response.status === 401) thongBaoPhienHetHan()
    if (!response.ok) {
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, content: data.content || {} }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

// ── AUTH (JWT - no Firebase) ──────────────────────────────────────────────────

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

// ── CUSTOM PAGES (CMS) APIs ──────────────────────────────────────────────────

export const layDanhSachTrangAdmin = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/pages`, {
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

export const taoTrangAdmin = async (payload) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/pages`, {
      method: 'POST',
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
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const capNhatTrangAdmin = async (slug, payload) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/pages/${slug}`, {
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
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}

export const xoaTrangAdmin = async (slug) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/admin/pages/${slug}`, {
      method: 'DELETE',
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

export const layNoiDungTrangPublic = async (slug) => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/pages/${slug}`)
    if (!response.ok) {
      if (response.status === 404) throw new Error('Không tìm thấy trang')
      const msg = await docLoiJsonTuResponse(response)
      throw new Error(msg)
    }
    const data = await response.json()
    return { thanhCong: true, data }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
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
  layCauHinhHeThongAdmin,
  capNhatCauHinhHeThongAdmin,
  layDanhSachPaymentsAdmin,
  xacNhanPaymentThuCongAdmin,
  dangNhapVoiEmail,
  dangKyVoiEmail,
  dangXuat,
  theoDoiTrangThaiXacThuc,
  layThemeHienTai,
  layNoiDungLandingAdmin,
  capNhatNoiDungLandingAdmin,
  resetNoiDungLandingAdmin,
  layDanhSachTrangAdmin,
  taoTrangAdmin,
  capNhatTrangAdmin,
  xoaTrangAdmin,
  layNoiDungTrangPublic,
  layNoiDungLandingPublic
}
