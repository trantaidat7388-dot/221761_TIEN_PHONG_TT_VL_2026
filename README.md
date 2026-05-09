<div align="center">

# Word2LaTeX — Hệ Thống Chuyển Đổi Tự Động Tài Liệu Word Sang LaTeX Học Thuật

**Chuyển đổi file Word (.docx / .docm) sang mã nguồn LaTeX chuẩn xuất bản chỉ với một cú nhấp chuột.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Mục Lục

- [Giới Thiệu](#giới-thiệu)
- [Tính Năng Nổi Bật](#tính-năng-nổi-bật)
- [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
- [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
- [Hướng Dẫn Cài Đặt](#hướng-dẫn-cài-đặt)
- [Cấu Hình Biến Môi Trường](#cấu-hình-biến-môi-trường)
- [Sử Dụng](#sử-dụng)
- [Pipeline CLI](#pipeline-cli-không-cần-giao-diện)
- [API Endpoints](#api-endpoints)
- [Luồng Chuyển Đổi](#luồng-chuyển-đổi)
- [Công Nghệ Sử Dụng](#công-nghệ-sử-dụng)
- [Kiểm Thử](#kiểm-thử)
- [Bảo Mật](#bảo-mật)
- [Giấy Phép](#giấy-phép)

---

## Giới Thiệu

**Word2LaTeX** là công cụ chuyển đổi tài liệu học thuật full-stack, giúp biến các file `.docx` / `.docm` thành gói mã nguồn LaTeX sẵn sàng nộp cho hội nghị hoặc tạp chí khoa học. Hệ thống phân tích cấu trúc bên trong của file Word thông qua **bộ phân tích cú pháp AST kết hợp Heuristics**, xây dựng **biểu diễn trung gian (IR)** độc lập với bố cục LaTeX, và dựng lại tài liệu thông qua **pipeline Jinja2** hỗ trợ **5+ mẫu nhà xuất bản** phổ biến nhất.

Kết quả đầu ra là một file **`.zip` sẵn dùng cho Overleaf**, bao gồm: file `.tex` hoàn chỉnh, toàn bộ ảnh được trích xuất, các file `.cls` / `.bst` / `.bib` phụ thuộc, và file **`.pdf` đã biên dịch**.

> **Sản phẩm chuyển đổi tài liệu** — Tập trung tối ưu hóa quy trình chuẩn bị bài báo khoa học từ bản thảo Word sang định dạng LaTeX chuẩn.

---

## Tính Năng Nổi Bật

### Mẫu LaTeX có sẵn

| # | Mẫu | Engine | Ghi chú |
|---|------|--------|---------|
| 1 | **IEEE Conference** | XeLaTeX | 2 cột, `IEEEtran.cls` |
| 2 | **Springer LNCS** | XeLaTeX | `llncs.cls`, Lecture Notes in Computer Science |
| 3 | **ACM SIG Proceedings** | XeLaTeX | `acmart.cls` sigconf format |
| 4 | **MDPI Open Access** | pdfLaTeX | `mdpi.cls`, tạp chí mở |
| 5 | **Elsevier (elsarticle)** | XeLaTeX | `elsarticle.cls`, Harvard bibliography |
| 6 | **Rho Class** | XeLaTeX | `rho.cls`, Research Article format |

Ngoài ra, người dùng có thể **tải lên mẫu riêng** (file `.tex` hoặc `.zip` chứa các file định dạng như `.cls`, `.sty`, `.bst`, `.bib`, `.csl`).

### Chuyển đổi thông minh

- **Phân tích AST + Heuristics** — Tự động nhận dạng tiêu đề, tác giả, đơn vị công tác, tóm tắt, từ khóa, heading, hình ảnh, bảng biểu, danh sách, và công thức toán học.
- **Bộ phân loại ngữ nghĩa** — Dự đoán vai trò của đoạn văn (TITLE, AUTHOR, ABSTRACT, HEADING, REFERENCE,...) dựa trên nội dung, vị trí, độ dài và định dạng — không cần model ML.
- **Chuyển đổi công thức toán học 3 tầng** — OMML → LaTeX qua (1) XSLT transform, (2) Pandoc fallback, (3) Manual recursive parser.
- **Hỗ trợ OLE Equation Editor 3.0** — Chuyển đổi công thức legacy nhúng dạng OLE (MTEF v3 binary) sang LaTeX.
- **Lọc ảnh thông minh** — Phân biệt ảnh nội dung và ảnh trang trí bằng Shannon entropy, đếm màu và phát hiện cạnh.
- **Xử lý bảng nâng cao** — Hỗ trợ `multirow` / `multicolumn`, phát hiện và loại bỏ bảng Mục lục (TOC).
- **Phân tích tác giả thông minh** — Tự động trích xuất và liên kết ký hiệu chú thích (`*`, `†`) và địa chỉ email.

### Hệ thống Web

- **Tiến trình thời gian thực (SSE)** — 6 bước chuyển đổi được đẩy trực tiếp đến trình duyệt qua Server-Sent Events.
- **Biên dịch dual-engine** — Tự động phát hiện engine phù hợp: XeLaTeX (mặc định) hoặc pdfLaTeX.
- **Xác thực JWT + Google OAuth** — Đăng nhập bằng tài khoản local hoặc Google, token HS256 (7 ngày).
- **Hệ thống Token Economy** — Quản lý quota chuyển đổi theo token, hỗ trợ gói Premium.
- **Thanh toán SePay (Polling Sync)** — Đối soát giao dịch tự động không cần Webhook, có state machine pending/failed/completed.
- **Quản trị Admin** — Dashboard quản lý user, audit log, cấp/thu hồi token.
- **Lộ trình quản trị Admin** — Xem checklist, kiến trúc quyền và backlog tại `docs/admin-governance-roadmap.md`.
- **Tài liệu SePay** — Luồng kỹ thuật tại `docs/sepay-payment-polling-sync.md`, checklist cấu hình nhanh ở mục **Cấu Hình Biến Môi Trường**.
- **Rate Limiting** — Giới hạn request theo nhóm (auth, convert, admin) để chống lạm dụng.
- **Dọn dẹp tự động** — Thư mục job tạm và file output được xóa theo TTL cấu hình.
- **Xử lý cục bộ nội dung tài liệu** — Nội dung Word/LaTeX được xử lý trên máy chủ của hệ thống; chỉ gọi dịch vụ bên ngoài khi dùng OAuth hoặc thanh toán.

---

## Cấu Trúc Dự Án

```
221761_TIEN_PHONG_TT_VL_2026/
├── backend/                              # Backend FastAPI + engine chuyển đổi
│   ├── app/                              # Lớp Web API
│   │   ├── main.py                       # Khởi tạo FastAPI app
│   │   ├── config.py                     # Đọc cấu hình từ .env
│   │   ├── database.py                   # Kết nối DB
│   │   ├── auth.py                       # Tiện ích auth
│   │   ├── models/
│   │   │   ├── base_db.py
│   │   │   └── __init__.py
│   │   ├── routers/                      # API endpoints
│   │   │   ├── auth_routes.py
│   │   │   ├── base.py
│   │   │   ├── file_upload.py
│   │   │   ├── chuyen_doi.py
│   │   │   ├── templates.py
│   │   │   ├── payment_routes.py
│   │   │   └── admin_routes.py
│   │   ├── security/
│   │   │   └── security.py
│   │   ├── services/
│   │   │   ├── token_service.py
│   │   │   └── sepay_sync.py
│   │   └── utils/
│   │       └── api_utils.py
│   ├── core_engine/                      # Pipeline Word -> LaTeX
│   │   ├── chuyen_doi.py
│   │   ├── ast_parser.py
│   │   ├── semantic_parser.py
│   │   ├── template_preprocessor.py
│   │   ├── jinja_renderer.py
│   │   ├── xu_ly_toan.py
│   │   ├── xu_ly_ole_equation.py
│   │   ├── xu_ly_anh.py
│   │   ├── xu_ly_bang.py
│   │   ├── word_loader.py
│   │   ├── author_strategies.py
│   │   ├── docx_compat.py
│   │   ├── tex_log_parser.py
│   │   ├── utils.py
│   │   ├── config.py
│   │   ├── publishers_manifest.json
│   │   └── OMML2MML.XSL
│   ├── storage/
│   │   ├── custom_templates/             # Template hệ thống + template upload
│   │   └── temp_jobs/                    # Job tạm, dọn theo TTL
│   ├── run_schema_migration.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .env.sepay.example
│   └── .env                              # File local, không commit
│
├── frontend/                             # React + Vite
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── components/
│   │   ├── config/
│   │   ├── context/
│   │   ├── services/
│   │   ├── utils/
│   │   └── features/
│   │       ├── landing/
│   │       ├── xac_thuc/
│   │       ├── chuyen_doi/
│   │       ├── lich_su/
│   │       ├── tai_khoan/
│   │       ├── premium/
│   │       └── admin/
│   ├── tests-e2e/                        # Playwright E2E
│   ├── playwright.config.js
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   └── .env                              # File local cho frontend (VITE_*)
│
├── tests/                                # Bộ test pytest (50+ files)
│   ├── conftest.py
│   ├── test_api_smoke.py
│   ├── test_compile.py
│   ├── test_injection.py
│   ├── test_payment_polling_sync.py
│   ├── test_rate_limit_auth.py
│   ├── test_rate_limit_convert_admin.py
│   ├── test_token_deduct_refund.py
│   └── ...
│
├── brain/                                # Thư mục làm việc/ghi chú nội bộ
├── FIX/                                  # Ghi chú sửa lỗi và phân tích
├── docs/                                 # Tài liệu kỹ thuật và roadmap
├── input_data/                           # Dữ liệu Word đầu vào mẫu
├── output/                               # Kết quả chuyển đổi (legacy)
├── outputs/                              # Kết quả chuyển đổi
├── images/                               # Ảnh minh họa / tài nguyên
│
├── run_api.py                            # Chạy API nhanh bằng Uvicorn
├── run_conversion_pipeline.py            # Chạy pipeline CLI
├── run_word_to_word_pipeline.py          # Chạy pipeline Word -> Word CLI
├── start.bat                             # Khởi động nhanh trên Windows
├── start.sh                              # Khởi động nhanh trên Linux/macOS
├── requirements.txt                      # Dependencies root
├── package-lock.json
├── pytest.ini
└── README.md
```

> Lưu ý: Dự án không dùng file `.env` ở thư mục gốc. Biến môi trường được tách theo từng phần tại `backend/.env` và `frontend/.env`.

---

## Yêu Cầu Hệ Thống

| Thành phần | Phiên bản | Bắt buộc? | Ghi chú |
|---|---|---|---|
| **Python** | 3.10+ | ✅ Có | Backend + core engine |
| **Node.js** | 18+ | ✅ Có | Frontend React |
| **npm** | 8+ | ✅ Có | Đi kèm Node.js |
| **LaTeX** (XeLaTeX/pdfLaTeX) | TeX Live / MiKTeX | ❌ Tùy chọn | Chỉ cần nếu muốn sinh PDF trên máy |

### Cài đặt LaTeX (tùy chọn)

*   **Cách 1: Cài đặt trên máy (Để có PDF ngay lập tức)**
    *   **Windows**: Khuyên dùng [MiKTeX](https://miktex.org/download) (nhẹ, tự tải gói lệnh) hoặc [TeX Live](https://tug.org/texlive/acquire-netinstall.html) (đầy đủ, ổn định cao).
    *   **macOS**: Cài đặt [MacTeX](https://www.tug.org/mactex/).
    *   **Linux**: `sudo apt install texlive-full`.
    *   **Yêu cầu**: Sau khi cài đặt, hãy đảm bảo lệnh `xelatex` có thể chạy được từ Terminal/CMD.

*   **Cách 2: Dùng Overleaf** (không cần cài)
    *   Hệ thống vẫn sinh file `.zip` mà không cần LaTeX.
    *   Tải lên [Overleaf](https://www.overleaf.com/) → Upload Project → tự động biên dịch PDF.



## Hướng Dẫn Cài Đặt

### Trình tự khuyến nghị sau khi clone

Checklist onboarding nhanh (5-10 phút):

- [ ] Cài `Python 3.10+`, `Node.js 18+` và kiểm tra có `python`, `node`, `npm` trong `PATH`
- [ ] Clone dự án về máy
- [ ] Tạo virtual environment và cài `backend/requirements.txt`
- [ ] Chạy `npm install` trong thư mục `frontend/`
- [ ] Tạo `backend/.env` và `frontend/.env` từ file `.env.example`
- [ ] Khởi động bằng `start.bat` (Windows) hoặc `start.sh` (Linux/macOS)

> **Lưu ý:** `start.bat` và `start.sh` đã được cấu hình để tự kiểm tra môi trường, tạo `outputs/` khi cần, cài `node_modules` nếu thiếu và chờ backend sẵn sàng trước khi mở frontend.

### 1. Clone dự án

```bash
git clone https://github.com/trantaidat7388-dot/221761_TIEN_PHONG_TT_VL_2026.git
cd 221761_TIEN_PHONG_TT_VL_2026
```

### 2. Tạo môi trường Python ảo

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Cài đặt thư viện Python

```bash
pip install -r backend/requirements.txt
```

> **Lưu ý:** Backend đang dùng `bcrypt==3.2.2` để tương thích ổn định với `passlib`. Không nâng cấp bcrypt độc lập nếu chưa kiểm tra lại toàn bộ auth flow.

### 4. Cài đặt thư viện frontend

```bash
cd frontend
npm install
cd ..
```

### 5. Cấu hình biến môi trường

> **Lưu ý:** File `.env` chứa secret keys nên bị `.gitignore` — **KHÔNG có trên Git**. Thay vào đó, dự án cung cấp file **`.env.example`** (có trên Git) chứa giá trị mặc định để phát triển. Khi clone về lần đầu, bạn cần **copy file mẫu** này thành `.env`:

```bash
# Linux / macOS
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

```powershell
# Windows PowerShell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

> **Nếu dùng `start.bat` (Windows):** Script sẽ **tự động tạo** file `.env` từ `.env.example` nếu chưa có — bạn không cần copy thủ công.

### Các file quan trọng cần có sau khi clone

Các file dưới đây phải tồn tại trong repository để người mới clone có thể dựng lại môi trường mà không phải tự đoán cấu trúc:

- `backend/requirements.txt`
- `backend/.env.example`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/.env.example`
- `start.bat`
- `start.sh`
- `app_web_view/pubspec.yaml`
- `app_web_view/pubspec.lock`

### Tóm tắt SePay nhanh (sau khi clone)

- [ ] Tạo file môi trường:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

- [ ] Cập nhật tối thiểu trong `backend/.env`:
    - `SEPAY_API_KEY=<api-key-tu-sepay-dashboard>`
    - `NAME_WEB=W2L`
    - `SECRET_XOR_KEY=<so-nguyen-rieng-cua-du-an>`

- [ ] Trên SePay dashboard:
    - Đã liên kết tài khoản ngân hàng
    - Đã bật thông báo biến động số dư trên app ngân hàng
    - Đã tạo API key (key chỉ hiển thị 1 lần) và lưu an toàn

- [ ] (Tùy chọn) Cập nhật thông tin tài khoản nhận tiền trong `frontend/.env`:
    - `VITE_BANK_BIN`, `VITE_BANK_ACCOUNT`, `VITE_BANK_ACCOUNT_NAME`

- [ ] Khởi động lại backend sau khi đổi `.env`, rồi smoke test:
    - Tạo hóa đơn nạp token trên frontend
    - Chuyển khoản đúng nội dung `{NAME_WEB}NAPTOKEN{HEX_ID}`
    - Polling `GET /api/payment/status/{id}` trả `completed`

- [ ] Nếu đang ở môi trường dev và chưa có luồng ngân hàng thật, xác nhận thủ công qua:
    - `POST /api/payment/dev/complete/{id}`

> Luồng kỹ thuật chi tiết: `docs/sepay-payment-polling-sync.md`.

---

## Cấu Hình Biến Môi Trường

### Backend (`backend/.env` — chỉ sử dụng file này)

| Biến | Mặc định | Mô tả |
|---|---|---|
| `APP_ENV` | `development` | Chế độ chạy: `development` hoặc `production` |
| `JWT_SECRET_KEY` | *(bắt buộc đổi)* | Khóa ký JWT (ít nhất 32 ký tự, bắt buộc ở production) |
| `GOOGLE_CLIENT_ID` | *(trống)* | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | *(trống)* | Google OAuth Client Secret |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/auth/google/callback` | Callback URL cho Google OAuth |
| `FRONTEND_URL` | `http://localhost:5173` | URL frontend (để backend redirect kèm token) |
| `SEPAY_API_KEY` | *(trống)* | API key SePay (nạp token) |
| `NAME_WEB` | `W2L` | Prefix nội dung chuyển khoản SePay |
| `SECRET_XOR_KEY` | *(trống)* | Số nguyên dùng mã hóa nội dung SePay |
| ... | ... | ... |

> **Lưu ý:**
> - Chỉ sử dụng file `backend/.env` cho backend. Không cần và không nên tạo file `.env` ở thư mục gốc dự án.
> - Nếu lỡ tạo file `.env` ngoài root, hãy xóa để tránh nhầm lẫn.
> - Khi deploy hoặc phát triển, luôn kiểm tra và chỉnh sửa biến môi trường trong `backend/.env`.

### Tài khoản Admin mặc định

Khi backend khởi động, hệ thống tự đảm bảo có một tài khoản admin mặc định:

- **Username:** `admin`
- **Email:** `admin@word2latex.local`
- **Password:** `Admin@123456`

Bạn có thể đổi các giá trị này trong `backend/.env` bằng các biến `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.

> **Khuyến nghị bảo mật:** Đổi `ADMIN_PASSWORD` ngay sau lần chạy đầu tiên.

### Quy tắc token hiện tại

- Tài khoản `admin` chuyển đổi không bị trừ token.
- Tài khoản gói `free` có quota mặc định `60` trang (1 trang = 1 token).
- Khi hết quota, cần nạp token hoặc nâng gói để tiếp tục chuyển đổi.

### Frontend (`frontend/.env`)

| Biến | Mô tả |
|---|---|
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth Client ID (phải giống `GOOGLE_CLIENT_ID` ở backend) |
| `VITE_API_URL` | URL API backend (mặc định: `http://localhost:8000`) |

> **Bảo mật:** API Key, Secret Key chỉ được lưu trong `backend/.env` — KHÔNG bao giờ lộ trên frontend. Frontend chỉ giao tiếp với backend qua JWT token.

### Cấu hình Google OAuth (Redirect Flow) - tóm tắt nhanh

- [ ] Tạo/chọn project trong Google Cloud Console và bật **Google People API**
- [ ] Cấu hình **OAuth consent screen**:
    - App type: `External`
    - Điền thông tin app cơ bản
    - Thêm email test user khi app ở trạng thái `Testing`
- [ ] Tạo **OAuth Client ID** (`Web application`) với:
    - Authorized JavaScript origins: `http://localhost:5173`
    - Authorized redirect URIs:
        - `http://localhost:8000/api/auth/google/callback`
        - `http://localhost:8000/api/auth/google/callback/flutter`
- [ ] Cập nhật biến môi trường:
    - `backend/.env`: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GOOGLE_REDIRECT_URI_FLUTTER`, `FRONTEND_URL`
    - `frontend/.env`: `VITE_GOOGLE_CLIENT_ID`
- [ ] Restart backend + frontend
- [ ] Kiểm tra nhanh:
    - Mở `http://localhost:8000/api/auth/google/login` (nếu redirect sang Google là backend đã đọc key)
    - Đăng nhập Google từ `http://localhost:5173`

Lỗi thường gặp:
- `GOOGLE_CLIENT_ID` thiếu: sai vị trí file `.env` hoặc chưa restart backend
- `redirect_uri_mismatch`: URI trên Google Console không khớp 100%

### Quy trình rotate JWT key an toàn

1. Tạo khóa mới → gán vào `JWT_SECRET_KEY`.
2. Chuyển khóa cũ → `JWT_PREVIOUS_SECRET_KEYS`.
3. Deploy backend.
4. Chờ hết thời gian sống token (mặc định 7 ngày).
5. Xóa khóa cũ khỏi `JWT_PREVIOUS_SECRET_KEYS`.

---

## Sử Dụng

### Khởi động nhanh — 1 Click (Windows)

Nhấp đúp vào **`start.bat`** ở thư mục gốc. Script sẽ tự động:

1. Dừng các tiến trình cũ đang chiếm cổng `8000` và `5173`
2. Dọn dẹp thư mục `__pycache__`
3. Kích hoạt `.venv` và cài đặt thư viện Python
4. Khởi động **backend FastAPI** (`localhost:8000`) trong cửa sổ terminal riêng
5. Khởi động **frontend Vite** (`localhost:5173`) trong cửa sổ terminal riêng
6. Chờ 8 giây rồi tự động mở trình duyệt

### Khởi động nhanh (Linux/macOS)

```bash
chmod +x start.sh
./start.sh
```

### Khởi động Backend bằng `run_api.py`

```bash
# Chạy mặc định (auto-reload bật, port 8000)
python run_api.py

# Tùy chỉnh host/port
python run_api.py --host 0.0.0.0 --port 9000

# Tắt auto-reload (production)
python run_api.py --no-reload
```

### Khởi động thủ công (từng phần riêng)

**Backend:**
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Truy cập `http://localhost:5173` trên trình duyệt.

---

## Pipeline CLI (Không cần giao diện)

Nếu không muốn vào web UI, có thể chạy pipeline chuyển đổi trực tiếp bằng script:

- **Input 1**: 1 file Word (`.docx` hoặc `.docm`)
- **Input 2**: 1 file ZIP template LaTeX
- **Output**: thư mục kết quả chứa `.tex` và `.zip` (tùy chọn thêm `.pdf`)

### Lệnh chạy cơ bản

```powershell
# PowerShell (Windows)
python run_conversion_pipeline.py `
    --word input_data/Template_word/<ten_file_word>.docx `
    --template-zip <duong_dan_template_zip>.zip `
    --output-dir outputs/pipeline_cli
```

```bash
# Bash (Linux/macOS)
python run_conversion_pipeline.py \
    --word input_data/Template_word/<ten_file_word>.docx \
    --template-zip <duong_dan_template_zip>.zip \
    --output-dir outputs/pipeline_cli
```

### Tùy chọn nâng cao

```bash
# Biên dịch PDF (cần xelatex/pdflatex trong PATH)
python run_conversion_pipeline.py \
    --word <file>.docx --template-zip <template>.zip \
    --output-dir outputs/pipeline_cli --compile-pdf

# Giữ thư mục job để debug
python run_conversion_pipeline.py \
    --word <file>.docx --template-zip <template>.zip \
    --output-dir outputs/pipeline_cli --keep-workdir
```

## Pipeline Word -> Word CLI

Script dành cho chuyển đổi trực tiếp giữa Springer Word và IEEE Word:

- `springer-to-ieee`: Springer Word -> IEEE Word
- `ieee-to-springer`: IEEE Word -> Springer Word

```powershell
python run_word_to_word_pipeline.py `
    --input-word input_data/Template_word/<ten_file>.docx `
    --direction ieee-to-springer `
    --output-dir outputs/word_to_word
```

```bash
python run_word_to_word_pipeline.py \
    --input-word input_data/Template_word/<ten_file>.docx \
    --direction springer-to-ieee \
    --output-dir outputs/word_to_word
```

Tùy chọn template riêng:

```bash
python run_word_to_word_pipeline.py \
    --input-word <file>.docm \
    --direction ieee-to-springer \
    --template-word input_data/Template_word/splnproc2510.docm \
    --output-dir outputs/word_to_word
```

---

## API Endpoints

Swagger UI tương tác: `http://localhost:8000/docs`

### Endpoints chính

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/` | Metadata API và navigation links |
| `GET` | `/health` | Kiểm tra trạng thái server |
| `GET` | `/docs` | Swagger UI (tài liệu API chi tiết) |

### Auth & User

| Method | Path | Mô tả |
|---|---|---|
| `POST` | `/api/auth/register` | Đăng ký tài khoản mới |
| `POST` | `/api/auth/login` | Đăng nhập (trả JWT) |
| `POST` | `/api/auth/google` | Đăng nhập bằng Google ID Token |
| `GET` | `/api/auth/google/login` | Redirect sang Google consent screen |
| `GET` | `/api/auth/google/callback` | Callback từ Google OAuth |
| `GET` | `/api/auth/me` | Lấy thông tin user hiện tại |

### Chuyển đổi

| Method | Path | Mô tả |
|---|---|---|
| `POST` | `/api/chuyen-doi` | Upload file Word và chuyển đổi (SSE stream) |
| `GET` | `/api/chuyen-doi/stream/{job_id}` | Theo dõi tiến trình chuyển đổi |
| `GET` | `/api/chuyen-doi/download/{job_id}` | Tải file kết quả (.zip) |

### Template

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/api/templates` | Liệt kê các mẫu LaTeX có sẵn |
| `POST` | `/api/templates/upload` | Tải lên mẫu LaTeX tùy chỉnh |
| `DELETE` | `/api/templates/{name}` | Xóa mẫu tùy chỉnh |

### Admin

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/api/admin/users` | Danh sách tất cả user |
| `PATCH` | `/api/admin/users/{id}` | Cập nhật thông tin / quyền user |
| `GET` | `/api/admin/audit-logs` | Xem nhật ký hoạt động admin |

---

## Luồng Chuyển Đổi

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Upload      │     │  AST Parser  │     │  Template        │     │  Jinja2       │
│  .docx/.docm │────►│  Word XML    │────►│  Preprocessor    │────►│  Renderer     │
│              │     │  → IR (JSON) │     │  Inject tags     │     │  IR → .tex    │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────┬───────┘
                           │                                            │
                    ┌──────┴──────┐                              ┌──────▼───────┐
                    │ Xử lý chuyên│                              │  Biên dịch    │
                    │ biệt:       │                              │  XeLaTeX /    │
                    │ • Toán OMML │                              │  pdfLaTeX     │
                    │ • OLE Eq.   │                              │  → .pdf       │
                    │ • Ảnh       │                              └──────┬───────┘
                    │ • Bảng      │                                     │
                    └─────────────┘                              ┌──────▼───────┐
                                                                 │  Package ZIP  │
                                                                 │  .tex + .pdf  │
                                                                 │  + images     │
                                                                 │  + .cls/.bst  │
                                                                 └──────────────┘
```

1. **Upload** — Nhận file `.docx` / `.docm` (≤ 10MB) qua API
2. **Tiền xử lý** — Loại bỏ VBA macro (`.docm`), chuyển Strict Open XML → Transitional
3. **Phân tích AST** — Duyệt XML Word, phân loại ngữ nghĩa, trích xuất metadata + body nodes → IR
4. **Xử lý chuyên biệt** — Toán (OMML/OLE), ảnh (lọc trang trí), bảng (multirow/multicolumn)
5. **Tiền xử lý template** — Inject tag Jinja2 vào mẫu LaTeX đã chọn
6. **Render** — Kết hợp IR + template Jinja2 → file `.tex` hoàn chỉnh
7. **Biên dịch** — XeLaTeX hoặc pdfLaTeX (tự động phát hiện) → PDF
8. **Đóng gói** — Tạo `.zip` chứa `.tex`, `.pdf`, ảnh, và các file phụ thuộc

---

## Công Nghệ Sử Dụng

| Tầng | Công nghệ | Phiên bản |
|---|---|---|
| **Backend API** | FastAPI, Uvicorn | 0.115.0, 0.32.0 |
| **Engine chuyển đổi** | python-docx, lxml, Pillow, olefile, Jinja2 | 1.1.0, ≥4.9, ≥10.4, 0.47, ≥3.1.4 |
| **Template rendering** | Jinja2 (custom delimiters `<< >>`) | ≥3.1.4 |
| **Xác thực** | python-jose (JWT HS256), passlib, bcrypt | 3.3.0, 1.7.4, 4.0.1 |
| **Cơ sở dữ liệu** | SQLite via SQLAlchemy | 2.0.36 |
| **Frontend** | React, Vite, TailwindCSS | 18.2, 5.0, 3.4 |
| **UI** | Framer Motion, Lucide React, React Dropzone | 10.16, 0.303, 14.2 |
| **Chuyển đổi toán** | XSLT (OMML → MathML → LaTeX), Pandoc (fallback) | — |
| **Biên dịch PDF** | XeLaTeX + pdfLaTeX (dual-engine) | TeX Live / MiKTeX |

---

## Kiểm Thử

### Unit tests (Backend)

```bash
# Chạy toàn bộ test
pytest

# Chạy test cụ thể
pytest tests/test_api_smoke.py -v

# Chạy với coverage
pytest --cov=backend
```

Danh sách test hiện có (24 file):

| File test | Kiểm thử |
|---|---|
| `test_api_smoke.py` | Smoke test các API endpoint chính |
| `test_injection.py` | Chống injection vào LaTeX |
| `test_compile.py` | Biên dịch LaTeX |
| `test_token_deduct_refund.py` | Token economy (trừ/hoàn token) |
| `test_rate_limit_auth.py` | Rate limiting cho auth |
| `test_rate_limit_convert_admin.py` | Rate limiting cho convert/admin |
| `test_admin_token_audit.py` | Admin audit log |
| `test_author_fix.py` | Xử lý tác giả |
| `test_fontspec_injection.py` | Font specification injection |
| `test_texsoup*.py` | TexSoup parsing |
| `test_pdftex_*.py` | pdfTeX regex |
| `test_mdpi_title.py` | MDPI template title |
| `test_oscm.py` | OSCM format |
| `test_apacite_fix.py` | Apacite bibliography |
| ... | ... |

### E2E tests (Frontend)

```bash
cd frontend
npm run test:e2e
```

---

## Bảo Mật

### API Key & Secret

- ✅ Tất cả API Key, Secret Key chỉ lưu trong `backend/.env` — **KHÔNG** lộ trên frontend.
- ✅ Google OAuth Client Secret chỉ xử lý ở backend.
- ✅ Frontend giao tiếp với backend qua **JWT token** (HS256, 7 ngày).
- ✅ Hỗ trợ **rotate JWT key** an toàn (không làm user bị đăng xuất đột ngột).

### Xác thực & Phân quyền

- ✅ JWT không trạng thái, lưu trong `localStorage` (phù hợp cho môi trường dev/nội bộ).
- ✅ Có **silent re-auth**: frontend tự xác thực lại token theo chu kỳ, tự đăng xuất khi nhận `401`.
- ✅ Hệ thống phân quyền: `user` / `admin` — admin có dashboard quản trị riêng.
- ✅ **Audit log** ghi lại mọi hành động admin.

### Chống lạm dụng

- ✅ **Rate limiting** theo nhóm: auth (30/phút), convert (20/phút), admin (120/phút).
- ✅ **Request ID** (UUID) gắn vào mọi request để truy vết.
- ✅ Giới hạn upload file: Word ≤ 10MB, Template ≤ 20MB.

### Lưu ý khi triển khai production

- Đổi `JWT_SECRET_KEY` thành chuỗi random dài ≥ 32 ký tự.
- Đặt `APP_ENV=production`.
- Cân nhắc chuyển JWT sang mô hình `httpOnly + Secure + SameSite cookie` + CSRF protection khi deploy công khai.

---

## Lưu Ý Về Mẫu LaTeX (Custom Templates)

Khi tải lên mẫu tùy chỉnh, khuyến khích đóng gói thành file **`.zip`**:

| Loại file | Tác dụng |
|---|---|
| **`.tex`** | File mã nguồn chính (chứa cấu trúc tài liệu) |
| **`.cls`** | LaTeX Class file (layout, font, margin) |
| **`.sty`** | Style file (macro bổ trợ) |
| **`.bst`** | BibTeX Style (cách trình bày tham khảo) |
| **`.bib`** | Bibliography (dữ liệu trích dẫn) |
| **`.csl`** | Citation Style Language |

> **Tại sao nên dùng ZIP?** Một file `.tex` đơn lẻ thường thiếu các file phụ trợ. ZIP đảm bảo đầy đủ và có thể biên dịch ngay trên Overleaf.

---

## Giấy Phép

Dự án được cấp phép theo **MIT License**. Xem [LICENSE](LICENSE) để biết chi tiết.
