#!/usr/bin/env python3
"""Cross-platform repository safety validation for Affiliate Friction Auditor."""

from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_SUFFIXES = {".zip", ".log", ".pyc"}
FORBIDDEN_PARTS = {"__pycache__", "destination_screenshots", "screenshots"}
FORBIDDEN_PREFIXES = (".env",)
PRIVATE_EXAMPLE_MARKERS = ("nolodejesescapar.com", "nolodejesescapar")

PYTHON_TARGETS = [
    ROOT / "scripts" / "_site_config.py",
    ROOT / "scripts" / "phase0_7_destination_posts.py",
    ROOT / "scripts" / "phase0_8_opportunity_matrix.py",
    ROOT / "scripts" / "phase0_9_product_offer.py",
    ROOT / "src" / "affiliate_friction_auditor" / "__init__.py",
]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [Path(p.decode("utf-8")) for p in result.stdout.split(b"\0") if p]


def is_forbidden(path: Path) -> bool:
    posix = path.as_posix()
    if posix.startswith("outputs/") and posix != "outputs/.gitkeep":
        return True
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return True
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        return True
    return any(path.name.startswith(prefix) and path.name != ".env.example" for prefix in FORBIDDEN_PREFIXES)


def check_examples() -> list[str]:
    errors: list[str] = []
    examples = ROOT / "examples"
    for path in examples.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for marker in PRIVATE_EXAMPLE_MARKERS:
            if marker in text:
                errors.append(f"private marker {marker!r} found in {path.relative_to(ROOT)}")
    return errors


def check_python_syntax() -> list[str]:
    errors: list[str] = []
    for path in PYTHON_TARGETS:
        if not path.exists():
            errors.append(f"missing Python target: {path.relative_to(ROOT)}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(str(exc))
    return errors


def main() -> int:
    errors: list[str] = []

    forbidden = [path.as_posix() for path in tracked_files() if is_forbidden(path)]
    if forbidden:
        errors.extend(f"forbidden tracked file: {path}" for path in forbidden)

    errors.extend(check_examples())
    errors.extend(check_python_syntax())

    if errors:
        print("REPO_SAFE=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("REPO_SAFE=PASS")
    print("Tracked-file policy: PASS")
    print("Sanitized examples: PASS")
    print("Python syntax: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
