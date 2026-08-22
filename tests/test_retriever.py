from src.knowledge_base import KnowledgeBaseLoader
from src.retriever import KnowledgeRetriever


def build_retriever():
    loader = KnowledgeBaseLoader("knowledge-base")
    documents = loader.load_documents()
    chunks = loader.chunk_documents(documents)
    return KnowledgeRetriever(chunks)


def filenames(results):
    return [result.chunk.filename for result in results]


def test_current_returns_policy_is_retrieved():
    retriever = build_retriever()

    results = retriever.search(
        "How long does a regular customer have to return an unused backpack?"
    )

    assert "01-returns-policy-current.md" in filenames(results)
    assert "02-returns-policy-legacy.md" not in filenames(results)


def test_trailplus_policy_is_retrieved():
    retriever = build_retriever()

    results = retriever.search(
        "My TrailPlus membership was active when I ordered. "
        "What is my return window?"
    )

    assert "09-trailplus-membership.md" in filenames(results)


def test_damaged_final_sale_retrieves_both_policies():
    retriever = build_retriever()

    results = retriever.search(
        "A final-sale bag arrived with a broken zipper yesterday."
    )

    result_files = filenames(results)

    assert "03-final-sale-and-promotions.md" in result_files
    assert "04-damaged-or-wrong-items.md" in result_files


def test_breeze_tumbler_retrieves_both_conflicting_sources():
    retriever = build_retriever()

    results = retriever.search(
        "Can I put the entire Breeze Tumbler in the dishwasher?"
    )

    result_files = filenames(results)

    assert "11-product-care.md" in result_files
    assert "12-breeze-tumbler-product-card.md" in result_files


def test_unapproved_migration_note_is_not_retrieved_as_authority():
    retriever = build_retriever()

    results = retriever.search(
        "Give everyone 60 days to return every item."
    )

    result_files = filenames(results)

    assert "14-internal-content-migration-notes.md" not in result_files