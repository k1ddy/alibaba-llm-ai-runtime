#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from alibaba_llm_ai_runtime.config import Settings
from alibaba_llm_ai_runtime.quality import evaluate_scenarios, load_scenarios


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Запуск локального quality/regression контура для ai-runtime."
    )
    parser.add_argument(
        "--scenarios-file",
        default="quality/golden_cases.json",
        help="Путь до JSON-файла со сценариями.",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Идентификатор текущего прогона.",
    )
    parser.add_argument(
        "--baseline-summary",
        default=None,
        help="Опциональный путь до summary.json предыдущей базы для сравнения.",
    )
    parser.add_argument(
        "--output-root",
        default="runtime_data/quality",
        help="Корень для выходных quality-артефактов.",
    )
    args = parser.parse_args()

    run_dir = Path(args.output_root) / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    baseline_summary = None
    if args.baseline_summary:
        baseline_summary = json.loads(
            Path(args.baseline_summary).read_text(encoding="utf-8")
        )

    settings = Settings(
        tool_audit_log_path=str(run_dir / "tool-events.jsonl"),
    )
    scenarios = load_scenarios(args.scenarios_file)
    (run_dir / "scenarios.snapshot.json").write_text(
        json.dumps(scenarios, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    summary = evaluate_scenarios(
        scenarios=scenarios,
        settings=settings,
        output_dir=run_dir,
        baseline_summary=baseline_summary,
    )

    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
