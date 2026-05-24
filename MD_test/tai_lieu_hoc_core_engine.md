# 📚 Tài Liệu Tự Học: Kiến Trúc & Luồng Xử Lý Core Engine (Word ➔ LaTeX)

Tài liệu này được biên soạn chi tiết giúp bạn tự học, tìm hiểu sâu sắc về kiến trúc, thuật toán và luồng xử lý của bộ lõi chuyển đổi tài liệu khoa học từ **Word (.docx/.doc/.docm) sang LaTeX & PDF** nằm tại thư mục [backend/core_engine](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine).

---

## 🎯 1. Bức Tranh Tổng Quan: Mô Hình Kiến Trúc Đường Ống (Pipeline)

Bộ lõi hoạt động như một **đường ống chuyển đổi (Pipeline)** 5 bước tuần tự. Điểm đặc sắc ở đây là việc sử dụng cấu trúc cây **IR (Intermediate Representation - Biểu diễn trung gian)**. 

### Tại sao cần IR (Cây AST)?
Nếu dịch trực tiếp từ Word XML sang LaTeX, code sẽ cực kỳ phức tạp và dễ lỗi vì định dạng của Word (Open XML) và LaTeX hoàn toàn khác nhau.
*   **Word XML**: Lưu trữ tài liệu dưới dạng các nút XML phẳng, rời rạc chứa định dạng hiển thị trực quan (visual formatting).
*   **LaTeX**: Yêu cầu cấu trúc logic phân cấp ngữ nghĩa rõ ràng (semantic hierarchy) như `\section`, `\subsection`, `\begin{abstract}`.
*   **Giải pháp (Cây AST/IR)**: Phân tích Word XML thành một cấu trúc cây JSON trung lập lưu đầy đủ ý nghĩa (metadata, heading, paragraph, math, table, image). Sau đó, từ cây này ta có thể render ra bất kỳ định dạng nào (LaTeX, HTML, Markdown) một cách dễ dàng.

---

## 🛠️ 2. Chi Tiết Thuật Toán & Cơ Chế Của Từng Module

Hãy cùng đi sâu vào từng giai đoạn để hiểu rõ logic lập trình đằng sau:

### Giai đoạn 1: Làm sạch & Khắc phục định dạng lỗi ([word_loader.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_loader.py))

Khi người dùng upload một file Word, hệ thống không trực tiếp mở bằng thư viện python-docx ngay mà phải xử lý qua bộ lọc:

1.  **Dọn dẹp Macro độc hại (`.docm`)**:
    *   *Vấn đề*: Tệp `.docm` chứa mã VBA macro thường bị hệ điều hành chặn hoặc làm hỏng cấu trúc ZIP của Open XML.
    *   *Thuật toán*: Hệ thống coi file Word như một file ZIP. Giải nén file ra bộ nhớ tạm, tìm và xóa bỏ file nhị phân chứa macro (`vbaProject.bin`), dọn dẹp các thẻ khai báo macro trong file cấu trúc chính (`[Content_Types].xml` và `_rels/.rels`), sau đó nén lại thành file `.docx` sạch hoàn toàn.
2.  **Khắc phục lỗi Strict Open XML**:
    *   *Vấn đề*: Một số phần mềm xuất file Word theo chuẩn "Strict" XML khiến các thư viện đọc XML tiêu chuẩn bị lỗi namespace.
    *   *Thuật toán*: Tự động chuyển đổi namespace của Strict XML sang Transitional XML bằng regex để các thư viện phân tích cú pháp hoạt động mượt mà.
3.  **Chuyển đổi tệp `.doc` cũ**:
    *   Nếu phát hiện tệp tin định dạng `.doc` nhị phân cũ (Word 97-2003), hệ thống gọi lệnh ngầm **LibreOffice (Headless mode)** để convert sang `.docx` chuẩn XML trước khi xử lý.

---

### Giai đoạn 2: Trích xuất Cây Ngữ nghĩa AST ([ast_parser.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/ast_parser.py))

