#!/usr/bin/env python3
"""
Plumbline Memory Graph Projector
Projects the productive graph by filtering out artifacts ineligible for global projection.
"""

import json
import os
import sys
from typing import Dict, List, Any
from plumbline_memory_schema_validator import validate_json_artifact, SCHEMAS

def load_artifacts_from_directory(data_dir: str, artifact_type: str) -> List[Dict[str, Any]]:
    """
    Load all artifacts of a given type from the data directory.
    
    Returns:
        List of artifact dictionaries.
    """
    artifacts = []
    artifact_dir = os.path.join(data_dir, artifact_type)
    if not os.path.isdir(artifact_dir):
        return artifacts
    
    for filename in os.listdir(artifact_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(artifact_dir, filename)
            is_valid, error = validate_json_artifact(filepath)
            if not is_valid:
                print(f"Warning: Skipping invalid artifact {filepath}: {error}", file=sys.stderr)
                continue
            with open(filepath, 'r') as f:
                artifact = json.load(f)
                artifacts.append(artifact)
    return artifacts

def project_graph(data_dir: str, output_file: str) -> Dict[str, Any]:
    """
    Project the productive graph from graph_node and graph_edge artifacts.
    
    Returns:
        A dictionary containing the projected graph and a report.
    """
    # Load nodes and edges
    nodes = load_artifacts_from_directory(data_dir, 'graph_node')
    edges = load_artifacts_from_directory(data_dir, 'graph_edge')
    
    # Filter for eligible artifacts
    productive_nodes = [node for node in nodes if node.get('eligible_for_global_projection', False)]
    productive_edges = [edge for edge in edges if edge.get('eligible_for_global_projection', False)]
    
    # Build the productive graph
    productive_graph = {
        'nodes': productive_nodes,
        'edges': productive_edges
    }
    
    # Generate a report
    report = {
        'total_nodes': len(nodes),
        'productive_nodes': len(productive_nodes),
        'total_edges': len(edges),
        'productive_edges': len(productive_edges),
        'excluded_nodes': len(nodes) - len(productive_nodes),
        'excluded_edges': len(edges) - len(productive_edges),
        'timestamp': __import__('datetime').datetime.now().isoformat() + 'Z'
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write the productive graph
    with open(output_file, 'w') as f:
        json.dump(productive_graph, f, indent=2)
    
    return {
        'graph': productive_graph,
        'report': report
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Project the productive graph from Plumbline memory artifacts.')
    parser.add_argument('--data-dir', default='data', help='Directory containing artifact subdirectories')
    parser.add_argument('--out', '--output', dest='output', default='data/graph_projection/productive_graph.json',
                        help='Output file for the productive graph (JSON)')
    parser.add_argument('--json', action='store_true', help='Output the report as JSON to stdout')
    
    args = parser.parse_args()
    
    result = project_graph(args.data_dir, args.output)
    
    if args.json:
        print(json.dumps(result['report'], indent=2))
    else:
        print(f"Projected graph saved to {args.output}")
        print(f"Report: {result['report']}")

if __name__ == '__main__':
    main()