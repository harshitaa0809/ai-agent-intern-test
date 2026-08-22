from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    document_id: str
    title: str
    status: str
    effective_date: str
    last_reviewed: str
    audience: str
    policy_authority: str
    content: str
    filename: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    document_id: str
    filename: str
    title: str
    heading: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)