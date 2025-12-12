"""Validate configuration consistency across all config files.

This script ensures that config/base.yaml and app.yaml are in sync.
Run this before deployment to catch configuration drift.

Usage:
    uv run python scripts/validate_config.py
"""

import sys
from pathlib import Path

import yaml


def validate_config() -> bool:
  """Validate that config/base.yaml matches app.yaml values.

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
      f"DB_HOST mismatch:\n"
      f"  app.yaml = {app_env.get('DB_HOST')}\n"
      f"  base.yaml = {base['database']['host']}"
    )

  # Check database port
  if app_env.get('DB_PORT'):
    try:
      app_port = int(app_env.get('DB_PORT'))
      if app_port != base['database']['port']:
        errors.append(
          f"DB_PORT mismatch:\n"
          f"  app.yaml = {app_port}\n"
          f"  base.yaml = {base['database']['port']}"
        )
    except (ValueError, TypeError):
      errors.append(f"DB_PORT in app.yaml is not a valid integer: {app_env.get('DB_PORT')}")

  # Check database name
  if app_env.get('DB_NAME') != base['database']['name']:
    errors.append(
      f"DB_NAME mismatch:\n"
      f"  app.yaml = {app_env.get('DB_NAME')}\n"
      f"  base.yaml = {base['database']['name']}"
    )

  # Check database user
  if app_env.get('DB_USER') != base['database']['user']:
    errors.append(
      f"DB_USER mismatch:\n"
      f"  app.yaml = {app_env.get('DB_USER')}\n"
      f"  base.yaml = {base['database']['user']}"
    )

  # Report results
  if errors:
    print('❌ Configuration validation failed:\n')
    for i, error in enumerate(errors, 1):
      print(f'{i}. {error}\n')
    print('💡 Fix: Update app.yaml or config/base.yaml to match')
    print('   config/base.yaml is the single source of truth')
    print('   app.yaml should reference the same values')
    return False

  print('✅ Configuration is consistent')
  print(f'   Validated: {base_config_path.name} ⟷ {app_yaml_path.name}')
  return True


if __name__ == '__main__':
  success = validate_config()
  sys.exit(0 if success else 1)
