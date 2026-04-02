# Huong dan lay Google Client ID cho du an

Tai lieu nay chi can khi ban muon bat dang nhap Google.
Neu chua can, co the bo qua va he thong van chay auth local binh thuong.

## 1) Tao du an tren Google Cloud Console

1. Mo https://console.cloud.google.com/
2. Tao Project moi hoac chon project san co.
3. Bat API "Google Identity" neu duoc yeu cau.

## 2) Cau hinh OAuth Consent Screen

1. Vao APIs & Services -> OAuth consent screen.
2. Chon User Type (External/Internal tuy nhu cau).
3. Dien thong tin co ban: app name, support email.
4. Them Authorized domains (neu co domain that).
5. Save va publish consent screen (co the de Testing o pre-release).

## 3) Tao OAuth Client ID cho Web

1. Vao APIs & Services -> Credentials.
2. Chon Create Credentials -> OAuth client ID.
3. Application type: Web application.
4. Dat ten client.
5. Them Authorized JavaScript origins:
   - http://localhost:5173
   - URL frontend production (neu co)
6. (Neu can redirect flow) them Authorized redirect URIs.
7. Create.

Ket qua ban nhan duoc:
- Client ID (dung duoc o frontend va backend verify audience)
- Client Secret (khong bat buoc cho flow id_token hien tai)

Luu y bao mat:
- Khong paste Client Secret len chat/repo.
- Flow dang nhap hien tai cua du an chi can Client ID, khong can Client Secret.
- Neu secret da bi lo, hay rotate ngay trong Google Cloud Console.

## 4) Set bien moi truong cho du an nay

Backend (.env hoac env runtime):
- GOOGLE_CLIENT_ID=<your_google_client_id>

Frontend (Vite env):
- VITE_GOOGLE_CLIENT_ID=<your_google_client_id>

## 5) Kiem tra nhanh

1. Khoi dong lai backend/frontend sau khi set env.
2. Mo trang dang nhap.
3. Nhan nut Google.
4. Dang nhap thanh cong se tra ve JWT cua he thong.

## 6) Loi thuong gap

- Loi "Google token sai client_id":
  - GOOGLE_CLIENT_ID backend khong khop client id tren frontend.
- Nut Google khong hien:
  - Chua set VITE_GOOGLE_CLIENT_ID.
  - Origin localhost chua duoc khai bao trong Google Console.
- Dang nhap that bai o moi truong production:
  - Domain production chua them vao Authorized JavaScript origins.
