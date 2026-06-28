import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import os
import tempfile
import json
import unittest
from plumbline_memory_schema_validator import validate_json_artifact, validate_artifacts_in_directory

class TestPlumblineMemorySchemaValidator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        # Create subdirectories for each artifact type
        for artifact_type in ['loop_run', 'watcher_check', 'retro_record', 'memory_event', 'graph_node', 'graph_edge', 'telegram_report']:
            os.makedirs(os.path.join(self.data_dir, artifact_type), exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def create_artifact(self, artifact_type, artifact_id, data=None):
        """Helper to create a valid artifact file."""
        if data is None:
            data = {}
        # Base data for each artifact type
        base_data = {
            'loop_run': {
                'id': artifact_id,
                'timestamp': '2026-06-25T12:00:00Z',
                'trigger': 'test',
                'generated_artifacts': []
            },
            'watcher_check': {
                'id': artifact_id,
                'timestamp': '2026-06-25T12:00:00Z',
                'loop_run_id': 'loop_run_1',
                'status': 'pass',
                'details': {}
            },
            'retro_record': {
                'id': artifact_id,
                'timestamp': '2026-06-25T12:00:00Z',
                'loop_run_id': 'loop_run_1',
                'lessons_learned': ['lesson1'],
                'adjustments': ['adjustment1']
            },
            'memory_event': {
                'id': artifact_id,
                'timestamp': '2026-06-25T12:00:00Z',
                'loop_run_id': 'loop_run_1',
                'event_type': 'test_event',
                'content': {'key': 'value'}
            },
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
            },
            'telegram_report': {
                'id': artifact_id,
                'timestamp': '2026-06-25T12:00:00Z',
                'loop_run_id': 'loop_run_1',
                'delivery_status': 'telegram_ready_artifact_created',
                'content': {'message': 'test'}
            }
        }[artifact_type]
        base_data.update(data)
        filepath = os.path.join(self.data_dir, artifact_type, f'{artifact_type}_{artifact_id}.json')
        with open(filepath, 'w') as f:
            json.dump(base_data, f)
        return filepath

    def test_valid_loop_run(self):
        filepath = self.create_artifact('loop_run', '001')
        is_valid, error = validate_json_artifact(filepath)
        self.assertTrue(is_valid, f"Valid loop_run should pass: {error}")

    def test_missing_required_field(self):
        filepath = self.create_artifact('loop_run', '002', {'timestamp': '2026-06-25T12:00:00Z', 'trigger': 'test', 'generated_artifacts': []})
        # Missing 'id'
        is_valid, error = validate_json_artifact(filepath)
        self.assertFalse(is_valid)
        self.assertIn('Missing required field: id', error)

    def test_invalid_json(self):
        filepath = os.path.join(self.data_dir, 'loop_run', 'bad.json')
        with open(filepath, 'w') as f:
            f.write('{ invalid json')
        is_valid, error = validate_json_artifact(filepath)
        self.assertFalse(is_valid)
        self.assertIn('Invalid JSON', error)

    def test_invalid_enum(self):
        filepath = self.create_artifact('watcher_check', '003', {'status': 'invalid_status'})
        is_valid, error = validate_json_artifact(filepath)
        self.assertFalse(is_valid)
        self.assertIn('must be one of', error)

    def test_invalid_datetime_format(self):
        filepath = self.create_artifact('loop_run', '004', {'timestamp': 'not-a-date'})
        is_valid, error = validate_json_artifact(filepath)
        self.assertFalse(is_valid)
        self.assertIn('must be a valid ISO 8601 datetime', error)

    def test_artifact_type_inference_from_filename(self):
        # Create a file named loop_run_005.json in the loop_run directory
        filepath = self.create_artifact('loop_run', '005')
        # Our create_artifact does not add artifact_type, so data does not have it.
        # The validator will infer from the filename.
        with open(filepath, 'r') as f:
            data = json.load(f)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        is_valid, error = validate_json_artifact(filepath)
        self.assertTrue(is_valid, f"Should infer artifact type from filename: {error}")

    def test_validate_artifacts_in_directory(self):
        # Create a few valid artifacts
        self.create_artifact('loop_run', '006')
        self.create_artifact('watcher_check', '007')
        # Create an invalid one (missing id)
        invalid_path = self.create_artifact('retro_record', '008', {})
        with open(invalid_path, 'r') as f:
            data = json.load(f)
        del data['id']
        with open(invalid_path, 'w') as f:
            json.dump(data, f)

        results = validate_artifacts_in_directory(self.data_dir)
        self.assertEqual(len(results), 3)  # We created 3 files
        # Check that the first two are valid and the third is invalid
        self.assertTrue(results[0][1])  # loop_run
        self.assertTrue(results[1][1])  # watcher_check
        self.assertFalse(results[2][1]) # retro_record
        self.assertIn('Missing required field: id', results[2][2])

if __name__ == '__main__':
    unittest.main()