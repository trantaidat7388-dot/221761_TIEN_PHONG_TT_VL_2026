"""CLI pipeline for Word-to-Word conversion (Springer <-> IEEE).

Supports:
- Springer Word -> IEEE Word
- IEEE Word -> Springer Word
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_IEEE_WORD_TEMPLATE = ROOT_DIR / "input_data" / "Template_word" / "conference-template-a4 (ieee).docx"
DEFAULT_SPRINGER_WORD_TEMPLATE = ROOT_DIR / "input_data" / "Template_word" / "splnproc2510.docm"


def _sanitize_stem(filename: str) -> str:
    raw_stem = Path(filename).stem
    sanitized = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in raw_stem)
    sanitized = sanitized.strip("_-")
    return sanitized or "document"


def _validate_word_input(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Khong tim thay file Word: {path}")
    if path.suffix.lower() not in {".docx", ".docm"}:
        raise ValueError("Chi chap nhan file Word .docx hoac .docm")


def _validate_template_input(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Khong tim thay file template Word: {path}")
    if path.suffix.lower() not in {".docx", ".docm"}:
        raise ValueError("Template Word phai co duoi .docx hoac .docm")


def run_pipeline(
    input_word: Path,
    direction: str,
    output_dir: Path,
    template_word: Path | None = None,
) -> Path:
    _validate_word_input(input_word)

    direction = direction.strip().lower()
    if direction not in {"springer-to-ieee", "ieee-to-springer"}:
        raise ValueError("direction phai la 'springer-to-ieee' hoac 'ieee-to-springer'")

    if template_word is None:
        if direction == "springer-to-ieee":
            template_word = DEFAULT_IEEE_WORD_TEMPLATE
        else:
            template_word = DEFAULT_SPRINGER_WORD_TEMPLATE

    _validate_template_input(template_word)

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = _sanitize_stem(input_word.name)

    job_dir = output_dir / f"job_word2word_{safe_name}_{timestamp}"
    images_dir = job_dir / "images"
    job_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    if direction == "springer-to-ieee":
        output_name = f"{safe_name}_{timestamp}_ieee.docx"
        renderer = IEEEWordRenderer()
    else:
        output_name = f"{safe_name}_{timestamp}_springer.docx"
        renderer = SpringerWordRenderer()

    output_path = output_dir / output_name

    parser = WordASTParser(str(input_word), thu_muc_anh=str(images_dir))
    ir_data = parser.parse()

    if direction == "springer-to-ieee":
        renderer.render(
            ir_data=ir_data,
            output_path=str(output_path),
            image_root_dir=str(job_dir),
            ieee_template_path=str(template_word),
        )
    else:
        renderer.render(
            ir_data=ir_data,
            output_path=str(output_path),
            image_root_dir=str(job_dir),
            springer_template_path=str(template_word),
        )

    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pipeline chuyen doi Word sang Word (Springer <-> IEEE)."
    )
    parser.add_argument("--input-word", required=True, help="Duong dan file Word dau vao (.docx/.docm)")
    parser.add_argument(
        "--direction",
        required=True,
        choices=["springer-to-ieee", "ieee-to-springer"],
        help="Huong chuyen doi: springer-to-ieee hoac ieee-to-springer",
    )
    parser.add_argument("--output-dir", required=True, help="Thu muc luu file Word dau ra")
    parser.add_argument(
        "--template-word",
        required=False,
        help="(Tuy chon) duong dan file template Word (.docx/.docm). Neu bo qua se dung template mac dinh.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        output_path = run_pipeline(
            input_word=Path(args.input_word).resolve(),
            direction=args.direction,
            output_dir=Path(args.output_dir).resolve(),
            template_word=Path(args.template_word).resolve() if args.template_word else None,
        )
    except Exception as exc:
        print(f"[ERROR] Pipeline that bai: {exc}", file=sys.stderr)
        return 1

    print("Pipeline thanh cong.")
    print(f"- Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
