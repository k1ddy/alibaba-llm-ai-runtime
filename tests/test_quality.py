from pathlib import Path

from alibaba_llm_ai_runtime.config import Settings
from alibaba_llm_ai_runtime.quality import evaluate_scenarios, load_scenarios


def test_evaluate_scenarios_generates_summary(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scenarios = load_scenarios(repo_root / "quality" / "golden_cases.json")
    settings = Settings(
        knowledge_source_dir=str(repo_root / "knowledge" / "source"),
        tool_audit_log_path=str(tmp_path / "tool-events.jsonl"),
    )

    summary = evaluate_scenarios(
        scenarios=scenarios,
        settings=settings,
        output_dir=tmp_path / "quality-run",
    )

    assert summary["all_passed"] is True
    assert summary["scenario_count"] == 4
    assert summary["failed_steps"] == 0
    assert (tmp_path / "quality-run" / "summary.json").exists()
    assert (tmp_path / "quality-run" / "brief.md").exists()
