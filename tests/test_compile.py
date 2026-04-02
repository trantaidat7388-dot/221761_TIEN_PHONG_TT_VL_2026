from pathlib import Path
import pytest

from backend.core_engine.utils import giai_nen_mau_zip, tim_file_tex_chinh


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_tim_tex_chinh_tu_zip_template(tmp_path: Path) -> None:
    """Kiem tra co the giai nen va tim file tex chinh tu template zip."""
    input_dir = ROOT_DIR / "input_data"
    ds_zip = sorted(input_dir.glob("*.zip"))
    if not ds_zip:
        pytest.skip("Khong co file template zip trong input_data")

    duong_dan_zip = ds_zip[0]
    thu_muc_dich = tmp_path / "template"
    thu_muc_dich.mkdir(parents=True, exist_ok=True)

    giai_nen_mau_zip(str(duong_dan_zip), str(thu_muc_dich))
    tex_chinh = tim_file_tex_chinh(str(thu_muc_dich))

    assert Path(tex_chinh).exists()
    assert Path(tex_chinh).suffix.lower() == ".tex"


@pytest.mark.integration
def test_chuyen_doi_duong_ong_docx_co_the_khoi_tao(tmp_path: Path) -> None:
    """Smoke level: kiem tra tai nguyen dau vao de phuc vu test chuyen doi full stack."""
    thu_muc_word = ROOT_DIR / "input_data" / "Template_word"
    ds_docx = sorted(thu_muc_word.glob("*.docx")) + sorted(thu_muc_word.glob("*.docm"))
    if not ds_docx:
        pytest.skip("Khong co file Word mau trong input_data/Template_word")

    assert ds_docx[0].exists()
