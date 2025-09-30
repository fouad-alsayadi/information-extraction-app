#!/usr/bin/env python3
"""Debug script to test Databricks job ID and connection."""

import os
from databricks.sdk import WorkspaceClient

def test_databricks_connection():
    """Test Databricks connection and job ID."""
    print("Testing Databricks connection...")

    # Check environment variables
    job_id_str = os.getenv('DATABRICKS_JOB_ID')
    print(f"DATABRICKS_JOB_ID from env: {job_id_str}")

    if not job_id_str:
        print("❌ DATABRICKS_JOB_ID not set")
        return

    # Try to convert to int
    try:
        job_id = int(job_id_str)
        print(f"✅ Job ID converted to int: {job_id}")
        print(f"Job ID type: {type(job_id)}")
        print(f"Job ID bit length: {job_id.bit_length()}")
    except ValueError as e:
        print(f"❌ Failed to convert job ID to int: {e}")
        return

    # Test Databricks client
    try:
        client = WorkspaceClient()
        print("✅ Databricks client created successfully")

        # Try to get current user to test connection
        user = client.current_user.me()
        print(f"✅ Connected as: {user.user_name}")

    except Exception as e:
        print(f"❌ Databricks client failed: {e}")
        return

    # Try to list jobs to see if our job ID exists
    try:
        jobs_list = list(client.jobs.list(limit=100))
        print(f"✅ Found {len(jobs_list)} jobs in workspace")

        # Look for our specific job ID
        target_job = None
        for job in jobs_list:
            if job.job_id == job_id:
                target_job = job
                break

        if target_job:
            print(f"✅ Found target job: {target_job.settings.name}")
        else:
            print(f"❌ Job ID {job_id} not found in workspace")
            print("Available job IDs:")
            for job in jobs_list[:10]:  # Show first 10
                print(f"  - {job.job_id}: {job.settings.name}")

    except Exception as e:
        print(f"❌ Failed to list jobs: {e}")

    # Try to directly get the specific job
    try:
        job_detail = client.jobs.get(job_id=job_id)
        print(f"✅ Successfully retrieved job: {job_detail.settings.name}")

        # Try a test run (dry run - don't actually trigger)
        print("✅ Job ID is valid and accessible")

    except Exception as e:
        print(f"❌ Failed to get specific job {job_id}: {e}")

if __name__ == "__main__":
    test_databricks_connection()