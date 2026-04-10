# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

@[c:\221761_TIEN_PHONG_TT_VL_2026\Refining IEEE Word Conversion.md] . sửa tiếp , công thức còn sai 

*Listed directory [221761_TIEN_PHONG_TT_VL_2026](file:///c:/221761_TIEN_PHONG_TT_VL_2026) *

*Viewed [Refining IEEE Word Conversion.md](file:///c:/221761_TIEN_PHONG_TT_VL_2026/Refining%20IEEE%20Word%20Conversion.md) *

*Grep searched codebase*

*Listed directory [core_engine](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine) *

*Viewed [xu_ly_toan.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_toan.py) *

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Viewed [ast_parser.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/ast_parser.py) *

*Viewed [ast_parser.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/ast_parser.py) *

*User accepted the command `.venv\Scripts\pip show latex2mathml`*

*Checked command status*

*Viewed [xu_ly_ole_equation.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/xu_ly_ole_equation.py) *

*User accepted the command `ls backend/core_engine/*.XSL`*

*User accepted the command `pandoc --version`*

*Checked command status*

### User Input

Continue

---

## Kế hoạch bài toán 3: Chuyển đổi ngược Word IEEE -> Word Springer

### Mục tiêu
- Chuyển tài liệu Word bố cục IEEE (2 cột, heading số La Mã, caption IEEE) về bố cục Springer (1 cột, style heading Springer, caption Springer, author block Springer).
- Giữ tối đa nội dung học thuật: tiêu đề, tác giả, abstract, từ khóa, heading, bảng, hình, công thức, tài liệu tham khảo.
- Hạn chế mất định dạng công thức bằng cách ưu tiên bảo toàn Office Math (OMML).

### Phạm vi chuyển đổi
- Metadata: title, authors, affiliations, email, abstract, keywords.
- Body: section/subsection/subsubsection, paragraph, list, figure, table, equation.
- References: chuyển về style tham khảo của Springer (không để numbering IEEE kiểu [1] cứng trong text nếu style đã tự quản lý).

### Kiến trúc đề xuất
- Bước 1: Parse IEEE Word -> IR trung gian
- Bước 2: Chuẩn hóa IR theo schema Springer (chuẩn hóa heading/caption/equation node)
- Bước 3: Render IR -> Springer Word theo template Springer upload

### Work packages
1. Parser IEEE-specific
- Nhận diện heading IEEE (I., A., B., ...) và map về cấp section logic.
- Nhận diện caption IEEE: "Fig. n.", "TABLE I" + dòng tiêu đề.
- Nhận diện equation layout table (3 cột) và khôi phục equation node + tag.
- Nhận diện references IEEE ([n]) và tách text reference sạch.

2. IR Normalizer for Springer
- Mapping heading:
	- IEEE level 1 -> \section
	- IEEE level 2 -> \subsection
	- IEEE level 3 -> \subsubsection hoặc paragraph-style theo template
- Mapping caption:
	- Figure: "Fig. n." -> "Figure n."
	- Table: "TABLE I" + title -> "Table n."
- Mapping author block:
	- Gom nhóm tên + affiliation + email theo format Springer.

3. Springer renderer
- Dùng template Springer gốc, clear content body nhưng giữ section/page setup.
- Áp style Springer thay vì hardcode Times New Roman khi style template có sẵn.
- Equation ưu tiên OMML marker; fallback LaTeX readable nếu thiếu OMML.

4. Validation và regression test
- Snapshot test cho 3 nhóm input:
	- IEEE có công thức nhiều (OMML + equation table)
	- IEEE có bảng rộng + hình + caption phức hợp
	- IEEE có author block nhiều tác giả
- So khớp các tiêu chí:
	- Đủ section/caption/reference
	- Công thức không bị flatten text thô
	- Tác giả không dính placeholder/template text

### Tiêu chí hoàn thành (Definition of Done)
- File output Springer mở được trên Word, không vỡ layout chính.
- >= 95% heading/caption/equation/reference được map đúng theo expected fixtures.
- Không mất công thức OMML ở các case có OMML đầu vào.
- Bộ test tự động pass cho pipeline IEEE -> Springer.

### Rủi ro kỹ thuật
- OMML từ tài liệu IEEE có thể bị bọc khác dạng (oMath/oMathPara/table-cell container).
- Khác biệt style name giữa các template Springer (lncs, svjour, sn-article) cần map mềm bằng style lookup.
- References có thể lẫn plain text + hyperlink, cần làm sạch trước khi render.

*Grep searched codebase*

*Edited relevant file*

*User accepted the command `.venv\Scripts\python brain\8e632577-93b4-4fd2-86c4-3443755a8f20\scratch\test_omml.py`*

*Checked command status*

*User accepted the command `ls -Recurse -Filter *.XSL`*

*User accepted the command `.venv\Scripts\pip show lxml`*

*Checked command status*

*Edited relevant file*

### Planner Response

I have analyzed the math formula conversion logic and identified the root cause: the current pipeline flattens native Word math into low-quality plain text.

I have created an **[implementation_plan.md](file:///C:/Users/ASUS/.gemini/antigravity/brain/8e632577-93b4-4fd2-86c4-3443755a8f20/implementation_plan.md)** to upgrade the system to preserve and render native Office Math (OMML) for high-fidelity output.

Please review the plan and let me know if you would like me to proceed with the implementation.

### User Input

tóm tắt và từ khóa xếp 1 cột là đúng hay sai

*Searched web for IEEE conference template abstract keywords 1 column or 2 columns*

### Planner Response

Theo quy chuẩn bài báo Hội nghị (Conference) của IEEE, việc xếp Tóm tắt (Abstract) và Từ khóa (Keywords) tràn ngang 1 cột là **SAI**.

**Đúng chuẩn IEEE:**
*   **Tiêu đề và Tác giả:** Xếp 1 cột (tràn ngang trang).
*   **Tóm tắt và Từ khóa:** Phải nằm ở đầu của **cột bên trái** trong bố cục 2 cột (ngay phía dưới khối tác giả và phía trên phần Introduction).

**Nguyên nhân trong code hiện tại:**
Bộ renderer đang gọi hàm thêm Tóm tắt/Từ khóa *trước khi* chia 2 cột, nên nó bị đẩy ra ngoài và chiếm toàn bộ chiều ngang trang.

Tôi sẽ cập nhật **[implementation_plan.md](file:///C:/Users/ASUS/.gemini/antigravity/brain/8e632577-93b4-4fd2-86c4-3443755a8f20/implementation_plan.md)** để sửa đồng thời cả lỗi Công thức và lỗi bố cục Tóm tắt/Từ khóa này.

Tôi đã cập nhật kế hoạch, bạn có đồng ý để tôi tiến hành sửa cả hai phần này không?

### User Input

bạn hãy sửa code lại 

*Edited relevant file*

*Edited relevant file*

*Viewed [ast_parser.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/ast_parser.py) *

*Edited relevant file*

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Edited relevant file*

### User Input

Continue

*Edited relevant file*

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Edited relevant file*

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Grep searched codebase*

*Grep searched codebase*

*Grep searched codebase*

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Grep searched codebase*

### User Input

Continue

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Viewed [word_ieee_renderer.py](file:///c:/221761_TIEN_PHONG_TT_VL_2026/backend/core_engine/word_ieee_renderer.py) *

*Edited relevant file*

*User accepted the command `.venv\Scripts\python backend\test_end_to_end_ieee.py`*

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue

### User Input

Continue