#!/usr/bin/env python3
"""
DEMO VERSION of generate_result.py

Simulates both error sources (Airflow DAG/task state + BigQuery
workflow_files table) with hardcoded / randomized fake data instead
of making real network calls. Writes airflow_result.json in the same
shape the real script would, so downstream stages (flatten_result.py,
Fail On Errors) can be tested end-to-end without GCP or Composer access.

Usage:
    python3 generate_result.py --load-date 20260816 --environment dev
    python3 generate_result.py --load-date 20260816 --environment dev --force-errors
    python3 generate_result.py --load-date 20260816 --environment dev --force-clean
"""

import argparse
import json
import random
import sys
from datetime import datetime, timezone


def fake_airflow_check(load_date, force_errors, force_clean, rng):
    """Pretend to hit the Composer/Airflow REST API."""
    if force_clean:
        failed = []
    elif force_errors:
        failed = ["process_creative_files"]
    else:
        # ~30% chance of a random task failure, for a realistic demo run
        failed = ["process_campaign_files"] if rng.random() < 0.3 else []

    dag_run_state = "failed" if failed else "success"

    errors = [
        {
            "error_type": "dag_task",
            "severity": "critical",
            "message": f"Task '{task_id}' failed for load_date={load_date}",
            "task_id": task_id,
        }
        for task_id in failed
    ]

    dag_run = {
        "state": dag_run_state,
        "failed_tasks": failed,
        "run_id": f"manual__{load_date}T00:00:00+00:00",
    }

    return dag_run, errors


def fake_bigquery_check(load_date, environment, force_errors, force_clean, rng):
    """Pretend to query `{project}.sidekick_audit.workflow_files`."""
    if force_clean:
        rows = []
    elif force_errors:
        rows = [
            {
                "object_name": "campaign_export_20260816_003.json",
                "file_type": "campaign",
                "platform": "meta",
                "error_message": "Unrecognized key 'campaign_id_v2' — schema mismatch",
                "run_id": "manual__20260816T00:00:00+00:00",
                "processed_at": "2026-08-16T04:12:07Z",
            },
            {
                "object_name": "creative_export_20260816_011.json",
                "file_type": "creative",
                "platform": "tiktok",
                "error_message": "Malformed JSON: unexpected end of input at byte 4021",
                "run_id": "manual__20260816T00:00:00+00:00",
                "processed_at": "2026-08-16T04:13:52Z",
            },
        ]
    else:
        # ~40% chance of 0-2 random file failures
        sample_errors = [
            ("campaign_export_{}_007.json".format(load_date), "campaign", "meta",
             "Missing required field 'account_id'"),
            ("creative_export_{}_014.json".format(load_date), "creative", "tiktok",
             "Malformed JSON: unexpected token at byte 512"),
            ("creative_export_{}_019.json".format(load_date), "creative", "snapchat",
             "Unsupported platform code 'sc2'"),
        ]
        n = rng.choice([0, 0, 1, 2]) if rng.random() < 0.4 else 0
        chosen = rng.sample(sample_errors, k=min(n, len(sample_errors)))
        rows = [
            {
                "object_name": obj,
                "file_type": ftype,
                "platform": platform,
                "error_message": msg,
                "run_id": f"manual__{load_date}T00:00:00+00:00",
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            for obj, ftype, platform, msg in chosen
        ]

    errors = [
        {
            "error_type": "file_operation",
            "severity": "critical",
            "message": row["error_message"],
            "object_name": row["object_name"],
            "file_type": row["file_type"],
            "platform": row["platform"],
        }
        for row in rows
    ]

    return errors


def main():
    parser = argparse.ArgumentParser(description="DEMO: generate airflow_result.json with fake data")
    parser.add_argument("--load-date", default="AUTO", help="YYYYMMDD or AUTO")
    parser.add_argument("--environment", default="dev", choices=["prod", "dev"])
    parser.add_argument("--output", default="airflow_result.json")
    parser.add_argument("--skip-dag-check", action="store_true",
                         help="Demo flag, mirrors the real script's signature")
    parser.add_argument("--airflow-creds", default=None,
                         help="Accepted but ignored in demo mode")
    parser.add_argument("--force-errors", action="store_true",
                         help="Always produce at least one error of each type")
    parser.add_argument("--force-clean", action="store_true",
                         help="Always produce a clean, error-free result")
    parser.add_argument("--seed", type=int, default=None,
                         help="Random seed, for reproducible demo runs")
    args = parser.parse_args()

    if args.force_errors and args.force_clean:
        print("ERROR: --force-errors and --force-clean are mutually exclusive", file=sys.stderr)
        sys.exit(2)

    rng = random.Random(args.seed)

    load_date = args.load_date
    if load_date == "AUTO":
        load_date = datetime.now(timezone.utc).strftime("%Y%m%d")

    print(f"[DEMO] Simulating checks for load_date={load_date}, environment={args.environment}")
    print("[DEMO] No real Airflow or BigQuery connections are made.")

    all_errors = []

    if args.skip_dag_check:
        print("[DEMO] Skipping fake Airflow check (--skip-dag-check)")
        dag_run = {"state": "skipped", "failed_tasks": [], "run_id": None}
    else:
        dag_run, dag_errors = fake_airflow_check(load_date, args.force_errors, args.force_clean, rng)
        all_errors.extend(dag_errors)

    file_errors = fake_bigquery_check(load_date, args.environment, args.force_errors, args.force_clean, rng)
    all_errors.extend(file_errors)

    result = {
        "dag_id": "sidekick_audit_sync",
        "load_date": load_date,
        "environment": args.environment,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "demo_mode": True,
        "dag_run": dag_run,
        "errors": all_errors,
        "critical_error_count": len(all_errors),
        "has_errors": len(all_errors) > 0,
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[DEMO] Wrote {args.output} — critical_error_count={result['critical_error_count']}")

    sys.exit(1 if result["has_errors"] else 0)


if __name__ == "__main__":
    main()
