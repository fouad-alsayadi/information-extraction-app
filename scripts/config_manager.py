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


def update_env_local(db_password: str) -> bool:
  """Update .env.local with database password.

  Args:
      db_password: Database password

  Returns:
      True if update successful, False otherwise
  """
  try:
    env_local_path = Path('.env.local')

    # Read existing .env.local if it exists
    existing_lines = []
    db_password_found = False

    if env_local_path.exists():
      with open(env_local_path) as f:
        for line in f:
          # Skip existing DB_PASSWORD line
          if line.strip().startswith('DB_PASSWORD='):
            db_password_found = True
            continue
          existing_lines.append(line.rstrip('\n'))

    # Add DB_PASSWORD at the end if not already there
    if not db_password_found:
      # Add empty line before secrets section if needed
      if existing_lines and existing_lines[-1] != '':
        existing_lines.append('')
      # Add comment if not present
      if '# Local development secrets' not in '\n'.join(existing_lines):
        existing_lines.append('# Local development secrets')

    # Always add the DB_PASSWORD line (either replacing or adding new)
    existing_lines.append(f'DB_PASSWORD={db_password}')

    # Write back to .env.local
    with open(env_local_path, 'w') as f:
      f.write('\n'.join(existing_lines))
      if existing_lines:  # Add final newline if there's content
        f.write('\n')

    console.print(f'[green]✅ Updated {env_local_path} with DB_PASSWORD[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error updating .env.local: {e}[/red]')
    return False


def update_app_yaml_with_resources() -> bool:
  """Update app.yaml with app resource references.

  All configuration comes from base.yaml. app.yaml only contains references
  to app resources (secrets, volumes, jobs) via valueFrom.

  Returns:
      True if update successful, False otherwise
  """
  try:
    app_path = Path('app.yaml')

    if not app_path.exists():
      console.print(f'[red]❌ {app_path} not found[/red]')
      return False

    # Load app.yaml
    with open(app_path) as f:
      app = yaml.safe_load(f) or {}

    # Update app.yaml with only resource references (no direct values)
    # These reference app resources defined when creating the Databricks App
    app['env'] = [
      {'name': 'APP_ENV', 'value': 'app'},
      {'name': 'DB_PASSWORD', 'valueFrom': 'lakebase_db_password'},
      {'name': 'UPLOAD_BASE_PATH', 'valueFrom': 'documents_upload_volume'},
      {'name': 'DATABRICKS_JOB_ID', 'valueFrom': 'information_extraction_job'},
    ]

    # Write back
    with open(app_path, 'w') as f:
      yaml.safe_dump(app, f, default_flow_style=False, sort_keys=False)

    console.print(f'[green]✅ Updated {app_path} with app resource references[/green]')
    return True

  except Exception as e:
    console.print(f'[red]❌ Error updating app.yaml: {e}[/red]')
    return False


def validate_config_consistency() -> List[str]:
  """Validate all configs are consistent.

  Runs validation checks and returns list of errors found.

  Since database config is centralized in base.yaml and only DB_PASSWORD
  is in app.yaml, there's minimal validation needed.

  Returns:
      List of error messages (empty if valid)
  """
  try:
    base_path = Path('config/base.yaml')
    app_path = Path('app.yaml')
    env_local_path = Path('.env.local')

    errors = []

    if not base_path.exists():
      errors.append(f'{base_path} not found')
      return errors

    if not app_path.exists():
      errors.append(f'{app_path} not found')
      return errors

    # Load config files
    with open(base_path) as f:
      base = yaml.safe_load(f) or {}

    with open(app_path) as f:
      app = yaml.safe_load(f) or {}

    # Check that base.yaml has required sections
    if 'database' not in base:
      errors.append('database section missing in base.yaml')

    if 'databricks' not in base:
      errors.append('databricks section missing in base.yaml')

    if 'upload' not in base:
      errors.append('upload section missing in base.yaml')

    # Check that app.yaml has required resource references
    env_vars = app.get('env', [])
    env_names = {item.get('name') for item in env_vars if 'name' in item}

    required_env_vars = {'DB_PASSWORD', 'UPLOAD_BASE_PATH', 'DATABRICKS_JOB_ID'}
    missing_vars = required_env_vars - env_names

    if missing_vars:
      errors.append(f'Missing required env variables in app.yaml: {", ".join(missing_vars)}')

    # Check that .env.local has DB_PASSWORD for local development
    if env_local_path.exists():
      with open(env_local_path) as f:
        env_local_content = f.read()
        if 'DB_PASSWORD=' not in env_local_content:
          errors.append('DB_PASSWORD not found in .env.local (required for local development)')

    return errors

  except Exception as e:
    return [f'Error validating config: {e}']


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
