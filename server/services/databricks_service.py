"""Databricks integration service for document processing."""

import json
import os
from typing import Any, Dict

from databricks.sdk import WorkspaceClient


class DatabricksService:
    """Service for triggering and monitoring Databricks jobs."""

    @staticmethod
    def _get_client() -> WorkspaceClient:
        """Get Databricks workspace client."""
        # Use environment variables or Databricks CLI authentication
        return WorkspaceClient()

    @staticmethod
    def _get_job_id() -> int:
        """Get the Databricks job ID from environment variables."""
        job_id = os.getenv('DATABRICKS_JOB_ID')
        if not job_id:
            raise ValueError('DATABRICKS_JOB_ID environment variable not set')
        try:
            return int(job_id)
        except ValueError:
            raise ValueError(f'DATABRICKS_JOB_ID must be a valid integer, got: {job_id}')

    @staticmethod
    async def trigger_extraction_job(
        job_id: int,
        schema_id: int
    ) -> int:
        """Trigger Databricks notebook for document processing."""
        try:
            client = DatabricksService._get_client()
            databricks_job_id = DatabricksService._get_job_id()

            # Prepare notebook parameters (simplified to match original folio-parse-stream)
            notebook_params = {
                'job_id': str(job_id),
                'schema_id': str(schema_id)
            }

            # Trigger the job
            response = client.jobs.run_now(
                job_id=databricks_job_id,
                notebook_params=notebook_params
            )

            return response.run_id

        except Exception as e:
            raise Exception(f'Failed to trigger Databricks job: {str(e)}')

    @staticmethod
    async def get_job_status(run_id: int) -> Dict[str, Any]:
        """Get detailed status of a Databricks job run."""
        try:
            client = DatabricksService._get_client()

            # Get run details
            run = client.jobs.get_run(run_id=run_id)

            # Extract relevant status information
            status_info = {
                'run_id': run.run_id,
                'job_id': run.job_id,
                'run_name': run.run_name,
                'state': {},
                'start_time': run.start_time,
                'end_time': run.end_time,
                'run_duration': run.run_duration,
                'setup_duration': run.setup_duration,
                'execution_duration': run.execution_duration,
                'cleanup_duration': run.cleanup_duration,
                'run_page_url': run.run_page_url,
            }

            # Add state information if available
            if run.state:
                status_info['state'] = {
                    'life_cycle_state': run.state.life_cycle_state.value if run.state.life_cycle_state else None,
                    'result_state': run.state.result_state.value if run.state.result_state else None,
                    'state_message': run.state.state_message,
                }

            # Add task information if available
            if run.tasks:
                status_info['tasks'] = []
                for task in run.tasks:
                    task_info = {
                        'task_key': task.task_key,
                        'run_id': task.run_id,
                        'start_time': task.start_time,
                        'end_time': task.end_time,
                        'execution_duration': task.execution_duration,
                    }

                    if task.state:
                        task_info['state'] = {
                            'life_cycle_state': task.state.life_cycle_state.value if task.state.life_cycle_state else None,
                            'result_state': task.state.result_state.value if task.state.result_state else None,
                            'state_message': task.state.state_message,
                        }

                    status_info['tasks'].append(task_info)

            return status_info

        except Exception as e:
            raise Exception(f'Failed to get Databricks job status: {str(e)}')

    @staticmethod
    async def cancel_job(run_id: int) -> bool:
        """Cancel a running Databricks job."""
        try:
            client = DatabricksService._get_client()
            client.jobs.cancel_run(run_id=run_id)
            return True

        except Exception as e:
            raise Exception(f'Failed to cancel Databricks job: {str(e)}')

    @staticmethod
    def get_job_logs(run_id: int) -> str:
        """Get logs from a Databricks job run (placeholder - logs API might need different implementation)."""
        try:
            # Note: This is a simplified implementation
            # In practice, you might need to use the Databricks REST API
            # or other methods to retrieve job logs
            client = DatabricksService._get_client()

            # For now, return a placeholder message
            return f'Logs for run {run_id} - implement log retrieval based on your needs'

        except Exception as e:
            raise Exception(f'Failed to get job logs: {str(e)}')