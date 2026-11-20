import os

from app.ingest import ingest
from app.store import Store

DOCS = os.path.join(os.path.dirname(__file__), '..', 'sample_docs')


def test_manual_is_split_by_section_with_pages():
    chunks, title, pages = ingest(os.path.join(DOCS, 'Solvane_SV-10_Battery_Manual.pdf'), 'manual')
    assert title == 'SV-10 Home Battery Manual'
    assert pages == 4
    sections = {c.section for c in chunks}
    assert '7. Error codes' in sections
    errors = [c for c in chunks if c.section == '7. Error codes']
    assert all(c.page == 3 for c in errors)
    assert any('E08' in c.text for c in errors)


def test_running_headers_and_footers_are_removed():
    chunks, _, _ = ingest(os.path.join(DOCS, 'Solvane_Employee_Handbook_2026.pdf'), 'hb')
    assert not any('Sample document for demonstration purposes' in c.text for c in chunks)


def test_keyword_search_finds_exact_error_code(tmp_path):
    store = Store(str(tmp_path))
    chunks, title, pages = ingest(os.path.join(DOCS, 'Solvane_SV-10_Battery_Manual.pdf'), 'manual')
    store.add(
        {'id': 'manual', 'title': title, 'pages': pages, 'chunks': len(chunks), 'added': 0, 'file': 'm.pdf'}, chunks
    )
    hits = store.search('error E08 fan fault', k=3)
    assert hits and 'E08' in hits[0]['text']


def test_remove_document(tmp_path):
    store = Store(str(tmp_path))
    chunks, title, pages = ingest(os.path.join(DOCS, 'Solvane_Support_and_Warranty_Policy.pdf'), 'policy')
    store.add(
        {'id': 'policy', 'title': title, 'pages': pages, 'chunks': len(chunks), 'added': 0, 'file': 'p.pdf'}, chunks
    )
    store.remove('policy')
    assert store.chunks == [] and store.docs == {}
    assert Store(str(tmp_path)).chunks == []  # persisted
