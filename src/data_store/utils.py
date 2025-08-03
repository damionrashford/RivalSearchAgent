from typing import Dict

def validate_node_data(node: Dict):
    required = ['name', 'type', 'facts']
    for key in required:
        if key not in node:
            raise ValueError(f"Missing {key} in node data")
    if not isinstance(node['facts'], list):
        raise ValueError("facts must be list")
