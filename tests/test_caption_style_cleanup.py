from backend.core_engine.ast_parser import WordASTParser


def test_caption_normalization_for_table_and_figure_prefixes():
    p = WordASTParser("dummy.docx")

    assert p._chuan_hoa_ten_caption("Table 1: Performance comparison", "table") == "Performance comparison"
    assert p._chuan_hoa_ten_caption("BANG 3.1 - Ket qua huan luyen", "table") == "Ket qua huan luyen"

    assert p._chuan_hoa_ten_caption("Figure 2: Architecture", "figure") == "Architecture"
    assert p._chuan_hoa_ten_caption("Fig. 4.2 - Accuracy chart", "figure") == "Accuracy chart"
    assert p._chuan_hoa_ten_caption("HINH 5: Bieu do tong quan", "figure") == "Bieu do tong quan"
