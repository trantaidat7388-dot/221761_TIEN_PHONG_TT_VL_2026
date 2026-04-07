# He thong Thanh toan SePay — Polling & Sync

Tai lieu ky thuat chi tiet ve luong nap tien tu dong khong qua Webhook.

---

## 1. Tong quan kien truc

He thong thanh toan Word2LaTeX su dung co che **Polling Sync** thay vi Webhook:

- **Khong can domain/port public** — hoat dong ca tren localhost, VPS noi bo
- **Khong can SSL certificate** — khong can HTTPS cho webhook endpoint
- **Do tin cay cao** — khong mat giao dich do webhook fail

### So sanh Webhook vs Polling

| Tieu chi | Webhook | Polling (chung ta dung) |
|---|---|---|
| Can domain/port public | Co | Khong |
| Can SSL/HTTPS | Co | Khong |
| Do tre | < 1s | 3-10s |
| Mat giao dich | Co the | Khong |
| Do phuc tap | Cao | Thap |
| Hoat dong tren localhost | Khong | Co |

---

## 2. Luong xu ly chi tiet (Payment Flow Sequence)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Frontend │    │ Backend  │    │ Database │    │ SePay    │
│ (React)  │    │ (FastAPI)│    │ (SQLite) │    │ API      │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │
     │ POST /create  │               │               │
     │──────────────>│               │               │
     │               │ INSERT payment│               │
     │               │──────────────>│               │
     │               │   (pending)   │               │
     │  {hex_id,     │               │               │
     │   noidung_ck} │               │               │
     │<──────────────│               │               │
     │               │               │               │
     │ Hien thi QR   │               │               │
     │ Nguoi dung    │               │               │
     │ quet va        │               │               │
     │ chuyen khoan  │               │               │
     │               │               │               │
     │ GET /status   │               │               │
     │──────────────>│               │               │
     │               │  GET /transactions            │
     │               │──────────────────────────────>│
     │               │  [...transactions]            │
     │               │<──────────────────────────────│
     │               │               │               │
     │               │ Regex match   │               │
     │               │ + amount check│               │
     │               │               │               │
     │               │ UPDATE payment│               │
     │               │──────────────>│               │
     │               │  (completed)  │               │
     │               │               │               │
     │               │ UPDATE user   │               │
     │               │──────────────>│               │
     │               │ (token += N)  │               │
     │               │               │               │
     │ {completed}   │               │               │
     │<──────────────│               │               │
```

---

## 3. Backend Implementation

### 3.1. Tao hoa don — `POST /api/payment/create`

File: `backend/app/routers/payment_routes.py`

```python
@router.post("/create")
def tao_payment(req: YeuCauTaoPayment, db, current_user):
    # 1. Validate so tien toi thieu
    if req.amount_vnd < 10000:
        raise HTTPException(400, "So tien nap toi thieu la 10,000 VND")

    # 2. Ty le: 1 VND = 1 Token
    token_amount = req.amount_vnd

    # 3. Tao record payment
    payment = Payment(
        user_id=current_user.id,
        amount_vnd=req.amount_vnd,
        token_amount=token_amount,
        status="pending"
    )
    db.add(payment)
    db.commit()

    # 4. Ma hoa payment ID
    hex_id = encode_payment_id(payment.id)
    noidung_ck = f"{NAME_WEB}NAPTOKEN{hex_id}"

    return {
        "payment_id": payment.id,
        "hex_id": hex_id,
        "noidung_ck": noidung_ck,  # Noi dung chuyen khoan
        "amount_vnd": payment.amount_vnd,
        "token_amount": payment.token_amount
    }
```

### 3.2. Kiem tra trang thai — `GET /api/payment/status/{id}`

```python
@router.get("/status/{payment_id}")
def kiem_tra_trang_thai(payment_id, db, current_user):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()

    # 1. Da completed → tra ve ngay
    if payment.status == "completed":
        return {"status": "completed"}

    # 2. Check het han (60 phut)
    if payment.status == "pending":
        if datetime.utcnow() > payment.created_at + timedelta(minutes=60):
            payment.status = "failed"
            db.commit()

    # 3. Goi SePay API doi soat
    is_paid, tx_id = check_payment_status(payment.id, payment.amount_vnd)

    if is_paid:
        # 4. Thanh cong → cap nhat
        payment.status = "completed"
        current_user.token_balance += payment.token_amount

        # 5. Ghi ledger
        db.add(TokenLedger(
            user_id=current_user.id,
            delta_token=payment.token_amount,
            balance_after=current_user.token_balance,
            reason="nap token qua sepay"
        ))
        db.commit()

        return {"status": "completed", "token_nhan": payment.token_amount}

    return {"status": payment.status}
```

### 3.3. Logic doi soat (Reconciliation)

File: `backend/app/services/sepay_sync.py`

```python
import re
import urllib.request
import json

SECRET_XOR_KEY = 0x5EAFB

def encode_payment_id(p_id: int) -> str:
    """Ma hoa ID hoa don bang toan tu XOR."""
    return hex(p_id ^ SECRET_XOR_KEY)[2:].upper()

def decode_payment_id(hex_str: str) -> int:
    """Giai ma ID hoa don tu chuoi Hex."""
    return int(hex_str, 16) ^ SECRET_XOR_KEY

def get_sepay_transactions():
    """Goi SePay API lay danh sach giao dich gan nhat."""
    url = "https://my.sepay.vn/userapi/transactions/list"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {SEPAY_API_KEY}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        return data.get("transactions", [])

