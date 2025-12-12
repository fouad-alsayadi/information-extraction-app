"""Centralized configuration management for Information Extraction App.

This module provides a unified configuration system that works across three environments:
1. Local development - loads from YAML files with plaintext secrets
2. Databricks App - loads from YAML + environment variables (from app.yaml)
3. Databricks Jobs - loads from YAML + Databricks secrets

Usage:
    from server.config import get_config

    config = get_config()
    print(config.database.host)
    print(config.upload.base_path)
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml


def detect_environment() -> str:
  """Detect runtime environment: local, app, or job.

  Returns:
      'local': Local development environment
      'app': Databricks App deployment
      'job': Databricks Job/Notebook environment
  """
  if os.getenv('DATABRICKS_RUNTIME_VERSION'):
    return 'job'  # Databricks notebook
  elif os.getenv('PORT') == '8080':
    return 'app'  # Databricks App
  else:
    return 'local'  # Local development


@dataclass
class DatabaseConfig:
  """Database configuration."""

  host: str
  port: int
  name: str
  user: str
  password: str
  schema: str


@dataclass
class DatabricksConfig:
  """Databricks-specific configuration."""

  job_id: int
  output_table: str


@dataclass
class UploadConfig:
  """File upload configuration."""

  base_path: str
  max_size_mb: int
  allowed_extensions: List[str]


@dataclass
class AppConfig:
  """Complete application configuration."""

  database: DatabaseConfig
  databricks: DatabricksConfig
  upload: UploadConfig
  environment: str


def load_config() -> AppConfig:
  """Load configuration from appropriate source based on environment.

  Returns:
      AppConfig: Fully loaded and validated configuration

  Raises:
      ValueError: If required configuration is missing
      FileNotFoundError: If required config files are missing
  """
  env = detect_environment()
  config_dir = Path(__file__).parent.parent / 'config'

  # Load base config (always required)
  base_yaml = config_dir / 'base.yaml'
  if not base_yaml.exists():
    raise FileNotFoundError(f'Base configuration not found: {base_yaml}')

  with open(base_yaml) as f:
    base = yaml.safe_load(f)

  if env == 'local':
    return _load_local_config(base, config_dir)
  elif env == 'app':
    return _load_app_config(base)
  else:  # job
    return _load_job_config(base)


def _load_local_config(base: dict, config_dir: Path) -> AppConfig:
  """Load config for local development.

  Args:
      base: Base configuration dict
      config_dir: Path to config directory

  Returns:
      AppConfig: Configuration for local development
  """
  # Overlay local.yaml if it exists
  local_yaml = config_dir / 'local.yaml'
  if local_yaml.exists():
    with open(local_yaml) as f:
      local = yaml.safe_load(f)
      if local:
        _deep_merge(base, local)

  # Load secrets.yaml (required for local dev)
  secrets_file = config_dir / 'secrets.yaml'
  if not secrets_file.exists():
    raise FileNotFoundError(
      'config/secrets.yaml not found. '
      'Copy config/secrets.yaml.example and fill in your local secrets.'
    )

  with open(secrets_file) as f:
    secrets = yaml.safe_load(f)

  if not secrets or 'database' not in secrets or 'password' not in secrets['database']:
    raise ValueError('config/secrets.yaml must contain database.password')

  # Build config
  return AppConfig(
    database=DatabaseConfig(
      host=base['database']['host'],
      port=base['database']['port'],
      name=base['database']['name'],
      user=base['database']['user'],
      password=secrets['database']['password'],
      schema=base['database']['schema'],
    ),
    databricks=DatabricksConfig(
      job_id=base['databricks']['job_id'], output_table=base['databricks']['output_table']
    ),
    upload=UploadConfig(
      base_path=secrets.get('upload', {}).get('base_path', base['upload']['base_path']),
      max_size_mb=base['upload']['max_size_mb'],
      allowed_extensions=base['upload']['allowed_extensions'],
    ),
    environment='local',
  )


def _load_app_config(base: dict) -> AppConfig:
  """Load config for Databricks App (from environment variables).

  Databricks App deployment sets environment variables from app.yaml.

  Args:
      base: Base configuration dict

  Returns:
      AppConfig: Configuration for Databricks App deployment

  Raises:
      ValueError: If required environment variables are not set
  """
  # Databricks App sets env vars from app.yaml
  db_password = os.getenv('DB_PASSWORD')
  if not db_password:
    raise ValueError(
      'DB_PASSWORD environment variable not set. '
      'Check app.yaml configuration and Databricks secrets.'
    )

  upload_path = os.getenv('UPLOAD_BASE_PATH')
  if not upload_path:
    raise ValueError(
      'UPLOAD_BASE_PATH environment variable not set. '
      'Check app.yaml configuration and Databricks secrets.'
    )

  job_id_str = os.getenv('DATABRICKS_JOB_ID')
  if not job_id_str:
    raise ValueError(
      'DATABRICKS_JOB_ID environment variable not set. '
      'Check app.yaml configuration and Databricks secrets.'
    )

  try:
    job_id = int(job_id_str)
  except ValueError as e:
    raise ValueError(f'DATABRICKS_JOB_ID must be an integer, got: {job_id_str}') from e

  return AppConfig(
    database=DatabaseConfig(
      host=base['database']['host'],
      port=base['database']['port'],
      name=base['database']['name'],
      user=base['database']['user'],
      password=db_password,
      schema=base['database']['schema'],
    ),
    databricks=DatabricksConfig(job_id=job_id, output_table=base['databricks']['output_table']),
    upload=UploadConfig(
      base_path=upload_path,
      max_size_mb=base['upload']['max_size_mb'],
      allowed_extensions=base['upload']['allowed_extensions'],
    ),
    environment='app',
  )


def _load_job_config(base: dict) -> AppConfig:
  """Load config for Databricks Job (from dbutils secrets).

  Args:
      base: Base configuration dict

  Returns:
      AppConfig: Configuration for Databricks Job environment

  Raises:
      ImportError: If dbutils is not available
      ValueError: If secrets cannot be loaded
  """
  try:
    from databricks.sdk.runtime import dbutils
  except ImportError as e:
    raise ImportError(
      'databricks.sdk.runtime.dbutils not available. '
      'This module can only be used in Databricks notebooks.'
    ) from e

  # Load secrets
  secret_scope = base['secrets']['database_password']['scope']
  secret_key = base['secrets']['database_password']['key']

  try:
    db_password = dbutils.secrets.get(scope=secret_scope, key=secret_key)
  except Exception as e:
    raise ValueError(
      f'Failed to load database password from Databricks secrets '
      f'(scope={secret_scope}, key={secret_key}): {e}'
    ) from e

  return AppConfig(
    database=DatabaseConfig(
      host=base['database']['host'],
      port=base['database']['port'],
      name=base['database']['name'],
      user=base['database']['user'],
      password=db_password,
      schema=base['database']['schema'],
    ),
    databricks=DatabricksConfig(
      job_id=base['databricks']['job_id'], output_table=base['databricks']['output_table']
    ),
    upload=UploadConfig(
      base_path=base['upload']['base_path'],
      max_size_mb=base['upload']['max_size_mb'],
      allowed_extensions=base['upload']['allowed_extensions'],
    ),
    environment='job',
  )


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


# Global config instance (loaded once at startup)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
  """Get the application configuration (singleton pattern).

  The configuration is loaded once on first call and cached for subsequent calls.

  Returns:
      AppConfig: The application configuration

  Raises:
      ValueError: If configuration is invalid or missing
      FileNotFoundError: If required config files are missing
  """
  global _config
  if _config is None:
    _config = load_config()
  return _config


def reset_config() -> None:
  """Reset the global config instance (useful for testing).

  This forces a reload on the next call to get_config().
  """
  global _config
  _config = None
