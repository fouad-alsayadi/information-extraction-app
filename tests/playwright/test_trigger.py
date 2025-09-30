#!/usr/bin/env python3
"""Test the actual Databricks job trigger to debug the issue."""

import os
from databricks.sdk import WorkspaceClient

def test_job_trigger():
    """Test triggering the Databricks job."""

    # Get job ID from environment
    job_id_str = os.getenv('DATABRICKS_JOB_ID')
    if not job_id_str:
        print("❌ DATABRICKS_JOB_ID not set")
        return

    job_id = int(job_id_str)
    print(f"Using job ID: {job_id}")

    # Create client
    client = WorkspaceClient()

    # Test parameters
    test_job_id = 11  # The job we created in the app
    test_schema_id = 4  # The schema we created

    notebook_params = {
        'analysis_id': str(test_job_id),
        'schema_id': str(test_schema_id)
    }

    print(f"Notebook params: {notebook_params}")

    # Try to trigger the job
    try:
        print("Triggering job...")
        response = client.jobs.run_now(
            job_id=job_id,
            notebook_params=notebook_params
        )

        print(f"✅ Job triggered successfully!")
        print(f"Run ID: {response.run_id}")
        print(f"Run ID type: {type(response.run_id)}")
        print(f"Run ID bit length: {response.run_id.bit_length()}")

        # Check if this is the issue - maybe run_id is too large
        try:
            # Try to store as different integer types
            run_id_int = int(response.run_id)
            print(f"Run ID as int: {run_id_int}")

            # Check if it fits in 32-bit signed integer
            if run_id_int > 2147483647:
                print("⚠️  Run ID is larger than 32-bit signed integer limit")

            # Check if it fits in 64-bit signed integer
            if run_id_int > 9223372036854775807:
                print("⚠️  Run ID is larger than 64-bit signed integer limit")

        except Exception as e:
            print(f"❌ Error converting run ID: {e}")

    except Exception as e:
        print(f"❌ Failed to trigger job: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_job_trigger()