"""Test that pdftex is stripped from \\documentclass options."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.core_engine.template_preprocessor import TemplatePreprocessor

def test_remove_pdftex_from_mdpi():
    """Test removing pdftex from a complex bracket like MDPI."""
    tex = (
        "\\documentclass[preprints,article,submit,pdftex,moreauthors]{Definitions/mdpi}\n"
        "\\begin{document}\n"
        "Hello World\n"
        "\\end{document}\n"
    )
    result = TemplatePreprocessor.auto_tag(tex)
    assert "pdftex" not in result, "pdftex should be removed"
def test_remove_pdftex_only_option():
    """Test removing pdftex when it's the only option."""
    tex = (
        "\\documentclass[pdftex]{article}\n"
        "\\begin{document}\n"
        "Hello World\n"
        "\\end{document}\n"
    )
    result = TemplatePreprocessor.auto_tag(tex)
    assert "pdftex" not in result
    assert "article" in result

def test_leave_other_options_intact():
    """Test that it doesn't touch other options."""
    tex = (
        "\\documentclass[a4paper,12pt]{article}\n"
        "\\begin{document}\n"
        "Hello World\n"
        "\\end{document}\n"
    )
    result = TemplatePreprocessor.auto_tag(tex)
    assert "a4paper" in result
    assert "12pt" in result


if __name__ == "__main__":
    test_remove_pdftex_from_mdpi()
    print("PASS: test_remove_pdftex_from_mdpi")
    test_remove_pdftex_only_option()
    print("PASS: test_remove_pdftex_only_option")
    test_leave_other_options_intact()
    print("PASS: test_leave_other_options_intact")
    print("\nAll tests passed!")
