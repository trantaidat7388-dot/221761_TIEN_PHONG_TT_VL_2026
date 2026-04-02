# Huong dan lay Google OAuth KEY (Client ID/Client Secret)

Tai lieu nay huong dan tao key cho Google Dang nhap (Redirect Flow) de dung voi du an Word2LaTeX.

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
6. Bam Create, copy:
- Client ID
- Client Secret

## 5) Gan vao file env cua du an
### backend/.env
Cap nhat:

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:5173

### frontend/.env
Cap nhat:

VITE_GOOGLE_CLIENT_ID=your_google_client_id

## 6) Khoi dong lai he thong
Sau khi doi key, can restart backend va frontend de nap lai cau hinh.

## 7) Kiem tra nhanh
1. Mo trinh duyet tai http://localhost:5173
2. Bam Dang nhap Google theo Redirect Flow.
3. Neu cau hinh dung, se di qua Google va quay ve app thanh cong.

## Loi thuong gap
- "Thieu cau hinh GOOGLE_CLIENT_ID": backend chua nap dung bien env hoac chua restart.
- "redirect_uri_mismatch": Redirect URI tren Google Console khong trung 100% voi backend.
- Dang nhap xong quay lai login: kiem tra lai FRONTEND_URL va luong callback.

## Bao mat
- Khong commit file .env len git.
- Khong gui Client Secret len chat/cong khai.
- Neu lo secret, tao secret moi va thu hoi secret cu ngay.
