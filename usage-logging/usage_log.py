"""Append one timestamped line to a usage log. Python 3.8 or later, no dependencies.

Wiring it into your tool:

    1. Copy this file into your project next to your own code.
    2. Import it and call log_use() once per real use, at the point where the tool
       has actually done its job:

           from usage_log import log_use

           def main():
               args = parse_args()
               process(args)
               log_use("run", f"{len(args.files)} files")

    3. Set USAGE_LOG to an absolute path if you run your tool from more than one
       directory, which for a CLI tool you will:

           export USAGE_LOG="$HOME/code/mytool/usage.log"

Log it after the work succeeds, not before. A log of attempts is a different
number than a log of uses, and the claim you are making is about uses.

Do not log: secrets, tokens, passwords, API keys, email addresses, anyone else's
name, file contents, or absolute paths that expose a directory structure you
would not want public. This file ends up in a public repository. Counts, flags,
and durations are safe. "3 files" is evidence; "/Users/you/Desktop/tax-2025.pdf"
is a leak.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# USAGE_LOG wins if set. Otherwise the log sits next to this file.
LOG_PATH = Path(os.environ.get("USAGE_LOG") or Path(__file__).resolve().with_name("usage.log"))

# UTC so the format is identical in all three snippets and sorts lexicographically.
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _clean(value: object) -> str:
    """One use is one line, so tabs and newlines cannot survive in a field."""
    return " ".join(str(value).split())


def log_use(event: str = "run", detail: str = "") -> str:
    """Append '<timestamp>\\t<event>\\t<detail>' to the log. Returns the line written.

    Never raises. A broken log should not take your tool down with it, but it
    should say so on stderr rather than failing silently.
    """
    line = "{}\t{}\t{}\n".format(
        datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
        _clean(event) or "run",
        _clean(detail),
    )
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Append mode: each write lands at the end, even across concurrent runs.
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(line)
    except OSError as error:
        print(f"usage_log: could not write {LOG_PATH}: {error}", file=sys.stderr)
    return line


def count_uses() -> int:
    """How many times the tool has been used. This is <N> in your claim.

    A log that does not exist yet is zero uses, not an error.
    """
    try:
        with LOG_PATH.open(encoding="utf-8") as log_file:
            return sum(1 for line in log_file if line.strip())
    except FileNotFoundError:
        return 0
    except OSError as error:
        print(f"usage_log: could not read {LOG_PATH}: {error}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    # python3 usage_log.py [event] [detail...]
    event = sys.argv[1] if len(sys.argv) > 1 else "run"
    detail = " ".join(sys.argv[2:])
    sys.stdout.write(log_use(event, detail))
    print(f"{LOG_PATH}: {count_uses()} uses logged", file=sys.stderr)
