import re
from dataclasses import dataclass
from pathlib import Path


TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "we",
    "what",
    "with",
}


@dataclass(frozen=True)
class RetrievedChunk:
    citation: str
    source_path: str
    text: str
    score: float


class LocalFileRetriever:
    def __init__(self, source_dir: str | Path):
        self._source_dir = Path(source_dir)
        self._chunks = self._build_chunks()

    def search(self, query: str, *, top_k: int) -> list[RetrievedChunk]:
        query_terms = _terms(query)
        if not query_terms:
            return []

        ranked: list[RetrievedChunk] = []
        for chunk in self._chunks:
            score = _score(query_terms, _terms(chunk.text))
            if score <= 0:
                continue
            ranked.append(
                RetrievedChunk(
                    citation=chunk.citation,
                    source_path=chunk.source_path,
                    text=chunk.text,
                    score=score,
                )
            )

        ranked.sort(key=lambda item: (-item.score, item.citation))
        return ranked[:top_k]

    def _build_chunks(self) -> list[RetrievedChunk]:
        if not self._source_dir.exists():
            return []

        chunks: list[RetrievedChunk] = []
        for path in sorted(self._source_dir.rglob("*")):
            if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
                continue

            relative_path = path.relative_to(self._source_dir).as_posix()
            for index, text in enumerate(_split_into_chunks(path.read_text().strip()), start=1):
                chunks.append(
                    RetrievedChunk(
                        citation=f"{relative_path}:chunk-{index:02d}",
                        source_path=relative_path,
                        text=text,
                        score=0.0,
                    )
                )
        return chunks


def _split_into_chunks(text: str) -> list[str]:
    raw_parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    for part in raw_parts:
        cleaned = " ".join(
            line.strip().lstrip("#").strip() for line in part.splitlines() if line.strip()
        )
        if len(cleaned) >= 20:
            chunks.append(cleaned)
    return chunks


def _terms(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_RE.findall(text.lower())
        if token not in STOPWORDS and len(token) > 1
    }


def _score(query_terms: set[str], chunk_terms: set[str]) -> float:
    if not query_terms or not chunk_terms:
        return 0.0
    overlap = query_terms & chunk_terms
    if not overlap:
        return 0.0
    return len(overlap) / len(query_terms)
