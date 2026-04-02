<div align="center">

# Word2LaTeX — Chuyển Đổi Tài Liệu Word Sang LaTeX Học Thuật

**Chuyển đổi file Word (.docx / .docm) sang mã nguồn LaTeX chuẩn xuất bản chỉ với một cú nhấp chuột.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Giới Thiệu

**Word2LaTeX** là công cụ chuyển đổi tài liệu học thuật full-stack, giúp biến các file `.docx` / `.docm` thành gói mã nguồn LaTeX sẵn sàng nộp cho hội nghị hoặc tạp chí khoa học. Hệ thống phân tích cấu trúc bên trong của file Word thông qua **bộ phân tích cú pháp AST kết hợp Heuristics**, xây dựng **biểu diễn trung gian (IR)** độc lập với bố cục LaTeX, và dựng lại tài liệu thông qua **pipeline Jinja2** hỗ trợ **5 mẫu nhà xuất bản** phổ biến nhất.

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

Ngoài ra, người dùng có thể **tải lên mẫu riêng** (file `.tex` hoặc `.zip` chứa các file định dạng như `.cls`, `.sty`, `.bst`, `.bib`, `.csl`). **Khuyến khích sử dụng file ZIP** để đảm bảo đầy đủ các thành phần bổ trợ.

### Chuyển đổi thông minh

- **Phân tích AST + Heuristics** — Tự động nhận dạng tiêu đề, tác giả, đơn vị công tác, tóm tắt, từ khóa, heading, hình ảnh, bảng biểu, danh sách, và công thức toán học — ngay cả với file Word không dùng style chuẩn.
- **Bộ phân loại ngữ nghĩa** — Dự đoán vai trò của đoạn văn (TITLE, AUTHOR, ABSTRACT, HEADING, REFERENCE,...) dựa trên nội dung, vị trí, độ dài và định dạng — không cần model ML.
- **Chuyển đổi công thức toán học 3 tầng** — OMML → LaTeX qua (1) XSLT transform, (2) Pandoc fallback, (3) Manual recursive parser. Hỗ trợ phân số, căn thức, tích phân, tổng, ma trận, ký tự Hy Lạp,...
- **Hỗ trợ OLE Equation Editor 3.0** — Chuyển đổi công thức legacy nhúng dạng OLE (MTEF v3 binary) sang LaTeX, bao gồm bảng ánh xạ Unicode → LaTeX đầy đủ.
- **Lọc ảnh thông minh** — Phân biệt ảnh nội dung (biểu đồ, đồ thị, ảnh chụp) và ảnh trang trí (logo, icon) bằng Shannon entropy, đếm màu, phát hiện cạnh — chỉ giữ ảnh nội dung.
- **Xử lý bảng nâng cao** — Hỗ trợ `multirow` / `multicolumn`, phát hiện và loại bỏ bảng Mục lục (TOC), xử lý công thức toán bên trong ô bảng.
- **Phân tích tác giả thông minh** — Tự động trích xuất và liên kết ký hiệu chú thích (`*`, `†`) và địa chỉ email từ khối tác giả.

### Hệ thống

- **Tiến trình thời gian thực (SSE)** — 6 bước chuyển đổi được đẩy trực tiếp đến trình duyệt qua Server-Sent Events, kèm theo **đồng hồ đếm giây (timer)** thực tế.
- **Biên dịch dual-engine** — Tự động phát hiện engine phù hợp: XeLaTeX (mặc định) hoặc pdfLaTeX (cho mẫu MDPI / pgf). Sinh PDF phía server với báo cáo lỗi chi tiết.
- **Cơ chế ổn định & Timeout** — Đồng bộ timeout giữa frontend (35s) và backend (25s) để ngăn trạng thái treo. Tự động cảnh báo khi người dùng nhấn F5 hoặc đóng tab lúc đang xử lý để tránh mất kết nối stream.
- **Xác thực JWT** — Đăng nhập bằng token không trạng thái (HS256, 7 ngày). Lịch sử chuyển đổi được lưu riêng theo người dùng trong SQLite.
- **Chạy hoàn toàn offline** — Không gọi API bên ngoài. Toàn bộ xử lý diễn ra trên máy cục bộ.
- **Dọn dẹp tự động** — Thư mục job tạm và file output được xóa theo TTL cấu hình.

