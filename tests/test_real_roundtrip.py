"""Real-world round-trip test: Springer -> IEEE -> Springer."""
import sys
import io
import tempfile
from pathlib import Path

# Fix console encoding for Vietnamese characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, ".")
from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer

ROOT = Path(".")
IEEE_TEMPLATE = ROOT / "input_data" / "Template_word" / "conference-template-a4 (ieee).docx"
SPRINGER_TEMPLATE = ROOT / "input_data" / "Template_word" / "splnproc2510.docm"

# Try multiple real input files
candidates = [
    ROOT / "input_data" / "Template_word" / "Vietnamese Text-to-Speech System Using Artificial Intelligence (AI).docm",
    ROOT / "input_data" / "Template_word" / "26_HoPhuocLoi_DH22TIN03_1.docm",
    ROOT / "input_data" / "Template_word" / "08_TranTanDat_05_HeThongXuatTuDongTapTinTrinhBayTuNguonTapTinVanBanChoTruoc_DH22TIN06.docm",
    ROOT / "input_data" / "Template_word" / "Overview of Automatic Paper Money Recognition Systems Using Artificial Intelligence (AI).docm",
]

for input_file in candidates:
    if not input_file.exists():
        print(f"SKIP: {input_file.name} not found")
        continue

    print(f"\n{'#'*70}")
    print(f"# Testing: {input_file.name}")
    print(f"{'#'*70}")

    tmp = Path(tempfile.mkdtemp())

    # Step 1: Parse Springer
    p1 = WordASTParser(str(input_file), thu_muc_anh=str(tmp / "img1"), mode="word2word")
    ir1 = p1.parse()
    title1 = ir1["metadata"]["title"][:80]
    abs1 = ir1["metadata"]["abstract"][:120]
    kw1 = ir1["metadata"]["keywords"]
    body1 = len(ir1["body"])
    refs1 = len(ir1["references"])
    sec1 = sum(1 for n in ir1["body"] if n.get("type") == "section")

    print(f"  STEP 1 - Original:")
    print(f"    Title:    {title1}")
    print(f"    Abstract: {abs1}...")
    print(f"    Keywords: {kw1}")
    print(f"    Body: {body1} nodes, {sec1} sections, {refs1} refs")

    # Step 2: Render IEEE
    ieee_out = tmp / "ieee.docx"
    IEEEWordRenderer().render(
        ir_data=ir1,
        output_path=str(ieee_out),
        image_root_dir=str(tmp),
        ieee_template_path=str(IEEE_TEMPLATE),
    )

    # Step 3: Parse IEEE
    p2 = WordASTParser(str(ieee_out), thu_muc_anh=str(tmp / "img2"), mode="word2word")
    ir2 = p2.parse()
    title2 = ir2["metadata"]["title"][:80]
    abs2 = ir2["metadata"]["abstract"][:120]
    kw2 = ir2["metadata"]["keywords"]
    body2 = len(ir2["body"])
    refs2 = len(ir2["references"])
    sec2 = sum(1 for n in ir2["body"] if n.get("type") == "section")

    print(f"  STEP 3 - From IEEE:")
    print(f"    Title:    {title2}")
    print(f"    Abstract: {abs2}...")
    print(f"    Keywords: {kw2}")
    print(f"    Body: {body2} nodes, {sec2} sections, {refs2} refs")

    # Step 4: Render Springer
    springer_out = tmp / "springer.docx"
    SpringerWordRenderer().render(
        ir_data=ir2,
        output_path=str(springer_out),
        image_root_dir=str(tmp),
        springer_template_path=str(SPRINGER_TEMPLATE),
    )

    # Step 5: Parse final Springer
    p3 = WordASTParser(str(springer_out), thu_muc_anh=str(tmp / "img3"), mode="word2word")
    ir3 = p3.parse()
    title3 = ir3["metadata"]["title"][:80]
    abs3 = ir3["metadata"]["abstract"][:120]
    kw3 = ir3["metadata"]["keywords"]
    body3 = len(ir3["body"])
    refs3 = len(ir3["references"])
    sec3 = sum(1 for n in ir3["body"] if n.get("type") == "section")

    print(f"  STEP 5 - Final Springer:")
    print(f"    Title:    {title3}")
    print(f"    Abstract: {abs3}...")
    print(f"    Keywords: {kw3}")
    print(f"    Body: {body3} nodes, {sec3} sections, {refs3} refs")

    # Compare
    issues = []
    if not title3:
        issues.append("TITLE LOST")
    if not abs3:
        issues.append("ABSTRACT LOST")
    if abs3.startswith("---") or abs3.startswith("---"):
        issues.append("ABSTRACT STARTS WITH DASH")
    if abs3.lower().startswith("abstract"):
        issues.append("ABSTRACT PREFIX NOT STRIPPED")
    if sec3 == 0 and sec1 > 0:
        issues.append("ALL SECTIONS LOST")
    if body3 == 0:
        issues.append("BODY EMPTY")
    if refs3 == 0 and refs1 > 0:
        issues.append("ALL REFERENCES LOST")
    if len(kw3) == 0 and len(kw1) > 0:
        issues.append("ALL KEYWORDS LOST")

    if issues:
        print(f"  [FAIL] Issues: {', '.join(issues)}")
    else:
        print(f"  [PASS] Round-trip OK!")

    print(f"  Comparison:")
    print(f"    Title:    {'MATCH' if title1[:40] == title3[:40] else 'DIFF'}")
    print(f"    Keywords: {len(kw1)} -> {len(kw3)}")
    print(f"    Sections: {sec1} -> {sec3}")
    print(f"    Body:     {body1} -> {body3}")
    print(f"    Refs:     {refs1} -> {refs3}")
    print(f"  Output:  {springer_out}")

print("\nDone.")
