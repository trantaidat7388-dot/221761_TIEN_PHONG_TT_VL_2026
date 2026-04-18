// ThanhDieuHuong.jsx - Thanh điều hướng chính của ứng dụng

import { useMemo, useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Upload,
  ArrowRightLeft,
  History,
  Crown,
  Settings,
  LogOut,
  User,
  Shield,
  Menu,
  X,
  ChevronDown,
  Coins
} from 'lucide-react'
import toast from 'react-hot-toast'
import { dungXacThuc } from '../context/AuthContext'
import { NapTokenModal } from '../features/premium'


const ThanhDieuHuong = ({ nguoiDung }) => {
  // Component thanh điều hướng với menu responsive và dropdown user
  const { dangXuat, token } = dungXacThuc()
  const location = useLocation()
  const navigate = useNavigate()
  const [menuMo, setMenuMo] = useState(false)
  const [dropdownMo, setDropdownMo] = useState(false)
  const [avatarLoi, setAvatarLoi] = useState(false)
  const [modalNapTokenMo, setModalNapTokenMo] = useState(false)


  // Effect để navigate về trang giới thiệu khi logout
  useEffect(() => {
    if (!token && location.pathname !== '/') {
      navigate('/', { replace: true })
    }
  }, [token, location.pathname, navigate])

  const danhSachMenuCoBan = [
    { duongDan: '/chuyen-doi', nhan: 'Chuyển đổi', icon: Upload },
    { duongDan: '/chuyen-doi-word', nhan: 'Chuyển đổi Word', icon: ArrowRightLeft },
    { duongDan: '/lich-su', nhan: 'Lịch sử', icon: History },
    { duongDan: '/premium', nhan: 'Premium', icon: Crown },
    { duongDan: '/tai-khoan', nhan: 'Tài khoản', icon: Settings },
  ]
  const danhSachMenu = danhSachMenuCoBan

  const xuLyDangXuat = () => {
    // Đăng xuất bằng JWT
    try {
      navigate('/', { replace: true })
      dangXuat()
      toast.success('Đã đăng xuất')
    } catch {
      toast.error('Không thể đăng xuất')
    }
  }

  const layTenHienThi = () => {
    if (nguoiDung?.username) return nguoiDung.username
    if (nguoiDung?.displayName) return nguoiDung.displayName
    if (nguoiDung?.email) return nguoiDung.email.split('@')[0]
    return 'Người dùng'
  }

  const chuCaiDau = useMemo(() => {
    // Lấy chữ cái đầu của tên/email để làm avatar fallback
    const nguon = (nguoiDung?.displayName || nguoiDung?.email || '').trim()
    if (!nguon) return 'U'
    const phan = nguon
      .replace(/\s+/g, ' ')
      .split(' ')
      .filter(Boolean)
    if (phan.length >= 2) return (phan[0][0] + phan[phan.length - 1][0]).toUpperCase()
    return (phan[0]?.slice(0, 2) || 'U').toUpperCase()
  }, [nguoiDung?.displayName, nguoiDung?.email])

  const coTheHienAnh = Boolean(nguoiDung?.photoURL) && !avatarLoi

  return (
    <nav 
      className="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-white/10"
      style={{ paddingTop: 'var(--safe-area-top, env(safe-area-inset-top, 0px))' }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between min-h-[4rem]">
            {/* Logo */}
            <Link
              to="/chuyen-doi"
              className="flex items-center gap-3 group"
            >
              <motion.div
                className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20"
                whileHover={{ scale: 1.05, rotate: 5 }}
                whileTap={{ scale: 0.95 }}
              >
                <FileText className="w-5 h-5 text-white" />
              </motion.div>
              <span className="text-white font-semibold text-lg hidden sm:block group-hover:text-primary-300 transition-colors">
                Word2LaTeX
              </span>
            </Link>

            {/* Menu Desktop */}
            <div className="hidden md:flex items-center gap-1">
              {danhSachMenu.map((item) => {
                const Icon = item.icon
                const dangChon = location.pathname === item.duongDan
                return (
                  <Link
                    key={item.duongDan}
                    to={item.duongDan}
                    className={`
                      flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                      transition-all duration-200
                      ${dangChon
                        ? 'bg-primary-500/20 text-primary-300'
                        : 'text-white/70 hover:text-white hover:bg-white/10'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    {item.nhan}
                  </Link>
                )
              })}
            </div>

            {/* User Menu Desktop */}
            <div className="hidden md:flex items-center gap-4">
              {/* Token Balance Badge */}
              <button
                onClick={() => setModalNapTokenMo(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-amber-500/20 to-amber-600/10 border border-amber-500/30 hover:shadow-lg hover:shadow-amber-500/10 transition-all group"
              >
                <div className="p-1 bg-amber-500 rounded-full group-hover:scale-110 transition-transform shadow-sm">
                  <Coins className="w-3 h-3 text-white" />
                </div>
                <span className="text-amber-300 font-bold text-sm tracking-tight">
                  {new Intl.NumberFormat('vi-VN').format(nguoiDung?.token_balance || 0)}
                  <span className="ml-1 text-[10px] opacity-70 font-medium">TKN</span>
                </span>
              </button>


              <div className="relative">
                <button
                  onClick={() => setDropdownMo(!dropdownMo)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-white/10 transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-primary-500/30 flex items-center justify-center overflow-hidden">
                    {coTheHienAnh ? (
                      <img
                        src={nguoiDung.photoURL}
                        alt="Avatar"
                        className="w-8 h-8 rounded-full"
                        onError={() => setAvatarLoi(true)}
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-primary-500/30 flex items-center justify-center text-primary-200 text-xs font-semibold">
                        {chuCaiDau}
                      </div>
                    )}
                  </div>
                  <span className="text-white/80 text-sm max-w-[120px] truncate">
                    {layTenHienThi()}
                  </span>
                  <ChevronDown className={`w-4 h-4 text-white/50 transition-transform ${dropdownMo ? 'rotate-180' : ''}`} />
                </button>

                <AnimatePresence>
                  {dropdownMo && (
                    <motion.div
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 mt-2 w-48 glass-card py-2 shadow-xl"
                    >
                      <div className="px-4 py-2 border-b border-white/10">
                        <p className="text-white text-sm font-medium truncate">
                          {layTenHienThi()}
                        </p>
                        <p className="text-white/50 text-xs truncate">
                          {nguoiDung?.email}
                        </p>
                      </div>
                      {nguoiDung?.role === 'admin' && (
                        <Link
                          to="/quan-tri"
                          onClick={() => setDropdownMo(false)}
                          className="w-full flex items-center gap-2 px-4 py-2 text-sm text-cyan-300 hover:bg-cyan-500/10 transition-colors"
                        >
                          <Shield className="w-4 h-4" />
                          Cổng quản trị
                        </Link>
                      )}
                      <button
                        onClick={xuLyDangXuat}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        Đăng xuất
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Menu Mobile Toggle */}
            <button
              onClick={() => setMenuMo(!menuMo)}
              className="md:hidden p-2 rounded-xl hover:bg-white/10 transition-colors"
            >
              {menuMo ? (
                <X className="w-6 h-6 text-white" />
              ) : (
                <Menu className="w-6 h-6 text-white" />
              )}
            </button>
          </div>

        {/* Menu Mobile */}
        <AnimatePresence>
          {menuMo && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-white/10 overflow-hidden"
            >
              <div className="px-4 py-4 space-y-2">
                {danhSachMenu.map((item) => {
                  const Icon = item.icon
                  const dangChon = location.pathname === item.duongDan
                  return (
                    <Link
                      key={item.duongDan}
                      to={item.duongDan}
                      onClick={() => setMenuMo(false)}
                      className={`
                        flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium
                        transition-all duration-200
                        ${dangChon
                          ? 'bg-primary-500/20 text-primary-300'
                          : 'text-white/70 hover:text-white hover:bg-white/10'
                        }
                      `}
                    >
                      <Icon className="w-5 h-5" />
                      {item.nhan}
                    </Link>
                  )
                })}

                {/* Token Balance Badge Mobile */}
                <button
                  onClick={() => {
                    setMenuMo(false)
                    setModalNapTokenMo(true)
                  }}
                  className="flex items-center justify-between px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20 w-full"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-500/20 rounded-lg text-amber-400">
                      <Coins className="w-5 h-5" />
                    </div>
                    <span className="text-white font-medium">Số dư Token</span>
                  </div>
                  <span className="text-amber-400 font-bold text-lg">
                    {new Intl.NumberFormat('vi-VN').format(nguoiDung?.token_balance || 0)}
                  </span>
                </button>


                <div className="border-t border-white/10 pt-2 mt-2">
                  {nguoiDung?.role === 'admin' && (
                    <Link
                      to="/quan-tri"
                      onClick={() => setMenuMo(false)}
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-cyan-300 hover:bg-cyan-500/10 transition-colors"
                    >
                      <Shield className="w-5 h-5" />
                      Cổng quản trị
                    </Link>
                  )}
                  <div className="flex items-center gap-3 px-4 py-2">
                    <div className="w-10 h-10 rounded-full bg-primary-500/30 flex items-center justify-center overflow-hidden">
                      {coTheHienAnh ? (
                        <img
                          src={nguoiDung.photoURL}
                          alt="Avatar"
                          className="w-10 h-10 rounded-full"
                          onError={() => setAvatarLoi(true)}
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-primary-500/30 flex items-center justify-center text-primary-200 text-sm font-semibold">
                          {chuCaiDau}
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-medium truncate">
                        {layTenHienThi()}
                      </p>
                      <p className="text-white/50 text-xs truncate">
                        {nguoiDung?.email}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={xuLyDangXuat}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    <LogOut className="w-5 h-5" />
                    Đăng xuất
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Click outside to close dropdown */}
      {dropdownMo && (
        <div
          className="fixed inset-0 z-[-1]"
          onClick={() => setDropdownMo(false)}
        />
      )}

      {/* Modal Nạp Token */}
      <NapTokenModal 
        isOpen={modalNapTokenMo} 
        onClose={() => setModalNapTokenMo(false)} 
      />
    </nav>

  )
}

export default ThanhDieuHuong
