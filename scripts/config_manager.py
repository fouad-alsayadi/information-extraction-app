"""Configuration file management for setup wizard.

This module provides safe operations for updating configuration files including:
- config/base.yaml updates
- config/secrets.yaml creation
- app.yaml synchronization
- Configuration validation
"""

from pathlib import Path
from typing import Any, Dict, List

import yaml
from rich.console import Console

console = Console()


def update_base_config(updates: Dict[str, Any]) -> bool:
  """Update config/base.yaml with new values.

  Performs deep merge of updates into existing configuration while
  preserving structure and comments where possible.

  Args:
      updates: Dictionary of updates to merge into base config

  Returns:
      True if update successful, False otherwise
  """
  try:
    config_path = Path('config/base.yaml')

    if not config_path.exists():
      console.print(f'[red]❌ Config file not found: {config_path}[/red]')
      return False

    # Load existing config
    with open(config_path) as f:
      config = yaml.safe_load(f) or {}

    # Deep merge updates
    _deep_merge(config, updates)

    # Write back atomically (write to temp, then rename)
    temp_path = config_path.with_suffix('.yaml.tmp')
    with open(temp_path, 'w') as f:
      yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    # Atomic rename
    temp_path.replace(config_path)

    console.print(f'[green]✅ Updated {config_path}[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error updating config: {e}[/red]')
    return False


def _deep_merge(base: dict, overlay: dict) -> None:
  """Deep merge overlay dict into base dict.

  Modifies base in-place. Skips None values in overlay to avoid overwriting base values.

  Args:
      base: Base dictionary to merge into
      overlay: Dictionary to merge from
  """
  for key, value in overlay.items():
    # Skip None values - don't overwrite base config with empty overrides
    if value is None:
      continue

    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
      _deep_merge(base[key], value)
    else:
      base[key] = value


def create_secrets_yaml(db_password: str, upload_base_path: str = None) -> bool:
  """Create config/secrets.yaml from template.

  Args:
      db_password: Database password
      upload_base_path: Optional upload base path override

  Returns:
      True if creation successful, False otherwise
  """
  try:
    secrets_path = Path('config/secrets.yaml')

    if secrets_path.exists():
      console.print('[yellow]⚠️  config/secrets.yaml already exists, skipping[/yellow]')
      return True

    # Create secrets dict
    secrets = {'database': {'password': db_password}}

    if upload_base_path:
      secrets['upload'] = {'base_path': upload_base_path}

    # Write secrets file
    with open(secrets_path, 'w') as f:
      yaml.safe_dump(secrets, f, default_flow_style=False)

    console.print(f'[green]✅ Created {secrets_path}[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error creating secrets file: {e}[/red]')
    return False


def update_app_yaml_from_base() -> bool:
  """Sync app.yaml environment variables from base.yaml.

  Reads config/base.yaml and updates app.yaml environment variables to match,
  preserving other app.yaml settings.

  Returns:
      True if sync successful, False otherwise
  """
  try:
    base_path = Path('config/base.yaml')
    app_path = Path('app.yaml')

    if not base_path.exists():
      console.print(f'[red]❌ {base_path} not found[/red]')
      return False

    if not app_path.exists():
      console.print(f'[red]❌ {app_path} not found[/red]')
      return False

    # Load both files
    with open(base_path) as f:
      base = yaml.safe_load(f) or {}

    with open(app_path) as f:
      app = yaml.safe_load(f) or {}

    # Update app.yaml env vars to match base.yaml
    env_vars = app.get('env', [])
    env_map = {item['name']: item for item in env_vars if 'name' in item}

    # Update database settings
    if 'database' in base:
      db = base['database']
      env_map.setdefault('DB_HOST', {})['value'] = db.get('host', '')
      env_map.setdefault('DB_PORT', {})['value'] = str(db.get('port', 5432))
      env_map.setdefault('DB_NAME', {})['value'] = db.get('name', '')
      env_map.setdefault('DB_USER', {})['value'] = db.get('user', '')

    # Update job ID
    if 'databricks' in base and 'job_id' in base['databricks']:
      env_map.setdefault('DATABRICKS_JOB_ID', {})['value'] = str(base['databricks']['job_id'])

    # Update upload base path
    if 'upload' in base and 'base_path' in base['upload']:
      env_map.setdefault('UPLOAD_BASE_PATH', {})['value'] = base['upload']['base_path']

    # Rebuild env list with updated values
    updated_env = []
    for name, item in env_map.items():
      item['name'] = name
      updated_env.append(item)

    app['env'] = updated_env

    # Write back
    with open(app_path, 'w') as f:
      yaml.safe_dump(app, f, default_flow_style=False, sort_keys=False)

    console.print(f'[green]✅ Synced {app_path} with {base_path}[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error syncing app.yaml: {e}[/red]')
    return False


