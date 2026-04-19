# HƯỚNG DẪN KIỂM THỬ TRÊN ĐIỆN THOẠI (NGROK TÀI KHOẢN MỚI)

Tài liệu này đã được cập nhật để phù hợp với quy trình sử dụng Ngrok mới nhất, tối ưu hơn và dễ quản lý hơn.

---

## 1. QUY TRÌNH MỚI: MỘT CẦU NỐI DUY NHẤT (Vite Proxy)

Thay vì chạy nhiều đường hầm cho cả Frontend và Backend, chúng ta sẽ sử dụng kỹ thuật **Proxy**. 
- Bạn chỉ cần chạy **1 đường hầm Ngrok** trỏ vào cổng **5173** (Frontend).
- Mọi yêu cầu liên quan đến API (đăng nhập, chuyển đổi file) sẽ được Frontend tự động "chuyển tiếp" sang Backend (cổng 8000) đang chạy trên máy tính bạn.

**Lợi ích:** 
- Tiết kiệm tài nguyên tài khoản Ngrok.
- Chỉ cần quản lý 1 link Ngrok duy nhất.
- Tránh lỗi CORS và dễ dàng thiết lập Google OAuth.

---

## 2. CÁC BƯỚC THIẾT LẬP (LÀM 1 LẦN)

### Bước 1: Cập nhật Authtoken mới
- Truy cập [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken) để lấy token của tài khoản mới.
- Chạy file `start_ngrok.bat`, chọn số **1** và dán token của bạn vào.

### Bước 2: Lấy Static Domain (Khuyên dùng)
- Ngrok hiện tại cho phép mỗi tài khoản miễn phí có 1 domain cố định (ví dụ: `your-name.ngrok-free.app`). 
- Hãy tạo domain này trên dashboard của Ngrok để không bị đổi link mỗi ngày.

---

## 3. CÁCH VẬN HÀNH HÀNG NGÀY

### Bước 1: Khởi động hệ thống
- Chạy file `start.bat` để mở cả Backend và Frontend như bình thường.
- Đảm bảo bạn có thể vào `http://localhost:5173` trên máy tính.

### Bước 2: Kích hoạt Ngrok
- Chạy file `start_ngrok.bat`.
- Nếu bạn có domain cố định: Chọn **2** và nhập domain.
- Nếu dùng link ngẫu nhiên: Chọn **3**.

### Bước 3: Cập nhật cấu hình Backend
Khi Ngrok đã chạy, bạn sẽ có một địa chỉ (Link), ví dụ: `https://abcd.ngrok-free.app`.
Bạn **BẮT BUỘC** phải mở file `backend/.env` và thay thế các dòng sau bằng link mới:
```env
GOOGLE_REDIRECT_URI=https://abcd.ngrok-free.app/api/auth/google/callback
FRONTEND_URL=https://abcd.ngrok-free.app
CORS_ORIGINS=https://abcd.ngrok-free.app,http://localhost:5173
```
*(Lưu ý: Không được có dấu gạch chéo `/` ở cuối FRONTEND_URL).*

---

## 4. CẤU HÌNH GOOGLE CLOUD (Cực kỳ quan trọng)

Để tính năng Đăng nhập hoạt động trên điện thoại, bạn phải thêm Link Ngrok vào [Google Cloud Console](https://console.cloud.google.com/):
1. **Authorized JavaScript origins**: Thêm `https://abcd.ngrok-free.app`
2. **Authorized redirect URIs**: Bạn phải thêm **CẢ 2** link sau:
   - `https://abcd.ngrok-free.app/api/auth/google/callback`
   - `https://abcd.ngrok-free.app/api/auth/google/callback/flutter` (Dành cho App)

---

## 5. CÁCH ĐỔI TÀI KHOẢN NGROK (Khi bị giới hạn/Hết hạn)

Nếu bạn muốn chuyển sang một tài khoản Ngrok khác, hãy làm theo các cách sau:

### Cách 1: Sử dụng File Start
1. Chạy file `start_ngrok.bat`.
2. Chọn phím **1** (Thêm/Cập nhật Ngrok Authtoken).
3. Dán Authtoken của tài khoản mới vào và nhấn Enter.

### Cách 2: Sử dụng Terminal (Lệnh trực tiếp)
Mở PowerShell hoặc CMD và chạy lệnh sau:
```powershell
ngrok config add-authtoken <TOKEN_MOI_CUA_BAN>
```
*(Thay `<TOKEN_MOI_CUA_BAN>` bằng mã token thực tế lấy từ trang Dashboard của Ngrok).*

### Lưu ý sau khi đổi:
- Tắt cửa sổ Ngrok cũ đang chạy.
- Chạy lại Ngrok (theo bước 3.2) để nhận Link mới.
- **QUAN TRỌNG:** Phải cập nhật lại Link mới này vào file `backend/.env` và Google Cloud Console.

---

## 6. GIẢI QUYẾT LỖI
- **Lỗi 502 Bad Gateway:** Do Backend (cổng 8000) chưa bật hoặc bị treo. Hãy kiểm tra cửa số `start.bat`.
- **Lỗi Mismatch URI:** Do bạn chưa cập nhật link Ngrok mới vào `backend/.env` hoặc Google Cloud Console.
- **Màn hình cảnh báo của Ngrok:** Bấm nút "Visit Site" để vượt qua.