Đây là "bộ não" của quá trình phân tích cú pháp. Nó sử dụng một **State Machine (Máy trạng thái)** để đi qua các đoạn văn bản (paragraphs) và phân loại ngữ nghĩa của chúng:

1.  **Máy trạng thái Phân loại Vùng (Metadata Extraction)**:
    *   Hệ thống duy trì trạng thái hiện tại (`state = "TITLE"`).
    *   Đoạn văn đầu tiên thường được dự đoán là **TITLE**.
    *   Các đoạn tiếp theo chứa tên người, không chứa từ khóa trường học sẽ được phân loại là **AUTHOR**.
    *   Đoạn tiếp theo chứa địa chỉ, viện, trường sẽ là **AFFILIATION**.
    *   Khi gặp từ khóa "Abstract" hoặc "Tóm tắt", trạng thái chuyển sang **ABSTRACT**.
    *   Khi gặp "Keywords" hoặc "Từ khóa", trạng thái chuyển sang **KEYWORDS**.
    *   Khi vượt qua các phần trên, trạng thái chuyển sang **BODY** (Nội dung chính).
2.  **Bộ dự đoán ngữ nghĩa heuristics ([semantic_parser.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/semantic_parser.py))**:
    *   Sử dụng tần suất từ khóa đặc trưng (TF-IDF rút gọn) và định dạng (chữ in đậm `is_bold`, vị trí dòng) để xác định tiêu đề đề mục (Heading).
    *   Ví dụ: Nếu đoạn văn in đậm, ngắn (<15 từ) và khớp định dạng chữ số La Mã hoặc số tự nhiên (`I. Introduction`, `1. Cở sở lý thuyết`), nó sẽ được phân loại ngay thành **HEADING**.

---

### Giai đoạn 3: Bộ Ba Module Phụ Trợ (Toán, Bảng biểu, Hình ảnh)

#### 🧮 3.1. Xử lý Công thức Toán học ([xu_ly_toan.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_toan.py) & [xu_ly_ole_equation.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_ole_equation.py))
Trong tài liệu khoa học, công thức toán là phần phức tạp nhất. Word lưu trữ toán học dưới hai dạng chính:

*   **Dạng 1: OMML (Office Math Markup Language - XML toán học của Word)**:
    *   *Cơ chế dịch*: XML OMML rất dài dòng. Bộ lõi sử dụng một file biến đổi XSLT chuẩn của Microsoft (`OMML2MML.XSL`) để chuyển đổi OMML sang MathML (XML toán học web). Từ MathML, hệ thống dùng thuật toán ánh xạ regex hoặc thư viện phụ trợ để dịch thành chuỗi ký tự LaTeX chuẩn (ví dụ: `\frac{a}{b}`).
*   **Dạng 2: OLE Equation (Công thức nhúng cũ từ MathType)**:
    *   *Cơ chế dịch*: MathType lưu công thức dưới dạng các khối byte nhị phân nhúng (OLE binary object).
    *   *Thuật toán parse*: Bộ lõi mở luồng đọc nhị phân (binary stream), định vị header của MathType (tìm signature `MathType`), trích xuất chuỗi ký tự MathType Equation Byte Stream (MTEF). Sau đó, nó giải mã từng byte MTEF (chứa thông tin về biến, phân số, tích phân) để biên dịch ngược lại thành mã LaTeX chuẩn xác mà không cần ảnh chụp màn hình công thức.

#### 📊 3.2. Xử lý Bảng biểu phức tạp ([xu_ly_bang.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_bang.py))
Bảng biểu trong Word có thể bị gộp dòng (rowspan) hoặc gộp cột (colspan). Khi dịch sang LaTeX, ta phải sử dụng lệnh `\multicolumn` và `\multirow`.

