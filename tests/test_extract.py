import pytest
from src.core.extract import extract_triples, extract_search_results

def test_extract_triples():
    text = "Subject predicate object. Another sentence here."
    triples = extract_triples(text)
    assert len(triples) == 2
    assert triples[0] == ("Subject", "predicate", "object.")
    assert triples[1] == ("Another", "sentence", "here.")

def test_extract_search_results():
    sample_html = """
    <div class="g">
        <h3><a href="https://example.com">Title</a></h3>
        <div class="VwiC3b">Snippet text</div>
    </div>
    """
    results = extract_search_results(sample_html, 1)
    assert len(results) == 1
    assert results[0]['title'] == "Title"
    assert results[0]['link'] == "https://example.com"
    assert results[0]['snippet'] == "Snippet text"

def test_extract_no_results():
    assert extract_search_results("<html></html>", 10) == []
