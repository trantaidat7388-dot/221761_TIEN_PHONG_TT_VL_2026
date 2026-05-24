# 📝 Nhật ký sửa đổi dự án (Project Modification History)

Tài liệu này lưu trữ chi tiết toàn bộ các cập nhật, sửa đổi và nâng cấp của dự án qua từng lần làm việc để đảm bảo tính theo dõi và đồng bộ.

---

## 📅 Phiên làm việc: 25/05/2026

### 🛠️ Sửa lỗi Công thức toán học (Math Formulas) & Khoảng trắng Springer LNCS

#### 1. Các tệp tin thay đổi:
*   **[backend/core_engine/jinja_renderer.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/jinja_renderer.py)**:
    *   **Ngăn chặn việc co giãn tỷ lệ công thức bất thường trên Springer LNCS**: Giới hạn việc tự động bọc công thức bằng `\resizebox{\columnwidth}{!}{...}` chỉ dành riêng cho cấu hình IEEE (`doc_class == "ieee"`), do IEEE sử dụng bố cục 2 cột hẹp nên cần co giãn. Với Springer và các mẫu đơn cột khác, công thức được hiển thị tự nhiên bằng môi trường toán học chuẩn `\begin{equation}`, giải quyết triệt để lỗi công thức phình to và khoảng trắng thừa xung quanh công thức.
*   **[backend/core_engine/xu_ly_toan.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_toan.py)**:
    *   **Sửa lỗi nhân đôi dấu gạch chéo ngược (Doubled Backslashes `\\`) trong công thức**: Bản đồ ký tự Unicode sang LaTeX `OMML_CHAR_MAP` được định nghĩa bằng các dấu gạch chéo ngược kép (ví dụ: `r'\\rightarrow'`). Tuy nhiên, do chúng ta sử dụng hàm lambda làm bộ thay thế (`re.sub(..., lambda _m: rep)`), Python đã bỏ qua việc giải mã dấu gạch chéo ngược kép, dẫn đến LaTeX xuất ra các dấu gạch chéo ngược kép lỗi (như `\\rightarrow`, `\\ldots`, `\\coloneqq`, `\\mapsto`). Đã bổ sung logic chuẩn hóa `rep = replacement.replace('\\\\', '\\')` trước khi gọi `re.sub` để tất cả các ký tự toán học Unicode được chuyển đổi chính xác thành các lệnh LaTeX gạch chéo đơn chuẩn (`\rightarrow`, `\ldots`, `\coloneqq`, `\mapsto`).

#### 2. Kết quả nghiệm thu & Kiểm thử:
*   **Biên dịch PDF Springer LNCS tuyệt đẹp**: Chuyển đổi và biên dịch thành công tài liệu Blockchain-Based Management sang mẫu Springer LNCS (`Exit code: 0`).
*   **Công thức & Ký tự toán học chính xác 100%**: Các công thức (từ Equation 1 đến 11) hiển thị ở kích thước chữ tự nhiên, khoảng cách dòng thụt lề chuẩn xác, và các ký tự mũi tên (`\rightarrow`), phép gán (`\coloneqq`), ánh xạ (`\mapsto`), dấu ba chấm (`\ldots`) hiển thị hoàn toàn chính xác về mặt toán học.

---

### 🛠️ Sửa lỗi Biên dịch Thuật toán & Khớp liên kết chéo Bộ lõi (Core Engine)

#### 1. Các tệp tin thay đổi:
*   **[backend/core_engine/ast_parser.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/ast_parser.py)**:
    *   **Nâng cấp bộ phân tách bảng thuật toán ô đơn (Single-cell Algorithm Table)**: Thay vì bỏ qua toàn bộ ô khi khớp trùng tiêu đề, hệ thống tự động tách dòng (`\n`), trích xuất dòng đầu tiên chứa từ khóa làm tiêu đề thuật toán (`caption`) và phân tích toàn bộ các dòng tiếp theo thành các bước thực thi độc lập (`steps`). Điều này giải quyết triệt để lỗi biên dịch rỗng `algorithmic` (`missing \item` trên Overleaf).
*   **[backend/core_engine/jinja_renderer.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/jinja_renderer.py)**:
    *   **Sửa lỗi xung đột chế độ toán học (Math Mode Crash)**: Loại bỏ các ký tự `$` bọc thủ công cho mũi tên gán `←` trong môi trường thuật toán, thay thế bằng cú pháp lệnh toán học toàn văn an toàn `\ensuremath{\leftarrow}`. Điều này giúp XeLaTeX biên dịch thành công 100% không còn lỗi ngắt quãng luồng sinh PDF, khôi phục đầy đủ 100% trang văn bản phía sau (tệp PDF tăng kích thước từ 149 KB lên 171 KB).
    *   **Ánh xạ nhãn kép chương/mục chính (Dual Section Labeling)**: Tự động đếm thứ tự và chèn đồng thời nhãn chữ (ví dụ: `\label{sec:related_work}`) và nhãn số thứ tự (ví dụ: `\label{sec_2}`) cho toàn bộ các mục chính cấp 1.
    *   **Hỗ trợ nhãn mục Tài liệu tham khảo (References)**: Tự động đếm tổng số mục cấp 1 và chèn nhãn liên kết tương ứng (ví dụ: `\label{sec_6}`) ngay trước khối `thebibliography`, giải quyết triệt để cảnh báo lỗi liên kết chéo tĩnh `Reference 'sec_2' undefined` trên Overleaf.

