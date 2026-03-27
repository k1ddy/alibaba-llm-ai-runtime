import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from .app import create_app
from .config import Settings


def load_scenarios(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_scenarios(
    *,
    scenarios: list[dict[str, Any]],
    settings: Settings,
    output_dir: str | Path,
    baseline_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    passed_steps = 0
    failed_steps = 0

    for scenario in scenarios:
        scenario_result = _run_scenario(scenario, settings)
        passed_steps += sum(1 for step in scenario_result["steps"] if step["passed"])
        failed_steps += sum(1 for step in scenario_result["steps"] if not step["passed"])
        results.append(scenario_result)

    summary = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "scenario_count": len(results),
        "step_count": passed_steps + failed_steps,
        "passed_steps": passed_steps,
        "failed_steps": failed_steps,
        "all_passed": failed_steps == 0,
        "scenarios": results,
    }
    if baseline_summary is not None:
        summary["baseline_comparison"] = compare_to_baseline(summary, baseline_summary)

    (output_path / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (output_path / "brief.md").write_text(_render_brief(summary), encoding="utf-8")

    return summary


def compare_to_baseline(
    current_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "current_passed_steps": current_summary["passed_steps"],
        "baseline_passed_steps": baseline_summary.get("passed_steps", 0),
        "current_failed_steps": current_summary["failed_steps"],
        "baseline_failed_steps": baseline_summary.get("failed_steps", 0),
        "regressed": current_summary["failed_steps"] > baseline_summary.get("failed_steps", 0),
    }


def _run_scenario(
    scenario: dict[str, Any],
    settings: Settings,
) -> dict[str, Any]:
    scenario_settings = deepcopy(settings)
    app = create_app(scenario_settings)
    client = TestClient(app)

    step_results: list[dict[str, Any]] = []
    for index, step in enumerate(scenario["steps"], start=1):
        trace_id = step.get("trace_id") or f"{scenario['id']}-step-{index}"
        response = client.post(
            "/v1/runtime/turn",
            headers={"x-trace-id": trace_id},
            json=step["request"],
        )
        payload = response.json()
        step_results.append(
            {
                "index": index,
                "trace_id": trace_id,
                "status_code": response.status_code,
                "passed": _matches_expectation(payload, step["expect"]),
                "payload": payload,
                "expect": step["expect"],
                "failures": _collect_failures(payload, step["expect"]),
            }
        )

    return {
        "id": scenario["id"],
        "description": scenario.get("description", ""),
        "all_passed": all(step["passed"] for step in step_results),
        "steps": step_results,
    }


def _matches_expectation(payload: dict[str, Any], expect: dict[str, Any]) -> bool:
    return not _collect_failures(payload, expect)


def _collect_failures(payload: dict[str, Any], expect: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key, value in expect.items():
        if key == "response_contains":
            if value not in payload.get("response_text", ""):
                failures.append(f"response_text missing substring: {value}")
        elif key == "citations_min":
            if payload.get("citations_used", 0) < value:
                failures.append(f"citations_used < {value}")
        elif key == "tool_status":
            statuses = [item.get("status") for item in payload.get("tool_results", [])]
            if value not in statuses:
                failures.append(f"tool_status missing: {value}")
        else:
            if payload.get(key) != value:
                failures.append(f"{key} != {value!r}")
    return failures


def _render_brief(summary: dict[str, Any]) -> str:
    lines = [
        "# Quality Brief",
        "",
        f"- Сценариев: `{summary['scenario_count']}`",
        f"- Шагов: `{summary['step_count']}`",
        f"- Успешных шагов: `{summary['passed_steps']}`",
        f"- Ошибочных шагов: `{summary['failed_steps']}`",
        f"- Общий статус: `{'PASS' if summary['all_passed'] else 'FAIL'}`",
    ]

    comparison = summary.get("baseline_comparison")
    if comparison:
        lines.extend(
            [
                "",
                "## Сравнение С Базой",
                f"- Успешных шагов сейчас: `{comparison['current_passed_steps']}`",
                f"- Успешных шагов в базе: `{comparison['baseline_passed_steps']}`",
                f"- Ошибочных шагов сейчас: `{comparison['current_failed_steps']}`",
                f"- Ошибочных шагов в базе: `{comparison['baseline_failed_steps']}`",
                f"- Регрессия: `{'yes' if comparison['regressed'] else 'no'}`",
            ]
        )

    if not summary["all_passed"]:
        lines.append("")
        lines.append("## Ошибки")
        for scenario in summary["scenarios"]:
            for step in scenario["steps"]:
                if step["passed"]:
                    continue
                lines.append(
                    f"- `{scenario['id']}` step `{step['index']}`: "
                    + "; ".join(step["failures"])
                )

    lines.append("")
    return "\n".join(lines)
