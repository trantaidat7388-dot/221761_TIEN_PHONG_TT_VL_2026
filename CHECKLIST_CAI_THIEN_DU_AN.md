# Checklist cai thien du an Word2LaTeX

## P0 - Bat buoc lam truoc (bao mat va an toan)

- [x] Chuyen SECRET_KEY JWT sang bien moi truong, khong hardcode trong ma nguon.
- [x] Them co che rotate key va tai lieu huong dan cap nhat key an toan.
- [x] Va loi Zip Slip trong API upload template (chan path traversal truoc khi extract).
- [x] Bo sung kiem tra kich thuoc va whitelist duoi file khi upload ZIP/Template.
- [x] Ra soat va giam cac diem `except Exception: pass` trong luong chuyen doi.

## P1 - On dinh va van hanh

- [x] Chuan hoa logging (thay print bang logging co cap do INFO/WARN/ERROR).
- [x] Gan request_id/job_id cho log de truy vet loi theo phien.
- [x] Tach cau hinh CORS, TTL, timeout qua bien moi truong co gia tri mac dinh ro rang.
- [x] Dieu chinh `start.bat` tranh kill tat ca python.exe/node.exe toan he thong.
- [x] Them script start cho Linux/macOS de de van hanh da nen tang.

## P2 - Chat luong ma va bao tri

- [x] Han che monkey patch global `python-docx` hoac dong goi patch thanh module rieng co test.
- [x] Tach bot logic dai trong `core_engine/chuyen_doi.py` thanh nhieu service nho theo SRP.
- [x] Chuan hoa dat ten ham/bien (de doc hon khi team phat trien mo rong).
- [x] Bo sung type hints day du cho cac ham public trong backend.
- [x] Bo sung docs cho cac branch fallback quan trong (docm, strict XML, compile fallback).

## P3 - Test va CI/CD

- [x] Chuyen cac test script thu cong thanh test co the chay tu dong voi pytest.
- [x] Loai bo hard-coded path trong test, dung fixture va duong dan tuong doi.
- [x] Them smoke test cho cac endpoint chinh (`/api/chuyen-doi-stream`, `/api/templates/upload`).
- [x] Tao workflow CI (lint + test) tren GitHub Actions.
- [x] Them regression test cho cac loi da gap (math, table, template injection).

## P4 - Frontend va bao mat phien dang nhap

- [ ] Danh gia chuyen tu localStorage token sang httpOnly cookie neu trien khai internet.
- [ ] Them xu ly refresh token hoac silent re-auth.
- [ ] Cai thien thong diep loi UX khi SSE mat ket noi giua chung.
- [ ] Them e2e test cho dang nhap, chuyen doi, tai file zip/pdf.

## Theo doi tien do

- [ ] Dat moc hoan thanh P0
- [x] Dat moc hoan thanh P1
- [x] Dat moc hoan thanh P2
- [x] Dat moc hoan thanh P3
- [ ] Dat moc hoan thanh P4
