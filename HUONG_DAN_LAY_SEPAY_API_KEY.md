# Huong dan chi tiet lay SePay API Key

Tai lieu nay huong dan tung buoc de lay API key tu SePay va cau hinh vao he thong Word2LaTeX.

---

## Muc luc

1. [Dieu kien truoc khi bat dau](#1-dieu-kien-truoc-khi-bat-dau)
2. [Dang ky tai khoan SePay](#2-dang-ky-tai-khoan-sepay)
3. [Lien ket tai khoan ngan hang](#3-lien-ket-tai-khoan-ngan-hang)
4. [Tao API Key](#4-tao-api-key)
5. [Cau hinh vao du an](#5-cau-hinh-vao-du-an)
6. [Kiem tra key da hoat dong](#6-kiem-tra-key-da-hoat-dong)
7. [Checklist cau hinh day du](#7-checklist-cau-hinh-day-du)
8. [Loi thuong gap va xu ly](#8-loi-thuong-gap-va-xu-ly)
9. [Bao mat](#9-bao-mat)
10. [Thong tin ky thuat chi tiet](#10-thong-tin-ky-thuat-chi-tiet)

---

## 1. Dieu kien truoc khi bat dau

Truoc khi cau hinh SePay, ban can chuan bi:

- [ ] Tai khoan SePay: https://my.sepay.vn (dang ky mien phi)
- [ ] It nhat 1 tai khoan ngan hang ho tro (MB Bank, Vietcombank, VPBank, BIDV, ACB, ...)
- [ ] Dien thoai cai app ngan hang tuong ung
- [ ] Bat thong bao bien dong so du tren app ngan hang

> **Luu y:** SePay hoat dong bang cach doc thong bao bien dong so du tu app ngan hang tren dien thoai. Neu tat thong bao, SePay khong the dong bo giao dich.

---

## 2. Dang ky tai khoan SePay

1. Truy cap `https://my.sepay.vn` tren trinh duyet.
2. Nhan **"Dang ky"** neu chua co tai khoan.
3. Dien thong tin:
   - Ho ten (theo CMND/CCCD)
   - Email (de nhan xac nhan)
   - So dien thoai (dang ky app ngan hang)
   - Mat khau
4. Xac nhan email qua link gui ve hop thu.
5. Dang nhap vao dashboard SePay.

---

## 3. Lien ket tai khoan ngan hang

Sau khi dang nhap SePay dashboard:

1. Vao menu **"Ngan hang"** hoac **"Tai khoan"**.
2. Nhan **"Them tai khoan ngan hang"**.
3. Chon ngan hang cua ban (VD: MB Bank).
4. Nhap thong tin:
   - So tai khoan ngan hang
   - Ten chu tai khoan (tu dong dien khi nhap dung so TK)
5. Xac nhan voi ma OTP gui den SĐT dang ky.
6. Tren dien thoai:
   - Mo app ngan hang (MB Bank, VCB, ...)
   - Dam bao da bat **quyen thong bao** cho app
   - Dam bao **thong bao bien dong so du dang bat**
7. Kiem tra: vao tab "Giao dich" tren SePay → chuyen khoan thu 1 giao dich nho → xem SePay co hien thi giao dich khong.

> **Giai thich:** SePay su dung co che "doc thong bao" tren dien thoai de biet khi nao co tien vao tai khoan. Dien thoai can bat, khong tat man hinh lau, va da cap quyen cho SePay app.

---

## 4. Tao API Key

1. Trong SePay dashboard, vao menu **"Cai dat"** → **"API"** (hoac truyen vao `https://my.sepay.vn/settings/api`).
2. Nhan **"Tao API Key moi"**.
3. Dat ten cho key, vi du:
   - `word2latex-dev` (cho moi truong development)
   - `word2latex-prod` (cho moi truong production)
4. **Copy key** ngay lap tuc - SePay chi hien thi key **MỘT LẦN DUY NHẤT**.
5. Luu key vao noi an toan (password manager, file .env).

> **Quan trong:** Neu mat key, ban phai tao key moi va cap nhat lai file .env.

### Cac loai quyen API

SePay API cho phep:
- **Doc giao dich** (`GET /userapi/transactions/list`) - day la API chinh ma he thong Word2LaTeX su dung
- **Doc thong tin tai khoan** - xem so du, thong tin ngan hang
- He thong Word2LaTeX chi can quyen **doc giao dich** de doi soat thanh toan.

---

## 5. Cau hinh vao du an

### 5.1. File backend/.env

Mo file `backend/.env` va them/cap nhat 3 bien sau:

```env
# SePay Payment Gateway
SEPAY_API_KEY=your_sepay_api_key_here
NAME_WEB=W2L
SECRET_XOR_KEY=387835
```

Giai thich tung bien:

| Bien | Gia tri | Muc dich |
|---|---|---|
| `SEPAY_API_KEY` | Key lay tu SePay dashboard | Xac thuc khi goi SePay API |
| `NAME_WEB` | `W2L` (hoac ten web cua ban) | Prefix noi dung chuyen khoan, VD: `W2LNAPTOKEN5EAAB` |
| `SECRET_XOR_KEY` | So nguyen bat ky | Dung de ma hoa payment ID thanh HEX, moi du an nen dung gia tri rieng |

### 5.2. File frontend/.env (tuy chon)

Neu ban da co thong tin ngan hang thuc te, them vao `frontend/.env`:

```env
# Bank info for QR code generation
VITE_BANK_BIN=970422
VITE_BANK_ACCOUNT=0123456789
VITE_BANK_ACCOUNT_NAME=NGUYEN VAN A
```

| Bien | Vi du | Mo ta |
|---|---|---|
| `VITE_BANK_BIN` | `970422` (MB Bank) | Ma BIN ngan hang (tra cuu tai vietqr.io) |
| `VITE_BANK_ACCOUNT` | `0123456789` | So tai khoan ngan hang nhan tien |
| `VITE_BANK_ACCOUNT_NAME` | `NGUYEN VAN A` | Ten chu tai khoan |

> **Ma BIN pho bien:**
> - MB Bank: `970422`
> - Vietcombank: `970436`
> - VPBank: `970432`
> - BIDV: `970418`
> - ACB: `970416`
> - Techcombank: `970407`

### 5.3. Khoi dong lai backend

```powershell
# Windows PowerShell
python run_api.py
```

```bash
# Linux / macOS
python run_api.py
```

---

## 6. Kiem tra key da hoat dong

### Buoc 1: Kiem tra API key bang curl/browser

```bash
curl -H "Authorization: Bearer YOUR_SEPAY_API_KEY" \
     https://my.sepay.vn/userapi/transactions/list
```

Ket qua mong doi: JSON chura danh sach giao dich. Neu tra ve loi 401 → key sai hoac het han.

### Buoc 2: Test luong nap tien tren frontend

1. Dang nhap frontend tai `http://localhost:5173`
2. Vao trang **Premium** → nhan **"Nap tien"**
3. Chon so tien (VD: 20.000 VND)
4. Nhan **"Tao ma thanh toan"**
5. He thong hien thi:
   - Ma QR (quet bang app ngan hang)
   - Noi dung chuyen khoan: `W2LNAPTOKEN{HEX_ID}`
   - So tien can chuyen
6. Quet QR bang app ngan hang → chuyen khoan dung so tien va noi dung
7. Doi 3-10 giay → he thong tu dong xac nhan va nap token

### Buoc 3: Kiem tra bang endpoint API

```bash
# Tao hoa don
curl -X POST http://localhost:8000/api/payment/create \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"amount_vnd": 20000}'

# Kiem tra trang thai
curl http://localhost:8000/api/payment/status/1 \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Buoc 4: Test o moi truong development (khong can ngan hang thuc)

Neu chua co ngan hang ket noi SePay, dung endpoint dev:

```bash
# Xac nhan thu cong (chi moi truong development)
curl -X POST http://localhost:8000/api/payment/dev/complete/1 \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Hoac nhan nut **"Xac nhan nap thu cong (Dev)"** tren giao dien frontend.

---

## 7. Checklist cau hinh day du

### Backend

- [ ] File `backend/.env` da co `SEPAY_API_KEY`
- [ ] File `backend/.env` da co `NAME_WEB`
- [ ] File `backend/.env` da co `SECRET_XOR_KEY`
- [ ] Backend da khoi dong lai sau khi cap nhat .env

### SePay Dashboard

- [ ] Da dang ky tai khoan SePay
- [ ] Da them tai khoan ngan hang (MB, VCB, VPBank, ...)
- [ ] Da bat thong bao bien dong so du tren app ngan hang
- [ ] Da cai app SePay tren dien thoai (neu can)
- [ ] Da tao va copy API key

### Frontend (tuy chon)

- [ ] File `frontend/.env` da co `VITE_BANK_BIN`
- [ ] File `frontend/.env` da co `VITE_BANK_ACCOUNT`
- [ ] File `frontend/.env` da co `VITE_BANK_ACCOUNT_NAME`

### Kiem tra end-to-end

- [ ] Tao hoa don nap tien thanh cong
- [ ] QR code hien thi dung thong tin
- [ ] Noi dung chuyen khoan dung format `{NAME_WEB}NAPTOKEN{HEX_ID}`
- [ ] Polling tra ve `completed` sau khi chuyen khoan

---

## 8. Loi thuong gap va xu ly

### 8.1. API key sai hoac het han

**Trieu chung:** Backend log bao loi khi goi SePay API, payment luon o trang thai `pending`.

**Xu ly:**
1. Kiem tra lai key trong `backend/.env`
2. Thu goi API thu cong bang curl (xem buoc 6.1)
3. Neu van loi → vao SePay dashboard tao key moi

### 8.2. Chuyen khoan nhung he thong khong nhan

**Trieu chung:** Da chuyen khoan thanh cong nhung polling van tra ve `pending`.

**Kiem tra:**
1. **Noi dung chuyen khoan sai:** Phai chua dung `W2LNAPTOKEN{HEX_ID}` (khong dau cach, khong ky tu dac biet)
2. **So tien thieu:** Phai >= so tien yeu cau
3. **SePay chua dong bo:** Kiem tra app ngan hang da bat thong bao chua → doi 1-2 phut rồi refresh
4. **Dien thoai tat man hinh:** SePay can dien thoai bat de doc thong bao

### 8.3. QR Code khong hien thi

**Trieu chung:** QR code bi broken image hoac khong load.

**Xu ly:**
1. Kiem tra mang internet
2. Kiem tra `VITE_BANK_BIN` va `VITE_BANK_ACCOUNT` dung chua
3. Thu truy cap URL QR truc tiep: `https://api.vietqr.io/image/{BIN}-{ACCOUNT}-yXwL0O`

### 8.4. Sai NAME_WEB

**Trieu chung:** Frontend tao noi dung CK la `W2LNAPTOKEN...` nhung backend regex khong match.

**Xu ly:** Dam bao `NAME_WEB` giong nhau trong `backend/.env` va logic frontend. Gia tri mac dinh la `W2L`.

---

## 9. Bao mat

### Quy tac bat buoc

- ❌ **KHONG** commit API key len git (da co trong .gitignore)
- ❌ **KHONG** gui API key qua chat/email cong khai
- ❌ **KHONG** de API key trong source code frontend
- ✅ Chi luu API key trong file `backend/.env`
- ✅ Rotate key moi 30-90 ngay
- ✅ Neu nghi ngo lo key → thu hoi ngay va tao key moi

### Rotate key

1. Vao SePay dashboard → tao key moi
2. Cap nhat `SEPAY_API_KEY` trong `backend/.env`
3. Khoi dong lai backend
4. Thu hoi (revoke) key cu tren SePay dashboard

---

## 10. Thong tin ky thuat chi tiet

### 10.1. Luong thanh toan (Polling Sync)

```
Frontend                     Backend                     SePay API
   |                            |                           |
   |-- POST /payment/create --> |                           |
   |                            |-- Tao payment (pending) --|
   |<-- {hex_id, noidung_ck} --|                           |
   |                            |                           |
   |-- Hien thi QR Code        |                           |
   |                            |                           |
   |-- GET /payment/status --> |                           |
   |                            |-- GET /transactions -----> |
   |                            |<-- [...transactions] ----- |
   |                            |-- Regex match noi dung     |
   |                            |-- Kiem tra so tien         |
   |                            |-- Cap nhat completed       |
   |<-- {status: completed} ---|                           |
```

### 10.2. XOR Obfuscation

Payment ID khong duoc dung truc tiep (1, 2, 3...) de tranh nguoi dung doan ID cua nhau.

```python
SECRET_XOR_KEY = 0x5EAFB  # Thay doi cho moi du an

def encode_payment_id(p_id: int) -> str:
    return hex(p_id ^ SECRET_XOR_KEY)[2:].upper()

def decode_payment_id(hex_str: str) -> int:
    return int(hex_str, 16) ^ SECRET_XOR_KEY

# Vi du:
# encode_payment_id(1) → "5EAFA"
# encode_payment_id(2) → "5EAF9"
# decode_payment_id("5EAFA") → 1
```

### 10.3. Regex so khop noi dung chuyen khoan

Noi dung chuyen khoan thuong bi ngan hang them ky tu, bo dau cach, vien hoa khac nhau. He thong su dung regex linh hoat:

```python
prefix = re.escape(NAME_WEB) + r"\s*NAPTOKEN"
pattern = rf"{prefix}([A-Fa-f0-9]+)"

# Match duoc ca:
# "W2LNAPTOKEN5EAFA"
# "W2L NAPTOKEN5EAFA"
# "w2lnaptoken5eafa"
# "GD: W2LNAPTOKEN5EAFA CHUYEN TIEN"
```

### 10.4. State Machine

```
pending ──────────────> completed (khi doi soat thanh cong)
   |                         ^
   |                         |
   └──> failed ──────────────┘ (tien ve muon van xu ly)
         (60 phut timeout)
```

- `pending`: Dang cho tien ve
- `completed`: Da nhan du tien, da nap token
- `failed`: Hoa don het han (60 phut). **Luu y:** He thong van tiep tuc doi soat sau khi failed, neu tim thay tien van chuyen sang completed.

### 10.5. SePay API endpoint su dung

```
GET https://my.sepay.vn/userapi/transactions/list
Headers:
  Authorization: Bearer {SEPAY_API_KEY}
  Content-Type: application/json

Response:
{
  "transactions": [
    {
      "id": "123456",
      "transaction_content": "W2LNAPTOKEN5EAFA",
      "amount_in": 20000,
      "transaction_date": "2026-04-07 06:00:00"
    }
  ]
}
```
