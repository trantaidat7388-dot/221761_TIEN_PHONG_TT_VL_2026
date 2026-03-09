// App.jsx - Component gốc của ứng dụng Word2LaTeX

import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThanhDieuHuong, LoadingManHinh } from './components'
import { TrangDangNhap } from './features/xac_thuc'
import { TrangChuyenDoi } from './features/chuyen_doi'
import { TrangLichSu } from './features/lich_su'

// Layout chung cho các trang có thanh điều hướng
const LayoutChung = () => {
  const { user } = useAuth()
  if (!user) return <Navigate to="/dang-nhap" replace />
  return (
    <>
      <ThanhDieuHuong nguoiDung={user} />
      <Outlet />
    </>
  )
}

const AppRoutes = () => {
  const { user } = useAuth()

  return (
    <Routes>
      {/* Route công khai */}
      <Route
        path="/dang-nhap"
        element={user ? <Navigate to="/chuyen-doi" replace /> : <TrangDangNhap />}
      />

      {/* Routes yêu cầu đăng nhập */}
      <Route element={<LayoutChung />}>
        <Route
          path="/chuyen-doi"
          element={user ? <TrangChuyenDoi nguoiDung={user} /> : <Navigate to="/dang-nhap" replace />}
        />
        <Route
          path="/lich-su"
          element={user ? <TrangLichSu nguoiDung={user} /> : <Navigate to="/dang-nhap" replace />}
        />
      </Route>

      {/* Redirect mặc định */}
      <Route
        path="*"
        element={<Navigate to={user ? '/chuyen-doi' : '/dang-nhap'} replace />}
      />
    </Routes>
  )
}

const App = () => (
  <AuthProvider>
    <AppRoutes />
  </AuthProvider>
)

export default App
