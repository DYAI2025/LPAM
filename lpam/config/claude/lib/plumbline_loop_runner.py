#!/usr/bin/env python3
"""
Plumbline Loop Runner
Executes a minimal Plumbline loop: generate artifacts, validate, project graph, generate report.
"""

import json
import os
import sys
from datetime import datetime, timezone
import uuid

# We'll import the validator and projector from the same package
# Since we are in the same package, we can import them directly.
# However, to avoid import issues when run as a script, we'll adjust the path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from plumbline_memory_schema_validator import validate_json_artifact, validate_artifacts_in_directory
from plumbline_memory_graph_projection import project_graph

def generate_artifact(artifact_type, artifact_id, loop_run_id, override_fields=None):
    """Generate a basic artifact of the given type with required fields."""
    if override_fields is None:
        override_fields = {}
    
    base = {
        "loop_run": {
            "id": artifact_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trigger": "manual",
            "generated_artifacts": []
        },
        "watcher_check": {
            "id": artifact_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loop_run_id": loop_run_id,
            "status": "pass",
            "details": {"check": "initial"}
        },
        "retro_record": {
            "id": artifact_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loop_run_id": loop_run_id,
            "lessons_learned": ["test lesson"],
            "adjustments": ["test adjustment"]
        },
        "memory_event": {
            "id": artifact_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loop_run_id": loop_run_id,
            "event_type": "test_event",
            "content": {"data": "test"}
        },
        "graph_node": {
            "id": artifact_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loop_run_id": loop_run_id,
            "label": f"Node {artifact_id}",
            "type": "test",
            "properties": {"value": artifact_id},
            "eligible_for_global_projection": True  # default to eligible
        },
        "graph_edge": {
            "id": artifact_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loop_run_id": loop_run_id,
            "source_id": f"node{artifact_id}_src",
            "target_id": f"node{artifact_id}_tgt",
            "label": f"Edge {artifact_id}",
            "type": "test",
            "properties": {"value": artifact_id},
            "eligible_for_global_projection": True  # default to eligible
        },
        "telegram_report": {
            "id": artifact_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loop_run_id": loop_run_id,
            "delivery_status": "telegram_ready_artifact_created",
            "content": {"summary": "Loop completed"}
        }
    }[artifact_type]
    
    base.update(override_fields)
    return base

def ensure_directory(directory):
    """Ensure the directory exists."""
    os.makedirs(directory, exist_ok=True)

def write_artifact(artifact_type, artifact_id, data, data_dir):
    """Write an artifact to the appropriate subdirectory."""
    artifact_dir = os.path.join(data_dir, artifact_type)
    ensure_directory(artifact_dir)
    file_path = os.path.join(artifact_dir, f"{artifact_type}_{artifact_id}.json")
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    return file_path

