"""Drift check for the generated TypeScript types file.

Reimports the generator each test run, regenerates the file in memory, and
asserts byte-for-byte equality against the committed
`apps/web/app/admin/soundsystem/_lib/generated-inference-types.ts`. If this
fails, regenerate locally:

    cd services/soundsystem-inference
    python scripts/generate_ts_types.py

The pytest message shows a short diff so the reason is visible immediately.
"""

from __future__ import annotations

from difflib import unified_diff

import pytest

from scripts.generate_ts_types import OUTPUT_PATH, generate


def test_generator_output_is_deterministic_across_runs() -> None:
    first = generate()
    second = generate()
    assert first == second


def test_generated_ts_types_match_committed_file() -> None:
    expected = generate()
    if not OUTPUT_PATH.exists():
        pytest.fail(
            f"{OUTPUT_PATH} does not exist. Run `python scripts/generate_ts_types.py` to create it."
        )
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual == expected:
        return

    diff = list(
        unified_diff(
            actual.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile="committed",
            tofile="generated",
            n=2,
        )
    )
    head = "".join(diff[:40])
    pytest.fail(
        "Generated TS types are stale. Run "
        "`python scripts/generate_ts_types.py` from "
        "services/soundsystem-inference to refresh.\n\n"
        "First lines of diff:\n" + head
    )
