"""Anti-sameness and eval-gate checks.

These fail on a fresh clone on purpose:
  - MAKE_IT_YOURS.md still has TODO markers
  - the eval set is smaller than the gate requires

CI runs them in the job that is allowed to be red until you finish.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_make_it_yours_has_no_todo():
    text = (ROOT / "MAKE_IT_YOURS.md").read_text()
    leftovers = [
        f"line {i}: {line.strip()}"
        for i, line in enumerate(text.splitlines(), start=1)
        if re.search(r"\bTODO\b", line)
    ]
    assert not leftovers, "MAKE_IT_YOURS.md still has TODO entries:\n" + "\n".join(leftovers)


def test_eval_gate_passes():
    """Requires >= 20 cases and a feature that beats the baseline.

    On a fresh clone this fails. That is the assignment, printed as a test.
    """
    result = subprocess.run(
        [sys.executable, "-m", "evals.run", "--gate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "LLM_PROVIDER": "stub"},
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
