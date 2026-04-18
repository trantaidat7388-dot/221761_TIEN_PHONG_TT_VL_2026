# Huong dan lay Google OAuth KEY (Client ID/Client Secret)

Tai lieu nay huong dan tao key cho Google Dang nhap (Redirect Flow) de dung voi du an Word2LaTeX.

## 0) Sau khi clone ve may moi/odia khac, tao file env dung vi tri

Vi du ban clone vao:

D:\du-an\221761_TIEN_PHONG_TT_VL_2026

Thi bat buoc phai co 2 file sau:

- D:\du-an\221761_TIEN_PHONG_TT_VL_2026\backend\.env
- D:\du-an\221761_TIEN_PHONG_TT_VL_2026\frontend\.env

Neu thieu 1 trong 2 file nay, he thong se bao thieu key.

### Cach tao nhanh (PowerShell - Windows)

1. Mo terminal tai thu muc goc du an.
2. Chay lenh:

Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env

### Cach tao nhanh (macOS/Linux)

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

## 1) Tao hoac chon Project tren Google Cloud
1. Mo trang: https://console.cloud.google.com/
2. Chon project san co hoac tao project moi.

## 2) Bat API can thiet
1. Vao **APIs & Services > Library**.
2. Tim va bat **Google People API** (khuyen nghi bat).

## 3) Cau hinh OAuth consent screen
1. Vao **APIs & Services > OAuth consent screen**.
2. Chon loai app:
- External (thong dung)
3. Dien thong tin co ban (App name, support email...).
4. Them email cua ban vao Test users (neu app dang o trang thai Testing).

## 4) Tao OAuth Client ID
1. Vao **APIs & Services > Credentials**.
2. Chon **Create Credentials > OAuth client ID**.
3. Application type: **Web application**.
4. Dat ten cho client.
5. Them cac gia tri sau:
- Authorized JavaScript origins:
  - http://localhost:5173
- Authorized redirect URIs:
  - http://localhost:8000/api/auth/google/callback
  - http://localhost:8000/api/auth/google/callback/flutter (Dành cho Mobile)
6. Bam Create, copy:
- Client ID
- Client Secret

## 5) Gan vao file env cua du an
### backend/.env
Cap nhat:

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
GOOGLE_REDIRECT_URI_FLUTTER=http://localhost:8000/api/auth/google/callback/flutter
FRONTEND_URL=http://localhost:5173

### frontend/.env
Cap nhat:

VITE_GOOGLE_CLIENT_ID=your_google_client_id

Luu y:
- `backend/.env` chua key backend (GOOGLE_CLIENT_SECRET) va backend doc file nay luc khoi dong.
- `frontend/.env` chi can `VITE_GOOGLE_CLIENT_ID`.
- Neu doi o dia hoac doi thu muc clone, van phai tao 2 file tren theo duong dan moi.

## 6) Khoi dong lai he thong
Sau khi doi key, can restart backend va frontend de nap lai cau hinh.

## 7) Kiem tra nhanh
1. Mo trinh duyet tai http://localhost:5173
2. Bam Dang nhap Google theo Redirect Flow.
3. Neu cau hinh dung, se di qua Google va quay ve app thanh cong.

Kiem tra backend da nhan key chua:
- Mo URL: http://localhost:8000/api/auth/google/login
- Neu backend redirect sang `accounts.google.com` la da doc duoc `backend/.env`.
- Neu bao thieu `GOOGLE_CLIENT_ID` thi ban dang tao sai vi tri file `backend/.env` hoac chua restart backend.

## Loi thuong gap
- "Thieu cau hinh GOOGLE_CLIENT_ID": backend chua nap dung bien env hoac chua restart.
- "redirect_uri_mismatch": Redirect URI tren Google Console khong trung 100% voi backend.
- Dang nhap xong quay lai login: kiem tra lai FRONTEND_URL va luong callback.

## Bao mat
- Khong commit file .env len git.
- Khong gui Client Secret len chat/cong khai.
- Neu lo secret, tao secret moi va thu hoi secret cu ngay.
