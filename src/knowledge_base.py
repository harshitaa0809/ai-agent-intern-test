from pathlib import Path
from typing import Any

import yaml

from .models import Document, DocumentChunk


class KnowledgeBaseLoader:
    """Load and parse the supplied Markdown knowledge base."""

    def __init__(self, knowledge_base_dir: str | Path):
        self.knowledge_base_dir = Path(knowledge_base_dir)

    def load_documents(self) -> list[Document]:
        documents = []

        for path in sorted(self.knowledge_base_dir.glob("*.md")):
            documents.append(self._load_document(path))

        return documents

    def _load_document(self, path: Path) -> Document:
        text = path.read_text(encoding="utf-8")

        metadata, content = self._parse_front_matter(text)

        required_fields = [
            "document_id",
            "title",
            "status",
            "effective_date",
            "last_reviewed",
            "audience",
            "policy_authority",
        ]

        missing = [field for field in required_fields if field not in metadata]

        if missing:
            raise ValueError(
                f"{path.name} is missing required metadata: {', '.join(missing)}"
            )

        return Document(
            document_id=str(metadata["document_id"]),
            title=str(metadata["title"]),
            status=str(metadata["status"]),
            effective_date=str(metadata["effective_date"]),
            last_reviewed=str(metadata["last_reviewed"]),
            audience=str(metadata["audience"]),
            policy_authority=str(metadata["policy_authority"]),
            content=content.strip(),
            filename=path.name,
            metadata=metadata,
        )

    @staticmethod
    def _parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
        if not text.startswith("---"):
            raise ValueError("Markdown document does not contain YAML front matter.")

        parts = text.split("---", 2)

        if len(parts) != 3:
            raise ValueError("Invalid YAML front matter.")

        metadata_text = parts[1]
        content = parts[2]

        metadata = yaml.safe_load(metadata_text) or {}

        if not isinstance(metadata, dict):
            raise ValueError("Document metadata must be a YAML mapping.")

        return metadata, content

    def chunk_documents(
        self,
        documents: list[Document],
    ) -> list[DocumentChunk]:
        chunks = []

        for document in documents:
            chunks.extend(self._chunk_document(document))

        return chunks

    def _chunk_document(self, document: Document) -> list[DocumentChunk]:
        sections = self._split_into_sections(document.content)

        chunks = []

        for heading, content in sections:
            if not content.strip():
                continue

            chunks.append(
                DocumentChunk(
                    document_id=document.document_id,
                    filename=document.filename,
                    title=document.title,
                    heading=heading,
                    content=content.strip(),
                    metadata=document.metadata.copy(),
                )
            )

        return chunks

    @staticmethod
    def _split_into_sections(content: str) -> list[tuple[str, str]]:
        lines = content.splitlines()

        sections: list[tuple[str, str]] = []
        current_heading = "Introduction"
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("## "):
                if current_lines:
                    sections.append(
                        (
                            current_heading,
                            "\n".join(current_lines).strip(),
                        )
                    )

                current_heading = stripped[3:].strip()
                current_lines = []
            elif stripped.startswith("# "):
                continue
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(
                (
                    current_heading,
                    "\n".join(current_lines).strip(),
                )
            )

        return sections