import os
import tempfile
import json
import unittest
from plumbline_loop_runner import run_loop

class TestPlumblineLoopRunner(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'data')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_run_loop_creates_required_artifacts(self):
        # Run the loop
        success = run_loop(self.data_dir)
        self.assertTrue(success, "The loop should run successfully")

        # Check that the required artifact directories have been created
        required_artifact_types = [
            'loop_run',
            'watcher_check',
            'retro_record',
            'memory_event',
            'graph_node',
            'graph_edge',
            'telegram_report'
        ]
        for artifact_type in required_artifact_types:
            artifact_dir = os.path.join(self.data_dir, artifact_type)
            self.assertTrue(os.path.isdir(artifact_dir), f"Directory for {artifact_type} should exist")
            # Check that there is at least one JSON file in each directory
            files = [f for f in os.listdir(artifact_dir) if f.endswith('.json')]
            self.assertGreater(len(files), 0, f"There should be at least one {artifact_type} JSON file")

        # Check that the loop_run artifact references the generated artifacts
        loop_run_dir = os.path.join(self.data_dir, 'loop_run')
        loop_run_files = [f for f in os.listdir(loop_run_dir) if f.endswith('.json')]
        self.assertEqual(len(loop_run_files), 1, "There should be exactly one loop_run file")
        loop_run_path = os.path.join(loop_run_dir, loop_run_files[0])
        with open(loop_run_path, 'r') as f:
            loop_run = json.load(f)
        self.assertIn('generated_artifacts', loop_run, "loop_run should have a generated_artifacts field")
        # Check that the generated_artifacts list contains the expected types (we can check for at least one of each type)
        # For simplicity, we'll just check that the list is not empty and contains strings
        self.assertIsInstance(loop_run['generated_artifacts'], list)
        self.assertTrue(all(isinstance(item, str) for item in loop_run['generated_artifacts']))
        # We expect at least 7 artifacts (one of each type)
        self.assertGreaterEqual(len(loop_run['generated_artifacts']), 7)

        # Check that the telegram_report has the correct delivery_status
        telegram_report_dir = os.path.join(self.data_dir, 'telegram_report')
        telegram_report_files = [f for f in os.listdir(telegram_report_dir) if f.endswith('.json')]
        self.assertEqual(len(telegram_report_files), 1, "There should be exactly one telegram_report file")
        telegram_report_path = os.path.join(telegram_report_dir, telegram_report_files[0])
        with open(telegram_report_path, 'r') as f:
            telegram_report = json.load(f)
        self.assertEqual(telegram_report.get('delivery_status'), 'telegram_ready_artifact_created',
                         "telegram_report should have delivery_status 'telegram_ready_artifact_created'")

        # Check that the graph projection was created and excludes fake artifacts
        # We know that the loop runner creates one fake node and one fake edge (as per the loop contract)
        graph_projection_dir = os.path.join(self.data_dir, 'graph_projection')
        self.assertTrue(os.path.isdir(graph_projection_dir), "graph_projection directory should exist")
        productive_graph_path = os.path.join(graph_projection_dir, 'productive_graph.json')
        self.assertTrue(os.path.isfile(productive_graph_path), "productive_graph.json should exist")
        with open(productive_graph_path, 'r') as f:
            productive_graph = json.load(f)
        # The productive graph should have nodes and edges (the real ones)
        # We created one real node and one real edge (the fake ones are excluded)
        # Actually, the loop runner creates one real node, one real edge, one fake node, one fake edge.
        # So the productive graph should have 1 node and 1 edge.
        self.assertEqual(len(productive_graph.get('nodes', [])), 1, "There should be 1 productive node")
        self.assertEqual(len(productive_graph.get('edges', [])), 1, "There should be 1 productive edge")

if __name__ == '__main__':
    unittest.main()