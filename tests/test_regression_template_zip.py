from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from backend.core_engine.utils import giai_nen_mau_zip, tim_file_tex_chinh


def test_regression_chan_path_traversal_trong_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "doc_hai.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../evil.tex", "\\documentclass{article}")

    with pytest.raises(ValueError):
        giai_nen_mau_zip(str(zip_path), str(tmp_path / "extract"))


def test_regression_tim_main_tex_tu_zip_con_thu_muc(tmp_path: Path) -> None:
    zip_path = tmp_path / "template.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project/main.tex", "\\documentclass{article}\\begin{document}abc\\end{document}")
        zf.writestr("project/readme.txt", "huong dan")

    thu_muc_giai_nen = tmp_path / "extract"
    giai_nen_mau_zip(str(zip_path), str(thu_muc_giai_nen))
    tex_chinh = tim_file_tex_chinh(str(thu_muc_giai_nen))

    assert Path(tex_chinh).name.lower().endswith(".tex")
    assert Path(tex_chinh).exists()
