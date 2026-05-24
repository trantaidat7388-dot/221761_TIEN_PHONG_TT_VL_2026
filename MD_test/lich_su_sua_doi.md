# 📝 Nhật ký sửa đổi dự án (Project Modification History)

Tài liệu này lưu trữ chi tiết toàn bộ các cập nhật, sửa đổi và nâng cấp của dự án qua từng lần làm việc để đảm bảo tính theo dõi và đồng bộ.

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

