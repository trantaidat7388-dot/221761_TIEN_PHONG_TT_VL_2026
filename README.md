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
- [Docker TeX Live (XeLaTeX)](#docker-tex-live-xelatex)
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

> **Dự án nghiên cứu** — Phát triển bởi sinh viên Đại học, nhằm mục tiêu tự động hóa quy trình chuẩn bị bài báo khoa học từ bản thảo Word sang định dạng LaTeX chuẩn.

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
- **Quản trị Admin** — Dashboard thống kê tương tác với **Recharts** giúp vẽ các biểu đồ phân tích (Tăng trưởng người dùng, tỷ trọng Free/Premium, biểu đồ Doanh thu SePay theo ngày), quản lý người dùng, template, hóa đơn và nhật ký thao tác (Audit Log).
- **Lộ trình quản trị Admin** — Xem checklist, kiến trúc quyền và backlog tại `docs/admin-governance-roadmap.md`.
- **Tài liệu SePay** — Luồng kỹ thuật tại `docs/sepay-payment-polling-sync.md`, hướng dẫn lấy key tại `HUONG_DAN_LAY_SEPAY_API_KEY.md`.
- **Rate Limiting** — Giới hạn request theo nhóm (auth, convert, admin) để chống lạm dụng.
- **Dọn dẹp tự động** — Thư mục job tạm và file output được xóa theo TTL cấu hình.
- **Chạy hoàn toàn offline** — Không gọi API bên ngoài. Toàn bộ xử lý diễn ra trên máy cục bộ.

---

## Cấu Trúc Dự Án

```
221761_TIEN_PHONG_TT_VL_2026/
├── backend/                             # Thư mục chính chứa mã nguồn backend
│   ├── app/                             # Lớp Web API (FastAPI)
│   │   ├── main.py                      # Điểm khởi đầu ứng dụng (Khởi tạo FastAPI, Routes, Middleware)
│   │   ├── config.py                    # Quản lý cấu hình dự án (đọc từ file .env)
│   │   ├── database.py                  # Kết nối Database (SQLite + SQLAlchemy)
│   │   ├── auth.py                      # Hàm tiện ích xác thực (JWT, hash password)
│   │   ├── models/                      # Định nghĩa các mô hình dữ liệu (DB models)
│   │   │   ├── __init__.py              # ORM entities (User, ConversionHistory, TokenLedger, AdminAuditLog)
│   │   │   └── base_db.py              # Kết nối và thao tác với Database (export Base/Session/engine)
│   │   ├── routers/                     # Chứa các file định nghĩa API endpoints (Routes)
│   │   │   ├── auth_routes.py           # API xác thực (Login, Register, Google OAuth, JWT)
│   │   │   ├── base.py                  # API cơ bản (Health check, root)
│   │   │   ├── file_upload.py           # Facade tổng hợp API upload/download
│   │   │   ├── chuyen_doi.py            # API xử lý chuyển đổi Word → LaTeX (SSE stream)
│   │   │   ├── templates.py             # API quản lý mẫu LaTeX (upload/list/delete)
│   │   │   └── admin_routes.py          # API quản trị hệ thống (user management, audit)
│   │   ├── security/                    # Logic bảo mật
│   │   │   └── security.py              # Xử lý JWT, Hashing password, quyền admin
│   │   ├── services/                    # Các dịch vụ xử lý logic nghiệp vụ
│   │   │   └── token_service.py         # Token economy (trừ/hoàn token, ledger)
│   │   └── utils/                       # Các hàm tiện ích dùng trong logic app
│   │       └── api_utils.py             # Helpers (dọn dẹp thư mục mồ côi, file utils)
│   │
│   ├── core_engine/                     # Engine chuyển đổi cốt lõi (Python thuần)
│   │   ├── chuyen_doi.py                # Lớp điều phối ChuyenDoiWordSangLatex
│   │   ├── ast_parser.py                # WordASTParser: XML Word → IR (JSON)
│   │   ├── semantic_parser.py           # Bộ phân loại ngữ nghĩa heuristic
│   │   ├── template_preprocessor.py     # Inject tag Jinja2 vào mẫu LaTeX
│   │   ├── jinja_renderer.py            # JinjaLaTeXRenderer: IR + template → .tex
│   │   ├── xu_ly_toan.py                # OMML → LaTeX (XSLT / Pandoc / manual parser)
│   │   ├── xu_ly_ole_equation.py        # OLE Equation Editor 3.0 (MTEF binary) → LaTeX
│   │   ├── xu_ly_anh.py                 # Lọc ảnh thông minh (entropy, cạnh, histogram)
│   │   ├── xu_ly_bang.py                # Xử lý bảng (multirow, multicolumn, TOC filter)
│   │   ├── word_loader.py               # Tiền xử lý file Word (.docm → .docx, Strict → Transitional)
│   │   ├── author_strategies.py         # Strategy pattern cho phân tích tác giả
│   │   ├── docx_compat.py               # Xử lý tương thích định dạng Word
│   │   ├── utils.py                     # Biên dịch LaTeX, đóng gói ZIP
│   │   ├── tex_log_parser.py            # Phân tích log LaTeX → lỗi có cấu trúc
│   │   ├── config.py                    # Hằng số, namespace XML, Regex engine
│   │   ├── publishers_manifest.json     # Manifest các nhà xuất bản hỗ trợ
│   │   └── OMML2MML.XSL                 # XSLT stylesheet (OMML → MathML)
│   │
│   ├── storage/                         # Thư mục lưu trữ dữ liệu
│   │   ├── custom_templates/            # Mẫu LaTeX hệ thống + người dùng tải lên
│   │   └── temp_jobs/                   # Thư mục job đang chạy (tự dọn theo TTL)
│   │
│   ├── .env.example                     # File mẫu biến môi trường
│   └── requirements.txt                 # Danh sách thư viện Python cần cài đặt
│
├── frontend/                            # React 18 + Vite 5 SPA
│   ├── src/
│   │   ├── App.jsx                      # Router chính (/dang-nhap, /chuyen-doi, /lich-su)
│   │   ├── main.jsx                     # Entry point React
│   │   ├── index.css                    # Global styles (TailwindCSS)
│   │   ├── components/                  # UI components dùng chung
│   │   │   ├── ThanhDieuHuong.jsx       # Navigation bar
│   │   │   ├── NutBam.jsx               # Button component
│   │   │   ├── KhungThongBao.jsx        # Notification/alert component
│   │   │   └── Loading.jsx              # Loading spinner
│   │   ├── features/                    # Feature modules (tách theo chức năng)
│   │   │   ├── xac_thuc/               # Trang đăng nhập / đăng ký
│   │   │   ├── chuyen_doi/             # Trang chuyển đổi Word → LaTeX
│   │   │   ├── lich_su/                # Trang lịch sử chuyển đổi
│   │   │   ├── tai_khoan/              # Trang quản lý tài khoản
│   │   │   ├── premium/               # Trang đăng ký Premium
│   │   │   └── admin/                  # Trang quản trị (admin dashboard)
│   │   ├── context/                     # React Context (AuthContext - JWT state)
│   │   ├── services/                    # API client
│   │   │   └── api.js                   # SSE streaming client + REST API calls
│   │   ├── config/                      # Cấu hình frontend
│   │   └── utils/                       # Hàm tiện ích frontend
│   ├── tests-e2e/                       # Playwright E2E tests
│   ├── package.json                     # Dependencies frontend
│   └── vite.config.js                   # Cấu hình Vite
│
├── tests/                               # Unit tests (pytest) - 24 file test
│   ├── conftest.py                      # Pytest fixtures
│   ├── test_api_smoke.py                # Smoke test API endpoints
│   ├── test_injection.py                # Test chống injection
│   ├── test_compile.py                  # Test biên dịch LaTeX
│   ├── test_token_deduct_refund.py      # Test token economy
│   ├── test_rate_limit_auth.py          # Test rate limiting
│   ├── test_admin_token_audit.py        # Test admin audit log
│   └── ...                              # Và các test khác
│
├── input_data/                          # Dữ liệu đầu vào mẫu (template Word)
├── outputs/                             # Thư mục lưu kết quả chuyển đổi
│
├── run_api.py                           # Script khởi động nhanh API bằng Uvicorn
├── run_conversion_pipeline.py           # Script chạy pipeline CLI (không cần web UI)
├── start.bat                            # Trình khởi động 1-click (Windows)
├── start.sh                             # Script khởi động cho Linux/macOS
├── requirements.txt                     # Thư viện Python (core engine - CLI mode)
├── pytest.ini                           # Cấu hình pytest
├── .env                                 # Biến môi trường (DB Info, Secret Keys) - KHÔNG đẩy lên Git
├── .gitignore                           # Danh sách file/thư mục bỏ qua khi push Git
├── HUONG_DAN_LAY_GOOGLE_OAUTH_KEY.md    # Hướng dẫn lấy Google OAuth credentials
└── README.md                            # Hướng dẫn chi tiết dự án (file này)
```

### Ánh xạ với cấu trúc bài tập mẫu

| Cấu trúc mẫu (`api_base/`) | Dự án thực tế | Ghi chú |
|---|---|---|
| `app/main.py` | `backend/app/main.py` | Khởi tạo FastAPI, Routes, Middleware |
| `app/config.py` | `backend/app/config.py` | Đọc cấu hình từ `.env` |
| `app/models/base_db.py` | `backend/app/models/base_db.py` | Kết nối Database |
| `app/routers/auth.py` | `backend/app/routers/auth_routes.py` | API xác thực (Login, JWT, Google OAuth) |
| `app/routers/base.py` | `backend/app/routers/base.py` | API cơ bản (Health check) |
| `app/routers/file_upload.py` | `backend/app/routers/file_upload.py` | API upload/download file |
| `app/security/security.py` | `backend/app/security/security.py` | JWT, Hashing password |
| `app/utils/helpers.py` | `backend/app/utils/api_utils.py` | Hàm tiện ích cho API |
| `chatbot/` hoặc `ingestion/` | `backend/core_engine/` | Module xử lý chuyển đổi Word → LaTeX (18 file) |
| `utils/upload_temp/` | `backend/storage/temp_jobs/` | Lưu trữ file tạm |
| `test/` | `tests/` | 24 file unit test (pytest) |
| `run_api.py` | `run_api.py` | Khởi động nhanh API bằng Uvicorn |
| `start.sh` | `start.sh` + `start.bat` | Script khởi chạy (Linux + Windows) |
| `.env` | `backend/.env` | Biến môi trường (secrets) |
| `requirements.txt` | `backend/requirements.txt` | Danh sách thư viện Python |
| `readme.md` | `README.md` | Hướng dẫn chi tiết dự án |

---

## Yêu Cầu Hệ Thống

| Thành phần | Phiên bản | Bắt buộc? | Ghi chú |
|---|---|---|---|
| **Python** | 3.10+ | ✅ Có | Backend + core engine |
| **Node.js** | 18+ | ✅ Có | Frontend React |
| **npm** | 8+ | ✅ Có | Đi kèm Node.js |
| **Docker Desktop** | 4.x+ | ❌ Tùy chọn | Dùng để chạy TeX Live/XeLaTeX bằng container |
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

*   **Cách 3: Dùng Docker TeX Live (khuyến nghị khi deploy server)**
    *   Không cần cài TeX Live trực tiếp vào máy host.
    *   Môi trường biên dịch đồng nhất giữa local, CI/CD và production.
    *   Xem mục [Docker TeX Live (XeLaTeX)](#docker-tex-live-xelatex) để cài và chạy.

---

## Docker TeX Live (XeLaTeX)

Phần này dùng khi bạn muốn biên dịch PDF bằng XeLaTeX thông qua Docker thay vì cài TeX Live/MiKTeX trực tiếp lên máy.

### 1. Cài Docker Desktop (Windows)

1. Tải Docker Desktop tại: https://www.docker.com/products/docker-desktop/
2. Cài đặt theo wizard mặc định, bật tùy chọn WSL2 nếu được hỏi.
3. Khởi động lại máy nếu trình cài đặt yêu cầu.
4. Mở Docker Desktop và chờ trạng thái chuyển sang `Engine running`.
5. Kiểm tra bằng PowerShell:

```powershell
docker --version
docker compose version
```

> Nếu lệnh chưa nhận, mở lại terminal hoặc restart VS Code.

### 2. Build image TeX Live của dự án

```powershell
docker build -t word2latex-texlive:latest -f docker/texlive/Dockerfile .
```

### 3. Biên dịch 1 file `.tex` bằng Docker (XeLaTeX)

Giả sử bạn có file `main.tex` trong thư mục `outputs/pipeline_cli`:

```powershell
docker compose -f docker-compose.texlive.yml run --rm texlive xelatex -interaction=nonstopmode -halt-on-error ./main.tex
```

### 4. Biên dịch 2 lượt để ổn định mục lục/references

```powershell
docker compose -f docker-compose.texlive.yml run --rm texlive xelatex -interaction=nonstopmode -halt-on-error ./main.tex
docker compose -f docker-compose.texlive.yml run --rm texlive xelatex -interaction=nonstopmode -halt-on-error ./main.tex
```

### 5. Đổi thư mục làm việc / file đầu vào

Mặc định service `texlive` mount thư mục `outputs/pipeline_cli` vào container tại `/workspace`.

- Muốn dùng thư mục khác, sửa volume trong `docker-compose.texlive.yml`.
- Muốn biên dịch file khác, thay `./main.tex` bằng tên file tương ứng.

### 6. Kịch bản deploy internet

- Nếu backend của bạn có bước compile PDF trên server: nên cài Docker trên server và dùng image này để compile.
- Nếu server chỉ tạo `.tex` và cho người dùng tải lên Overleaf: không bắt buộc Docker TeX Live.

---

## Hướng Dẫn Cài Đặt

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

> **Lưu ý:** Dự án ghim `bcrypt==4.0.1` để tương thích với `passlib`. Không nâng cấp bcrypt độc lập.

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

Sau đó mở file `backend/.env` và chỉnh sửa các giá trị cần thiết (xem mục [Cấu Hình Biến Môi Trường](#cấu-hình-biến-môi-trường)). Với mục đích **dev/test**, giữ nguyên giá trị mặc định là đủ dùng.

### Checklist SePay setup nhanh (cho team)

1. Copy mẫu cấu hình SePay:

```bash
# Linux / macOS
cp backend/.env.sepay.example backend/.env.sepay.local
```

```powershell
# Windows PowerShell
Copy-Item backend/.env.sepay.example backend/.env.sepay.local
```

2. Mở `backend/.env` và điền tối thiểu 3 biến sau:
- `SEPAY_API_KEY=<api-key-tu-sepay-dashboard>`
- `NAME_WEB=W2L` (prefix nội dung chuyển khoản)
- `SECRET_XOR_KEY=<so-nguyen-rieng-cua-du-an>`

3. Trên SePay Dashboard:
- Đã thêm tài khoản ngân hàng (MB/VCB/VPB...)
- Đã bật app ngân hàng trên điện thoại để SePay đồng bộ biến động số dư
- Đã tạo API key và copy đúng vào `backend/.env`

4. Khởi động lại backend sau khi cập nhật `.env`.

5. Smoke test nhanh luồng nạp tiền:
- Đăng nhập frontend -> vào Premium -> tạo hóa đơn nạp
- Chuyển khoản đúng nội dung `{NAME_WEB}NAPTOKEN{HEX_ID}`
- Kiểm tra polling `GET /api/payment/status/{id}` trả về `completed`

> Tài liệu chi tiết: `docs/sepay-payment-polling-sync.md` và `HUONG_DAN_LAY_SEPAY_API_KEY.md`.

---

## Cấu Hình Biến Môi Trường

### Backend (`backend/.env`)

| Biến | Mặc định | Mô tả |
|---|---|---|
| `APP_ENV` | `development` | Chế độ chạy: `development` hoặc `production` |
| `JWT_SECRET_KEY` | *(bắt buộc đổi)* | Khóa ký JWT (ít nhất 32 ký tự, bắt buộc ở production) |
|  |  |  
|  |  |  > **Ví dụ khóa mạnh:** `FAKNM8SByfmg5bwBZHV+PYx9d0gXcBkQOuyT38g1XrQ=` (base64, 44 ký tự)
|  |  |  > Có thể sinh bằng Python: `import secrets; print(secrets.token_urlsafe(48))`
|  |  |  > Không dùng password ngắn, UUID, hoặc chuỗi dễ đoán.
| `JWT_PREVIOUS_SECRET_KEYS` | *(trống)* | Khóa cũ (phân tách bằng dấu phẩy) — dùng khi rotate key |
| `CORS_ALLOW_ALL` | `0` | Đặt `1` cho phép mọi origin (chỉ dùng khi dev) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Các origin được phép (phân tách bằng dấu phẩy) |
| `LOG_LEVEL` | `INFO` | Mức log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MAX_DOC_UPLOAD_MB` | `10` | Giới hạn upload file Word (MB) |
| `MAX_TEMPLATE_UPLOAD_MB` | `20` | Giới hạn upload template (MB) |
| `GOOGLE_CLIENT_ID` | *(trống)* | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | *(trống)* | Google OAuth Client Secret |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/auth/google/callback` | Callback URL cho Google OAuth |
| `FRONTEND_URL` | `http://localhost:5173` | URL frontend (để backend redirect kèm token) |
| `SSE_CLEANUP_DELAY_SECONDS` | `3600` | Thời gian giữ job SSE trước khi dọn (giây) |
| `LATEX_COMPILE_TIMEOUT_SECONDS` | `30` | Timeout biên dịch LaTeX (giây) |
| `TEMP_TTL_HOURS` | `6` | Số giờ trước khi xóa thư mục job tạm |
| `OUTPUT_TTL_HOURS` | `24` | Số giờ trước khi xóa file output |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `30` | Giới hạn request auth/phút |
| `RATE_LIMIT_CONVERT_PER_MINUTE` | `20` | Giới hạn request convert/phút |
| `RATE_LIMIT_ADMIN_PER_MINUTE` | `120` | Giới hạn request admin/phút |
| `FREE_PLAN_MAX_PAGES` | `60` | Giới hạn gói thường: 60 trang (1 trang = 1 token) |
| `ADMIN_USERNAME` | `admin` | Tên đăng nhập admin mặc định (tạo khi startup) |
| `ADMIN_EMAIL` | `admin@word2latex.local` | Email admin mặc định (tạo khi startup) |
| `ADMIN_PASSWORD` | `Admin@123456` | Mật khẩu admin mặc định (đổi ngay khi triển khai thực tế) |

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

### Cấu hình Google OAuth

Xem hướng dẫn đầy đủ tại: [`HUONG_DAN_LAY_GOOGLE_OAUTH_KEY.md`](HUONG_DAN_LAY_GOOGLE_OAUTH_KEY.md)

#### Gợi ý chuẩn cho Avatar (AVT) khi đăng nhập Google

- Bắt buộc giữ đủ scope: `openid email profile`.
- Dùng Redirect Flow: `GET /api/auth/google/login` -> Google -> `GET /api/auth/google/callback` -> frontend `/?token=...`.
- Sau khi frontend nhận token, gọi `GET /api/auth/me` để đồng bộ hồ sơ phiên hiện tại.
- Nếu chưa lưu avatar trong DB, UI nên fallback bằng chữ cái đầu tên/email (tránh ô trống avatar).
- Nếu bổ sung cột avatar về sau, ưu tiên lưu URL ảnh HTTPS từ Google userinfo và luôn có fallback initials trong giao diện.

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
