# SỔ TAY HƯỚNG DẪN KIỂM THỬ ỨNG DẪN TRÊN ĐIỆN THOẠI VỚI NGROK

Tài liệu này cung cấp kiến thức nền tảng và các bước thiết lập chi tiết để đưa ứng dụng đang code trên máy tính (localhost) lên điện thoại di động thông qua môi trường Internet bằng công cụ Ngrok.

---

## 1. KHÁI NIỆM CƠ BẢN (Dành cho người mới)

### 1.1 Localhost là gì? Tại sao điện thoại không vào được?
Khi bạn lập trình trên máy tính, trang web của bạn chạy trên địa chỉ dạng `http://localhost:5173`. Từ `localhost` ám chỉ "Mạng nội bộ bên trong cái máy tính này".
Vì thế, nếu bạn lấy mạng wifi 4G của điện thoại mở `http://localhost:5173`, điện thoại sẽ cố gắng tự tìm ứng dụng bên trong bộ nhớ của chính con điện thoại đó (chắc chắn là không có) => Nó sẽ báo lỗi **"Không thể kết nối" (Site can't be reached)**.

### 1.2 Ngrok là gì?
Để điện thoại có thể "nhìn thấy" máy tính đang cắm code, chúng ta cần một **cầu nối (Đường hầm / Tunnel)**. 
Ngrok đóng vai trò là cây cầu đó. Ngrok sinh ra một địa chỉ "Có thật trên mạng Internet" (ví dụ: `https://nacho...ngrok-free.dev`). Khi điện thoại truy cập vào link này, máy chủ Ngrok trên không gian mạng sẽ hứng lấy dữ liệu đó và bí mật đẩy nó qua ống dẫn ngầm thẳng vào cổng 5173 trên máy tính của bạn.

### 1.3 Tại sao phải dùng Tên miền cố định (Static Domain)?
Bản miễn phí của Ngrok thường có tính xấu: mỗi lần mở lại ứng dụng nó sẽ vứt trả một tên miền rác mới (như `ds4q.ngrok-free.app`). 
Nếu dùng link ngẫu nhiên này, mỗi ngày bạn lập trình bạn lại phải đi sửa code, sửa `.env` và sửa API Google. Rất đau đầu!
Rất may tài khoản của chúng ta đã được cấp 1 tên miền danh dự miễn phí mãi mãi: `nacho-disjoin-deprecate.ngrok-free.dev`. Chỉ cần chạy đúng tên miền này là hệ sinh thái code của bạn vững như bàn thạch!

---

## 2. HƯỚNG DẪN LỆNH CHẠY NGROK VÀ Ý NGHĨA 

Để kích hoạt Cầu nối Cố định, bạn mở một cửa sổ CMD đen nhánh (không tắt hay liên quan đến cửa sổ start.bat của Backend) và gõ đúng lệnh sau:

```bash
ngrok http --domain=nacho-disjoin-deprecate.ngrok-free.dev 5173
```

**Bảng mổ xẻ phẫu thuật lệnh chạy:**
| Thành phần | Giải thích chức năng |
| :--- | :--- |
| `ngrok` | Gọi khởi động phần mềm ngrok đã cài trong Windows. |
| `http` | Báo cho ngrok biết hãy mã hoá dữ liệu qua giao thức web HTTP/HTTPS. |
| `--domain=...` | Ép buộc ngrok sử dụng **Bằng được** cái tên miền vĩnh viễn đã xin được. |
| `5173` | Cổng dịch vụ của Vite Frontend mà đường hầm này sẽ đổ vào khi đến được máy tính. |

---

## 3. CÁCH CÀI ĐẶT VÀ VẬN HÀNH KIỂM THỬ HÀNG NGÀY

Đây là thói quen mà bạn nên làm mỗi khi ngồi vào bàn để viết Code và Test:

### Bước 1: Khởi động máy chủ ứng dụng nội bộ
- **Hành động:** Chạy file `start.bat`.
- **Kết quả:** Ngồi chờ đến khi trình duyệt hiện lên giao diện Word2LaTeX ở `http://localhost:5173`. Không được tắt cái màn đen CMD đi, hãy thu nhỏ nó xuống khay màn hình.

### Bước 2: Kích hoạt Ngrok xuyên tường lửa
- **Hành động:** Mở 1 cửa sổ CMD mới tinh. Dán lệnh: `ngrok http --domain=nacho-disjoin-deprecate.ngrok-free.dev 5173` rồi Enter.
- **Kết quả:** Nó báo chữ **Online** màu xanh nhạt. Máy tính của bạn đã được hòa mình vào mạng Internet đại chúng.

### Bước 3: Đưa lên điện thoại (Hoặc máy tính người khác)
- **Hành động:** Gửi đường link `https://nacho-disjoin-deprecate.ngrok-free.dev` cho bạn bè, hoặc tự nhập thẳng vào Chrome/Safari trên điện thoại.
- **Kết quả:** 
   - Nếu là lần đầu tiên vào bằng trình duyệt, Ngrok có thể hiện màn hình chống Lừa đảo (Cảnh báo). Bấm nút **"Visit Site"**.
   - Giao diện của bạn sẽ load đầy đủ. Thử ngay các tính năng gọi API, đăng nhập,...!

---

## 4. BÍ kÍP GIẢI QUYẾT CÁC LỖI THƯỜNG GẶP

### ⛔ ERR_NGROK_3200 (The endpoint is offline)
- **Nghĩa là:** Điện thoại đang truy cập cái link nhưng Ngrok trên máy tính của bạn thì đang ngủ tắt máy.
- **Cách sửa:** Quên làm Bước 2 rồi! Mở lệnh ngrok lên, giữ nó ở trạng thái online.

### ⛔ Đăng nhập Google báo uỷ quyền URL / Mismatch
- **Nghĩa là:** Bạn chưa thêm cái tên miền "nacho-disjoin..." vào **Google Cloud Console**.
- **Cách sửa:** Lên quản lý Application GCP. Tại thông tin OAuth 2.0 Credentials, thêm `https://nacho-disjoin-deprecate.ngrok-free.dev` vào cả mục `Origins` và chèn `/api/auth/google/callback` vào mục thư mục tiếp nhận.

### ⛔ Bấm Đăng Nhập bình thường không chịu chạy (Lỗi ngầm chặn gói mạng Vite)
- **Nghĩa là:** Backend API bị bức tường của Ngrok chặn mồm. 
- **Cách sửa:** Hệ thống code hiện tại đã tự động nhúng công nghệ "Pass thẻ từ ngrok-skip-browser-warning" vào mọi thao tác fetch API. Nếu bạn bị lỗi này thì chỉ cần load lại trang là được; vấn đề này đã vĩnh viễn bị loại trừ.
