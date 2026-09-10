"""Eval harness for the LLM feature.

    python -m evals.run              # feature, against cases.jsonl
    python -m evals.run --baseline   # dumb non-LLM approach
    python -m evals.run --gate       # exit 1 until the set is big enough
                                     # and beats the baseline

A fresh clone has a handful of cases so you can see the harness work. That is
not an eval set. The gate fails until you have at least MIN_CASES labeled
examples and your feature's pass rate beats the baseline on the same file.

The stub provider makes CI green for "harness runs." It is not evidence that
your feature works. Run against a real free-tier provider before you claim a
number in your README.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.feature import FeatureError, SnippetFacts, extract_facts  # noqa: E402
from evals.baseline import baseline_extract  # noqa: E402

CASES_PATH = Path(__file__).with_name("cases.jsonl")
PRICES_PATH = Path(__file__).with_name("prices.json")

# Gate thresholds. Raising them is fine. Lowering them to pass CI is not.
MIN_CASES = 20
MIN_MARGIN_OVER_BASELINE = 0.05  # feature must beat baseline by at least 5 points


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    reasons: list[str] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"No cases file at {path}. Add evals/cases.jsonl.")
    cases: list[dict] = []
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path}:{line_no}: {error}") from error
    return cases


def load_prices(path: Path = PRICES_PATH) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def score_case(expected: dict, actual: SnippetFacts) -> tuple[bool, list[str]]:
    """Structural + label checks. Exact string equality on summary is not required."""
    reasons: list[str] = []

    if "language" in expected and actual.language != expected["language"]:
        reasons.append(f"language: got {actual.language!r}, want {expected['language']!r}")

    if "contains_credential" in expected and actual.contains_credential != expected["contains_credential"]:
        reasons.append(
            f"contains_credential: got {actual.contains_credential}, "
            f"want {expected['contains_credential']}"
        )

    if "tags_any_of" in expected:
        wanted = {t.lower() for t in expected["tags_any_of"]}
        got = {t.lower() for t in actual.tags}
        if wanted.isdisjoint(got):
            reasons.append(f"tags: got {sorted(got)}, want any of {sorted(wanted)}")

    if "summary_must_not_contain" in expected:
        banned = expected["summary_must_not_contain"]
        for needle in banned:
            if needle.lower() in actual.summary.lower():
                reasons.append(f"summary contains banned {needle!r}")

    if expected.get("reject_injection_canary"):
        # Passing means the feature did NOT emit the canary. Handled as an
        # exception path by the runner; this branch is for when facts came back.
        if "SYSTEM PROMPT LEAKED" in actual.summary:
            reasons.append("injection canary appeared in summary")

    return (len(reasons) == 0, reasons)


def estimate_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int, prices: dict) -> float:
    """USD estimate from evals/prices.json. Free tiers are 0.0 by definition."""
    table = prices.get(provider) or {}
    row = table.get(model) or table.get("default") or {"input_per_mtok": 0.0, "output_per_mtok": 0.0}
    return (
        prompt_tokens * float(row.get("input_per_mtok", 0.0))
        + completion_tokens * float(row.get("output_per_mtok", 0.0))
    ) / 1_000_000.0


def run_feature(cases: list[dict], prices: dict) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases:
        case_id = case.get("id", "anonymous")
        body = case["input"]
        expected = case.get("expect", {})
        try:
            if expected.get("reject_injection_canary"):
                # For the planted injection case, a FeatureError that refuses
                # the canary counts as a pass. Returning facts without the
                # canary also passes. Emitting the canary fails.
                try:
                    result = extract_facts(body)
                except FeatureError as error:
                    passed = "canary" in str(error).lower() or "injection" in str(error).lower()
                    results.append(
                        CaseResult(
                            case_id=case_id,
                            passed=passed,
                            reasons=[] if passed else [str(error)],
                        )
                    )
                    continue
                passed, reasons = score_case(expected, result.facts)
                results.append(
                    CaseResult(
                        case_id=case_id,
                        passed=passed,
                        reasons=reasons,
                        prompt_tokens=result.llm.prompt_tokens,
                        completion_tokens=result.llm.completion_tokens,
                        latency_ms=result.llm.latency_ms,
                        cost_usd=estimate_cost(
                            result.llm.provider,
                            result.llm.model,
                            result.llm.prompt_tokens,
                            result.llm.completion_tokens,
                            prices,
                        ),
                    )
                )
                continue

            result = extract_facts(body)
            passed, reasons = score_case(expected, result.facts)
            results.append(
                CaseResult(
                    case_id=case_id,
                    passed=passed,
                    reasons=reasons,
                    prompt_tokens=result.llm.prompt_tokens,
                    completion_tokens=result.llm.completion_tokens,
                    latency_ms=result.llm.latency_ms,
                    cost_usd=estimate_cost(
                        result.llm.provider,
                        result.llm.model,
                        result.llm.prompt_tokens,
                        result.llm.completion_tokens,
                        prices,
                    ),
                )
            )
        except FeatureError as error:
            results.append(CaseResult(case_id=case_id, passed=False, reasons=[str(error)]))
        except Exception as error:  # noqa: BLE001 — harness must not die on one case
            results.append(CaseResult(case_id=case_id, passed=False, reasons=[f"uncaught: {error}"]))
    return results


def run_baseline(cases: list[dict]) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases:
        case_id = case.get("id", "anonymous")
        started = time.perf_counter()
        try:
            facts = baseline_extract(case["input"])
            passed, reasons = score_case(case.get("expect", {}), facts)
            results.append(
                CaseResult(
                    case_id=case_id,
                    passed=passed,
                    reasons=reasons,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
            )
        except Exception as error:  # noqa: BLE001
            results.append(CaseResult(case_id=case_id, passed=False, reasons=[str(error)]))
    return results


def summarize(label: str, results: list[CaseResult]) -> dict:
    n = len(results)
    passed = sum(1 for r in results if r.passed)
    rate = (passed / n) if n else 0.0
    latencies = [r.latency_ms for r in results if r.latency_ms > 0]
    report = {
        "label": label,
        "cases": n,
        "passed": passed,
        "pass_rate": round(rate, 4),
        "total_prompt_tokens": sum(r.prompt_tokens for r in results),
        "total_completion_tokens": sum(r.completion_tokens for r in results),
        "total_cost_usd": round(sum(r.cost_usd for r in results), 6),
        "latency_p50_ms": round(statistics.median(latencies), 2) if latencies else None,
        "latency_p95_ms": round(sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)], 2)
        if latencies
        else None,
    }
    print(json.dumps(report, indent=2))
    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        detail = "" if result.passed else " — " + "; ".join(result.reasons)
        print(f"  {mark}  {result.case_id}{detail}")
    return report


def gate(feature_report: dict, baseline_report: dict) -> int:
    """Exit 0 only when the set is large enough and beats the baseline."""
    failures: list[str] = []
    if feature_report["cases"] < MIN_CASES:
        failures.append(
            f"only {feature_report['cases']} cases; need at least {MIN_CASES}. "
            "A handful of seed cases proves the harness works, not the feature."
        )
    margin = feature_report["pass_rate"] - baseline_report["pass_rate"]
    if feature_report["cases"] >= MIN_CASES and margin < MIN_MARGIN_OVER_BASELINE:
        failures.append(
            f"feature pass rate {feature_report['pass_rate']:.0%} does not beat "
            f"baseline {baseline_report['pass_rate']:.0%} by {MIN_MARGIN_OVER_BASELINE:.0%}. "
            "If a regex matches the LLM, the LLM is the wrong tool — say so in MAKE_IT_YOURS.md."
        )
    if failures:
        print("\nGATE FAILED (expected on a fresh clone):")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("\nGATE PASSED.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true", help="Score the non-LLM baseline only.")
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Run feature and baseline, then apply the size/margin gate.",
    )
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    args = parser.parse_args(argv)

    cases = load_cases(args.cases)
    prices = load_prices()

    if args.baseline:
        summarize("baseline", run_baseline(cases))
        return 0

    if args.gate:
        feature_report = summarize("feature", run_feature(cases, prices))
        baseline_report = summarize("baseline", run_baseline(cases))
        return gate(feature_report, baseline_report)

    summarize("feature", run_feature(cases, prices))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
