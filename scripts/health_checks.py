"""Health checks and validation for setup wizard.

This module provides functions for validating the setup including:
- Local development server health
- Deployed app health
- Job triggering capability
"""

import os
import signal
import subprocess
import time
from typing import Optional

import httpx
from rich.console import Console

console = Console()


def check_local_server(timeout: int = 60) -> bool:
  """Start server, test health endpoint, stop server.

  Args:
      timeout: Maximum seconds to wait for server startup

  Returns:
      True if server starts and health check passes, False otherwise
  """
  try:
    console.print('[cyan]Testing local development server...[/cyan]')

    # Start watch.sh in background
    console.print('[dim]Starting ./watch.sh...[/dim]')
    process = subprocess.Popen(
      ['./watch.sh'],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      preexec_fn=os.setsid if hasattr(os, 'setsid') else None,
    )

    # Wait for server to start (look for "Uvicorn running" in logs)
    start_time = time.time()
    server_started = False

    while time.time() - start_time < timeout:
      # Check if process is still running
      if process.poll() is not None:
        stdout, stderr = process.communicate()
        console.print('[red]❌ watch.sh exited unexpectedly[/red]')
        console.print(f'[dim]stdout: {stdout}[/dim]')
        console.print(f'[dim]stderr: {stderr}[/dim]')
        return False

      # Try to hit health endpoint
      try:
        response = httpx.get('http://localhost:8000/health', timeout=2)
        if response.status_code == 200:
          server_started = True
          console.print('[green]✅ Server started successfully[/green]')
          break
      except (httpx.ConnectError, httpx.TimeoutException):
        # Server not ready yet, keep waiting
        pass

      time.sleep(2)

    if not server_started:
      console.print(f'[red]❌ Server did not start within {timeout} seconds[/red]')
      _stop_process(process)
      return False

    # Test health endpoint
    try:
      response = httpx.get('http://localhost:8000/health', timeout=5)
      data = response.json()

      if response.status_code == 200 and data.get('status') == 'healthy':
        console.print('[green]✅ Health endpoint responding correctly[/green]')
        console.print(f'[dim]Database status: {data.get("database", "unknown")}[/dim]')
        success = True
      else:
        console.print(f'[yellow]⚠️  Unexpected health response: {data}[/yellow]')
        success = False

    except Exception as e:
      console.print(f'[red]❌ Health check failed: {e}[/red]')
      success = False

    # Stop server
    console.print('[dim]Stopping server...[/dim]')
    _stop_process(process)
    time.sleep(2)  # Give it time to clean up

    return success

  except Exception as e:
    console.print(f'[red]❌ Error testing local server: {e}[/red]')
    return False


def _stop_process(process: subprocess.Popen) -> None:
  """Stop a process and its children gracefully.

  Args:
      process: Process to stop
  """
  try:
    # Try graceful shutdown first (SIGTERM)
    if hasattr(os, 'killpg'):
      # Kill process group (Unix)
      os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    else:
      # Kill single process (Windows)
      process.terminate()

    # Wait up to 5 seconds for graceful shutdown
    try:
      process.wait(timeout=5)
    except subprocess.TimeoutExpired:
      # Force kill if still running
      if hasattr(os, 'killpg'):
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
      else:
        process.kill()
      process.wait()

  except Exception as e:
    console.print(f'[yellow]⚠️  Error stopping process: {e}[/yellow]')


