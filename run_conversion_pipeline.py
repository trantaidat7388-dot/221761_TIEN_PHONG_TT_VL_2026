"""Pipeline CLI chuyen doi 1 file Word + 1 file ZIP template sang goi ket qua LaTeX.

Script nay cho phep nguoi dung chay chuyen doi bang dong lenh, khong can UI.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from backend.core_engine.chuyen_doi import ChuyenDoiWordSangLatex
from backend.core_engine.utils import (
    bien_dich_latex,
    dong_goi_thu_muc_dau_ra,
    don_dep_file_rac,
    giai_nen_mau_zip,
    tim_file_tex_chinh,
)


def _sanitize_stem(filename: str) -> str:
    raw_stem = Path(filename).stem
    sanitized = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in raw_stem)
    sanitized = sanitized.strip("_-")
    return sanitized or "document"


def _normalize_generated_tex(tex_path: Path, images_folder: Path, job_folder: Path) -> None:
    tex_raw = tex_path.read_text(encoding="utf-8", errors="ignore")
    tex_raw = re.sub(r"<<\s*metadata\.[a-zA-Z0-9_]+\s*>>(?:\s*\{[^{}]*\}\s*)*", "", tex_raw)

    images_abs = str(images_folder).replace("\\", "/")
    job_abs = str(job_folder).replace("\\", "/")
    tex_raw = tex_raw.replace(images_abs + "/", "images/").replace(images_abs, "images")
    tex_raw = tex_raw.replace(job_abs + "/", "").replace(job_abs, "")

    images_abs_win = str(images_folder).replace("/", "\\")
    job_abs_win = str(job_folder).replace("/", "\\")
    tex_raw = tex_raw.replace(images_abs_win + "\\", "images/").replace(images_abs_win, "images")
    tex_raw = tex_raw.replace(job_abs_win + "\\", "").replace(job_abs_win, "")

    tex_path.write_text(tex_raw, encoding="utf-8")


def run_pipeline(
    word_file: Path,
    template_zip: Path,
    output_dir: Path,
    compile_pdf: bool,
    keep_workdir: bool,
) -> tuple[Path, Path]:
    if not word_file.exists():
        raise FileNotFoundError(f"Khong tim thay file Word: {word_file}")
    if not template_zip.exists():
        raise FileNotFoundError(f"Khong tim thay file template ZIP: {template_zip}")

    if word_file.suffix.lower() not in {".docx", ".docm"}:
        raise ValueError("File Word dau vao phai co duoi .docx hoac .docm")
    if template_zip.suffix.lower() != ".zip":
        raise ValueError("Template dau vao phai la file .zip")

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = _sanitize_stem(word_file.name)
    job_folder = output_dir / f"job_{safe_name}_{timestamp}"
    images_folder = job_folder / "images"
    images_folder.mkdir(parents=True, exist_ok=True)

    word_copy = job_folder / f"{safe_name}{word_file.suffix.lower()}"
    shutil.copy2(word_file, word_copy)

    template_zip_copy = job_folder / "uploaded_template.zip"
    shutil.copy2(template_zip, template_zip_copy)

    print("[1/5] Giai nen template ZIP...")
    giai_nen_mau_zip(str(template_zip_copy), str(job_folder))
    template_zip_copy.unlink(missing_ok=True)

    main_template_path = Path(tim_file_tex_chinh(str(job_folder)))
    template_tex_dir = main_template_path.parent
    if template_tex_dir != job_folder:
        shutil.copytree(template_tex_dir, job_folder, dirs_exist_ok=True)
    template_path = job_folder / main_template_path.name

    output_tex_name = f"{safe_name}_{timestamp}.tex"
    output_tex_path = job_folder / output_tex_name

    print("[2/5] Chuyen doi Word -> LaTeX...")
    converter = ChuyenDoiWordSangLatex(
        duong_dan_word=str(word_copy),
        duong_dan_template=str(template_path),
        duong_dan_dau_ra=str(output_tex_path),
        thu_muc_anh=str(images_folder),
        mode="demo",
    )
    converter.chuyen_doi()

    if not output_tex_path.exists():
        raise RuntimeError("Khong tao duoc file .tex dau ra")

    print("[3/5] Chuan hoa duong dan trong file .tex...")
    _normalize_generated_tex(output_tex_path, images_folder, job_folder)

    if compile_pdf:
        print("[4/5] Bien dich PDF (tuy chon)...")
        ok, err_msg = bien_dich_latex(str(output_tex_path), thu_muc_bien_dich=str(job_folder))
        if not ok:
            raise RuntimeError(f"Bien dich PDF that bai:\n{err_msg}")
        don_dep_file_rac(str(output_tex_path))
    else:
        print("[4/5] Bo qua bien dich PDF theo cau hinh.")

    output_zip_name = output_tex_name.replace(".tex", ".zip")
    output_zip_path = job_folder / output_zip_name
    print("[5/5] Dong goi ket qua ZIP...")
    dong_goi_thu_muc_dau_ra(str(job_folder), str(output_zip_path), generated_tex_name=output_tex_name)

    if not keep_workdir:
        final_zip_path = output_dir / output_zip_name
        final_tex_path = output_dir / output_tex_name
        shutil.copy2(output_zip_path, final_zip_path)
        shutil.copy2(output_tex_path, final_tex_path)
        shutil.rmtree(job_folder, ignore_errors=True)
        return final_tex_path, final_zip_path

    return output_tex_path, output_zip_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pipeline chuyen doi: 1 Word + 1 template ZIP -> thu muc ket qua"
    )
    parser.add_argument("--word", required=True, help="Duong dan file Word (.docx/.docm)")
    parser.add_argument("--template-zip", required=True, help="Duong dan file ZIP chua template LaTeX")
    parser.add_argument("--output-dir", required=True, help="Thu muc luu ket qua")
    parser.add_argument(
        "--compile-pdf",
        action="store_true",
        help="Neu bat, script se bien dich them PDF sau khi tao .tex",
    )
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Giu lai thu muc job_<...> de debug thay vi chi giu file ket qua cuoi",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        tex_path, zip_path = run_pipeline(
            word_file=Path(args.word).resolve(),
            template_zip=Path(args.template_zip).resolve(),
            output_dir=Path(args.output_dir).resolve(),
            compile_pdf=args.compile_pdf,
            keep_workdir=args.keep_workdir,
        )
    except Exception as exc:
        print(f"[ERROR] Pipeline that bai: {exc}", file=sys.stderr)
        return 1

    print("\nPipeline thanh cong.")
    print(f"- TEX: {tex_path}")
    print(f"- ZIP: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
