import json
import os
import sys


def main():
    input_file = sys.argv[1]

    with open(input_file) as f:
        result = json.load(f)

    output_dir = "slack_payloads"
    os.makedirs(output_dir, exist_ok=True)

    files = result.get("files", [])

    failed_count = 0

    for file in files:

        # Only create Slack payloads for failed files
        if file.get("status") != "FAILED":
            continue

        payload = {
            "notification_type": "FILE_FAILURE",
            "status": "FAILED",
            "dag_name": result["dag_name"],
            "run_id": result["run_id"],
            "folder_date": result["folder_date"],
            "file_name": file["object_name"],
            "file_type": file["file_type"],
            "platform": file["platform"],
            "stage": file["stage"],
            "error_message": file.get("error_message") or "",
        }

        failed_count += 1

        output_file = f"{output_dir}/file_failure_{failed_count}.json"

        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)

        print(f"Created {output_file}")

    print(f"Created {failed_count} failure payload(s)")


if __name__ == "__main__":
    main()