def check_payment_status(payment_id, expected_amount_vnd):
    """Kiem tra doi soat trang thai nap tien.
    Tra ve (True, transaction_id) neu thanh cong."""
    target_hex = encode_payment_id(payment_id)

    # Regex linh hoat: match ca khi ngan hang them ky tu
    prefix = re.escape(NAME_WEB) + r"\s*NAPTOKEN"
    pattern = rf"{prefix}([A-Fa-f0-9]+)"

    transactions = get_sepay_transactions()

    for tx in transactions:
        content = str(tx.get('transaction_content', tx.get('content', '')))
        amount_in = float(tx.get('amount_in', tx.get('amount', 0)))

        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            found_hex = match.group(1).upper()
            if found_hex == target_hex and amount_in >= expected_amount_vnd:
                return True, str(tx.get('id'))

    return False, ""
```

---

## 4. Frontend Implementation

### 4.1. Tao hoa don va hien thi QR

File: `frontend/src/features/premium/NapTokenModal.jsx`

```javascript
// Tao hoa don
const xuLyTaoHoaDon = async () => {
    const res = await taoHoaDonNapTien(amount)
    setHoaDon(res.data) // {payment_id, hex_id, noidung_ck, amount_vnd}
}

// QR Code su dung VietQR API
const qrUrl = `https://api.vietqr.io/image/${bankBin}-${bankAccount}-yXwL0O`
    + `?accountName=${encodeURIComponent(bankName)}`
    + `&amount=${hoaDon.amount_vnd}`
    + `&addInfo=${encodeURIComponent(hoaDon.noidung_ck)}`
```

### 4.2. Polling trang thai

```javascript
// Poll moi 5 giay
useEffect(() => {
    if (!hoaDon?.payment_id) return

    const pollId = setInterval(async () => {
        const res = await kiemTraTrangThaiHoaDon(hoaDon.payment_id)
        if (res.data.status === 'completed') {
            clearInterval(pollId)
            toast.success('Nap tien thanh cong!')
            await lamMoiThongTinNguoiDung()
        }
    }, 5000) // 5 giay

    return () => clearInterval(pollId)
}, [hoaDon?.payment_id])
```

---

## 5. Quan ly trang thai (State Machine)

### 5.1. Cac trang thai

| Trang thai | Mo ta | Chuyen tiep |
|---|---|---|
| `pending` | Dang cho tien ve | → `completed` hoac → `failed` |
| `completed` | Da nhan du tien, da nap token cho user | (trang thai cuoi) |
| `failed` | Hoa don het han (60 phut) | → `completed` (neu tien ve muon) |

### 5.2. Tinh linh hoat

**Luu y quan trong:** Ngay ca khi hoa don o trang thai `failed`, he thong van tiep tuc doi soat SePay. Neu tim thay giao dich trung khop, hoa don van duoc chuyen sang `completed` va nap token cho user.

Dieu nay dam bao: **khong mat tien cua user** trong moi truong hop.

---

## 6. Bao mat

### 6.1. XOR Obfuscation

- Payment ID thuc (1, 2, 3...) khong duoc dung truc tiep trong noi dung chuyen khoan
- XOR voi SECRET_XOR_KEY de tao HEX ID duy nhat
- Muc dich: tranh nguoi dung doan ID cua nguoi khac

### 6.2. API Key bao mat

- SEPAY_API_KEY chi luu trong `backend/.env`
- KHONG bao gio expose ra frontend
- Frontend chi giao tiep voi backend qua JWT token

### 6.3. Endpoint dev-only

- `POST /api/payment/dev/complete/{id}` chi hoat dong khi `APP_ENV != production`
- Dung de test luong thanh toan ma khong can ngan hang thuc

---

## 7. Cau hinh SePay Dashboard

### Buoc tat:

1. Dang ky tai khoan tai `https://my.sepay.vn`
2. Them tai khoan ngan hang (MB, VCB, VPB, BIDV, ACB, ...)
3. Cai app ngan hang tren dien thoai
4. Bat thong bao bien dong so du
5. Tao API Key tren SePay dashboard
6. Dien key vao `backend/.env`

### Yeu cau ky thuat:

- Dien thoai phai bat va co mang
- App ngan hang phai bat quyen thong bao
- SePay app can quyen doc thong bao (Android)

> **Xem chi tiet:** `HUONG_DAN_LAY_SEPAY_API_KEY.md` tai thu muc goc du an.

---

## 8. Admin Payment Management

Admin co the quan ly tat ca payments thong qua Admin Dashboard:

### API Endpoints

| Method | Path | Mo ta |
|---|---|---|
| `GET` | `/api/admin/payments` | Liet ke tat ca payments |
| `PATCH` | `/api/admin/payments/{id}/complete` | Xac nhan payment thu cong |

### Chuc nang admin

1. **Xem tat ca hoa don** — Filter theo trang thai (pending/completed/failed)
2. **Xac nhan thu cong** — Khi khach chuyen sai noi dung hoac SePay khong match:
   - Admin xem giao dich thuc te tren dashboard ngan hang
   - Admin bam "Xac nhan" → he thong cap nhat completed va nap token
   - Hanh dong duoc ghi vao audit log
3. **Thong ke doanh thu** — Tong so payments, so thanh cong, tong doanh thu

> GUI admin duoc tach rieng tai `/quan-tri` voi tab "Thanh toan" chuyen biet.
