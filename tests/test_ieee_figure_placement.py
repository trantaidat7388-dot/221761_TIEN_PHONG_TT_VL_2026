from backend.core_engine.jinja_renderer import JinjaLaTeXRenderer


def test_ieee_figure_placement_flexible_float_hint():
    src = (
        "\\begin{figure}[H]\\centering\\includegraphics{a}\\caption{Top 3 EKI Algorithms}\\end{figure}\n"
        "\\begin{figure}[!ht]\\centering\\includegraphics{b}\\caption{Use-case diagram of the system}\\end{figure}\n"
        "\\begin{table}[H]x\\end{table}\n"
    )
    out = JinjaLaTeXRenderer(".")._normalize_ieee_figure_placement(src)

    assert out.count("\\begin{figure}[htbp]") == 2
    assert "\\captionof{figure}{" not in out
    assert "\\begin{table}[H]" in out


def test_springer_float_placement_avoids_hard_H():
    src = (
        "\\begin{figure}[H]\\centering\\includegraphics{a}\\caption{x}\\end{figure}\n"
        "\\begin{table}[H]x\\end{table}\n"
        "\\section{Next}\n"
    )
    out = JinjaLaTeXRenderer(".")._normalize_springer_float_placement(src)

    assert "\\begin{figure}[!ht]" in out
    assert "\\begin{table}[H]" in out
    assert "\\FloatBarrier\n\\section{Next}" in out


def test_remove_float_barriers_from_body_text():
    src = "\\FloatBarrier\nA\n\\FloatBarrier\n\\begin{figure}[htbp]x\\end{figure}\n"
    out = JinjaLaTeXRenderer(".")._remove_float_barriers(src)

    assert "\\FloatBarrier" not in out
    assert "\\begin{figure}[htbp]" in out


def test_ieee_figure_near_next_section_is_converted_to_inline():
    src = (
        "\\begin{figure}[H]\\centering\\includegraphics{a}\\caption{x}\\label{fig:a}\\end{figure}\n\n"
        "Short conclusion sentence before next section.\n\n"
        "\\section{Conclusion}\n"
    )

    out = JinjaLaTeXRenderer(".")._normalize_ieee_figure_placement(src)

    assert "\\begin{figure}" not in out
    assert "\\refstepcounter{figure}" in out
    assert "\\small Fig. \\thefigure. x" in out
    assert "\\label{fig:a}" in out


def test_ieee_captionless_figure_is_kept_inline_without_float():
    src = (
        "\\begin{figure}[htbp]\\centering\\includegraphics[width=0.62\\columnwidth]{images/f1.png}\\caption{}\\label{fig:f1}\\end{figure}\\n"
    )

    out = JinjaLaTeXRenderer(".")._normalize_ieee_figure_placement(src)

    assert "\\begin{figure}" not in out
    assert "\\includegraphics[width=0.62\\columnwidth]{images/f1.png}" in out
    assert "\\refstepcounter{figure}" not in out
