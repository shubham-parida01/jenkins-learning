import json


def main():
    result = {
        "status": "FAILED",
        "dag_name": "ttd_ingestion",
        "run_id": "manual__20260814_171500",
        "folder_date": "20260814",

        "summary": {
            "total_files": 3,
            "successful": 2,
            "failed": 1,
        },

        "files": [
            {
                "object_name": "campaign_001.json",
                "file_type": "campaign",
                "platform": "ttd",
                "status": "SUCCESS",
                "stage": "BQ_LOAD",
                "error_message": None,
            },
            {
                "object_name": "campaign_002.json",
                "file_type": "campaign",
                "platform": "ttd",
                "status": "FAILED",
                "stage": "TRANSFORM",
                "error_message": "Missing CreativeId at creatives[0]",
            },
            {
                "object_name": "creative_003.json",
                "file_type": "creative",
                "platform": "ttd",
                "status": "SUCCESS",
                "stage": "BQ_LOAD",
                "error_message": None,
            },
        ],
    }

    with open("airflow_result.json", "w") as f:
        json.dump(result, f, indent=2)

    print("Created airflow_result.json")


if __name__ == "__main__":
    main()