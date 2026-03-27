"""Test that fontspec injection skips commented \\documentclass lines."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.core_engine.template_preprocessor import TemplatePreprocessor


def test_skips_commented_documentclass():
    """fontspec must appear only ONCE, after the active \\documentclass."""
    tex = (
        "% \\documentclass[preprints]{Definitions/mdpi}\n"
        "\\documentclass[journal]{Definitions/mdpi}\n"
        "\\begin{document}\n"
        "Hello\n"
        "\\end{document}\n"
    )
    result = TemplatePreprocessor.auto_tag(tex)
    count = result.count("\\usepackage{fontspec}")
    assert count == 1, f"Expected 1 fontspec, got {count}.\n---\n{result[:500]}"

    # It must appear AFTER the active (non-commented) \\documentclass
    dc_pos = result.find("\\documentclass[journal]")
    fs_pos = result.find("\\usepackage{fontspec}")
    assert dc_pos != -1, "Active \\documentclass not found"
    assert fs_pos > dc_pos, (
        f"fontspec ({fs_pos}) appears before active \\documentclass ({dc_pos})"
    )


def test_no_injection_when_already_present():
    """If fontspec is already in the source, don't inject again."""
    tex = (
        "\\documentclass{article}\n"
        "\\usepackage{fontspec}\n"
        "\\begin{document}\n"
        "Hello\n"
        "\\end{document}\n"
    )
    result = TemplatePreprocessor.auto_tag(tex)
    count = result.count("\\usepackage{fontspec}")
    assert count == 1, f"Expected 1 fontspec, got {count}"


def test_no_injection_when_setmainfont_present():
    """If \\setmainfont is present, don't inject fontspec."""
    tex = (
        "\\documentclass{article}\n"
        "\\setmainfont{Times New Roman}\n"
        "\\begin{document}\n"
        "Hello\n"
        "\\end{document}\n"
    )
    result = TemplatePreprocessor.auto_tag(tex)
    assert "\\usepackage{fontspec}" not in result or result.count("\\usepackage{fontspec}") == 0, \
        "fontspec should not be injected when \\setmainfont is present"


if __name__ == "__main__":
    test_skips_commented_documentclass()
    print("PASS: test_skips_commented_documentclass")
    test_no_injection_when_already_present()
    print("PASS: test_no_injection_when_already_present")
    test_no_injection_when_setmainfont_present()
    print("PASS: test_no_injection_when_setmainfont_present")
    print("\nAll tests passed!")
