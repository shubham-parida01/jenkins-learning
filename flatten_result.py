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

    for index, file in enumerate(files, start=1):

        payload = {
            "notification_type": (
                "FILE_FAILURE"
                if file["status"] == "FAILED"
                else "FILE_SUCCESS"
            ),
            "status": file["status"],
            "dag_name": result["dag_name"],
            "run_id": result["run_id"],
            "folder_date": result["folder_date"],
            "file_name": file["object_name"],
            "file_type": file["file_type"],
            "platform": file["platform"],
            "stage": file["stage"],
            "error_message": file.get("error_message") or "",
        }

        output_file = f"{output_dir}/file_{index}.json"

        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)

        print(f"Created {output_file}")


if __name__ == "__main__":
    main()