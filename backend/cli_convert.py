"""
CLI one-shot converter for developers.

Usage example:
python -m backend.cli_convert --input input.docx --template template.zip
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from backend.core_engine.chuyen_doi import ChuyenDoiWordSangLatex
from backend.core_engine.utils import (
    bien_dich_latex,
    dong_goi_thu_muc_dau_ra,
    giai_nen_mau_zip,
    tim_file_tex_chinh,
)


def _validate_input_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise ValueError(f"Input file không tồn tại: {path}")
    if path.suffix.lower() not in {".docx", ".docm"}:
        raise ValueError("Chỉ hỗ trợ input .docx hoặc .docm")


def _copy_tree_contents(src_dir: Path, dst_dir: Path) -> None:
    for item in src_dir.iterdir():
        target = dst_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _prepare_template(template: Path, work_dir: Path) -> Path:
    if not template.exists():
        raise ValueError(f"Template không tồn tại: {template}")

    suffix = template.suffix.lower()

    if template.is_file() and suffix == ".zip":
        giai_nen_mau_zip(str(template), str(work_dir))
        return Path(tim_file_tex_chinh(str(work_dir)))

    if template.is_file() and suffix == ".tex":
        # Copy toàn bộ thư mục chứa template để hỗ trợ .cls/.sty/.bib đi kèm.
        _copy_tree_contents(template.parent, work_dir)
        return work_dir / template.name

    if template.is_dir():
        _copy_tree_contents(template, work_dir)
        return Path(tim_file_tex_chinh(str(work_dir)))

    raise ValueError("Template phải là .zip, .tex hoặc thư mục template")


def _normalize_tex_paths(tex_path: Path, images_dir: Path, work_dir: Path) -> None:
    tex_raw = tex_path.read_text(encoding="utf-8", errors="ignore")
    images_abs = str(images_dir).replace("\\", "/")
    work_abs = str(work_dir).replace("\\", "/")
    tex_raw = tex_raw.replace(images_abs + "/", "images/").replace(images_abs, "images")
    tex_raw = tex_raw.replace(work_abs + "/", "").replace(work_abs, "")

    images_abs_win = str(images_dir).replace("/", "\\")
    work_abs_win = str(work_dir).replace("/", "\\")
    tex_raw = tex_raw.replace(images_abs_win + "\\", "images/").replace(images_abs_win, "images")
    tex_raw = tex_raw.replace(work_abs_win + "\\", "").replace(work_abs_win, "")

    tex_path.write_text(tex_raw, encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="word2latex-cli",
        description="Convert DOCX/DOCM + template(.zip/.tex/dir) into ZIP output in a new run folder.",
    )
    parser.add_argument("--input", required=True, help="Đường dẫn file .docx hoặc .docm")
    parser.add_argument("--template", required=True, help="Đường dẫn template (.zip/.tex/thư mục)")
    parser.add_argument(
        "--out-root",
        default="outputs/cli_runs",
        help="Thư mục gốc chứa các run output (mặc định: outputs/cli_runs)",
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Bỏ qua bước compile PDF (vẫn xuất ZIP chứa .tex + assets)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_file = Path(args.input).expanduser().resolve()
    template_path = Path(args.template).expanduser().resolve()
    out_root = Path(args.out_root).expanduser().resolve()

    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    work_dir = out_root / run_id

    try:
        _validate_input_file(input_file)
        out_root.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=False)

        source_copy = work_dir / f"source{input_file.suffix.lower()}"
        shutil.copy2(input_file, source_copy)

        template_tex = _prepare_template(template_path, work_dir)

        output_tex_name = f"output_{datetime.now().strftime('%H%M%S')}.tex"
        output_tex = work_dir / output_tex_name
        images_dir = work_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        converter = ChuyenDoiWordSangLatex(
            duong_dan_word=str(source_copy),
            duong_dan_template=str(template_tex),
            duong_dan_dau_ra=str(output_tex),
            thu_muc_anh=str(images_dir),
            mode="demo",
        )
        converter.chuyen_doi()

        if not output_tex.exists():
            raise RuntimeError("Không tạo được file .tex đầu ra")

        _normalize_tex_paths(output_tex, images_dir, work_dir)

        compile_ok = True
        compile_error = ""
        if not args.skip_compile:
            compile_ok, compile_error = bien_dich_latex(str(output_tex), thu_muc_bien_dich=str(work_dir))
            if not compile_ok:
                raise RuntimeError(f"Biên dịch PDF thất bại:\n{compile_error[:4000]}")

        result_zip = work_dir / "result.zip"
        dong_goi_thu_muc_dau_ra(
            str(work_dir),
            str(result_zip),
            generated_tex_name=output_tex.name,
        )

        summary = {
            "thanh_cong": True,
            "run_id": run_id,
            "input": str(input_file),
            "template": str(template_path),
            "work_dir": str(work_dir),
            "tex_file": output_tex.name,
            "zip_file": str(result_zip),
            "compiled_pdf": compile_ok and not args.skip_compile,
        }
        (work_dir / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"[OK] Chuyển đổi thành công. Thư mục output: {work_dir}")
        print(f"[OK] File ZIP: {result_zip}")
        return 0

    except Exception as exc:
        error_summary = {
            "thanh_cong": False,
            "run_id": run_id,
            "error": str(exc),
        }
        try:
            work_dir.mkdir(parents=True, exist_ok=True)
            (work_dir / "run-summary.json").write_text(
                json.dumps(error_summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        print(f"[ERROR] {exc}", file=sys.stderr)
        print(f"[INFO] Xem thư mục run lỗi: {work_dir}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
