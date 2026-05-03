import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'
import {
  layTongQuanAdmin,
  layDanhSachNguoiDungAdmin,
  layLichSuToanHeThongAdmin,
  layAuditLogsAdmin,
  layDanhSachPaymentsAdmin,
  layCauHinhHeThongAdmin,
  layDanhSachTemplateAdmin,
  layTokenLedgerToanHeThongAdmin,
} from '../../../services/api'

export const useAdminData = () => {
  const [dangTai, setDangTai] = useState(true)
  const [tongQuan, setTongQuan] = useState(null)
  const [danhSachNguoiDung, setDanhSachNguoiDung] = useState([])
  const [danhSachLichSu, setDanhSachLichSu] = useState([])
  const [danhSachTemplate, setDanhSachTemplate] = useState([])
  const [danhSachAuditLogs, setDanhSachAuditLogs] = useState([])
  const [danhSachTokenLedger, setDanhSachTokenLedger] = useState([])
  const [danhSachPayments, setDanhSachPayments] = useState([])
  const [cauHinhMeta, setCauHinhMeta] = useState(null)
  const [cauHinhHeThong, setCauHinhHeThong] = useState({
    token_min_cost_vnd: 1,
    free_plan_max_pages: 60,
    max_doc_upload_mb: 10,
    rate_limit_admin_per_minute: 120,
  })

  const taiDuLieu = useCallback(async () => {
    setDangTai(true)
    try {
      const [overviewRes, usersRes, historyRes, auditRes, paymentsRes, systemConfigRes, ledgerRes] = await Promise.all([
        layTongQuanAdmin(),
        layDanhSachNguoiDungAdmin(),
        layLichSuToanHeThongAdmin(200),
        layAuditLogsAdmin(200),
        layDanhSachPaymentsAdmin(200),
        layCauHinhHeThongAdmin(),
        layTokenLedgerToanHeThongAdmin(200),
      ])
      const templatesRes = await layDanhSachTemplateAdmin()

      if (overviewRes.thanhCong) setTongQuan(overviewRes.data)
      if (usersRes.thanhCong) setDanhSachNguoiDung(usersRes.danhSach)
      if (historyRes.thanhCong) setDanhSachLichSu(historyRes.danhSach)
      if (auditRes.thanhCong) setDanhSachAuditLogs(auditRes.danhSach)
      if (ledgerRes.thanhCong) setDanhSachTokenLedger(ledgerRes.danhSach)
      if (templatesRes.thanhCong) setDanhSachTemplate(templatesRes.danhSach)
      if (paymentsRes.thanhCong) setDanhSachPayments(paymentsRes.danhSach)
      if (systemConfigRes.thanhCong && systemConfigRes.data?.settings) {
        setCauHinhHeThong({
          token_min_cost_vnd: Number(systemConfigRes.data.settings.token_min_cost_vnd || 1),
          free_plan_max_pages: Number(systemConfigRes.data.settings.free_plan_max_pages || 60),
          max_doc_upload_mb: Number(systemConfigRes.data.settings.max_doc_upload_mb || 10),
          rate_limit_admin_per_minute: Number(systemConfigRes.data.settings.rate_limit_admin_per_minute || 120),
        })
        setCauHinhMeta(systemConfigRes.data.meta || null)
      }
    } catch (error) {
      toast.error(error.message || 'Khong the tai du lieu trang Admin')
    } finally {
      setDangTai(false)
    }
  }, [])

  return {
    dangTai,
    tongQuan,
    danhSachNguoiDung, setDanhSachNguoiDung,
    danhSachLichSu, setDanhSachLichSu,
    danhSachTemplate, setDanhSachTemplate,
    danhSachAuditLogs,
    danhSachTokenLedger, setDanhSachTokenLedger,
    danhSachPayments, setDanhSachPayments,
    cauHinhMeta, setCauHinhMeta,
    cauHinhHeThong, setCauHinhHeThong,
    taiDuLieu
  }
}
