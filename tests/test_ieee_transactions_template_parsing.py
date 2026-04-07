from backend.core_engine.ast_parser import WordASTParser


def test_ieee_membership_suffix_is_not_split_into_fake_author():
    parser = WordASTParser("dummy.docx")
    parsed = parser._parse_authors([
        "First A. Author, Fellow, IEEE",
        "Dept. name of organization",
        "City, Country",
    ])

    assert len(parsed) == 1
    assert parsed[0]["name"].lower().startswith("first a. author")


def test_transactions_template_does_not_force_generic_figure_caption_text():
    parser = WordASTParser(
        "input_data/Template_word/Transactions-template-and-instructions-on-how-to-create-your-article.doc.docx"
    )
    ir = parser.parse()

    fig_nodes = [
        n for n in ir.get("body", [])
        if n.get("type") == "paragraph" and "\\begin{figure" in (n.get("text") or "")
    ]
    assert fig_nodes
    assert "\\caption{" in fig_nodes[0]["text"]
    assert "\\caption{Figure}" not in fig_nodes[0]["text"]


def test_transactions_template_preserves_actual_figure_caption_text():
    parser = WordASTParser(
        "input_data/Template_word/Transactions-template-and-instructions-on-how-to-create-your-article.doc.docx"
    )
    ir = parser.parse()

    fig_nodes = [
        n for n in ir.get("body", [])
        if n.get("type") == "paragraph" and "\\begin{figure" in (n.get("text") or "")
    ]
    assert fig_nodes
    assert "Magnetization as a function of applied field" in fig_nodes[0]["text"]


def test_transactions_template_does_not_duplicate_figures_or_references():
    parser = WordASTParser(
        "input_data/Template_word/Transactions-template-and-instructions-on-how-to-create-your-article.doc.docx"
    )
    ir = parser.parse()

    fig_nodes = [
        n for n in ir.get("body", [])
        if n.get("type") == "paragraph" and "\\begin{figure" in (n.get("text") or "")
    ]
    assert len(fig_nodes) == 1
    # The template contains a large built-in sample reference section,
    # but should not explode to hundreds of fake entries.
    assert 0 < len(ir.get("references", [])) < 80
