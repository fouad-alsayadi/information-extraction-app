"""Validate configuration consistency across all config files.

This script ensures that config/base.yaml and app.yaml are in sync.
Run this before deployment to catch configuration drift.

Usage:
    uv run python scripts/validate_config.py
    uv run python scripts/validate_config.py --auto-fix  # Fix mismatches automatically
"""

import sys
from pathlib import Path

import yaml


def validate_config(auto_fix: bool = False) -> bool:
  """Validate that config/base.yaml matches app.yaml values.

  Args:
      auto_fix: If True, automatically fix mismatches by updating app.yaml

  Returns:
      True if configuration is consistent, False otherwise
  """
  project_root = Path(__file__).parent.parent

  # Load base config
  base_config_path = project_root / 'config' / 'base.yaml'
  if not base_config_path.exists():
    print(f'❌ Configuration file not found: {base_config_path}')
    return False

  with open(base_config_path) as f:
    base = yaml.safe_load(f)

  # Load app.yaml
  app_yaml_path = project_root / 'app.yaml'
  if not app_yaml_path.exists():
    print(f'❌ app.yaml not found: {app_yaml_path}')
    return False

  with open(app_yaml_path) as f:
    app = yaml.safe_load(f)

  errors = []

  # Validate database config
  app_env = {item['name']: item.get('value') for item in app.get('env', []) if 'value' in item}

  # Check database host
  if app_env.get('DB_HOST') != base['database']['host']:
    errors.append(
      f'DB_HOST mismatch:\n'
      f'  app.yaml = {app_env.get("DB_HOST")}\n'
      f'  base.yaml = {base["database"]["host"]}'
    )

  # Check database port
  if app_env.get('DB_PORT'):
    try:
      app_port = int(app_env.get('DB_PORT'))
      if app_port != base['database']['port']:
        errors.append(
          f'DB_PORT mismatch:\n  app.yaml = {app_port}\n  base.yaml = {base["database"]["port"]}'
        )
    except (ValueError, TypeError):
      errors.append(f'DB_PORT in app.yaml is not a valid integer: {app_env.get("DB_PORT")}')

  # Check database name
  if app_env.get('DB_NAME') != base['database']['name']:
    errors.append(
      f'DB_NAME mismatch:\n'
      f'  app.yaml = {app_env.get("DB_NAME")}\n'
      f'  base.yaml = {base["database"]["name"]}'
    )

  # Check database user
  if app_env.get('DB_USER') != base['database']['user']:
    errors.append(
      f'DB_USER mismatch:\n'
      f'  app.yaml = {app_env.get("DB_USER")}\n'
      f'  base.yaml = {base["database"]["user"]}'
    )

  # Report results
  if errors:
    print('❌ Configuration validation failed:\n')
    for i, error in enumerate(errors, 1):
      print(f'{i}. {error}\n')

    if auto_fix:
      print('🔧 Auto-fixing mismatches...')
      if _auto_fix_app_yaml(app_yaml_path, base, app):
        print('✅ app.yaml has been updated to match config/base.yaml')
        return True
      else:
        print('❌ Failed to auto-fix app.yaml')
        return False
    else:
      print('💡 Fix: Update app.yaml or config/base.yaml to match')
      print('   config/base.yaml is the single source of truth')
      print('   app.yaml should reference the same values')
      print('   Or run with --auto-fix to automatically update app.yaml')
      return False

  print('✅ Configuration is consistent')
  print(f'   Validated: {base_config_path.name} ⟷ {app_yaml_path.name}')
  return True


def _auto_fix_app_yaml(app_yaml_path: Path, base: dict, app: dict) -> bool:
  """Auto-fix app.yaml to match base.yaml configuration.

  Args:
      app_yaml_path: Path to app.yaml
      base: Parsed base.yaml config
      app: Parsed app.yaml config

  Returns:
      True if successful, False otherwise
  """
  try:
    # Update app.yaml env vars to match base.yaml
    env_vars = app.get('env', [])
    env_map = {item['name']: item for item in env_vars if 'name' in item}

    # Update database settings
    if 'database' in base:
      db = base['database']
      env_map.setdefault('DB_HOST', {'name': 'DB_HOST'})['value'] = db.get('host', '')
      env_map.setdefault('DB_PORT', {'name': 'DB_PORT'})['value'] = str(db.get('port', 5432))
      env_map.setdefault('DB_NAME', {'name': 'DB_NAME'})['value'] = db.get('name', '')
      env_map.setdefault('DB_USER', {'name': 'DB_USER'})['value'] = db.get('user', '')

    # Rebuild env list with updated values
    updated_env = list(env_map.values())
    app['env'] = updated_env

    # Write back to file
    with open(app_yaml_path, 'w') as f:
      yaml.safe_dump(app, f, default_flow_style=False, sort_keys=False)

    return True

  except Exception as e:
    print(f'Error auto-fixing app.yaml: {e}')
    return False


if __name__ == '__main__':
  # Check for --auto-fix flag
  auto_fix = '--auto-fix' in sys.argv
  success = validate_config(auto_fix=auto_fix)
  sys.exit(0 if success else 1)