def check_deployed_app(app_url: str, max_retries: int = 5, initial_wait: int = 10) -> bool:
  """Test deployed app endpoints with retry logic.

  Args:
      app_url: Deployed app URL
      max_retries: Maximum number of retry attempts (default: 5)
      initial_wait: Initial wait time in seconds before first attempt (default: 10)

  Returns:
      True if app is healthy, False otherwise
  """
  import time

  try:
    console.print(f'[cyan]Testing deployed app: {app_url}[/cyan]')
    console.print(f'[dim]Waiting {initial_wait}s for app to start...[/dim]')
    time.sleep(initial_wait)

    # Test health endpoint with retry
    health_check_passed = False
    for attempt in range(1, max_retries + 1):
      try:
        health_url = f'{app_url}/health'
        console.print(f'[dim]Attempt {attempt}/{max_retries}...[/dim]')
        response = httpx.get(health_url, timeout=10, follow_redirects=True)
        console.print(f'[dim]Status code: {response.status_code}[/dim]')

        # Check if we got redirected to a login page (OAuth) - check this first regardless of status
        if 'Databricks - Sign In' in response.text or 'login' in response.text.lower():
          console.print(
            '[yellow]⚠️  App requires OAuth authentication (redirected to login)[/yellow]'
          )
          console.print('[green]✅ App is running and responding (auth required)[/green]')
          health_check_passed = True
          break  # App is up, just requires auth

        # Check for successful health check response
        if response.status_code == 200:
          # Check if response is JSON
          content_type = response.headers.get('content-type', '')
          if 'application/json' in content_type:
            try:
              data = response.json()
              console.print(f'[dim]Response: {data}[/dim]')
              if data.get('status') == 'healthy':
                console.print('[green]✅ App health check passed[/green]')
                console.print(f'[dim]Database status: {data.get("database", "unknown")}[/dim]')
                health_check_passed = True
                break  # Success, exit retry loop
              else:
                console.print(f'[yellow]⚠️  App health check returned: {data}[/yellow]')
            except Exception as json_err:
              console.print(f'[yellow]⚠️  Failed to parse JSON: {json_err}[/yellow]')
              console.print(f'[dim]Response preview: {response.text[:200]}[/dim]')
          else:
            console.print('[yellow]⚠️  Health endpoint returned non-JSON response[/yellow]')
            console.print(f'[dim]Response preview: {response.text[:200]}[/dim]')
        else:
          console.print(
            f'[yellow]⚠️  Health endpoint returned status {response.status_code}[/yellow]'
          )
          console.print(f'[dim]Response preview: {response.text[:200]}[/dim]')

      except Exception as e:
        console.print(f'[yellow]⚠️  Health check attempt {attempt} failed: {e}[/yellow]')
        import traceback
        console.print(f'[dim]{traceback.format_exc()}[/dim]')

      # Wait before next retry (exponential backoff)
      if attempt < max_retries:
        wait_time = 5 * attempt  # 5s, 10s, 15s, 20s
        console.print(f'[dim]Waiting {wait_time}s before next attempt...[/dim]')
        time.sleep(wait_time)

    if not health_check_passed:
      console.print('[red]❌ Health check failed after all retries[/red]')
      return False

    # Test API endpoint (requires OAuth, may redirect)
    try:
      api_url = f'{app_url}/api/user/me'
      response = httpx.get(api_url, timeout=10, follow_redirects=False)

      # Expect either 200 (if we have valid session) or 401/302 (needs auth)
      if response.status_code in [200, 401, 302, 303]:
        console.print('[green]✅ API endpoints accessible[/green]')
      else:
        console.print(
          f'[yellow]⚠️  API endpoint returned unexpected status: {response.status_code}[/yellow]'
        )

    except Exception as e:
      console.print(f'[yellow]⚠️  Could not test API endpoint: {e}[/yellow]')

    return True

  except Exception as e:
    console.print(f'[red]❌ Error testing deployed app: {e}[/red]')
    return False


def test_job_triggering(job_id: int, timeout: int = 60) -> bool:
  """Test job can be triggered.

  Args:
      job_id: Databricks job ID
      timeout: Maximum seconds to wait for job to complete (optional, for lightweight test)

  Returns:
      True if job can be triggered, False otherwise
  """
  try:
    console.print(f'[cyan]Testing job triggering (Job ID: {job_id})...[/cyan]')

    # Trigger job run
    result = subprocess.run(
      ['databricks', 'jobs', 'run-now', '--job-id', str(job_id), '--output', 'json'],
      capture_output=True,
      text=True,
    )

    if result.returncode != 0:
      console.print(f'[red]❌ Failed to trigger job: {result.stderr}[/red]')
      return False

    # Parse run ID from output
    try:
      import json

      output = json.loads(result.stdout)
      run_id = output.get('run_id')

      if not run_id:
        console.print('[yellow]⚠️  Job triggered but could not get run ID[/yellow]')
        return True  # Still consider success since trigger worked

      console.print(f'[green]✅ Job triggered successfully (Run ID: {run_id})[/green]')

      # Optional: Poll for completion (lightweight test, short timeout)
      if timeout > 0:
        console.print(f'[dim]Polling job status (timeout: {timeout}s)...[/dim]')
        start_time = time.time()

        while time.time() - start_time < timeout:
          status_result = subprocess.run(
            ['databricks', 'jobs', 'get-run', '--run-id', str(run_id), '--output', 'json'],
            capture_output=True,
            text=True,
          )

          if status_result.returncode == 0:
            status = json.loads(status_result.stdout)
            state = status.get('state', {}).get('life_cycle_state')

            if state in ['TERMINATED', 'SKIPPED']:
              result_state = status.get('state', {}).get('result_state')
              if result_state == 'SUCCESS':
                console.print('[green]✅ Job completed successfully[/green]')
              else:
                console.print(f'[yellow]⚠️  Job completed with state: {result_state}[/yellow]')
              return True

          time.sleep(5)

        console.print(f'[dim]Job still running after {timeout}s (this is expected)[/dim]')

      return True

    except Exception as e:
      console.print(f'[yellow]⚠️  Could not parse job output: {e}[/yellow]')
      return True  # Still success since trigger worked

  except Exception as e:
    console.print(f'[red]❌ Error testing job: {e}[/red]')
    return False


def test_database_connection(host: str, port: int, database: str, user: str, password: str) -> bool:
  """Test database connection.

  Args:
      host: Database host
      port: Database port
      database: Database name
      user: Database user
      password: Database password

  Returns:
      True if connection successful, False otherwise
  """
  try:
    import psycopg2

    console.print(f'[cyan]Testing database connection to {host}:{port}/{database}[/cyan]')

    conn = psycopg2.connect(
      host=host,
      port=port,
      database=database,
      user=user,
      password=password,
      sslmode='require',
      connect_timeout=10,
    )

    # Test with a simple query
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    cursor.fetchone()
    cursor.close()
    conn.close()

    console.print('[green]✅ Database connection successful[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Database connection failed: {e}[/red]')
    return False
