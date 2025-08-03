import pytest
import json
from src.data_store.manager import DataStoreManager

@pytest.fixture
def manager(tmp_path):
    path = tmp_path / "test.json"
    m = DataStoreManager()
    m.storage_path = str(path)
    # Clear any existing data for clean test
    m.graph.clear()
    m.nodes.clear()
    return m

def test_add_nodes(manager):
    nodes = [{"name": "test", "type": "node", "facts": ["fact1"]}]
    added = manager.add_nodes(nodes)
    assert len(added) == 1
    assert manager.nodes[0] == nodes[0]

def test_add_links(manager):
    manager.add_nodes([{"name": "a", "type": "node", "facts": []}, {"name": "b", "type": "node", "facts": []}])
    links = [{"from": "a", "to": "b", "relation": "rel"}]
    added = manager.add_links(links)
    assert len(added) == 1
    assert manager.graph.has_edge("a", "b")

def test_add_facts(manager):
    manager.add_nodes([{"name": "test", "type": "node", "facts": []}])
    facts = [{"node_name": "test", "facts": ["newfact"]}]
    added = manager.add_facts(facts)
    assert added[0]['added_facts'] == ["newfact"]
    assert "newfact" in manager.nodes[0]['facts']

def test_remove_nodes(manager):
    manager.add_nodes([{"name": "test", "type": "node", "facts": []}])
    manager.remove_nodes(["test"])
    assert len(manager.nodes) == 0

def test_search_nodes(manager):
    manager.add_nodes([{"name": "test", "type": "node", "facts": ["query fact"]}])
    result = manager.search_nodes("query")
    assert len(result['nodes']) == 1

def test_save_load(manager):
    manager.add_nodes([{"name": "test", "type": "node", "facts": []}])
    manager.save()
    new_manager = DataStoreManager()
    new_manager.storage_path = manager.storage_path
    new_manager.load()
    assert len(new_manager.nodes) == 1
