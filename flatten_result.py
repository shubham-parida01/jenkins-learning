#!/usr/bin/env python3
"""
flatten_result.py

Reads airflow_result.json and writes one flat, single-level Slack-ready
JSON payload per error into --output-dir. Works the same whether the
input came from the real generate_result.py or the demo version.

Output schema (one file per error):
{
  "run_id": "...",
  "file_name": "...",
  "platform": "...",
  "notification_type": "...",
  "file_type": "...",
  "stage": "...",
  "status": "...",
  "folder_date": "...",
  "dag_name": "...",
  "error_message": "..."
}

Usage:
    python3 flatten_result.py airflow_result.json --output-dir slack_payloads
"""

import argparse
import json
import os
import sys


def build_slack_payload(dag_id, load_date, environment, dag_run, error):
    error_type = error.get("error_type", "unknown")

    if error_type == "dag_task":
        file_name = error.get("task_id", "unknown")
        platform = "airflow"
        file_type = "dag_task"
    elif error_type == "file_operation":
        file_name = error.get("object_name", "unknown")
        platform = error.get("platform", "unknown")
        file_type = error.get("file_type", "unknown")
    else:
        file_name = "unknown"
        platform = "unknown"
        file_type = "unknown"

    return {
        "run_id": error.get("run_id") or dag_run.get("run_id", "unknown"),
        "file_name": file_name,
        "platform": platform,
        "notification_type": error_type,
        "file_type": file_type,
        "stage": environment,
        "status": dag_run.get("state", "unknown"),
        "folder_date": load_date,
        "dag_name": dag_id,
        "error_message": error.get("message", "No message provided"),
    }


def main():
    parser = argparse.ArgumentParser(description="Flatten airflow_result.json into Slack payloads")
    parser.add_argument("result_file", help="Path to airflow_result.json")
    parser.add_argument("--output-dir", default="slack_payloads")
    args = parser.parse_args()

    if not os.path.exists(args.result_file):
        print(f"ERROR: {args.result_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(args.result_file) as f:
        result = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    # Clear out any stale payloads from a previous run
    for fname in os.listdir(args.output_dir):
        if fname.endswith(".json"):
            os.remove(os.path.join(args.output_dir, fname))

    errors = result.get("errors", [])

    if not errors:
        print("[flatten] No errors found — nothing to write.")
        return

    dag_id = result.get("dag_id", "unknown_dag")
    load_date = result.get("load_date", "unknown")
    environment = result.get("environment", "unknown")
    dag_run = result.get("dag_run", {})

    for i, error in enumerate(errors, start=1):
        payload = build_slack_payload(dag_id, load_date, environment, dag_run, error)
        out_path = os.path.join(args.output_dir, f"error_{i:03d}.json")
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"[flatten] Wrote {out_path}")

    print(f"[flatten] {len(errors)} payload(s) written to {args.output_dir}/ (will be sent one at a time)")


if __name__ == "__main__":
    main()