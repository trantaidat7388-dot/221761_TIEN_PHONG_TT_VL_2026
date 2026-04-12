# Admin Governance Roadmap

## Muc tieu
Xac dinh pham vi quan tri, trang thai hien tai va cac viec can hoan thien de dat muc admin quan ly toan bo he thong.

## Trang thai hien tai
### Da co
- Dang nhap admin rieng: /quan-tri/dang-nhap
- Dashboard admin rieng: /quan-tri
- Quan ly nguoi dung: role, premium, cong/tru token, xoa user
- Quan ly payment: xem danh sach, xac nhan thu cong
- Quan ly template: xem/xoa/tai len
- Quan ly audit log
- Quan ly cau hinh qua API: /api/admin/system-config

### Chua full
- Chua co co che versioning/rollback cho cau hinh he thong
- Chua co phan quyen chi tiet theo nhom admin (super admin, moderator, support)
- Chua co trang dashboard canh bao bao mat/tuan thu

## Kien truc quyen (de xuat)
- role=user: chuc nang nguoi dung thuong
- role=admin: quan tri van hanh
- role=super_admin (backlog): quan tri cau hinh nhay cam va nhan su

## Checklist governance
- [x] Bat buoc token JWT + role check cho route admin
- [x] Audit log cho hanh dong quan tri quan trong
- [x] Endpoint thong ke tong quan
- [x] Endpoint quan ly payment va token
- [x] Endpoint quan ly cau hinh co xac thuc admin
- [ ] Chinh sach phan quyen cap cao (super_admin)
- [ ] Chinh sach rotate secret key dinh ky
- [ ] Dashboard canh bao anomaly cho luong admin

## Backlog uu tien
1. Them role super_admin va route chi doc danh cho support.
2. Them xac nhan 2 buoc cho action nguy co cao (xoa user, tru token lon).
3. Bo sung lich su thay doi cau hinh (who/when/old/new).
4. Bo sung e2e test cho luong admin config.

## Test lien quan hien co
- tests/test_admin_token_audit.py
- tests/test_rate_limit_convert_admin.py
- tests/test_token_deduct_refund.py