---

## Yêu Cầu Hệ Thống

| **npm** | 8+ | Đi kèm với Node.js |

### Hướng dẫn cài đặt LaTeX (Chọn 1 trong 2)

*   **Cách 1: Cài đặt trên máy (Để có PDF ngay lập tức)**
    *   **Windows**: Khuyên dùng [MiKTeX](https://miktex.org/download) (nhẹ, tự tải gói lệnh) hoặc [TeX Live](https://tug.org/texlive/acquire-netinstall.html) (đầy đủ, ổn định cao).
    *   **macOS**: Cài đặt [MacTeX](https://www.tug.org/mactex/).
    *   **Linux**: `sudo apt install texlive-full`.
    *   **Yêu cầu**: Sau khi cài đặt, hãy đảm bảo lệnh `xelatex` có thể chạy được từ Terminal/CMD.

*   **Cách 2: Sử dụng Overleaf (Không cần cài đặt, khuyên dùng cho máy yếu)**
    *   Nếu bạn không cài LaTeX, hệ thống vẫn sẽ sinh ra file **`.zip`**.
    *   Truy cập [Overleaf](https://www.overleaf.com/), tạo dự án mới và chọn **Upload Project**.
    *   Tải file `.zip` từ Word2LaTeX lên. Overleaf sẽ tự động biên dịch và hiển thị PDF cho bạn.


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

### 5. Cấu hình biến môi trường backend (bảo mật JWT)

Tạo file `.env` cho backend từ mẫu:

```bash
cp backend/.env.example backend/.env
```

Trên Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

Thiết lập tối thiểu:

- `JWT_SECRET_KEY`: khóa ký JWT hiện tại (bắt buộc ở production)
- `JWT_PREVIOUS_SECRET_KEYS`: danh sách khóa cũ (phân tách dấu phẩy) để hỗ trợ rotate key không làm người dùng đăng xuất ngay
- `APP_ENV=production`: bật chế độ production

#### Quy trình rotate key an toàn

1. Tạo khóa mới và gán vào `JWT_SECRET_KEY`.
2. Chuyển khóa cũ sang `JWT_PREVIOUS_SECRET_KEYS`.
3. Deploy backend.
4. Chờ hết thời gian sống token (mặc định 7 ngày).
5. Xóa khóa cũ khỏi `JWT_PREVIOUS_SECRET_KEYS`.

---

## Sử Dụng

### Khởi động nhanh (Windows)

Nhấp đúp vào **`start.bat`** ở thư mục gốc. Script sẽ tự động:

1. Dừng các tiến trình cũ đang chiếm cổng `8000` và `5173`
2. Dọn dẹp thư mục `__pycache__`
3. Kích hoạt `.venv` và cài đặt thư viện Python
4. Khởi động **backend FastAPI** (`localhost:8000`) trong cửa sổ terminal riêng
5. Khởi động **frontend Vite** (`localhost:5173`) trong cửa sổ terminal riêng
6. Chờ 12 giây rồi tự động mở trình duyệt

Nhấn phím bất kỳ trong cửa sổ `start.bat` để dừng cả hai server.

### Khởi động nhanh (Linux/macOS)

```bash
chmod +x start.sh
./start.sh
```

Script sẽ:

1. Giải phóng các cổng `8000`, `5173`, `3000`
2. Dọn thư mục `__pycache__`
3. Kích hoạt hoặc tạo `.venv` rồi cài dependencies backend
4. Chạy backend và frontend ở chế độ nền
5. Ghi log vào `outputs/backend.log` và `outputs/frontend.log`

---

## Biến Môi Trường Backend

Các biến chính (xem đầy đủ trong `backend/.env.example`):

- `APP_ENV`: `development` hoặc `production`
- `JWT_SECRET_KEY`: khóa ký token hiện tại
- `JWT_PREVIOUS_SECRET_KEYS`: danh sách khóa cũ để hỗ trợ rotate key
- `LOG_LEVEL`: mức log (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `CORS_ALLOW_ALL`, `CORS_ORIGINS`: cấu hình CORS
- `MAX_DOC_UPLOAD_MB`, `MAX_TEMPLATE_UPLOAD_MB`: giới hạn upload
- `SSE_CLEANUP_DELAY_SECONDS`: thời gian giữ job SSE trước khi dọn
- `LATEX_COMPILE_TIMEOUT_SECONDS`: timeout compile LaTeX
- `TEMP_TTL_HOURS`, `OUTPUT_TTL_HOURS`: TTL dọn dữ liệu tạm/output

### Khởi động thủ công

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

## API Endpoints

Swagger UI tương tác: `http://localhost:8000/docs`

| `GET` | `/api/health` | — | Kiểm tra trạng thái server |
| `GET` | `/docs` | — | Swagger UI (Tài liệu API chi tiết) |

---

## Lưu ý về Mẫu LaTeX (Custom Templates)

Khi tải lên mẫu LaTeX tùy chỉnh, hệ thống khuyến khích bạn đóng gói thành một file **`.zip`** bao gồm các thành phần sau:

| Loại file | Tác dụng | Tại sao cần? |
|---|---|---|
| **`.tex`** | File mã nguồn chính | Chứa cấu trúc tài liệu và các thẻ Jinja2 (`<< >>`) để ép dữ liệu từ Word vào. |
| **`.cls`** | LaTeX Class file | Định nghĩa layout, font, margin của bài báo (Ví dụ: `IEEEtran.cls`, `acmart.cls`). |
| **`.sty`** | Style file | Chứa các macro bổ trợ hoặc cấu hình gói lệnh riêng cho mẫu đó. |
| **`.bst`** | BibTeX Style | Định nghĩa cách trình bày danh mục tham khảo (Vd: số thứ tự [1], hoặc Harvard (Name, Year)). |
| **`.bib`** | Bibliography | File chứa dữ liệu trích dẫn. Hệ thống sẽ tự động ghép trích dẫn từ Word vào đây. |
| **`.csl`** | Citation Style Language | Quy tắc trích dẫn chuẩn (thường dùng cho Pandoc). Hệ thống hỗ trợ đính kèm file này trong gói ZIP kết quả. |

> [!TIP]
> **Tại sao nên ưu tiên file ZIP?**
> Một file `.tex` đơn lẻ thường không chứa đủ thông tin về font và định dạng của các tạp chí lớn. Việc tải lên file ZIP giúp bạn có toàn quyền kiểm soát giao diện cuối cùng và đảm bảo file ZIP kết quả có thể biên dịch ngay lập tức trên Overleaf mà không thiếu file phụ trợ.


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
5. **Tiền xử lý template** — Inject tag Jinja2 (`<< >>`) vào mẫu LaTeX đã chọn
6. **Render** — Kết hợp IR + template Jinja2 → file `.tex` hoàn chỉnh
7. **Biên dịch** — XeLaTeX hoặc pdfLaTeX (tự động phát hiện) → PDF
8. **Đóng gói** — Tạo `.zip` chứa `.tex`, `.pdf`, ảnh, và các file phụ thuộc

---

## Cấu Trúc Dự Án

```
Word2Latex/
├── start.bat                        # Trình khởi động 1-click (Windows)
├── backend/                         # Source code Backend
│   ├── app/                         # Lớp Web API (FastAPI)
│   │   ├── main.py                  # Entry point, cấu hình CORS, ghép Router
│   │   ├── config.py                # Cấu hình biến môi trường, đường dẫn
│   │   ├── database.py              # Khởi tạo SQLite engine
│   │   ├── models.py                # Các Model dữ liệu SQLAlchemy
│   │   ├── auth.py                  # Helper functions xử lý JWT auth
│   │   ├── routers/                 # Quản lý các endpoint riêng biệt
│   │   │   ├── auth_routes.py       # API Đăng nhập, Đăng ký, Lịch sử
│   │   │   ├── chuyen_doi.py        # API Xử lý Word → LaTeX (Stream/Upload)
│   │   │   └── templates.py         # API Quản lý mẫu LaTeX
│   │   └── utils/                   # Hàm phụ trợ riêng cho Web API
│   │
│   ├── core_engine/                 # Engine chuyển đổi cốt lõi (Python thuần)
│   │   ├── chuyen_doi.py            # Lớp điều phối ChuyenDoiWordSangLatex
│   │   ├── ast_parser.py            # WordASTParser: XML Word → IR (JSON)
│   │   ├── semantic_parser.py       # Bộ phân loại ngữ nghĩa heuristic (không ML)
│   │   ├── template_preprocessor.py # Inject tag Jinja2 vào mẫu LaTeX
│   │   ├── jinja_renderer.py        # JinjaLaTeXRenderer: IR + template → .tex
│   │   ├── xu_ly_toan.py            # OMML → LaTeX (XSLT / Pandoc / manual parser)
│   │   ├── xu_ly_ole_equation.py    # OLE Equation Editor 3.0 (MTEF binary) → LaTeX
│   │   ├── xu_ly_anh.py             # Lọc ảnh thông minh (entropy, cạnh, histogram)
│   │   ├── xu_ly_bang.py            # Xử lý bảng (multirow, multicolumn, TOC filter)
│   │   ├── utils.py                 # Biên dịch LaTeX, đóng gói ZIP
│   │   ├── tex_log_parser.py        # Phân tích log LaTeX → lỗi có cấu trúc
│   │   ├── config.py                # Hằng số, namespace XML, Regex engine
│   │   └── OMML2MML.XSL             # XSLT stylesheet (OMML → MathML)
│   │
│   ├── storage/                     # Thư mục dữ liệu
│   │   ├── custom_templates/        # Mẫu hệ thống + người dùng tải lên
│   │   └── temp_jobs/               # Nơi chứa các thư mục job đang chạy
│   │
│   └── requirements.txt             # Thư viện Python (backend)
│
└── frontend/                        # React 18 + Vite 5 SPA
    ├── package.json
    └── src/
        ├── App.jsx                  # Router: /dang-nhap, /chuyen-doi, /lich-su
        ├── components/              # UI components (TailwindCSS + Framer Motion)
        ├── context/                 # AuthContext (JWT state)
        └── services/                # api.js — SSE streaming client
```

(*) Mẫu Elsevier được lưu dưới dạng tên tùy chỉnh trong `backend/storage/custom_templates/`.

---

## Công Nghệ Sử Dụng

| Tầng | Công nghệ | Phiên bản |
|---|---|---|
| **Backend API** | FastAPI, Uvicorn | 0.115.0, 0.32.0 |
| **Engine chuyển đổi** | python-docx, lxml, Pillow, olefile | 1.1.0, ≥4.9, ≥10.4, 0.47 |
| **Xác thực** | python-jose (JWT HS256), passlib, bcrypt | —, —, 4.0.1 |
| **Cơ sở dữ liệu** | SQLite via SQLAlchemy | 2.0.36 |
| **Frontend** | React, Vite, TailwindCSS | 18.2, 5.0, 3.4 |
| **UI** | Framer Motion, Lucide React, React Dropzone | 10.16, 0.303, 14.2 |
| **Chuyển đổi toán** | XSLT (OMML → MathML → LaTeX), Pandoc (fallback) | — |
| **Biên dịch PDF** | XeLaTeX + pdfLaTeX (dual-engine) | TeX Live / MiKTeX |

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
