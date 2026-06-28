import os
import tempfile
import json
import unittest
from plumbline_memory_graph_projection import project_graph

class TestPlumblineMemoryGraphProjection(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        # Create subdirectories for graph_node and graph_edge
        os.makedirs(os.path.join(self.data_dir, 'graph_node'), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'graph_edge'), exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def create_artifact(self, artifact_type, artifact_id, data=None):
        """Helper to create a valid artifact file."""
        if data is None:
            data = {}
        # Base data for each artifact type
        base_data = {
            'graph_node': {
                'id': artifact_id,
                'timestamp': '2026-06-25T12:00:00Z',
                'loop_run_id': 'loop_run_1',
                'label': 'Test Node',
                'type': 'test_type',
                'properties': {'prop': 'value'},
                'eligible_for_global_projection': True
            },
            'graph_edge': {
                'id': artifact_id,
                'timestamp': '2026-06-25T12:00:00Z',
                'loop_run_id': 'loop_run_1',
                'source_id': 'node1',
                'target_id': 'node2',
                'label': 'Test Edge',
                'type': 'test_type',
                'properties': {'prop': 'value'},
                'eligible_for_global_projection': True
            }
        }[artifact_type]
        base_data.update(data)
        filepath = os.path.join(self.data_dir, artifact_type, f'{artifact_type}_{artifact_id}.json')
        with open(filepath, 'w') as f:
            json.dump(base_data, f)
        return filepath

    def test_project_graph_with_all_eligible(self):
        # Create one eligible node and one eligible edge
        self.create_artifact('graph_node', 'node1')
        self.create_artifact('graph_edge', 'edge1')

        result = project_graph(self.data_dir, os.path.join(self.test_dir, 'output.json'))
        self.assertEqual(result['report']['total_nodes'], 1)
        self.assertEqual(result['report']['productive_nodes'], 1)
        self.assertEqual(result['report']['total_edges'], 1)
        self.assertEqual(result['report']['productive_edges'], 1)
        self.assertEqual(result['report']['excluded_nodes'], 0)
        self.assertEqual(result['report']['excluded_edges'], 0)

    def test_project_graph_with_fake_artifacts(self):
        # Create one eligible node and one fake node (ineligible)
        self.create_artifact('graph_node', 'node1')  # eligible by default
        self.create_artifact('graph_node', 'fake_node1', {'eligible_for_global_projection': False})
        # Create one eligible edge and one fake edge
        self.create_artifact('graph_edge', 'edge1')
        self.create_artifact('graph_edge', 'fake_edge1', {'eligible_for_global_projection': False})

        result = project_graph(self.data_dir, os.path.join(self.test_dir, 'output.json'))
        self.assertEqual(result['report']['total_nodes'], 2)
        self.assertEqual(result['report']['productive_nodes'], 1)
        self.assertEqual(result['report']['total_edges'], 2)
        self.assertEqual(result['report']['productive_edges'], 1)
        self.assertEqual(result['report']['excluded_nodes'], 1)
        self.assertEqual(result['report']['excluded_edges'], 1)

    def test_project_graph_with_no_artifacts(self):
        result = project_graph(self.data_dir, os.path.join(self.test_dir, 'output.json'))
        self.assertEqual(result['report']['total_nodes'], 0)
        self.assertEqual(result['report']['productive_nodes'], 0)
        self.assertEqual(result['report']['total_edges'], 0)
        self.assertEqual(result['report']['productive_edges'], 0)
        self.assertEqual(result['report']['excluded_nodes'], 0)
        self.assertEqual(result['report']['excluded_edges'], 0)

if __name__ == '__main__':
    unittest.main()