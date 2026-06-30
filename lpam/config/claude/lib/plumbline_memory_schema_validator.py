#!/usr/bin/env python3
"""
Plumbline Memory Schema Validator
Validates JSON artifacts against predefined schemas for each artifact type.
"""

import json
import sys
import os
from typing import Dict, Any, List, Tuple, Optional

# Schema definitions for each artifact type
SCHEMAS = {
    "loop_run": {
        "required": ["id", "timestamp", "trigger", "generated_artifacts"],
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "trigger": {"type": "string"},
            "generated_artifacts": {"type": "array", "items": {"type": "string"}}
        }
    },
    "watcher_check": {
        "required": ["id", "timestamp", "loop_run_id", "status", "details"],
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "loop_run_id": {"type": "string"},
            "status": {"type": "string", "enum": ["pass", "fail", "warning"]},
            "details": {"type": "object"}
        }
    },
    "retro_record": {
        "required": ["id", "timestamp", "loop_run_id", "lessons_learned", "adjustments"],
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "loop_run_id": {"type": "string"},
            "lessons_learned": {"type": "array", "items": {"type": "string"}},
            "adjustments": {"type": "array", "items": {"type": "string"}}
        }
    },
    "memory_event": {
        "required": ["id", "timestamp", "loop_run_id", "event_type", "content"],
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "loop_run_id": {"type": "string"},
            "event_type": {"type": "string"},
            "content": {"type": "object"}
        }
    },
    "graph_node": {
        "required": ["id", "timestamp", "loop_run_id", "label", "type", "properties", "eligible_for_global_projection"],
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "loop_run_id": {"type": "string"},
            "label": {"type": "string"},
            "type": {"type": "string"},
            "properties": {"type": "object"},
            "eligible_for_global_projection": {"type": "boolean"}
        }
    },
    "graph_edge": {
        "required": ["id", "timestamp", "loop_run_id", "source_id", "target_id", "label", "type", "properties", "eligible_for_global_projection"],
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "loop_run_id": {"type": "string"},
            "source_id": {"type": "string"},
            "target_id": {"type": "string"},
            "label": {"type": "string"},
            "type": {"type": "string"},
            "properties": {"type": "object"},
            "eligible_for_global_projection": {"type": "boolean"}
        }
    },
    "telegram_report": {
        "required": ["id", "timestamp", "loop_run_id", "delivery_status", "content"],
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "loop_run_id": {"type": "string"},
            "delivery_status": {"type": "string", "enum": ["telegram_ready_artifact_created", "sent", "failed"]},
            "content": {"type": "object"}
        }
    }
}

def validate_json_artifact(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a JSON artifact file against its schema.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"
    
    # Determine artifact type from filename or content
    # We expect the artifact type to be part of the filename or a field in the JSON
    # For simplicity, we'll look for an "artifact_type" field, or infer from directory/filename
    artifact_type = data.get("artifact_type")
    if not artifact_type:
        # Try to infer from the file path
        filename = os.path.basename(filepath)
        # Remove extension and any ID suffix
        base = filename.split('.')[0]
        # Common pattern: <artifact_type>_<id>.json
        # We'll try to match against known types
        for atype in SCHEMAS.keys():
            if base.startswith(atype + "_") or base == atype:
                artifact_type = atype
                break
    
    if not artifact_type or artifact_type not in SCHEMAS:
        return False, f"Could not determine artifact type or unknown type: {artifact_type}"
    
    schema = SCHEMAS[artifact_type]
    
    # Check required fields
    for field in schema["required"]:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Type and format validation (basic)
    for field, constraints in schema["properties"].items():
        if field in data:
            value = data[field]
            expected_type = constraints.get("type")
            
            # Type checking
            if expected_type == "string":
                if not isinstance(value, str):
                    return False, f"Field '{field}' must be a string"
                # Format checking (simplified)
                if constraints.get("format") == "date-time":
                    # Very basic ISO 8601 check
                    if not (len(value) >= 19 and 'T' in value and (value.endswith('Z') or '+' in value or '-' in value[10:])):
                        return False, f"Field '{field}' must be a valid ISO 8601 datetime"
            elif expected_type == "boolean":
                if not isinstance(value, bool):
                    return False, f"Field '{field}' must be a boolean"
            elif expected_type == "array":
                if not isinstance(value, list):
                    return False, f"Field '{field}' must be an array"
                # Check item type if specified
                if "items" in constraints:
                    item_type = constraints["items"].get("type")
                    if item_type:
                        for i, item in enumerate(value):
                            if item_type == "string" and not isinstance(item, str):
                                return False, f"Field '{field}[{i}]' must be a string"
                            elif item_type == "object" and not isinstance(item, dict):
                                return False, f"Field '{field}[{i}]' must be an object"
            elif expected_type == "object":
                if not isinstance(value, dict):
                    return False, f"Field '{field}' must be an object"
            elif expected_type == "integer":
                if not isinstance(value, int):
                    return False, f"Field '{field}' must be an integer"
            
            # Enum validation
            if "enum" in constraints and value not in constraints["enum"]:
                return False, f"Field '{field}' must be one of {constraints['enum']}"
    
    return True, None

def validate_artifacts_in_directory(data_dir: str) -> List[Tuple[str, bool, Optional[str]]]:
    """
    Validate all JSON files in the data directory and its subdirectories.
    
    Returns:
        List of tuples (filepath, is_valid, error_message)
    """
    results = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                is_valid, error = validate_json_artifact(filepath)
                results.append((filepath, is_valid, error))
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate Plumbline memory artifacts')
    parser.add_argument('--data-dir', default='data', help='Directory containing artifact subdirectories')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--file', help='Validate a specific file instead of walking the directory')
    
    args = parser.parse_args()
    
    if args.file:
        # Validate a single file
        is_valid, error = validate_json_artifact(args.file)
        if args.json:
            result = {
                "file": args.file,
                "valid": is_valid,
                "error": error
            }
            print(json.dumps(result, indent=2))
        else:
            if is_valid:
                print(f"✓ {args.file}: Valid")
            else:
                print(f"✗ {args.file}: Invalid - {error}")
        sys.exit(0 if is_valid else 1)
    else:
        # Walk the data directory
        results = validate_artifacts_in_directory(args.data_dir)
        
        if args.json:
            output = []
            for filepath, is_valid, error in results:
                output.append({
                    "file": filepath,
                    "valid": is_valid,
                    "error": error
                })
            print(json.dumps(output, indent=2))
        else:
            all_valid = True
            for filepath, is_valid, error in results:
                if is_valid:
                    print(f"✓ {filepath}: Valid")
                else:
                    print(f"✗ {filepath}: Invalid - {error}")
                    all_valid = False
            
            if all_valid and results:
                print(f"\nAll {len(results)} artifacts are valid.")
            elif not results:
                print(f"No JSON artifacts found in {args.data_dir}")
            else:
                print(f"\nSome artifacts failed validation.")
            
            sys.exit(0 if all_valid else 1)

if __name__ == "__main__":
    main()