# SePay Payment Polling Sync

## Muc tieu
Tai lieu nay mo ta luong thanh toan SePay theo co che polling (khong dung webhook) trong he thong Word2LaTeX.

## Thanh phan chinh
- Backend API tao hoa don: /api/payment/create
- Backend API kiem tra trang thai: /api/payment/status/{payment_id}
- Backend API dev fallback: /api/payment/dev/complete/{payment_id}
- Frontend man hinh thanh toan QR: frontend/src/features/premium/TrangThanhToanPremium.jsx
- SePay sync helper: backend/app/services/sepay_sync.py

## Luong xu ly
1. Nguoi dung tao hoa don nap tien tu giao dien Premium.
2. Backend tao ban ghi Payment voi trang thai pending.
3. Backend tao noi dung chuyen khoan theo mau: {NAME_WEB}NAPTOKEN{HEX_ID}.
4. Frontend hien QR code VietQR + noi dung chuyen khoan.
5. Frontend polling /api/payment/status/{id} moi 5 giay.
6. Backend goi SePay API de doi soat giao dich:
   - Neu match so tien + noi dung, cap nhat payment -> completed.
   - Cong token cho user, ghi TokenLedger.
7. Frontend nhan completed, cap nhat UI thanh cong.

## Quy tac doi soat
- Hoa don pending qua 60 phut se duoc danh dau failed.
- He thong van tiep tuc cho phep doi soat giao dich ve muon.
- Kich hoat thanh cong khi tim thay transaction hop le tu SePay.

## Bien moi truong lien quan
- SEPAY_API_KEY
- NAME_WEB
- SECRET_XOR_KEY
- APP_ENV

## Van hanh va su co thuong gap
- pending lau: kiem tra thong bao ngan hang tren dien thoai va key SePay.
- sai noi dung chuyen khoan: khong match payment id.
- dev/local chua co ngan hang that: dung /api/payment/dev/complete/{payment_id}.

## Bao mat
- Khong hard-code SePay key trong source.
- Chi log metadata can thiet, tranh lo thong tin nhay cam.
- Rotate key neu nghi ngo bi lo.

## Test lien quan
- tests/test_payment_polling_sync.py