*   **Thuật toán ánh xạ ma trận ô**:
    1.  Hệ thống tạo ra một ma trận 2 chiều trống tương ứng với số hàng và số cột logic lớn nhất của bảng.
    2.  Duyệt qua từng ô XML thực tế trong Word.
    3.  Đọc thuộc tính `gridSpan` (số cột gộp) và `vMerge` (trạng thái gộp dòng: `restart` để bắt đầu gộp, hoặc `continue` để tiếp tục gộp dòng trên).
    4.  Điền tọa độ và đánh dấu các ô ảo trong ma trận để tránh ghi đè dữ liệu.
    5.  Khi kết xuất mã LaTeX, nếu phát hiện ô có gộp dòng/cột, hệ thống tự động chèn mã lệnh định dạng thích hợp như `\multicolumn{số_cột}{c}{nội_dung}` và `\multirow{số_hàng}{*}{nội_dung}` để bảng hiển thị cân đối.

#### 🖼️ 3.3. Xử lý Hình ảnh & Biểu đồ ([xu_ly_anh.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_anh.py))
*   **Lọc ảnh rác**: Word thường chứa các file ảnh trang trí siêu nhỏ hoặc các khối shape trống. Bộ lõi có bộ lọc kích thước (chỉ giữ ảnh có chiều rộng/cao lớn hơn ngưỡng tối thiểu) để tránh trích xuất các hình trang trí vụn vặt.
*   **Export Biểu đồ Vector (Chart)**:
    *   Các biểu đồ cột, tròn vẽ trực tiếp trong Word (Office DrawingML Chart) thực chất không phải là file ảnh mà là cấu trúc dữ liệu dựng hình động.
    *   *Thuật toán*: Trên hệ điều hành Windows, bộ lõi sử dụng **pywin32 (MS Word COM API)** khởi chạy ngầm tiến trình Word để kết xuất (export) chính xác các biểu đồ vector này thành tệp ảnh bitmap PNG sắc nét trước khi dịch.

---

### Giai đoạn 4: Tiền xử lý LaTeX Template ([template_preprocessor.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/template_preprocessor.py))

Mỗi nhà xuất bản (IEEE, Springer, Elsevier) có một tệp mẫu `.tex` hoàn toàn khác nhau. Bộ lõi giải quyết bài toán này bằng cơ chế **Auto-Tagging (Tự động gắn nhãn)**:

1.  Hệ thống nạp file `.tex` gốc của nhà xuất bản.
2.  Sử dụng thư viện cú pháp `TexSoup` để phân tích cấu trúc cây phân cấp lệnh của LaTeX.
3.  Tìm kiếm các khối lệnh đặc trưng như:
    *   `\title{...}` ➔ Sẽ được chuyển thành `\title{<< metadata.title >>}`
    *   `\begin{abstract} ... \end{abstract}` ➔ Chuyển thành `\begin{abstract}<< metadata.abstract >>\end{abstract}`
4.  Toàn bộ phần nội dung chính (body) sẽ được tự động chèn thẻ `<< body >>` tại vị trí thích hợp nhất.
5.  Điều này giúp chương trình thích ứng với bất kỳ template LaTeX mới nào mà người dùng tải lên mà không cần lập trình viên phải sửa đổi code lõi.

---

### Giai đoạn 5: Render và Xử lý Hậu kỳ LaTeX ([jinja_renderer.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/jinja_renderer.py))

Sau khi đã có cây dữ liệu IR (JSON) và tệp Template đã được gắn nhãn Jinja2, hệ thống thực hiện render mã nguồn LaTeX:

1.  **Làm sạch ký tự LaTeX (Escaping)**:
    *   Các ký tự như `_`, `%`, `&`, `#` trong Word khi sang LaTeX nếu không được xử lý sẽ làm hỏng trình biên dịch.
    *   *Thuật toán*: Hàm `loc_ky_tu` tự động tìm kiếm các ký tự đặc biệt nằm ngoài công thức toán học và thêm dấu gạch chéo ngược (`\_`, `\%`, `\&`) hoặc thay thế bằng ký tự an toàn.
