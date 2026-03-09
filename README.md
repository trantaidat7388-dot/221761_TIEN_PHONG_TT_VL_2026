<div align="center">

# Word2LaTeX — Chuyển Đổi Tài Liệu Word Sang LaTeX Học Thuật

**Chuyển đổi file Word (.docx / .docm) sang mã nguồn LaTeX chuẩn xuất bản chỉ với một cú nhấp chuột.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Giới Thiệu

**Word2LaTeX** là công cụ chuyển đổi tài liệu học thuật full-stack, giúp biến các file `.docx` / `.docm` thành gói mã nguồn LaTeX sẵn sàng nộp cho hội nghị hoặc tạp chí khoa học. Hệ thống phân tích cấu trúc bên trong của file Word thông qua **bộ phân tích cú pháp AST kết hợp Heuristics**, ánh xạ nội dung vào cấu trúc trung gian (IR), và dựng lại tài liệu LaTeX thông qua **pipeline Jinja2** hỗ trợ nhiều mẫu học thuật phổ biến.

Kết quả đầu ra là một file **`.zip` sẵn dùng cho Overleaf**, bao gồm: file `.tex` hoàn chỉnh, toàn bộ ảnh được trích xuất, các file `.cls` / `.bib` phụ thuộc, và tuỳ chọn cả file **`.pdf` đã biên dịch**.

> **Dự án nghiên cứu** — Phát triển bởi sinh viên Đại học, nhằm mục tiêu tự động hóa quy trình chuẩn bị bài báo khoa học từ bản thảo Word sang định dạng LaTeX chuẩn.

---

## Tính Năng Nổi Bật

- **Hỗ trợ nhiều mẫu LaTeX** — IEEE Conference (2 cột), Springer LNCS, và bất kỳ mẫu `.tex` / `.zip` nào do người dùng tự tải lên.
- **Phân tích AST + Heuristics** — Tự động nhận dạng tiêu đề, tác giả, đơn vị công tác, tóm tắt, mục lục, hình ảnh, bảng biểu, và công thức toán học — ngay cả với file Word không dùng style chuẩn.
- **Tiến trình thời gian thực (SSE)** — Các bước chuyển đổi được đẩy trực tiếp đến trình duyệt qua Server-Sent Events, không cần polling.
- **Chuyển đổi công thức toán học** — Phương trình OMML (Office Math Markup Language) được chuyển sang môi trường toán LaTeX qua XSLT.
- **Đánh số caption thập phân** — Hình 3.1, bảng 2.4,… được xử lý đúng.
- **Phân tích tác giả thông minh** — Tự động trích xuất và liên kết ký hiệu chú thích (`*`, `†`) và địa chỉ email từ khối tác giả.
- **Xác thực JWT** — Đăng nhập bằng token không trạng thái (FastAPI + python-jose). Lịch sử chuyển đổi được lưu riêng theo người dùng trong SQLite.
- **Chạy hoàn toàn offline** — Không gọi API bên ngoài. Toàn bộ xử lý diễn ra trên máy cục bộ.
- **Biên dịch XeLaTeX** — Sinh PDF phía server với báo cáo lỗi chi tiết qua bộ phân tích log LaTeX tùy chỉnh.

---

## Yêu Cầu Hệ Thống

| Phần mềm | Phiên bản | Ghi chú |
|---|---|---|
| **Python** | 3.10+ | Nên tạo môi trường ảo (`venv`) |
| **Node.js** | 18+ | Chạy giao diện React |
| **XeLaTeX** | TexLive / MiKTeX | Cần cho tính năng biên dịch PDF |
| **npm** | 8+ | Đi kèm với Node.js |

---

## Hướng Dẫn Cài Đặt

### 1. Clone dự án

```bash
git clone https://github.com/trantaidat7388-dot/Word2Latex.git
cd Word2Latex
```

### 2. Tạo môi trường Python ảo

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Cài đặt thư viện Python

```bash
pip install -r requirements.txt
```

