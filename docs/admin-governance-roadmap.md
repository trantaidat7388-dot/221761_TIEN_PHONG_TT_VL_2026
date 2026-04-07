# Admin Governance Roadmap

## 1) Checklist chuan cho trang Admin

### Must-have (bat buoc)
- [x] Phan quyen route Admin o frontend
- [x] Phan quyen endpoint Admin o backend
- [x] Quan ly user (list, role, premium, token)
- [x] Quan ly lich su chuyen doi (xem/xoa)
- [x] Quan ly template toan he thong (xem/xoa)
- [x] Hien thi audit logs tren UI Admin
- [x] Ghi audit khi thay doi role/premium/token/xoa user/xoa history/xoa template
- [x] Chan user thuong upload/xoa template toan he thong

### Should-have (nen co)
- [ ] Loc va tim kiem audit logs theo actor/action/time/request_id
- [ ] Loc user theo role/plan/trang thai hoat dong
- [ ] Soft delete user thay vi hard delete
- [ ] Xac nhan 2 buoc cho thao tac nguy hiem (xoa user, tru token lon)
- [ ] Quan ly payment/topup cho admin

### Nice-to-have (tot neu co)
- [ ] Role cap 2 (support/moderator)
- [ ] Dashboard suc khoe he thong (ti le loi, thoi gian xu ly TB)
- [ ] Canh bao bat thuong token/abuse

## 2) De xuat kien truc quyen cho Template Management

### Muc tieu
- Tach ro tai nguyen he thong va tai nguyen nguoi dung.
- Tranh chong cheo giua trang Chuyen doi va trang Admin.

### Mo hinh de xuat
- Global templates:
  - So huu boi he thong.
  - Chi Admin duoc upload/delete.
  - Moi user duoc read/list de chon khi convert.
- Personal templates:
  - So huu boi user.
  - User duoc CRUD tren template cua chinh minh.
  - Khong anh huong den user khac.

### API map de xuat
- Global:
  - GET /api/templates (public authenticated read)
  - POST /api/templates/upload (admin only)
  - DELETE /api/templates/{template_id} (admin only)
- Personal:
  - GET /api/my-templates
  - POST /api/my-templates/upload
  - DELETE /api/my-templates/{template_id}

### UI map de xuat
- Trang Chuyen doi:
  - Luon hien chon template.
  - Chi hien panel quan ly neu la Admin (global) hoac user co personal templates.
- Trang Admin:
  - Quan ly Global templates day du (upload/delete/audit).

## 3) Backlog uu tien (risk x effort)

### P0 (thuc hien ngay)
1. Day du audit tren UI Admin (list + columns can ban).
2. Khoa upload/delete template voi non-admin.
3. An panel quan ly template tren trang Chuyen doi neu khong phai admin.

### P1
1. Bo sung API + UI quan ly payment cho admin (loc theo status, user, time).
2. Bo sung bo loc user va audit log.
3. Chuyen xoa user sang soft delete.

### P2
1. Role support/moderator + phan quyen theo action.
2. Dashboard SLO chuyen doi (success rate, p95 processing time).
3. Rules canh bao bat thuong token.

## 4) KPI de do chat luong quan tri
- Tyle thao tac admin co audit: 100%.
- Tyle thao tac nguy hiem co xac nhan 2 buoc: >= 95%.
- Thoi gian truy vet su co qua request_id: < 10 phut.
- Tyle loi phan quyen (403 expected) dat dung theo test: 100%.
