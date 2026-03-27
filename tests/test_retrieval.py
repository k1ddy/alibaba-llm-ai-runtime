from pathlib import Path

from alibaba_llm_ai_runtime.retrieval import LocalFileRetriever


def test_local_file_retriever_returns_ranked_chunks(tmp_path: Path) -> None:
    source_dir = tmp_path / "knowledge" / "source"
    source_dir.mkdir(parents=True)
    (source_dir / "demo.md").write_text(
        "# Demo\n\n"
        "The bootstrap repository owns Terraform and cloud foundation resources.\n\n"
        "The runtime repository owns FastAPI request handling.\n"
    )

    retriever = LocalFileRetriever(source_dir)

    hits = retriever.search(
        "Which repository owns cloud foundation resources?",
        top_k=1,
    )

    assert len(hits) == 1
    assert hits[0].citation == "demo.md:chunk-01"
    assert "cloud foundation resources" in hits[0].text
