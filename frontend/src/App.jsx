// App.jsx - Component gốc của ứng dụng Word2LaTeX

import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { BoBaoBocXacThuc, dungXacThuc } from './context/AuthContext'
import { ThanhDieuHuong } from './components'
import { TrangDangNhap } from './features/xac_thuc'
import { TrangChuyenDoi, TrangChuyenDoiWordToWord } from './features/chuyen_doi'
import { TrangLichSu } from './features/lich_su'
import { TrangAdmin } from './features/admin'
import { TrangTaiKhoan } from './features/tai_khoan'
import { TrangPremium, TrangThanhToanPremium } from './features/premium'
import { TrangLanding } from './features/landing'
import { ThemeProvider } from './features/admin/context/AdminThemeContext'

// Layout chung cho các trang có thanh điều hướng
const BoCucChung = () => {
  const { nguoiDung } = dungXacThuc()
  if (!nguoiDung) return <Navigate to="/" replace />
  return (
    <>
      <ThanhDieuHuong nguoiDung={nguoiDung} />
      <Outlet />
    </>
  )
}

const CacTuyenUngDung = () => {
  const { token, nguoiDung } = dungXacThuc()

  return (
    <Routes>
      {/* Route công khai */}
      <Route path="/" element={nguoiDung ? <Navigate to="/chuyen-doi" replace /> : <TrangLanding />} />
      <Route
        path="/dang-nhap"
        element={nguoiDung ? <Navigate to="/chuyen-doi" replace /> : <TrangDangNhap />}
      />


      {/* Routes yêu cầu đăng nhập */}
      <Route element={<BoCucChung />}>
        <Route
          path="/chuyen-doi"
          element={nguoiDung ? <TrangChuyenDoi nguoiDung={nguoiDung} /> : <Navigate to="/dang-nhap" replace />}
        />
        <Route
          path="/chuyen-doi-word"
          element={nguoiDung ? <TrangChuyenDoiWordToWord /> : <Navigate to="/dang-nhap" replace />}
        />
        <Route
          path="/lich-su"
          element={nguoiDung ? <TrangLichSu nguoiDung={nguoiDung} /> : <Navigate to="/dang-nhap" replace />}
        />
        <Route
          path="/tai-khoan"
          element={nguoiDung ? <TrangTaiKhoan /> : <Navigate to="/dang-nhap" replace />}
        />
        <Route
          path="/premium"
          element={nguoiDung ? <TrangPremium /> : <Navigate to="/dang-nhap" replace />}
        />
        <Route
          path="/thanh-toan"
          element={nguoiDung ? <TrangThanhToanPremium /> : <Navigate to="/dang-nhap" replace />}
        />
      </Route>

      {/* Admin GUI tách riêng */}
      <Route
        path="/quan-tri"
        element={token && nguoiDung?.role === 'admin' ? <TrangAdmin /> : <Navigate to={token && nguoiDung ? '/chuyen-doi' : '/dang-nhap'} replace />}
      />

      {/* Redirect mặc định */}
      <Route
        path="*"
        element={<Navigate to={nguoiDung ? '/chuyen-doi' : '/'} replace />}
      />
    </Routes>
  )
}

const UngDung = () => (
  <ThemeProvider>
    <BoBaoBocXacThuc>
      <CacTuyenUngDung />
    </BoBaoBocXacThuc>
  </ThemeProvider>
)

export default UngDung
