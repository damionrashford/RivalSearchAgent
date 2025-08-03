import pytest
from src.data_store.utils import validate_node_data

def test_validate_node_data():
    valid_node = {"name": "test", "type": "node", "facts": ["fact1"]}
    validate_node_data(valid_node)  # Should pass
    invalid_node = {"name": "test", "type": "node"}
    with pytest.raises(ValueError):
        validate_node_data(invalid_node)