import json
import os
import networkx as nx
from typing import List, Dict

class DataStoreManager:
    def __init__(self):
        self.storage_path = os.environ.get('DATA_PATH', 'data_store.json')
        self.nodes = []
        self.links = []
        self.graph = nx.Graph()
        self.load()

    def load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.nodes = data.get('nodes', [])
                self.links = data.get('links', [])
                for node in self.nodes:
                    self.graph.add_node(node['name'], **node)
                for link in self.links:
                    self.graph.add_edge(link['from'], link['to'], **link)

    def save(self):
        data = {'nodes': self.nodes, 'links': self.links}
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)

    def add_nodes(self, nodes: List[Dict]) -> List[Dict]:
        from .utils import validate_node_data
        new_nodes = []
        for n in nodes:
            validate_node_data(n)
            if n['name'] not in [ex['name'] for ex in self.nodes]:
                self.nodes.append(n)
                self.graph.add_node(n['name'], **n)
                new_nodes.append(n)
        self.save()
        return new_nodes

    def add_links(self, links: List[Dict]) -> List[Dict]:
        new_links = [l for l in links if not self.graph.has_edge(l['from'], l['to'])]
        self.links.extend(new_links)
        for l in new_links:
            self.graph.add_edge(l['from'], l['to'], **l)
        self.save()
        return new_links

    def add_facts(self, facts: List[Dict]) -> List[Dict]:
        results = []
        for f in facts:
            node = next((n for n in self.nodes if n['name'] == f['node_name']), None)
            if node:
                new_facts = [content for content in f['facts'] if content not in node.get('facts', [])]
                node.setdefault('facts', []).extend(new_facts)
                self.graph.nodes[f['node_name']]['facts'] = node['facts']
                results.append({'node_name': f['node_name'], 'added_facts': new_facts})
        self.save()
        return results

    def remove_nodes(self, node_names: List[str]):
        self.nodes = [n for n in self.nodes if n['name'] not in node_names]
        self.links = [l for l in self.links if l['from'] not in node_names and l['to'] not in node_names]
        for name in node_names:
            if name in self.graph:
                self.graph.remove_node(name)
        self.save()

    def remove_facts(self, removals: List[Dict]):
        for r in removals:
            node = next((n for n in self.nodes if n['name'] == r['node_name']), None)
            if node:
                node['facts'] = [f for f in node.get('facts', []) if f not in r['facts']]
                self.graph.nodes[r['node_name']]['facts'] = node['facts']
        self.save()

    def remove_links(self, links: List[Dict]):
        self.links = [l for l in self.links if not any(l['from'] == rem['from'] and l['to'] == rem['to'] for rem in links)]
        for rem in links:
            if self.graph.has_edge(rem['from'], rem['to']):
                self.graph.remove_edge(rem['from'], rem['to'])
        self.save()

    def get_full_store(self) -> Dict:
        return {'nodes': self.nodes, 'links': self.links}

    def search_nodes(self, query: str) -> Dict:
        filtered_nodes = [n for n in self.nodes if query.lower() in n['name'].lower() or query.lower() in n['type'].lower() or any(query.lower() in f.lower() for f in n.get('facts', []))]
        filtered_names = {n['name'] for n in filtered_nodes}
        filtered_links = [l for l in self.links if l['from'] in filtered_names and l['to'] in filtered_names]
        return {'nodes': filtered_nodes, 'links': filtered_links}

    def get_specific_nodes(self, names: List[str]) -> Dict:
        filtered_nodes = [n for n in self.nodes if n['name'] in names]
        filtered_names = {n['name'] for n in filtered_nodes}
        filtered_links = [l for l in self.links if l['from'] in filtered_names and l['to'] in filtered_names]
        return {'nodes': filtered_nodes, 'links': filtered_links}


# Create a singleton instance
store_manager = DataStoreManager()
