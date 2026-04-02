# Release Runbook - Premium Token Google

Ngay cap nhat: 2026-04-03
Pham vi: Release cho cac ticket DB-001 den REL-001

## 1) Muc tieu release

- Kich hoat he thong premium/token tren backend/frontend.
- Dam bao admin quan ly duoc premium, token, lich su theo user.
- Dam bao luong dang nhap Google co the bat/tat qua cau hinh.

## 2) Pre-flight checklist

- [ ] Backup file DB SQLite hien tai: backend/word2latex.db
- [ ] Xac nhan branch release da merge day du
- [ ] Chay test quan trong:
  - [ ] tests/test_admin_token_audit.py
  - [ ] tests/test_api_smoke.py (hoac smoke subset)
- [ ] Xac nhan bien moi truong da set:
  - [ ] JWT_SECRET_KEY
  - [ ] GOOGLE_CLIENT_ID (backend)
  - [ ] VITE_GOOGLE_CLIENT_ID (frontend)
  - [ ] RATE_LIMIT_AUTH_PER_MINUTE
  - [ ] RATE_LIMIT_CONVERT_PER_MINUTE
  - [ ] RATE_LIMIT_ADMIN_PER_MINUTE

## 3) Trinh tu deploy

1. Stop backend/frontend process.
2. Backup DB:
   - copy backend/word2latex.db -> backend/word2latex.db.bak_YYYYMMDD_HHMMSS
3. Deploy code backend + frontend.
4. Start backend:
   - startup hook tu dong dam bao migration schema DB-001/002/003
   - hoac chay script migration thu cong: c:/221761_TIEN_PHONG_TT_VL_2026/.venv/Scripts/python.exe backend/run_schema_migration.py
5. Start frontend build/reload.
6. Kiem tra health:
   - GET /health = 200
7. Smoke auth/admin:
   - Login admin
   - GET /api/admin/users
   - GET /api/admin/audit-logs
8. Smoke convert:
   - Chuyen doi 1 file nho bang account user
   - Xac nhan token bi tru
   - Xac nhan ledger co ban ghi convert_deduct

## 4) Post-deploy verification

- [ ] Auth me tra ve plan_type va token_balance
- [ ] Admin grant token thanh cong
- [ ] Admin audit log co record action moi
- [ ] Lich su chuyen doi co pages_count/token_cost
- [ ] Luong Google login thanh cong (neu da set GOOGLE_CLIENT_ID)

## 5) Rollback 1 lenh (muc van hanh)

Neu release co van de nang:
1. Stop backend/frontend.
2. Revert code ve commit truoc release.
3. Restore DB tu backup gan nhat:
   - replace backend/word2latex.db bang file .bak
4. Start lai backend/frontend.
5. Kiem tra /health va login admin.

## 6) Known caveats

- Neu chua set GOOGLE_CLIENT_ID, nut Google van hien nhung khong dang nhap duoc.
- Rate limit la in-memory theo process; neu scale nhieu instance can doi sang Redis.
- SQLite phu hop pre-release; production nen chuyen sang PostgreSQL + migration tool chinh thuc.

## 7) Incident response nhanh

- Loi 401/403 bat thuong:
  - Kiem tra JWT_SECRET_KEY, role user, token het han.
- Loi 429 tang dot bien:
  - Kiem tra cau hinh RATE_LIMIT_*.
- Loi token so du am (khong ky vong):
  - Tam khoa endpoint convert, doi soat token_ledger va user.token_balance.
