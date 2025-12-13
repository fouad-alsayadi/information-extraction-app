"""Databricks resource management helpers for setup wizard.

This module provides functions for managing Databricks resources including:
- Unity Catalog Volumes
- Secrets
- Workspace file operations
- Job bundle deployment
- App creation with resources
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

import yaml
from databricks.sdk import WorkspaceClient
from rich.console import Console

console = Console()


def get_databricks_profile() -> Optional[str]:
  """Get Databricks profile from environment or .env.local.

  Returns:
      Profile name if using profile auth, None if using PAT auth
  """
  # Check environment variable first
  profile = os.getenv('DATABRICKS_CONFIG_PROFILE')
  if profile:
    return profile

  # Check .env.local file
  env_local = Path('.env.local')
  if env_local.exists():
    try:
      with open(env_local) as f:
        for line in f:
          if line.strip().startswith('DATABRICKS_CONFIG_PROFILE='):
            profile = line.strip().split('=', 1)[1].strip()
            return profile
    except Exception:
      pass

  return None


def build_databricks_cmd(cmd_parts: List[str]) -> List[str]:
  """Build Databricks CLI command with consistent profile.

  Args:
      cmd_parts: Command parts (e.g., ['databricks', 'catalogs', 'list'])

  Returns:
      Command with --profile flag if using profile auth
  """
  profile = get_databricks_profile()

  if profile:
    # Insert --profile flag after 'databricks' command
    return [cmd_parts[0], '--profile', profile] + cmd_parts[1:]

  return cmd_parts


def check_catalog_exists(catalog: str) -> bool:
  """Check if Unity Catalog exists.

  Args:
      catalog: Catalog name

  Returns:
      True if catalog exists, False otherwise
  """
  try:
    cmd = build_databricks_cmd(['databricks', 'catalogs', 'list'])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[yellow]⚠️  Could not list catalogs: {result.stderr}[/yellow]')
      return False

    # Check if catalog name appears in output
    return catalog in result.stdout

  except Exception as e:
    console.print(f'[red]❌ Error checking catalog: {e}[/red]')
    return False


def create_catalog(catalog: str) -> bool:
  """Create Unity Catalog.

  Args:
      catalog: Catalog name

  Returns:
      True if successful, False otherwise
  """
  try:
    console.print(f'[cyan]Creating catalog: {catalog}[/cyan]')

    cmd = build_databricks_cmd(['databricks', 'catalogs', 'create', catalog])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[red]❌ Failed to create catalog: {result.stderr}[/red]')
      return False

    console.print(f'[green]✅ Catalog created: {catalog}[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error creating catalog: {e}[/red]')
    return False


def check_schema_exists(catalog: str, schema: str) -> bool:
  """Check if schema exists in catalog.

  Args:
      catalog: Catalog name
      schema: Schema name

  Returns:
      True if schema exists, False otherwise
  """
  try:
    cmd = build_databricks_cmd(['databricks', 'schemas', 'list', catalog])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[yellow]⚠️  Could not list schemas: {result.stderr}[/yellow]')
      return False

    # Check if schema name appears in output
    return schema in result.stdout

  except Exception as e:
    console.print(f'[red]❌ Error checking schema: {e}[/red]')
    return False


def create_schema(catalog: str, schema: str) -> bool:
  """Create schema in catalog.

  Args:
      catalog: Catalog name
      schema: Schema name

  Returns:
      True if successful, False otherwise
  """
  try:
    console.print(f'[cyan]Creating schema: {catalog}.{schema}[/cyan]')

    cmd = build_databricks_cmd(['databricks', 'schemas', 'create', f'{catalog}.{schema}'])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[red]❌ Failed to create schema: {result.stderr}[/red]')
      return False

    console.print(f'[green]✅ Schema created: {catalog}.{schema}[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error creating schema: {e}[/red]')
    return False


def check_volume_exists(volume_path: str) -> bool:
  """Check if UC Volume exists using CLI.

  Args:
      volume_path: Full volume path like /Volumes/catalog/schema/volume_name

  Returns:
      True if volume exists, False otherwise
  """
  try:
    # Parse volume path
    parts = volume_path.strip('/').split('/')
    if len(parts) != 4 or parts[0] != 'Volumes':
      console.print(f'[yellow]⚠️  Invalid volume path format: {volume_path}[/yellow]')
      return False

    catalog, schema, volume_name = parts[1], parts[2], parts[3]

    # Check if volume exists
    cmd = build_databricks_cmd(['databricks', 'volumes', 'list', catalog, schema])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[yellow]⚠️  Could not list volumes: {result.stderr}[/yellow]')
      return False

    # Check if volume_name appears in output
    return volume_name in result.stdout

  except Exception as e:
    console.print(f'[red]❌ Error checking volume: {e}[/red]')
    return False


def create_volume(catalog: str, schema: str, volume_name: str) -> Optional[str]:
  """Create UC Volume and return full path.

  Args:
      catalog: Unity Catalog name
      schema: Schema name
      volume_name: Volume name

  Returns:
      Full volume path if successful, None otherwise
  """
  try:
    console.print(f'[cyan]Creating volume: {catalog}.{schema}.{volume_name}[/cyan]')

    cmd = build_databricks_cmd(
      ['databricks', 'volumes', 'create', catalog, schema, volume_name, 'MANAGED']
    )
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[red]❌ Failed to create volume: {result.stderr}[/red]')
      return None

    volume_path = f'/Volumes/{catalog}/{schema}/{volume_name}'
    console.print(f'[green]✅ Volume created: {volume_path}[/green]')
    return volume_path

  except Exception as e:
    console.print(f'[red]❌ Error creating volume: {e}[/red]')
    return None


def test_volume_write(volume_path: str) -> bool:
  """Test write permissions by uploading and deleting a test file.

  Args:
      volume_path: Full volume path

  Returns:
      True if write permissions verified, False otherwise
  """
  try:
    # Create a temporary test file
    test_filename = '.setup_wizard_test_file.txt'
    test_content = 'Setup wizard test - please delete'

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
      tmp.write(test_content)
      temp_path = tmp.name

    # Upload using WorkspaceClient
    w = WorkspaceClient()
    remote_path = f'{volume_path}/{test_filename}'

    console.print(f'[cyan]Testing write permissions to {volume_path}[/cyan]')

    # Upload test file
    with open(temp_path, 'rb') as f:
      w.files.upload(remote_path, f)

    console.print('[green]✅ Write test successful[/green]')

    # Clean up: Delete the test file
    try:
      w.files.delete(remote_path)
      console.print('[green]✅ Test file cleaned up[/green]')
    except Exception as e:
      console.print(f'[yellow]⚠️  Could not delete test file: {e}[/yellow]')

    # Clean up local temp file
    os.unlink(temp_path)

    return True

  except Exception as e:
    console.print(f'[red]❌ Write test failed: {e}[/red]')
    # Clean up temp file if it exists
    try:
      if 'temp_path' in locals():
        os.unlink(temp_path)
    except Exception:
      pass
    return False


def check_secret_exists(scope: str, key: str) -> bool:
  """Check if Databricks secret exists.

  Args:
      scope: Secret scope name
      key: Secret key name

  Returns:
      True if secret exists, False otherwise
  """
  try:
    cmd = build_databricks_cmd(['databricks', 'secrets', 'list-secrets', '--scope', scope])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      # Scope might not exist
      return False

    # Check if key appears in output
    return key in result.stdout

  except Exception as e:
    console.print(f'[yellow]⚠️  Error checking secret: {e}[/yellow]')
    return False


def create_secret(scope: str, key: str, value: str) -> bool:
  """Create Databricks secret.

  Args:
      scope: Secret scope name
      key: Secret key name
      value: Secret value

  Returns:
      True if secret created successfully, False otherwise
  """
  try:
    console.print(f'[cyan]Creating secret: {scope}/{key}[/cyan]')

    # First check if scope exists, create if it doesn't
    cmd = build_databricks_cmd(['databricks', 'secrets', 'list-scopes'])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if scope not in result.stdout:
      console.print(f'[cyan]Creating secret scope: {scope}[/cyan]')
      cmd = build_databricks_cmd(['databricks', 'secrets', 'create-scope', scope])
      result = subprocess.run(cmd, capture_output=True, text=True)
      if result.returncode != 0:
        console.print(f'[red]❌ Failed to create scope: {result.stderr}[/red]')
        return False

    # Create the secret using string input
    cmd = build_databricks_cmd(
      ['databricks', 'secrets', 'put-secret', scope, key, '--string-value', value]
    )
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[red]❌ Failed to create secret: {result.stderr}[/red]')
      return False

    console.print(f'[green]✅ Secret created: {scope}/{key}[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error creating secret: {e}[/red]')
    return False


def sync_project_to_workspace(workspace_path: str) -> bool:
  """Sync entire project to workspace including notebooks and config.

  Uses `databricks sync` to sync the project directory, respecting .gitignore.

  Args:
      workspace_path: Workspace destination path

  Returns:
      True if sync successful, False otherwise
  """
  try:
    console.print(f'[cyan]Syncing project to workspace: {workspace_path}[/cyan]')
    console.print('[dim]This may take a moment...[/dim]')

    # Run databricks sync with current directory
    cmd = build_databricks_cmd(['databricks', 'sync', '.', workspace_path])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
      console.print(f'[red]❌ Sync failed: {result.stderr}[/red]')
      return False

    console.print('[green]✅ Project synced to workspace[/green]')
    console.print(f'[dim]Location: {workspace_path}[/dim]')
    return True

  except subprocess.TimeoutExpired:
    console.print('[red]❌ Sync timed out after 2 minutes[/red]')
    return False
  except Exception as e:
    console.print(f'[red]❌ Error syncing to workspace: {e}[/red]')
    return False


def update_lakeflow_config(
  config_path: str,
  workspace_notebook_path: str,
) -> bool:
  """Update lakeflow-conf.yaml with deployment settings.

  Args:
      config_path: Path to lakeflow-conf.yaml
      workspace_notebook_path: Full workspace path to the notebook

  Returns:
      True if update successful, False otherwise
  """
  try:
    console.print(f'[cyan]Updating {config_path}[/cyan]')

    # Load existing YAML
    with open(config_path) as f:
      config = yaml.safe_load(f)

    # Update notebook_path in job configuration
    if 'resources' in config and 'jobs' in config['resources']:
      for job_name, job_config in config['resources']['jobs'].items():
        if 'tasks' in job_config:
          for task in job_config['tasks']:
            if 'notebook_task' in task:
              task['notebook_task']['notebook_path'] = workspace_notebook_path
              console.print(f'[green]✅ Updated notebook_path: {workspace_notebook_path}[/green]')

    # Write back to file
    with open(config_path, 'w') as f:
      yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    return True

  except Exception as e:
    console.print(f'[red]❌ Error updating lakeflow config: {e}[/red]')
    return False


def deploy_job_bundle(bundle_path: str) -> Optional[dict]:
  """Deploy job bundle and return job metadata including ID.

  Args:
      bundle_path: Path to job bundle directory

  Returns:
      Dict with job metadata including 'job_id', or None if failed
  """
  try:
    console.print('[cyan]Deploying Databricks job bundle...[/cyan]')

    # Change to bundle directory and deploy
    original_dir = os.getcwd()
    os.chdir(bundle_path)

    try:
      # Deploy the bundle (no JSON output available)
      cmd = build_databricks_cmd(['databricks', 'bundle', 'deploy'])
      result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

      if result.returncode != 0:
        console.print(f'[red]❌ Bundle deploy failed: {result.stderr}[/red]')
        return None

      console.print('[green]✅ Bundle deployed successfully[/green]')

      # Get bundle summary to extract job ID
      cmd = build_databricks_cmd(['databricks', 'bundle', 'summary'])
      summary_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

      if summary_result.returncode != 0:
        console.print(f'[yellow]⚠️  Could not get bundle summary: {summary_result.stderr}[/yellow]')
        return None

      # Parse summary output to extract job ID
      # Looking for pattern: "URL:  https://...jobs/123456?..."
      job_id = None
      for line in summary_result.stdout.split('\n'):
        if 'URL:' in line and '/jobs/' in line:
          # Extract job ID from URL
          try:
            url_part = line.split('URL:')[1].strip()
            job_id_str = url_part.split('/jobs/')[1].split('?')[0]
            job_id = int(job_id_str)
            break
          except (IndexError, ValueError):
            continue

      if not job_id:
        console.print('[yellow]⚠️  Could not extract job_id from bundle summary[/yellow]')
        console.print(f'[dim]Summary output:\n{summary_result.stdout}[/dim]')
        return None

      console.print(f'[green]✅ Job bundle deployed successfully[/green]')
      console.print(f'[green]   Job ID: {job_id}[/green]')

      return {'job_id': job_id}

    finally:
      os.chdir(original_dir)

  except subprocess.TimeoutExpired:
    console.print('[red]❌ Bundle deploy timed out after 3 minutes[/red]')
    return None
  except Exception as e:
    console.print(f'[red]❌ Error deploying bundle: {e}[/red]')
    return None


def check_job_exists(job_id: int) -> bool:
  """Verify job exists and is accessible.

  Args:
      job_id: Databricks job ID

  Returns:
      True if job exists, False otherwise
  """
  try:
    cmd = build_databricks_cmd(['databricks', 'jobs', 'get', str(job_id)])
    result = subprocess.run(cmd, capture_output=True, text=True)

    return result.returncode == 0

  except Exception as e:
    console.print(f'[yellow]⚠️  Error checking job: {e}[/yellow]')
    return False


def get_secret_config() -> Optional[dict]:
  """Load secret configuration from base.yaml.

  Returns:
      Secret config dict with 'scope' and 'key', or None if not found
  """
  try:
    base_yaml = Path('config/base.yaml')
    if not base_yaml.exists():
      return None

    with open(base_yaml) as f:
      config = yaml.safe_load(f)

    secrets = config.get('secrets', {})
    db_password = secrets.get('database_password', {})

    if 'scope' in db_password and 'key' in db_password:
      return db_password

    return None
  except Exception as e:
    console.print(f'[yellow]⚠️  Could not read secret config from base.yaml: {e}[/yellow]')
    return None


def check_app_exists(app_name: str) -> bool:
  """Check if Databricks App exists.

  Args:
      app_name: Name of the app

  Returns:
      True if app exists, False otherwise
  """
  try:
    cmd = build_databricks_cmd(['databricks', 'apps', 'get', app_name])
    result = subprocess.run(cmd, capture_output=True, text=True)

    return result.returncode == 0

  except Exception as e:
    console.print(f'[yellow]⚠️  Error checking app: {e}[/yellow]')
    return False


def get_app_service_principal(app_name: str) -> Optional[str]:
  """Get service principal ID from an existing app.

  Args:
      app_name: Name of the app

  Returns:
      Service principal ID if found, None otherwise
  """
  try:
    cmd = build_databricks_cmd(['databricks', 'apps', 'get', app_name, '--output', 'json'])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[yellow]⚠️  Could not get app details: {result.stderr}[/yellow]')
      return None

    app_data = json.loads(result.stdout)
    service_principal_id = app_data.get('service_principal_id')

    return service_principal_id

  except Exception as e:
    console.print(f'[yellow]⚠️  Error getting app service principal: {e}[/yellow]')
    return None


def update_app_resources(app_name: str, job_id: int, volume_path: str) -> bool:
  """Update Databricks App resources.

  Args:
      app_name: Name of the app
      job_id: Job ID to attach as resource
      volume_path: Volume path to attach as resource

  Returns:
      True if update successful, False otherwise
  """
  try:
    console.print(f'[cyan]Updating app resources: {app_name}[/cyan]')
    volume_path_parts = volume_path.split('/')
    volume_qualified_name = '.'.join(
      [volume_path_parts[-3], volume_path_parts[-2], volume_path_parts[-1]]
    )

    # Get secret configuration from base.yaml
    secret_config = get_secret_config()
    if not secret_config:
      console.print('[yellow]⚠️  Could not read secret config, using defaults[/yellow]')
      secret_config = {'scope': 'information_extraction', 'key': 'lakebase_db_password'}

    # Build JSON payload for update
    # Resource names must match app.yaml valueFrom values
    payload = {
      'resources': [
        {
          'name': 'information_extraction_job',  # Matches valueFrom in app.yaml
          'job': {'id': str(job_id), 'permission': 'CAN_MANAGE_RUN'}
        },
        {
          'name': 'documents_upload_volume',  # Matches valueFrom in app.yaml
          'uc_securable': {
            'permission': 'WRITE_VOLUME',
            'securable_full_name': volume_qualified_name,
            'securable_type': 'VOLUME',
          },
        },
        {
          'name': 'lakebase_db_password',  # Matches valueFrom in app.yaml
          'secret': {
            'scope': secret_config['scope'],
            'key': secret_config['key'],
            'permission': 'READ'
          },
        },
      ]
    }

    # Update app using --json flag
    cmd = build_databricks_cmd(['databricks', 'apps', 'update', app_name, '--json', json.dumps(payload)])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[red]❌ App update failed: {result.stderr}[/red]')
      return False

    console.print(f'[green]✅ App resources updated[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error updating app: {e}[/red]')
    return False


def grant_app_table_permissions(service_principal_id: str, catalog: str, schema: str) -> bool:
  """Grant app service principal permissions on catalog, schema, and tables.

  Args:
      service_principal_id: App service principal application ID
      catalog: Catalog name
      schema: Schema name

  Returns:
      True if all grants successful, False otherwise
  """
  try:
    console.print(f'[cyan]Granting table permissions to app service principal...[/cyan]')

    # Grant USE CATALOG on catalog
    console.print(f'[dim]Granting USE CATALOG on {catalog}...[/dim]')
    catalog_payload = {
      'changes': [
        {
          'principal': service_principal_id,
          'add': ['USE_CATALOG']
        }
      ]
    }

    cmd = build_databricks_cmd([
      'databricks', 'grants', 'update',
      'catalog', catalog,
      '--json', json.dumps(catalog_payload)
    ])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[yellow]⚠️  Could not grant USE CATALOG: {result.stderr}[/yellow]')
      # Don't fail - continue with other grants
    else:
      console.print(f'[green]✅ Granted USE CATALOG on {catalog}[/green]')

    # Grant USE SCHEMA + SELECT + MODIFY on schema
    console.print(f'[dim]Granting USE SCHEMA, SELECT, MODIFY on {catalog}.{schema}...[/dim]')
    schema_payload = {
      'changes': [
        {
          'principal': service_principal_id,
          'add': ['USE_SCHEMA', 'SELECT', 'MODIFY']
        }
      ]
    }

    cmd = build_databricks_cmd([
      'databricks', 'grants', 'update',
      'schema', f'{catalog}.{schema}',
      '--json', json.dumps(schema_payload)
    ])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[yellow]⚠️  Could not grant schema permissions: {result.stderr}[/yellow]')
      return False

    console.print(f'[green]✅ Granted USE SCHEMA, SELECT, MODIFY on {catalog}.{schema}[/green]')
    console.print('[green]✅ All table permissions granted successfully[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error granting permissions: {e}[/red]')
    return False


def create_app_with_resources(app_name: str, job_id: int, volume_path: str) -> Optional[dict]:
  """Create Databricks App with resource configuration.

  Args:
      app_name: Name for the Databricks App
      job_id: Job ID to attach as resource
      volume_path: Volume path to attach as resource

  Returns:
      Dict with app metadata including 'url', or None if failed
  """
  try:
    console.print(f'[cyan]Creating Databricks App: {app_name}[/cyan]')
    volume_path_parts = volume_path.split('/')
    volume_qualified_name = '.'.join([volume_path_parts[-3], volume_path_parts[-2], volume_path_parts[-1]])

    # Get secret configuration from base.yaml
    secret_config = get_secret_config()
    if not secret_config:
      console.print('[yellow]⚠️  Could not read secret config, using defaults[/yellow]')
      secret_config = {'scope': 'information_extraction', 'key': 'lakebase_db_password'}

    # Build JSON payload
    # Resource names must match app.yaml valueFrom values
    payload = {
      'name': app_name,
      'resources': [
        {
          'name': 'information_extraction_job',  # Matches valueFrom in app.yaml
          'job': {
            'id': str(job_id),
            'permission': 'CAN_MANAGE_RUN'
          }
        },
        {
          'name': 'documents_upload_volume',  # Matches valueFrom in app.yaml
          'uc_securable': {
            'permission': 'WRITE_VOLUME',
            'securable_full_name': volume_qualified_name,
            'securable_type': 'VOLUME'
          }
        },
        {
          'name': 'lakebase_db_password',  # Matches valueFrom in app.yaml
          'secret': {
            'scope': secret_config['scope'],
            'key': secret_config['key'],
            'permission': 'READ'
          }
        }
      ]
    }

    # Create app using --json flag
    cmd = build_databricks_cmd(['databricks', 'apps', 'create', '--json', json.dumps(payload)])
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
      console.print(f'[red]❌ App creation failed: {result.stderr}[/red]')
      return None

    # Parse response
    try:
      response = json.loads(result.stdout)
      app_url = response.get('url')

      console.print(f'[green]✅ App created successfully[/green]')
      if app_url:
        console.print(f'[green]   App URL: {app_url}[/green]')

      return response

    except json.JSONDecodeError as e:
      console.print(f'[yellow]⚠️  Could not parse app creation response: {e}[/yellow]')
      console.print(f'[dim]Output: {result.stdout}[/dim]')
      return {'raw_output': result.stdout}

  except Exception as e:
    console.print(f'[red]❌ Error creating app: {e}[/red]')
    return None
