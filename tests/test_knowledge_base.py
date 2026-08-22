from pathlib import Path

from src.knowledge_base import KnowledgeBaseLoader


def test_load_all_knowledge_base_documents():
    knowledge_base_dir = Path("knowledge-base")

    loader = KnowledgeBaseLoader(knowledge_base_dir)
    documents = loader.load_documents()

    assert len(documents) == 14


def test_current_returns_policy_metadata():
    loader = KnowledgeBaseLoader("knowledge-base")
    documents = loader.load_documents()

    document = next(
        doc
        for doc in documents
        if doc.filename == "01-returns-policy-current.md"
    )

    assert document.status == "active"
    assert document.policy_authority == "official"
    assert document.audience == "customer"
    assert document.document_id == "RET-2026-01"


def test_legacy_returns_policy_is_superseded():
    loader = KnowledgeBaseLoader("knowledge-base")
    documents = loader.load_documents()

    document = next(
        doc
        for doc in documents
        if doc.filename == "02-returns-policy-legacy.md"
    )

    assert document.status == "superseded"
    assert document.policy_authority == "official"


def test_chunks_preserve_source_metadata():
    loader = KnowledgeBaseLoader("knowledge-base")

    documents = loader.load_documents()
    chunks = loader.chunk_documents(documents)

    returns_chunks = [
        chunk
        for chunk in chunks
        if chunk.filename == "01-returns-policy-current.md"
    ]

    assert returns_chunks
    assert any(
        chunk.heading == "Standard return window"
        for chunk in returns_chunks
    )

    for chunk in returns_chunks:
        assert chunk.document_id == "RET-2026-01"
        assert chunk.metadata["status"] == "active"
        assert chunk.metadata["policy_authority"] == "official"