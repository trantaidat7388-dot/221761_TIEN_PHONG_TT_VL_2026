from backend.core_engine.utils import loc_ky_tu


def test_loc_ky_tu_removes_hebrew_and_bidi_controls():
    src = "Training data from במסגרת the VLSP\u202e evaluation"
    out = loc_ky_tu(src)

    assert "ב" not in out
    assert "במסגרת" not in out
    assert "\u202e" not in out
    assert "Training data from" in out
    assert "the VLSP" in out