def run_loop(data_dir="data"):
    """Run the Plumbline loop."""
    print("Starting Plumbline loop...")
    
    # Generate a unique ID for this loop run
    loop_run_id = str(uuid.uuid4())
    
    # We'll generate:
    # 1. loop_run
    # 2. watcher_check
    # 3. retro_record
    # 4. memory_event
    # 5. graph_node (real and fake)
    # 6. graph_edge (real and fake)
    # 7. telegram_report
    
    artifacts_to_create = []
    
    # 1. loop_run
    loop_run = generate_artifact("loop_run", loop_run_id, loop_run_id)
    # We'll update the generated_artifacts list after we create the others
    loop_run_path = write_artifact("loop_run", loop_run_id, loop_run, data_dir)
    artifacts_to_create.append(("loop_run", loop_run_id, loop_run_path))
    
    # 2. watcher_check
    watcher_check = generate_artifact("watcher_check", str(uuid.uuid4()), loop_run_id)
    watcher_check_path = write_artifact("watcher_check", watcher_check["id"], watcher_check, data_dir)
    artifacts_to_create.append(("watcher_check", watcher_check["id"], watcher_check_path))
    
    # 3. retro_record
    retro_record = generate_artifact("retro_record", str(uuid.uuid4()), loop_run_id)
    retro_record_path = write_artifact("retro_record", retro_record["id"], retro_record, data_dir)
    artifacts_to_create.append(("retro_record", retro_record["id"], retro_record_path))
    
    # 4. memory_event
    memory_event = generate_artifact("memory_event", str(uuid.uuid4()), loop_run_id)
    memory_event_path = write_artifact("memory_event", memory_event["id"], memory_event, data_dir)
    artifacts_to_create.append(("memory_event", memory_event["id"], memory_event_path))
    
    # 5. graph_node (real)
    graph_node_real = generate_artifact("graph_node", str(uuid.uuid4()), loop_run_id)
    graph_node_real_path = write_artifact("graph_node", graph_node_real["id"], graph_node_real, data_dir)
    artifacts_to_create.append(("graph_node", graph_node_real["id"], graph_node_real_path))
    
    # 6. graph_node (fake) - ineligible for global projection
    graph_node_fake = generate_artifact("graph_node", str(uuid.uuid4()), loop_run_id, 
                                        {"eligible_for_global_projection": False})
    graph_node_fake_path = write_artifact("graph_node", graph_node_fake["id"], graph_node_fake, data_dir)
    artifacts_to_create.append(("graph_node", graph_node_fake["id"], graph_node_fake_path))
    
    # 7. graph_edge (real)
    graph_edge_real = generate_artifact("graph_edge", str(uuid.uuid4()), loop_run_id)
    graph_edge_real_path = write_artifact("graph_edge", graph_edge_real["id"], graph_edge_real, data_dir)
    artifacts_to_create.append(("graph_edge", graph_edge_real["id"], graph_edge_real_path))
    
    # 8. graph_edge (fake) - ineligible for global projection
    graph_edge_fake = generate_artifact("graph_edge", str(uuid.uuid4()), loop_run_id, 
                                        {"eligible_for_global_projection": False})
    graph_edge_fake_path = write_artifact("graph_edge", graph_edge_fake["id"], graph_edge_fake, data_dir)
    artifacts_to_create.append(("graph_edge", graph_edge_fake["id"], graph_edge_fake_path))
    
    # 9. telegram_report
    telegram_report = generate_artifact("telegram_report", str(uuid.uuid4()), loop_run_id)
    telegram_report_path = write_artifact("telegram_report", telegram_report["id"], telegram_report, data_dir)
    artifacts_to_create.append(("telegram_report", telegram_report["id"], telegram_report_path))
    
    # Now update the loop_run with the list of generated artifact IDs
    generated_artifact_ids = [artifact[1] for artifact in artifacts_to_create if artifact[0] != "loop_run"]
    loop_run["generated_artifacts"] = generated_artifact_ids
    # Rewrite the loop_run file with the updated generated_artifacts
    with open(loop_run_path, 'w') as f:
        json.dump(loop_run, f, indent=2)
    
    print(f"Generated {len(artifacts_to_create)} artifacts.")
    
    # Step 2: Validate all artifacts
    print("Validating artifacts...")
    validation_results = validate_artifacts_in_directory(data_dir)
    all_valid = True
    for filepath, is_valid, error in validation_results:
        if not is_valid:
            print(f"  ✗ {filepath}: {error}")
            all_valid = False
        else:
            print(f"  ✓ {filepath}: Valid")
    
    if not all_valid:
        print("Validation failed. Aborting.")
        return False
    
    print("All artifacts are valid.")
    
    # Step 3: Project the graph (productive graph)
    print("Projecting graph...")
    output_dir = os.path.join(data_dir, "graph_projection")
    ensure_directory(output_dir)
    output_file = os.path.join(output_dir, "productive_graph.json")
    try:
        result = project_graph(data_dir, output_file)
        print(f"Graph projection complete. Output written to {output_file}")
        print(f"  Total nodes: {result['report']['total_nodes']}")
        print(f"  Productive nodes: {result['report']['productive_nodes']}")
        print(f"  Total edges: {result['report']['total_edges']}")
        print(f"  Productive edges: {result['report']['productive_edges']}")
        print(f"  Excluded nodes: {result['report']['excluded_nodes']}")
        print(f"  Excluded edges: {result['report']['excluded_edges']}")
    except Exception as e:
        print(f"Error during graph projection: {e}")
        return False
    
    # Step 4: The telegram_report was already generated in the artifacts step.
    # We could update it with more details, but for MVP we leave it as is.
    print("Telegram report artifact generated.")
    
    print("Plumbline loop completed successfully.")
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run the Plumbline loop.')
    parser.add_argument('--data-dir', default='data', help='Directory to store artifacts')
    parser.set_defaults(func=run_loop)
    
    args = parser.parse_args()
    success = args.func(args.data_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()