import boto3
import os
import tempfile
from io import BytesIO, StringIO
import json
import csv
from datetime import datetime  # Import datetime module


def lambda_handler(event, context):
    # Initialize boto3 clients
    codecommit = boto3.client("codecommit", region_name=os.environ["AWS_REGION"])
    s3 = boto3.client("s3")

    # Environment variables
    repo_name = os.environ.get("REPO_NAME")
    branch_name = os.environ.get("BRANCH_NAME", "mainline")  # Default to "mainline"
    bucket_name = "codeexamplestats"
    csv_file_key = "stats.csv"

    try:
        # Step 1: Retrieve the .stats file content directly from CodeCommit
        file_response = codecommit.get_file(
            repositoryName=repo_name,
            filePath=".stats",  # Specify the path to the .stats file
            commitSpecifier=branch_name,
        )

        # Convert .stats content to valid JSON if necessary
        file_content = file_response["fileContent"].decode("utf-8")
        try:
            stats_data = json.loads(file_content)  # Valid JSON parsing
        except json.JSONDecodeError:
            file_content = file_content.replace("'", '"')  # Replace single quotes
            stats_data = json.loads(file_content)

        # Step 2: Fetch the current stats.csv file from S3
        existing_rows = []
        try:
            csv_obj = s3.get_object(Bucket=bucket_name, Key=csv_file_key)
            csv_data = csv_obj["Body"].read().decode("utf-8")
            csv_reader = csv.DictReader(StringIO(csv_data))
            existing_rows = list(csv_reader)
        except s3.exceptions.NoSuchKey:
            existing_rows = []

        # Step 3: Append the new data from .stats file with a formatted timestamp
        new_row = {
            "sdks": stats_data["sdks"],
            "services": stats_data["services"],
            "examples": stats_data["examples"],
            "versions": stats_data["versions"],
            "snippets": stats_data["snippets"],
            "genai_none": stats_data["genai"]["none"],
            "genai_some": stats_data["genai"]["some"],
            "genai_most": stats_data["genai"]["most"],
            "timestamp": datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),  # Formatted timestamp
        }
        existing_rows.append(new_row)

        # Step 4: Save the updated data back to CSV and upload it to S3
        with StringIO() as output:
            # Include 'timestamp' in fieldnames to write the timestamp in the CSV
            writer = csv.DictWriter(output, fieldnames=new_row.keys())
            writer.writeheader()  # Ensure we have headers
            writer.writerows(existing_rows)
            s3.put_object(
                Bucket=bucket_name,
                Key=csv_file_key,
                Body=output.getvalue().encode("utf-8"),
            )

        print("Successfully updated stats.csv in S3 with new .stats data.")

    except Exception as e:
        print(f"Error occurred: {e}")
        return {"statusCode": 500, "body": "Failed to update stats.csv."}

    return {"statusCode": 200, "body": "stats.csv updated successfully in S3."}
