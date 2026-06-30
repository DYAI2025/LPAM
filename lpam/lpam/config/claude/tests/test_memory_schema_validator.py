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

    def test_valid_loop_run(self):
        # Create a valid loop_run artifact
        artifact = {
            'id': 'loop_run_001',
            'timestamp': '2026-06-25T12:00:00Z',
            'trigger': 'test',
            'generated_artifacts': []
        }
        filepath = os.path.join(self.data_dir, 'loop_run', 'loop_run_001.json')
        with open(filepath, 'w') as f:
            json.dump(artifact, f)
        is_valid, error = validate_json_artifact(filepath)
        self.assertTrue(is_valid, f"Valid loop_run should pass: {error}")

    def test_missing_required_field(self):
        # Create a loop_run artifact missing the 'id' field
        artifact = {
            'timestamp': '2026-06-25T12:00:00Z',
            'trigger': 'test',
            'generated_artifacts': []
        }
        filepath = os.path.join(self.data_dir, 'loop_run', 'loop_run_002.json')
        with open(filepath, 'w') as f:
            json.dump(artifact, f)
        is_valid, error = validate_json_artifact(filepath)
        self.assertFalse(is_valid, f"Missing id should be invalid: {error}")
        self.assertIn('Missing required field: id', error)

    def test_invalid_json(self):
        filepath = os.path.join(self.data_dir, 'loop_run', 'bad.json')
        with open(filepath, 'w') as f:
            f.write('{ invalid json')
        is_valid, error = validate_json_artifact(filepath)
        self.assertFalse(is_valid)
        self.assertIn('Invalid JSON', error)

    def test_invalid_enum(self):
        # Create a watcher_check with invalid status
        artifact = {
            'id': 'watcher_check_003',
            'timestamp': '2026-06-25T12:00:00Z',
            'loop_run_id': 'loop_run_1',
            'status': 'invalid_status',
            'details': {}
        }
        filepath = os.path.join(self.data_dir, 'watcher_check', 'watcher_check_003.json')
        with open(filepath, 'w') as f:
            json.dump(artifact, f)
        is_valid, error = validate_json_artifact(filepath)
        self.assertFalse(is_valid)
        self.assertIn('must be one of', error)

    def test_invalid_datetime_format(self):
        # Create a loop_run with invalid timestamp
        artifact = {
            'id': 'loop_run_004',
            'timestamp': 'not-a-date',
            'trigger': 'test',
            'generated_artifacts': []
        }
        filepath = os.path.join(self.data_dir, 'loop_run', 'loop_run_004.json')
        with open(filepath, 'w') as f:
            json.dump(artifact, f)
        is_valid, error = validate_json_artifact(filepath)
        self.assertFalse(is_valid)
        self.assertIn('must be a valid ISO 8601 datetime', error)

    def test_artifact_type_inference_from_filename(self):
        # Create a loop_run artifact without artifact_type field, but with correct filename
        artifact = {
            'id': 'loop_run_005',
            'timestamp': '2026-06-25T12:00:00Z',
            'trigger': 'test',
            'generated_artifacts': []
        }
        filepath = os.path.join(self.data_dir, 'loop_run', 'loop_run_005.json')
        with open(filepath, 'w') as f:
            json.dump(artifact, f)
        is_valid, error = validate_json_artifact(filepath)
        self.assertTrue(is_valid, f"Should infer artifact type from filename: {error}")

    def test_validate_artifacts_in_directory(self):
        # Create a few valid artifacts
        # loop_run_006
        artifact = {
            'id': 'loop_run_006',
            'timestamp': '2026-06-25T12:00:00Z',
            'trigger': 'test',
            'generated_artifacts': []
        }
        filepath = os.path.join(self.data_dir, 'loop_run', 'loop_run_006.json')
        with open(filepath, 'w') as f:
            json.dump(artifact, f)
        # watcher_check_007
        artifact = {
            'id': 'watcher_check_007',
            'timestamp': '2026-06-25T12:00:00Z',
            'loop_run_id': 'loop_run_006',
            'status': 'pass',
            'details': {}
        }
        filepath = os.path.join(self.data_dir, 'watcher_check', 'watcher_check_007.json')
        with open(filepath, 'w') as f:
            json.dump(artifact, f)
        # Create an invalid retro_record (missing id)
        artifact = {
            'timestamp': '2026-06-25T12:00:00Z',
            'loop_run_id': 'loop_run_006',
            'lessons_learned': ['lesson1'],
            'adjustments': ['adjustment1']
        }
        filepath = os.path.join(self.data_dir, 'retro_record', 'retro_record_008.json')
        with open(filepath, 'w') as f:
            json.dump(artifact, f)

        results = validate_artifacts_in_directory(self.data_dir)
        self.assertEqual(len(results), 3)  # We created 3 files
        # Check that the first two are valid and the third is invalid
        self.assertTrue(results[0][1])  # loop_run
        self.assertTrue(results[1][1])  # watcher_check
        self.assertFalse(results[2][1]) # retro_record
        self.assertIn('Missing required field: id', results[2][2])

if __name__ == '__main__':
    unittest.main()