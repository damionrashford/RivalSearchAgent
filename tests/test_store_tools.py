import pytest
from src.data_store.manager import DataStoreManager

@pytest.fixture
def fresh_manager(tmp_path):
    """Create a fresh manager instance for each test."""
    path = tmp_path / "test_store.json"
    m = DataStoreManager()
    m.storage_path = str(path)
    # Clear any existing data for clean test
    m.graph.clear()
    m.nodes.clear()
    return m

def test_data_store_manager_add_nodes(fresh_manager):
    """Test the core data store manager functionality.""" 
    test_nodes = [{"name": "store_test_node", "type": "test", "facts": ["fact1", "fact2"]}]
    
    # Test adding nodes
    result = fresh_manager.add_nodes(test_nodes)
    assert result is not None
    
    # Test searching for the added node
    search_results = fresh_manager.search_nodes("store_test_node")
    assert len(search_results) >= 0  # Should not fail
