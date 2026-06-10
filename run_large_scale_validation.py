"""Large-scale validation for Word -> LaTeX and Word -> Word pipelines.

The script scans input_data for Word documents, validates each input, converts
it to both IEEE and Springer targets, compiles LaTeX to PDF, and performs two
Word round trips:

    source -> IEEE Word -> Springer Word
    source -> Springer Word -> IEEE Word

Results are written as JSON and Markdown under the selected output directory.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from backend.core_engine.ast_parser import WordASTParser
from backend.core_engine.chuyen_doi import ChuyenDoiWordSangLatex
from backend.core_engine.utils import bien_dich_latex
from backend.core_engine.word_ieee_renderer import IEEEWordRenderer
from backend.core_engine.word_springer_renderer import SpringerWordRenderer


ROOT = Path(__file__).resolve().parent
INPUT_ROOT = ROOT / "input_data"
WORD_TEMPLATE_ROOT = INPUT_ROOT / "Template_word"
IEEE_WORD_TEMPLATE = WORD_TEMPLATE_ROOT / "conference-template-a4 (ieee).docx"
SPRINGER_WORD_TEMPLATE = WORD_TEMPLATE_ROOT / "splnproc2510.docm"
IEEE_LATEX_TEMPLATE_DIR = (
    ROOT / "backend" / "storage" / "custom_templates" / "IEEE-conference-template-062824"
)
IEEE_LATEX_TEMPLATE_NAME = "IEEE-conference-template-062824.tex"
SPRINGER_LATEX_TEMPLATE_DIR = (
    ROOT / "backend" / "storage" / "custom_templates" / "Springer_Lecture_Notes_in_Computer_Science"
)
SPRINGER_LATEX_TEMPLATE_NAME = "samplepaper.tex"

WORD_EXTENSIONS = {".docx", ".docm", ".doc"}
TOKEN_RE = re.compile(r"[A-Za-zÀ-ỹ0-9]{2,}", re.UNICODE)
LATEX_COMMAND_RE = re.compile(r"\\[A-Za-z@]+(?:\[[^\]]*\])?")
LATEX_BRACE_RE = re.compile(r"[{}$]")


def _safe_name(path: Path) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", path.stem).strip("_")
    return value[:100] or "document"


def _plain_text(value: Any) -> str:
    text = str(value or "")
    text = LATEX_COMMAND_RE.sub(" ", text)
    text = LATEX_BRACE_RE.sub(" ", text)
    text = re.sub(r"\\[%&#_]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _ir_text(ir: dict[str, Any]) -> str:
    metadata = ir.get("metadata", {}) or {}
    parts = [
        metadata.get("title", ""),
        metadata.get("abstract", ""),
        " ".join(str(item) for item in metadata.get("keywords", []) or []),
    ]
    for author in metadata.get("authors", []) or []:
        parts.append(author.get("name", ""))
        parts.extend(author.get("affiliations", []) or [])
    for node in ir.get("body", []) or []:
        parts.append(node.get("text", ""))
        if node.get("type") == "table":
            for row in node.get("data", []) or []:
                for cell in row:
                    parts.append(cell.get("text", ""))
        if node.get("type") == "algorithm":
            parts.append(node.get("caption", ""))
            parts.extend(step.get("text", "") for step in node.get("steps", []) or [])
    parts.extend(ref.get("text", "") for ref in ir.get("references", []) or [])
    return _plain_text(" ".join(str(part) for part in parts))


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in TOKEN_RE.findall(text)]


def _token_recall(source_text: str, target_text: str) -> float:
    source = Counter(_tokens(source_text))
    target = Counter(_tokens(target_text))
    if not source:
        return 1.0 if not target else 0.0
    kept = sum(min(count, target.get(token, 0)) for token, count in source.items())
    return round(kept / sum(source.values()), 4)


def _node_count(ir: dict[str, Any], node_type: str) -> int:
    return sum(1 for node in ir.get("body", []) or [] if node.get("type") == node_type)


def _figure_count(ir: dict[str, Any]) -> int:
    metadata = ir.get("metadata", {}) or {}
    count = int(metadata.get("total_images", 0) or 0)
    if count:
        return count
    return sum(
        len(re.findall(r"\\includegraphics", str(node.get("text", ""))))
        for node in ir.get("body", []) or []
    )


def _formula_count(ir: dict[str, Any]) -> int:
    metadata = ir.get("metadata", {}) or {}
    count = int(metadata.get("total_formulas", 0) or 0)
    if count:
        return count
    return sum(
        len(re.findall(r"\\begin\{equation\*?\}|«OMML:", str(node.get("text", ""))))
        for node in ir.get("body", []) or []
    )


def _ir_metrics(ir: dict[str, Any]) -> dict[str, Any]:
    metadata = ir.get("metadata", {}) or {}
    text = _ir_text(ir)
    return {
        "title": _plain_text(metadata.get("title", "")),
        "authors": len(metadata.get("authors", []) or []),
        "abstract_chars": len(_plain_text(metadata.get("abstract", ""))),
        "keywords": len(metadata.get("keywords", []) or []),
        "sections": _node_count(ir, "section"),
        "paragraphs": _node_count(ir, "paragraph"),
        "tables": _node_count(ir, "table"),
        "figures": _figure_count(ir),
        "formulas": _formula_count(ir),
        "algorithms": _node_count(ir, "algorithm"),
        "references": len(ir.get("references", []) or []),
        "text_chars": len(text),
        "text_tokens": len(_tokens(text)),
    }


def _parse_word(path: Path, image_dir: Path, mode: str = "word2word") -> dict[str, Any]:
    image_dir.mkdir(parents=True, exist_ok=True)
    return WordASTParser(str(path), thu_muc_anh=str(image_dir), mode=mode).parse()


def _pdf_metrics(pdf_path: Path) -> dict[str, Any]:
    reader = PdfReader(str(pdf_path))
    text_parts = []
    image_count = 0
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
        try:
            image_count += len(page.images)
        except Exception:
            pass
    text = _plain_text("\n".join(text_parts))
    return {
        "pages": len(reader.pages),
        "images": image_count,
        "text_chars": len(text),
        "text_tokens": len(_tokens(text)),
        "_text": text,
    }


def _severity_issues(
    source: dict[str, Any],
    target: dict[str, Any],
    recall: float,
) -> list[str]:
    issues = []
    if source["title"] and not target["title"]:
        issues.append("title_lost")
    if source["abstract_chars"] >= 80 and target["abstract_chars"] == 0:
        issues.append("abstract_lost")
    if source["sections"] > 0 and target["sections"] == 0:
        issues.append("sections_lost")
    if source["tables"] > target["tables"]:
        issues.append(f"tables_lost:{source['tables']}->{target['tables']}")
    if source["figures"] > target["figures"]:
        issues.append(f"figures_lost:{source['figures']}->{target['figures']}")
    if source["formulas"] > 0 and target["formulas"] == 0:
        issues.append(f"formulas_lost:{source['formulas']}->0")
    if source["references"] > 0 and target["references"] == 0:
        issues.append(f"references_lost:{source['references']}->0")
    if recall < 0.70:
        issues.append(f"low_text_recall:{recall:.1%}")
    return issues


def _classify_input(path: Path, metrics: dict[str, Any]) -> str:
    name = path.name.casefold()
    template_markers = (
        "template",
        "splnproc",
        "conference-template",
        "paper format",
        "transactions-template",
        "test_output",
        "_converted",
    )
    if any(marker in name for marker in template_markers):
        return "template_or_generated"
    if metrics["text_tokens"] < 80:
        return "sparse_or_invalid"
    if not metrics["title"] and metrics["sections"] == 0:
        return "unrecognized_structure"
    return "paper"


def _copy_latex_template(target: str, case_dir: Path) -> Path:
    if target == "ieee":
        source_dir = IEEE_LATEX_TEMPLATE_DIR
        main_name = IEEE_LATEX_TEMPLATE_NAME
    else:
        source_dir = SPRINGER_LATEX_TEMPLATE_DIR
        main_name = SPRINGER_LATEX_TEMPLATE_NAME
    template_dir = case_dir / "template"
    shutil.copytree(source_dir, template_dir, dirs_exist_ok=True)
    return template_dir / main_name


def _run_w2l(
    input_path: Path,
    source_metrics: dict[str, Any],
    source_text: str,
    target: str,
    case_dir: Path,
) -> dict[str, Any]:
    started = time.time()
    result: dict[str, Any] = {"target": target, "status": "failed"}
    try:
        template_path = _copy_latex_template(target, case_dir)
        images_dir = case_dir / "images"
        output_tex = case_dir / "main.tex"
        converter = ChuyenDoiWordSangLatex(
            duong_dan_word=str(input_path),
            duong_dan_template=str(template_path),
            duong_dan_dau_ra=str(output_tex),
            thu_muc_anh=str(images_dir.resolve()),
            mode="demo",
        )
        converter.chuyen_doi()
        tex = output_tex.read_text(encoding="utf-8", errors="ignore")
        compile_ok, compile_error = bien_dich_latex(
            str(output_tex),
            thu_muc_bien_dich=str(case_dir),
        )
        pdf_path = output_tex.with_suffix(".pdf")
        pdf_data = _pdf_metrics(pdf_path) if compile_ok and pdf_path.exists() else {}
        pdf_text = pdf_data.pop("_text", "")
        result.update(
            {
                "status": "passed" if compile_ok else "compile_failed",
                "tex_exists": output_tex.exists(),
                "pdf_exists": pdf_path.exists(),
                "compile_error": compile_error[-4000:] if compile_error else "",
                "tex_tables": len(re.findall(r"\\begin\{(?:table\*?|longtable)\}", tex)),
                "tex_figures": len(re.findall(r"\\includegraphics", tex)),
                "tex_equations": len(
                    re.findall(r"\\begin\{(?:equation\*?|align\*?|gather\*?)\}", tex)
                ),
                "pdf": pdf_data,
                "pdf_text_recall": _token_recall(source_text, pdf_text) if pdf_text else 0.0,
            }
        )
        issues = []
        if source_metrics["tables"] > result["tex_tables"]:
            issues.append(
                f"tables_missing_in_tex:{source_metrics['tables']}->{result['tex_tables']}"
            )
        if source_metrics["figures"] > result["tex_figures"]:
            issues.append(
                f"figures_missing_in_tex:{source_metrics['figures']}->{result['tex_figures']}"
            )
        if source_metrics["formulas"] > 0 and result["tex_equations"] == 0:
            issues.append(
                f"equations_missing_in_tex:{source_metrics['formulas']}->0"
            )
        if compile_ok and result["pdf_text_recall"] < 0.65:
            issues.append(f"low_pdf_text_recall:{result['pdf_text_recall']:.1%}")
        result["issues"] = issues
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()[-5000:]
    result["duration_seconds"] = round(time.time() - started, 2)
    return result


def _render_word(
    ir: dict[str, Any],
    target: str,
    output_path: Path,
    image_root: Path,
) -> None:
    if target == "ieee":
        IEEEWordRenderer().render(
            ir_data=ir,
            output_path=str(output_path),
            image_root_dir=str(image_root),
            ieee_template_path=str(IEEE_WORD_TEMPLATE),
        )
    else:
        SpringerWordRenderer().render(
            ir_data=ir,
            output_path=str(output_path),
            image_root_dir=str(image_root),
            springer_template_path=str(SPRINGER_WORD_TEMPLATE),
        )


def _run_w2w_roundtrip(
    source_ir: dict[str, Any],
    source_metrics: dict[str, Any],
    source_text: str,
    first_target: str,
    second_target: str,
    case_dir: Path,
) -> dict[str, Any]:
    started = time.time()
    result: dict[str, Any] = {
        "path": f"{first_target}_to_{second_target}",
        "status": "failed",
    }
    try:
        case_dir.mkdir(parents=True, exist_ok=True)
        first_path = case_dir / f"step1_{first_target}.docx"
        _render_word(source_ir, first_target, first_path, case_dir.parent)
        first_ir = _parse_word(first_path, case_dir / "step1_images")
        first_metrics = _ir_metrics(first_ir)
        first_text = _ir_text(first_ir)

        final_path = case_dir / f"step2_{second_target}.docx"
        _render_word(first_ir, second_target, final_path, case_dir)
        final_ir = _parse_word(final_path, case_dir / "step2_images")
        final_metrics = _ir_metrics(final_ir)
        final_text = _ir_text(final_ir)

        first_recall = _token_recall(source_text, first_text)
        final_recall = _token_recall(source_text, final_text)
        result.update(
            {
                "status": "passed",
                "first_output": str(first_path),
                "final_output": str(final_path),
                "first_metrics": first_metrics,
                "final_metrics": final_metrics,
                "first_text_recall": first_recall,
                "final_text_recall": final_recall,
                "first_issues": _severity_issues(
                    source_metrics, first_metrics, first_recall
                ),
                "final_issues": _severity_issues(
                    source_metrics, final_metrics, final_recall
                ),
            }
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()[-5000:]
    result["duration_seconds"] = round(time.time() - started, 2)
    return result


def _status_label(case: dict[str, Any]) -> str:
    if case.get("input_status") != "valid":
        return "INPUT_ERROR"
    operations = (case.get("w2l") or []) + (case.get("w2w") or [])
    if any(op.get("status") not in {"passed"} for op in operations):
        return "FAIL"
    has_issues = any(
        op.get("issues")
        or op.get("first_issues")
        or op.get("final_issues")
        for op in operations
    )
    return "WARN" if has_issues else "PASS"


def _write_reports(results: dict[str, Any], output_dir: Path) -> None:
    json_path = output_dir / "large_scale_validation.json"
    json_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    cases = results["cases"]
    summary = Counter(_status_label(case) for case in cases)
    lines = [
        "# Large-Scale Conversion Validation",
        "",
        f"- Generated: {results['generated_at']}",
        f"- Word inputs: {len(cases)}",
        f"- PASS: {summary['PASS']}",
        f"- WARN: {summary['WARN']}",
        f"- FAIL: {summary['FAIL']}",
        f"- INPUT_ERROR: {summary['INPUT_ERROR']}",
        "",
        "| Result | Input | Kind | Source metrics | W2L IEEE | W2L Springer | W2W I→S | W2W S→I |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for case in cases:
        metrics = case.get("source_metrics", {})
        metric_text = (
            f"T{metrics.get('tables', 0)} F{metrics.get('figures', 0)} "
            f"E{metrics.get('formulas', 0)} S{metrics.get('sections', 0)} "
            f"R{metrics.get('references', 0)}"
        )

        def op_text(op: dict[str, Any] | None, recall_key: str) -> str:
            if not op:
                return "-"
            status = op.get("status", "?")
            recall = op.get(recall_key)
            issue_count = len(
                (op.get("issues") or [])
                + (op.get("first_issues") or [])
                + (op.get("final_issues") or [])
            )
            recall_text = f" {recall:.0%}" if isinstance(recall, float) else ""
            return f"{status}{recall_text} ({issue_count})"

        w2l = {op["target"]: op for op in case.get("w2l", [])}
        w2w = {op["path"]: op for op in case.get("w2w", [])}
        lines.append(
            "| "
            + " | ".join(
                [
                    _status_label(case),
                    case["relative_path"].replace("|", "\\|"),
                    case.get("input_kind", "-"),
                    metric_text,
                    op_text(w2l.get("ieee"), "pdf_text_recall"),
                    op_text(w2l.get("springer"), "pdf_text_recall"),
                    op_text(w2w.get("ieee_to_springer"), "final_text_recall"),
                    op_text(w2w.get("springer_to_ieee"), "final_text_recall"),
                ]
            )
            + " |"
        )

    lines += ["", "## Errors And Warnings", ""]
    for case in cases:
        label = _status_label(case)
        if label == "PASS":
            continue
        lines.append(f"### {label}: {case['relative_path']}")
        if case.get("input_error"):
            lines.append(f"- Input: `{case['input_error']}`")
        for op in (case.get("w2l") or []) + (case.get("w2w") or []):
            issues = (
                (op.get("issues") or [])
                + (op.get("first_issues") or [])
                + (op.get("final_issues") or [])
            )
            if op.get("status") != "passed" or issues:
                name = op.get("target") or op.get("path")
                lines.append(
                    f"- `{name}`: status={op.get('status')}; "
                    f"issues={issues}; error={op.get('error', '')}"
                )
        lines.append("")
    (output_dir / "large_scale_validation.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def run(output_dir: Path, limit: int | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    word_files = sorted(
        path
        for path in INPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix.casefold() in WORD_EXTENSIONS
    )
    if limit:
        word_files = word_files[:limit]

    results: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_root": str(INPUT_ROOT),
        "output_root": str(output_dir),
        "cases": [],
    }

    for index, input_path in enumerate(word_files, start=1):
        relative = input_path.relative_to(ROOT)
        case_dir = output_dir / f"{index:02d}_{_safe_name(input_path)}"
        case_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[{index}/{len(word_files)}] {relative}", flush=True)
        case: dict[str, Any] = {
            "relative_path": str(relative),
            "size_bytes": input_path.stat().st_size,
            "input_status": "invalid",
            "w2l": [],
            "w2w": [],
        }
        try:
            source_ir = _parse_word(input_path, case_dir / "source_images")
            source_metrics = _ir_metrics(source_ir)
            source_text = _ir_text(source_ir)
            case.update(
                {
                    "input_status": "valid",
                    "input_kind": _classify_input(input_path, source_metrics),
                    "source_metrics": source_metrics,
                }
            )
        except Exception as exc:
            case["input_error"] = f"{type(exc).__name__}: {exc}"
            case["input_traceback"] = traceback.format_exc()[-5000:]
            results["cases"].append(case)
            _write_reports(results, output_dir)
            continue

        for target in ("ieee", "springer"):
            print(f"  W2L -> {target}", flush=True)
            op = _run_w2l(
                input_path,
                source_metrics,
                source_text,
                target,
                case_dir / f"w2l_{target}",
            )
            case["w2l"].append(op)
            _write_reports(results | {"cases": results["cases"] + [case]}, output_dir)

        for first_target, second_target in (
            ("ieee", "springer"),
            ("springer", "ieee"),
        ):
            print(f"  W2W -> {first_target} -> {second_target}", flush=True)
            op = _run_w2w_roundtrip(
                source_ir,
                source_metrics,
                source_text,
                first_target,
                second_target,
                case_dir / f"w2w_{first_target}_{second_target}",
            )
            case["w2w"].append(op)
            _write_reports(results | {"cases": results["cases"] + [case]}, output_dir)

        results["cases"].append(case)
        _write_reports(results, output_dir)

    _write_reports(results, output_dir)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "outputs" / "large_scale_validation"),
    )
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    results = run(Path(args.output_dir).resolve(), limit=args.limit)
    summary = Counter(_status_label(case) for case in results["cases"])
    print("\nSummary:", dict(summary))
    return 0 if summary["FAIL"] == 0 and summary["INPUT_ERROR"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
