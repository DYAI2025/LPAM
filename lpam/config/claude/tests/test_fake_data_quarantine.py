import os
import tempfile
import json
import unittest
from plumbline_memory_graph_projection import project_graph
from plumbline_memory_schema_validator import validate_json_artifact

class TestFakeDataQuarantine(unittest.TestCase):
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

    def test_fake_node_is_excluded_from_productive_graph(self):
        # Create a real node and edge (eligible)
        self.create_artifact('graph_node', 'real_node1')
        self.create_artifact('graph_edge', 'real_edge1')
        # Create a fake node (ineligible)
        self.create_artifact('graph_node', 'fake_node1', {'eligible_for_global_projection': False})
        # Create a fake edge (ineligible)
        self.create_artifact('graph_edge', 'fake_edge1', {'eligible_for_global_projection': False})

        result = project_graph(self.data_dir, os.path.join(self.test_dir, 'output.json'))
        # Check that the fake artifacts are excluded
        self.assertEqual(result['report']['total_nodes'], 2)
        self.assertEqual(result['report']['productive_nodes'], 1)  # only real_node1
        self.assertEqual(result['report']['total_edges'], 2)
        self.assertEqual(result['report']['productive_edges'], 1)  # only real_edge1
        self.assertEqual(result['report']['excluded_nodes'], 1)
        self.assertEqual(result['report']['excluded_edges'], 1)

    def test_fake_artifacts_are_valid_schema(self):
        # Create a fake node and edge and validate their schema
        node_path = self.create_artifact('graph_node', 'fake_node1', {'eligible_for_global_projection': False})
        edge_path = self.create_artifact('graph_edge', 'fake_edge1', {'eligible_for_global_projection': False})

        # Validate the fake node
        is_valid_node, error_node = validate_json_artifact(node_path)
        self.assertTrue(is_valid_node, f"Fake node should be valid: {error_node}")

        # Validate the fake edge
        is_valid_edge, error_edge = validate_json_artifact(edge_path)
        self.assertTrue(is_valid_edge, f"Fake edge should be valid: {error_edge}")

if __name__ == '__main__':
    unittest.main()