> **Lưu ý:** Dự án ghim `bcrypt==4.0.1` để tương thích với `passlib`. Không nâng cấp bcrypt độc lập.

### 4. Cài đặt thư viện frontend

```bash
cd frontend
npm install
cd ..
```

---

## Sử Dụng

### Khởi động nhanh (Windows)

Nhấp đúp vào **`start.bat`** ở thư mục gốc. Script sẽ tự động:

1. Dừng các tiến trình cũ đang chiếm cổng `8000` và `5173`
2. Dọn dẹp thư mục `__pycache__`
3. Kích hoạt `.venv` và chạy `pip install -r requirements.txt`
4. Khởi động **backend FastAPI** trong cửa sổ terminal riêng
5. Khởi động **frontend Vite** trong cửa sổ terminal riêng
6. Chờ 5 giây rồi tự động mở `http://localhost:5173` trên trình duyệt

### Khởi động thủ công

**Backend:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Truy cập `http://localhost:5173` trên trình duyệt.

### Tài liệu API

Swagger UI tương tác có sẵn tại `http://localhost:8000/docs` khi backend đang chạy.

---

## Cấu Trúc Dự Án

```
Word2Latex/
├── backend/                        # Ứng dụng FastAPI
│   ├── main.py                     # Các API route (chuyển đổi, xác thực, template)
│   ├── auth.py                     # Hỗ trợ JWT (tạo token, xác minh mật khẩu)
│   ├── models.py                   # Mô hình SQLAlchemy (User, ConversionHistory)
│   ├── database.py                 # SQLite engine + session factory
│   └── custom_templates/           # Mẫu LaTeX tích hợp sẵn và do người dùng tải lên
│
├── src/                            # Engine chuyển đổi cốt lõi (Python thuần)
│   ├── ast_parser.py               # Bộ phân tích AST: XML Word → IR dict
│   ├── jinja_renderer.py           # IR → LaTeX qua pipeline Jinja2
│   ├── chuyen_doi.py               # Điều phối (kết nối parser và renderer)
│   ├── xu_ly_toan.py               # Chuyển đổi OMML → LaTeX (XSLT)
│   ├── xu_ly_anh.py                # Trích xuất và chuẩn hóa đường dẫn ảnh
│   └── template_preprocessor.py   # Tiền xử lý template Jinja2
│
├── frontend/                       # React + Vite SPA
│   └── src/
│       ├── App.jsx
│       ├── components/             # Các thành phần UI
│       ├── context/                # AuthContext (trạng thái JWT)
│       └── services/               # api.js client SSE streaming
│
├── requirements.txt                # Thư viện Python
└── start.bat                       # Trình khởi động 1-click (Windows)
```

---

## Công Nghệ Sử Dụng

| Tầng | Công nghệ |
|---|---|
| **Backend API** | FastAPI, Uvicorn |
| **Engine chuyển đổi** | Python — lxml, python-docx, Jinja2 |
| **Xác thực** | python-jose (JWT), passlib + bcrypt |
| **Cơ sở dữ liệu** | SQLite via SQLAlchemy |
| **Frontend** | React 18, Vite, TailwindCSS |
| **Chuyển đổi toán học** | XSLT (OMML → MathML → LaTeX) |
| **Biên dịch PDF** | XeLaTeX (TeX Live / MiKTeX) |

---

## Cấu Hình

Biến môi trường (tùy chọn — đặt trước khi khởi động backend):

| Biến | Mặc định | Mô tả |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:5173` | Các origin được phép (phân cách bởi dấu phẩy) |
| `CORS_ALLOW_ALL` | `0` | Đặt `1` để cho phép mọi origin (chỉ dùng khi dev) |
| `TEMP_TTL_HOURS` | `6` | Số giờ trước khi xóa thư mục job tạm |
| `OUTPUT_TTL_HOURS` | `24` | Số giờ trước khi xóa file output |

---

## Giấy Phép

Dự án được cấp phép theo **MIT License**. Xem [LICENSE](LICENSE) để biết chi tiết.