2.  **Định dạng danh sách lồng cấp (`enumitem`)**:
    *   Word cho phép thụt lề thụ động bất kỳ lúc nào để tạo danh sách lồng nhau.
    *   *Thuật toán*: Bộ lõi duy trì một **Stack** theo dõi cấp độ thụt lề (`indentation level`). Khi cấp độ tăng lên, nó đẩy một lệnh mở danh sách `\begin{itemize}` hoặc `\begin{enumerate}` vào stack. Khi cấp độ giảm, nó đóng danh sách bằng `\end{itemize}` tương ứng. Điều này đảm bảo cấu trúc thẻ LaTeX lồng nhau chuẩn cú pháp.
3.  **Tự động tách & Sinh BibTeX cho tài liệu tham khảo**:
    *   Quét phần danh sách tài liệu tham khảo thô ở cuối file.
    *   Sử dụng regex phân tích cấu trúc để nhận diện: Tác giả, Tên bài báo, Tên tạp chí, Năm xuất bản.
    *   Tự động sinh ra tệp tham chiếu `.bib` chuẩn (ví dụ: `@article{ref1, author=...}`) và chèn lệnh `\cite{ref1}` vào các đoạn văn bản trong bài viết.

---

## 🧭 3. Hướng Dẫn Từng Bước Cách Đọc Mã Nguồn Để Học

Để nắm bắt nhanh nhất thuật toán của dự án, bạn nên mở và đọc các file theo đúng thứ tự luồng dữ liệu chạy dưới đây:

### 📍 Bước 1: Bắt đầu tại [chuyen_doi.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/chuyen_doi.py)
*   **Nhiệm vụ**: Xem hàm `thuc_hien_chuyen_doi()`.
*   **Mục tiêu học**: Xem cách controller khởi tạo các đối tượng và gọi tuần tự:
    ```python
    # Trích xuất cấu trúc Word thành cây IR trung gian
    parser = WordASTParser(self.duong_dan_word, ...)
    ir = parser.parse()
    
    # Chuẩn bị file template LaTeX của nhà xuất bản
    preprocessor = TemplatePreprocessor(self.duong_dan_template)
    template_content = preprocessor.preprocess()
    
    # Render dữ liệu từ IR vào template để ra file .tex hoàn chỉnh
    renderer = JinjaLaTeXRenderer(template_content)
    latex_code = renderer.render(ir)
    ```

### 📍 Bước 2: Đọc [ast_parser.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/ast_parser.py)
*   **Nhiệm vụ**: Tập trung vào hàm `_build_semantic_tree(self, elements)`.
*   **Mục tiêu học**: Hiểu cách máy trạng thái chuyển đổi giữa các vùng thông tin tiêu đề, tác giả, tóm tắt và nội dung chính của tài liệu Word.

### 📍 Bước 3: Xem các module giải thuật con
*   Xem [xu_ly_bang.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_bang.py) để học thuật toán lập ma trận và tính toán số hàng/cột gộp logic.
*   Xem [xu_ly_ole_equation.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_ole_equation.py) để học cách đọc dữ liệu byte nhị phân của các công thức cũ MathType.
*   Xem [xu_ly_toan.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_toan.py) để học cách gọi XSLT dịch công thức OMML XML sang MathML/LaTeX.

### 📍 Bước 4: Đọc [jinja_renderer.py](file:///d:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/jinja_renderer.py)
*   **Nhiệm vụ**: Xem cách hệ thống lặp qua danh sách các node trong cây IR để render ra văn bản LaTeX, định dạng ký tự toán và định vị danh mục tài liệu tham khảo.

---

> [!TIP]
> **Lời khuyên khi tự học**: Hãy vừa đọc tài liệu này vừa đối chiếu trực tiếp với mã nguồn thực tế. Các chú thích tiếng Việt trong từng hàm của dự án sẽ giải thích chi tiết ý nghĩa của từng biến số và các trường hợp xử lý biên cụ thể để bạn nắm vững kiến thức nhất!
