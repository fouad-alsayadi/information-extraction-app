"""Centralized configuration management for Information Extraction App.

This module provides a unified configuration system:
- All configuration is centralized in config/base.yaml
- Secrets come from environment variables:
  - DB_PASSWORD: Database password (from .env.local locally, app.yaml in Databricks)
  - UPLOAD_BASE_PATH: Upload directory (optional, defaults to base.yaml value)
  - DATABRICKS_JOB_ID: Job ID (optional, defaults to base.yaml value)

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

  base_path: str = '/tmp'  # Default to /tmp if not configured
  max_size_mb: int = 50
  allowed_extensions: List[str] = None

  def __post_init__(self):
    if self.allowed_extensions is None:
      self.allowed_extensions = ['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.txt']


@dataclass
class AppConfig:
  """Complete application configuration."""

  database: DatabaseConfig
  databricks: Optional[DatabricksConfig]
  upload: Optional[UploadConfig]


def load_config() -> AppConfig:
  """Load configuration from base.yaml and environment variables.

  Returns:
      AppConfig: Fully loaded and validated configuration

  Raises:
      ValueError: If required configuration is missing
      FileNotFoundError: If required config files are missing
  """
  config_dir = Path(__file__).parent.parent / 'config'

  # Load base config (always required)
  base_yaml = config_dir / 'base.yaml'
  if not base_yaml.exists():
    raise FileNotFoundError(f'Base configuration not found: {base_yaml}')

  with open(base_yaml) as f:
    base = yaml.safe_load(f)

  # Get DB_PASSWORD from environment or .env.local
  db_password = os.getenv('DB_PASSWORD')
  if not db_password:
    # Try loading from .env.local
    env_local = Path(__file__).parent.parent / '.env.local'
    if env_local.exists():
      with open(env_local) as f:
        for line in f:
          line = line.strip()
          if line.startswith('DB_PASSWORD='):
            db_password = line.split('=', 1)[1]
            break

  if not db_password:
    raise ValueError(
      'DB_PASSWORD not found. '
      'Add DB_PASSWORD to .env.local (local) or check app.yaml resources (app).'
    )

  # Get upload path and job ID (from env vars in app mode, from base.yaml in local mode)
  upload_base_path = os.getenv('UPLOAD_BASE_PATH')
  if not upload_base_path:
    upload_base_path = base['upload'].get('base_path', '/tmp')

  job_id_str = os.getenv('DATABRICKS_JOB_ID')
  if job_id_str:
    try:
      job_id = int(job_id_str)
    except ValueError as e:
      raise ValueError(f'DATABRICKS_JOB_ID must be an integer, got: {job_id_str}') from e
  else:
    # Fallback to base.yaml configuration
    if 'databricks' in base and 'job_id' in base['databricks']:
      job_id = base['databricks']['job_id']
    else:
      job_id = None

  # Build config
  return AppConfig(
    database=DatabaseConfig(
      host=base['database']['host'],
      port=base['database']['port'],
      name=base['database']['name'],
      user=base['database']['user'],
      password=db_password,
      schema=base['database']['schema'],
    ),
    databricks=(
      DatabricksConfig(job_id=job_id, output_table=base['databricks']['output_table'])
      if 'databricks' in base and 'output_table' in base['databricks'] and job_id
      else None
    ),
    upload=(
      UploadConfig(
        base_path=upload_base_path,
        max_size_mb=base['upload']['max_size_mb'],
        allowed_extensions=base['upload']['allowed_extensions'],
      )
      if (
        'upload' in base
        and 'max_size_mb' in base['upload']
        and 'allowed_extensions' in base['upload']
      )
      else None
    ),
  )


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