#### 2. Kết quả nghiệm thu & Kiểm thử:
*   **Biên dịch PDF thành công tuyệt đối**: Tài liệu ngân phiếu biên dịch thông suốt bằng XeLaTeX cục bộ đạt mã **`Exit code: 0`** hoàn mỹ, xuất ra tệp PDF hoàn chỉnh 4 trang chứa đầy đủ tiêu đề, các tác giả, tóm tắt, khối thuật toán định dạng thụt lề chuẩn, bảng biểu Experiments cân đối và 22 mục References.
*   **Quy trình chuyển đổi Word-to-Word**: Thực hiện chuyển đổi thành công tệp ngân phiếu từ IEEE sang Springer LNCS, sinh tệp Word Springer mới tuyệt đẹp.
*   **Kiểm thử hàng loạt (Batch Test 22 files)**: Thực hiện chạy thử nghiệm hàng loạt trên toàn bộ 22 tài liệu mẫu trong thư mục, đạt tỷ lệ chuyển đổi thành công **100.0%** (22/22 tệp tin .tex) và tỷ lệ biên dịch PDF thành công **100.0%** (22/22 tệp tin .pdf) cho cả hai mẫu IEEE Conference và Springer LNCS.
*   **Git Push**: Đã commit và push tất cả thay đổi cốt lõi lên nhánh `docs-20260524` của kho lưu trữ từ xa GitHub.

---

## 📅 Phiên làm việc: 24/05/2026

### 🚀 Đồng bộ hóa và Hoàn thiện App di động (Android & iOS WebView)

#### 1. Các tệp tin thay đổi:
*   **[app_web_view/lib/main.dart](file:///d:/221761_TIEN_PHONG_TT_VL_2026/app_web_view/lib/main.dart)**:
    *   **Thêm luồng giải mã Blob Base64 (`BLOB_DOWNLOAD`)**: Tiếp nhận dữ liệu Base64 từ WebView, giải mã nhị phân bằng `base64Decode`, lưu vào tệp tạm bằng `path_provider` và gọi Native Share Sheet qua `share_plus` để người dùng lưu/chia sẻ tệp tin trực tiếp.
    *   **Cải tiến luồng `OPEN_URL` & `APP_DOWNLOAD`**: Loại bỏ giới hạn `Platform.isIOS` để cả **Android và iOS** cùng được hưởng lợi từ việc tải file in-app (không bị đẩy ra Chrome ngoài, tránh được lỗi xác thực 401/404).
    *   **Nạp cầu nối JavaScript cho cả hai hệ điều hành**: Gọi hàm `_injectAppBridgeScript()` không điều kiện trong sự kiện `onPageFinished`.
    *   **Dọn dẹp import**: Loại bỏ import thừa `dart:typed_data` để đảm bảo code sạch 100% không còn cảnh báo.

#### 2. Kịch bản chặn và chuyển đổi Blob URL (JavaScript Bridge):
*   Khi người dùng click vào các liên kết tải xuống dạng `blob:`, JavaScript sẽ tự động:
    1.  Chặn hành vi mặc định của Webview.
    2.  Gọi `fetch` để lấy nhị phân Blob trực tiếp từ bộ nhớ Webview.
    3.  Chuyển đổi thành chuỗi **Base64** qua `FileReader`.
    4.  Gửi qua thông điệp `BLOB_DOWNLOAD` về Flutter để xử lý Share Sheet.

#### 3. Kết quả nghiệm thu & Kiểm thử:
*   **Flutter Static Analysis**: Chạy `flutter analyze lib/main.dart` đạt kết quả:
    > `No issues found! (ran in 2.3s)`
*   **Frontend React Production Build**: Chạy `npm run build` hoàn thành xuất sắc trong **26.03 giây** không có lỗi.
*   **Git Push**: Đã commit và push toàn bộ thay đổi sạch sẽ lên nhánh `fix-springer-formatting` của Git repository.

### 📚 Tài liệu hóa & Phân tích Kiến trúc Bộ lõi (Core Engine)

#### 1. Các tài liệu tạo mới & cập nhật:
*   **[implementation_plan.md](file:///C:/Users/ASUS/.gemini/antigravity-ide/brain/5e1a85b5-5306-403c-bfcd-301b4c498e3b/implementation_plan.md)**: Xây dựng sơ đồ kiến trúc hệ thống, sơ đồ luồng chạy dữ liệu bằng **Mermaid** trực quan và phân tích chi tiết chức năng của 13+ tệp tin trong bộ lõi `core_engine`.
*   **[walkthrough.md](file:///C:/Users/ASUS/.gemini/antigravity-ide/brain/5e1a85b5-5306-403c-bfcd-301b4c498e3b/walkthrough.md)**: Tóm tắt 4 bước của chu trình chuyển đổi thô từ Word -> cây trung gian AST -> template tiền xử lý -> file nguồn LaTeX & PDF.
*   **[tai_lieu_hoc_core_engine.md](file:///d:/221761_TIEN_PHONG_TT_VL_2026/tai_lieu_hoc_core_engine.md)**: Tạo cẩm nang tự học chuyên sâu giải thích chi tiết cơ chế hoạt động, thuật toán OLE, OMML, ánh xạ bảng biểu và máy trạng thái cho lập trình viên tìm hiểu bộ lõi chuyển đổi.

#### 2. Kết quả rà soát chú thích tiếng Việt:
*   Đã tiến hành kiểm tra toàn bộ thư mục `backend/core_engine/`. 100% các tệp tin cốt lõi (như `chuyen_doi.py`, `ast_parser.py`, `jinja_renderer.py`, `word_loader.py`, `xu_ly_bang.py`, v.v.) **đều đã được tích hợp sẵn các chú thích tiếng Việt cực kỳ chi tiết**, giúp người đọc và nhà phát triển dễ dàng nắm bắt thuật toán chuyển đổi nhanh chóng.