def validate_config_consistency() -> List[str]:
  """Validate all configs are consistent.

  Runs validation checks and returns list of errors found.

  Returns:
      List of error messages (empty if valid)
  """
  try:
    base_path = Path('config/base.yaml')
    app_path = Path('app.yaml')

    errors = []

    if not base_path.exists():
      errors.append(f'{base_path} not found')
      return errors

    if not app_path.exists():
      errors.append(f'{app_path} not found')
      return errors

    # Load both files
    with open(base_path) as f:
      base = yaml.safe_load(f) or {}

    with open(app_path) as f:
      app = yaml.safe_load(f) or {}

    # Build env map from app.yaml
    env_vars = app.get('env', [])
    env_map = {item['name']: item.get('value') for item in env_vars if 'name' in item}

    # Check database config
    if 'database' in base:
      db = base['database']

      if env_map.get('DB_HOST') != db.get('host'):
        errors.append(
          f'DB_HOST mismatch: app.yaml={env_map.get("DB_HOST")} vs base.yaml={db.get("host")}'
        )

      if env_map.get('DB_PORT') and int(env_map.get('DB_PORT', 0)) != db.get('port', 5432):
        errors.append(
          f'DB_PORT mismatch: app.yaml={env_map.get("DB_PORT")} vs base.yaml={db.get("port")}'
        )

      if env_map.get('DB_NAME') != db.get('name'):
        errors.append(
          f'DB_NAME mismatch: app.yaml={env_map.get("DB_NAME")} vs base.yaml={db.get("name")}'
        )

      if env_map.get('DB_USER') != db.get('user'):
        errors.append(
          f'DB_USER mismatch: app.yaml={env_map.get("DB_USER")} vs base.yaml={db.get("user")}'
        )

    return errors

  except Exception as e:
    return [f'Error validating config: {e}']


def add_job_config_section() -> bool:
  """Add job configuration section to config/base.yaml.

  This reads values from database, databricks, and secrets sections
  to avoid duplication and ensure consistency.

  Returns:
      True if update successful, False otherwise
  """
  try:
    # Read existing config
    base_yaml = Path('config/base.yaml')
    if not base_yaml.exists():
      console.print('[red]❌ config/base.yaml not found[/red]')
      return False

    with open(base_yaml) as f:
      config = yaml.safe_load(f) or {}

    # Get values from existing sections
    database = config.get('database', {})
    databricks = config.get('databricks', {})
    secrets = config.get('secrets', {})
    db_password = secrets.get('database_password', {})

    # Construct job config from existing values
    job_config = {
      'job': {
        'db_password_scope': db_password.get('scope', ''),
        'lakebase_db_password_key': db_password.get('key', ''),
        'lakebase_instance_host': database.get('host', ''),
        'lakebase_db_name': database.get('name', ''),
        'lakebase_schema_name': database.get('schema', ''),
        'ai_parse_document_output_table': databricks.get('output_table', ''),
      }
    }

    return update_base_config(job_config)

  except Exception as e:
    console.print(f'[red]❌ Error adding job config section: {e}[/red]')
    return False


def get_config_value(key_path: str) -> Any:
  """Get a value from config/base.yaml by dot-separated path.

  Args:
      key_path: Dot-separated path like 'database.host'

  Returns:
      Config value at path, or None if not found
  """
  try:
    config_path = Path('config/base.yaml')

    if not config_path.exists():
      return None

    with open(config_path) as f:
      config = yaml.safe_load(f) or {}

    # Navigate through nested dict
    keys = key_path.split('.')
    value = config
    for key in keys:
      if isinstance(value, dict) and key in value:
        value = value[key]
      else:
        return None

    return value

  except Exception:
    return None
