# Checklist thuc thi Premium/Token - Uu tien DB-001 den DB-003

Ngay tao: 2026-04-03
Trang thai tong: In Progress

## 1) Muc tieu phase hien tai

- Hoan tat thiet ke du lieu nen tang cho Premium, Token va lich su chuyen doi.
- Khoa pham vi phase nay vao 3 ticket dau tien:
  - DB-001
  - DB-002
  - DB-003
- Chua lam ticket BE/FE tiep theo cho den khi 3 ticket DB da Done va qua review.

## 2) Bang theo doi nhanh

| Ticket | Uu tien | Trang thai | Owner | Bat dau | Deadline | Blocker |
|---|---|---|---|---|---|---|
| DB-001 | P0 | TODO |  |  |  |  |
| DB-002 | P0 | TODO |  |  |  |  |
| DB-003 | P0 | TODO |  |  |  |  |

Quy uoc trang thai:
- TODO
- IN PROGRESS
- REVIEW
- DONE
- BLOCKED

## 3) Ticket chi tiet

## DB-001 - Mo rong bang users cho premium/token/google

### Scope bat buoc
- [ ] Them cot plan_type (free/premium).
- [ ] Them cot token_balance (int, non-null, default).
- [ ] Them cot premium_started_at.
- [ ] Them cot premium_expires_at.
- [ ] Them cot auth_provider (local/google).
- [ ] Them cot google_id (nullable, unique neu co gia tri).

### Rang buoc DB
- [ ] Index cho plan_type.
- [ ] Index cho premium_expires_at.
- [ ] Unique constraint cho google_id.
- [ ] Check default cho user cu (backfill free/local).

### Migration + rollback
- [ ] Tao migration script len.
- [ ] Tao migration rollback script xuong.
- [ ] Chay migration tren local DB sach.
- [ ] Chay migration tren local DB da co du lieu user.
- [ ] Xac nhan rollback khong mat du lieu quan trong.

### Model/backend dong bo
- [ ] Cap nhat model User trong backend.
- [ ] Cap nhat serializer/response auth/me de tra plan va token.
- [ ] Cap nhat tai lieu API noi bo.

### Done criteria DB-001
- [ ] Schema users da co du cac cot moi.
- [ ] User cu van dang nhap duoc sau migration.
- [ ] Unit test co ban pass.

---

## DB-002 - Tao bang token_ledger

### Scope bat buoc
- [ ] Tao bang token_ledger voi cac truong:
  - id
  - user_id
  - delta_token
  - balance_after
  - reason
  - job_id (nullable)
  - meta_json (nullable)
  - created_at

### Rang buoc DB
- [ ] FK token_ledger.user_id -> users.id.
- [ ] Index (user_id, created_at desc).
- [ ] Index reason.
- [ ] Rule delta co the am/duong (deduct/refund/grant).

### Migration + rollback
- [ ] Tao migration script len.
- [ ] Tao migration rollback script xuong.
- [ ] Test tao 1000 records ledger va query phan trang.

### Service contract (skeleton)
- [ ] Dinh nghia ham ghi ledger chung (chua can gan convert).
- [ ] Validate khong cho ghi ledger neu user_id khong ton tai.

### Done criteria DB-002
- [ ] Co the ghi ledger thu cong qua script test.
- [ ] Co the query ledger theo user nhanh va dung thu tu.
- [ ] Khong co loi FK/index sau migration.

---

## DB-003 - Mo rong bang conversion_history

### Scope bat buoc
- [ ] Them cot pages_count.
- [ ] Them cot token_cost.
- [ ] Them cot token_refunded (bool, default false).
- [ ] Them cot error_type (nullable).
- [ ] Them cot error_message (nullable).

### Rang buoc DB
- [ ] Index cho user_id + created_at (neu chua co thi bo sung).
- [ ] Index cho token_refunded.
- [ ] Backfill ban ghi cu voi gia tri mac dinh an toan.

### Migration + rollback
- [ ] Tao migration script len.
- [ ] Tao migration rollback script xuong.
- [ ] Chay migration tren du lieu lich su da ton tai.

### Dong bo model/backend
- [ ] Cap nhat model ConversionHistory.
- [ ] Chuan bi contract cho BE ticket tiep theo (gan token engine).

### Done criteria DB-003
- [ ] Ban ghi lich su moi co du truong pages/token.
- [ ] Ban ghi cu van doc duoc tren API lich su.
- [ ] Khong vo UI lich su hien tai.

## 4) Thu tu thuc hien de tranh xung dot

- [ ] Lam DB-001 truoc.
- [ ] Sau khi DB-001 done + review, moi bat dau DB-002.
- [ ] Sau khi DB-002 done + review, moi bat dau DB-003.

## 5) Kiem thu phase DB-001 -> DB-003

### Kiem thu ky thuat
- [ ] Chay test smoke auth/me sau migration.
- [ ] Chay test smoke lich su sau migration.
- [ ] Chay test truy van ledger theo user.

### Kiem thu du lieu
- [ ] User cu khong bi mat tai khoan.
- [ ] Lich su cu khong bi mat ban ghi.
- [ ] Co script doi soat schema truoc/sau migration.

### Kiem thu van hanh
- [ ] Co huong dan backup DB truoc migration.
- [ ] Co huong dan rollback 1 lenh.
- [ ] Co changelog cho team FE/BE.

## 6) Nhat ky cap nhat

| Ngay | Ticket | Cap nhat | Nguoi cap nhat |
|---|---|---|---|
| 2026-04-03 | Setup | Tao checklist phase DB-001 -> DB-003 |  |

## 7) Gate de mo phase tiep theo

Chi duoc bat dau BE-001 tro di khi tat ca dieu kien sau dat:
- [ ] DB-001 = DONE
- [ ] DB-002 = DONE
- [ ] DB-003 = DONE
- [ ] Da review schema va migration voi team
- [ ] Da xac nhan rollback thuc te
