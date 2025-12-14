"""Interactive setup wizard for Information Extraction App.

This wizard guides users through the complete setup process including:
- Databricks authentication
- Database configuration
- Unity Catalog and Volume setup
- Job deployment
- App configuration with resources
- Validation and health checks
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Import our helper modules
from scripts.config_manager import (
  update_env_local,
  update_base_config,
  validate_config_consistency,
)
from scripts.databricks_resources import (
  build_databricks_cmd,
  check_job_exists,
  check_secret_exists,
  check_volume_exists,
  create_app_with_resources,
  create_secret,
  create_volume,
  deploy_job_bundle,
  sync_project_to_workspace,
  test_volume_write,
  update_app_resources,
  update_lakeflow_config,
)
from scripts.health_checks import check_deployed_app, check_local_server, test_database_connection

console = Console()

# State file path
STATE_FILE = Path('.setup-state.json')


class SetupState:
  """Manages setup wizard state for resumability."""

  def __init__(self):
    """Initialize setup state."""
    self.state = self._load_state()

  def _load_state(self) -> dict:
    """Load state from file or create new state."""
    if STATE_FILE.exists():
      try:
        with open(STATE_FILE) as f:
          return json.load(f)
      except Exception as e:
        console.print(f'[yellow]⚠️  Could not load state file: {e}[/yellow]')
        return self._create_new_state()
    return self._create_new_state()

  def _create_new_state(self) -> dict:
    """Create new state dictionary."""
    return {
      'version': '1.0',
      'last_updated': datetime.now().isoformat(),
      'phases': {
        'dependencies_installed': False,
        'databricks_authenticated': False,
        'database_configured': False,
        'catalog_configured': False,
        'volume_configured': False,
        'job_deployed': False,
        'app_deployed': False,
      },
      'data': {
        'databricks_user': None,
        'database': {},
        'catalog': None,
        'schema': None,
        'volume_path': None,
        'workspace_path': None,
        'job_id': None,
        'app_url': None,
      },
    }

  def save(self):
    """Save state to file."""
    try:
      self.state['last_updated'] = datetime.now().isoformat()
      with open(STATE_FILE, 'w') as f:
        json.dump(self.state, f, indent=2)
    except Exception as e:
      console.print(f'[yellow]⚠️  Could not save state: {e}[/yellow]')

  def is_phase_complete(self, phase: str) -> bool:
    """Check if a phase is complete."""
    return self.state['phases'].get(phase, False)

  def mark_phase_complete(self, phase: str):
    """Mark a phase as complete."""
    self.state['phases'][phase] = True
    self.save()

  def set_data(self, key: str, value: Any):
    """Set data value."""
    self.state['data'][key] = value
    self.save()

  def get_data(self, key: str) -> Any:
    """Get data value."""
    return self.state['data'].get(key)

  def reset(self):
    """Reset all state."""
    self.state = self._create_new_state()
    if STATE_FILE.exists():
      STATE_FILE.unlink()
    console.print('[yellow]🔄 Setup state reset[/yellow]')


def print_header():
  """Print wizard header."""
  console.print()
  console.print(
    Panel.fit(
      '[bold cyan]Information Extraction App[/bold cyan]\n[dim]Enhanced Setup Wizard[/dim]',
      border_style='cyan',
    )
  )
  console.print()


def print_phase_header(phase_num: int, phase_name: str):
  """Print phase header."""
  console.print()
  console.print(f'[bold cyan]╔{"═" * 60}╗[/bold cyan]')
  console.print(f'[bold cyan]║  Phase {phase_num}: {phase_name.ljust(51)}║[/bold cyan]')
  console.print(f'[bold cyan]╚{"═" * 60}╝[/bold cyan]')
  console.print()


def check_dependencies(state: SetupState) -> bool:
  """Check/install required dependencies.

  Args:
      state: Setup state

  Returns:
      True if dependencies are ready, False otherwise
  """
  print_phase_header(1, 'Environment & Authentication')

  if state.is_phase_complete('dependencies_installed'):
    console.print('[dim]✅ Dependencies already installed (skipping)[/dim]')
    return True

  console.print('[cyan]Checking dependencies...[/cyan]')

  # Check uv
  try:
    result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
      console.print(f'[green]✅ uv found: {result.stdout.strip()}[/green]')
    else:
      console.print('[red]❌ uv not found - please install from https://docs.astral.sh/uv/[/red]')
      return False
  except FileNotFoundError:
    console.print('[red]❌ uv not found - please install from https://docs.astral.sh/uv/[/red]')
    return False

  # Check bun
  try:
    result = subprocess.run(['bun', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
      console.print(f'[green]✅ bun found: {result.stdout.strip()}[/green]')
    else:
      console.print('[red]❌ bun not found - please install from https://bun.sh/[/red]')
      return False
  except FileNotFoundError:
    console.print('[red]❌ bun not found - please install from https://bun.sh/[/red]')
    return False

  # Check databricks CLI
  try:
    result = subprocess.run(['databricks', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
      version = result.stdout.strip()
      console.print(f'[green]✅ Databricks CLI found: {version}[/green]')

      # Check if version >= 0.265.0 for apps support
      try:
        version_num = version.split()[2] if len(version.split()) > 2 else version
        major, minor, patch = version_num.split('.')
        if int(major) == 0 and int(minor) < 265:
          console.print(
            '[yellow]⚠️  Databricks CLI version < 0.265.0 may not support apps commands[/yellow]'
          )
          if Confirm.ask('Upgrade Databricks CLI?'):
            subprocess.run(['brew', 'upgrade', 'databricks'], check=False)
      except Exception:
        pass  # Version check failed, continue anyway

    else:
      console.print('[red]❌ Databricks CLI not found - please install it[/red]')
      return False
  except FileNotFoundError:
    console.print('[red]❌ Databricks CLI not found - please install it[/red]')
    return False

  # Install Python dependencies
  console.print('[cyan]Installing Python dependencies...[/cyan]')
  result = subprocess.run(['uv', 'sync', '--dev'], capture_output=True, text=True)
  if result.returncode != 0:
    console.print(f'[red]❌ Failed to install Python dependencies: {result.stderr}[/red]')
    return False
  console.print('[green]✅ Python dependencies installed[/green]')

  # Verify watchmedo is available (for watch.sh)
  try:
    subprocess.run(['uv', 'run', 'watchmedo', '--help'], capture_output=True, check=True)
    console.print('[green]✅ watchmedo available (auto-client generation ready)[/green]')
  except subprocess.CalledProcessError:
    console.print('[yellow]⚠️  watchmedo not found, watch.sh may not work properly[/yellow]')

  # Install Node dependencies
  console.print('[cyan]Installing Node dependencies...[/cyan]')
  result = subprocess.run(['bun', 'install'], cwd='client', capture_output=True, text=True)
  if result.returncode != 0:
    console.print(f'[red]❌ Failed to install Node dependencies: {result.stderr}[/red]')
    return False
  console.print('[green]✅ Node dependencies installed[/green]')

  state.mark_phase_complete('dependencies_installed')
  return True


def setup_databricks_auth(state: SetupState) -> bool:
  """Setup Databricks authentication.

  Args:
      state: Setup state

  Returns:
      True if authentication successful, False otherwise
  """
  if state.is_phase_complete('databricks_authenticated'):
    console.print('[dim]✅ Databricks already authenticated (skipping)[/dim]')
    return True

  console.print('[cyan]Checking Databricks authentication...[/cyan]')

  # Try to get current user
  cmd = build_databricks_cmd(['databricks', 'current-user', 'me', '--output', 'json'])
  result = subprocess.run(cmd, capture_output=True, text=True)

  if result.returncode == 0:
    try:
      user_info = json.loads(result.stdout)
      user_name = user_info.get('userName', 'Unknown')
      console.print(f'[green]✅ Authenticated as: {user_name}[/green]')
      state.set_data('databricks_user', user_name)

      # Check which auth method is being used
      databricks_host = os.getenv('DATABRICKS_HOST')
      databricks_token = os.getenv('DATABRICKS_TOKEN')
      databricks_profile = os.getenv('DATABRICKS_CONFIG_PROFILE')

      # Create .env.local with appropriate auth
      env_local_path = Path('.env.local')
      env_lines = []

      if databricks_profile:
        # Using profile via env var
        console.print(f'[dim]Using Databricks profile: {databricks_profile}[/dim]')
        env_lines.append(f'DATABRICKS_CONFIG_PROFILE={databricks_profile}\n')
      elif databricks_host and databricks_token:
        # Using PAT
        console.print(f'[dim]Using PAT for host: {databricks_host}[/dim]')
        env_lines.append(f'DATABRICKS_HOST={databricks_host}\n')
        env_lines.append(f'DATABRICKS_TOKEN={databricks_token}\n')
      else:
        # No env vars set, but authenticated - ask which profile to use
        databrickscfg = Path.home() / '.databrickscfg'
        if databrickscfg.exists():
          console.print('[yellow]⚠️  Authenticated but no profile set in environment[/yellow]')
          console.print('[cyan]Available profiles in ~/.databrickscfg[/cyan]')

          # Parse profiles from .databrickscfg
          import configparser

          config = configparser.ConfigParser()
          config.read(databrickscfg)
          profiles = []

          # Check if DEFAULT section exists
          if config.has_section('DEFAULT') or 'DEFAULT' in config:
            profiles.append('DEFAULT')

          # Add all other sections
          profiles.extend(config.sections())

          # Show available profiles
          for idx, profile in enumerate(profiles, 1):
            host = config.get(profile, 'host', fallback='unknown')
            console.print(f'  {idx}. {profile} ({host})')

          # Ask which profile to use
          profile_to_use = Prompt.ask(
            '\nWhich profile do you want to use?',
            choices=profiles,
            default=profiles[0] if profiles else 'DEFAULT',
          )

          env_lines.append(f'DATABRICKS_CONFIG_PROFILE={profile_to_use}\n')
          console.print(f'[green]✅ Will use profile: {profile_to_use}[/green]')
          state.set_data('databricks_profile', profile_to_use)
        else:
          console.print(
            '[yellow]⚠️  Could not determine auth method, .env.local not created[/yellow]'
          )

      # Write .env.local if we have content
      if env_lines:
        with open(env_local_path, 'w') as f:
          f.writelines(env_lines)
        console.print('[green]✅ Created .env.local for watch.sh[/green]')

      state.mark_phase_complete('databricks_authenticated')
      return True

    except json.JSONDecodeError:
      console.print('[yellow]⚠️  Could not parse user info[/yellow]')

  # Authentication failed, prompt user
  console.print('[yellow]⚠️  Not authenticated to Databricks[/yellow]')
  console.print()
  console.print('[bold]Please authenticate using one of these methods:[/bold]')
  console.print('  1. databricks auth login --host https://your-workspace.databricks.com')
  console.print('  2. Set environment variables:')
  console.print('     export DATABRICKS_HOST=https://your-workspace.databricks.com')
  console.print('     export DATABRICKS_TOKEN=dapi123...')
  console.print()

  if Confirm.ask('Run [bold]databricks auth login[/bold] now?'):
    # Prompt for host
    host = Prompt.ask('Databricks workspace URL', default='https://your-workspace.databricks.com')
    cmd = build_databricks_cmd(['databricks', 'auth', 'login', '--host', host])
    result = subprocess.run(cmd)
    if result.returncode == 0:
      console.print('[green]✅ Authentication successful[/green]')
      # Recursively call this function to complete setup
      return setup_databricks_auth(state)

  console.print('[red]❌ Authentication required to continue[/red]')
  return False


def configure_database(state: SetupState) -> bool:
  """Configure database connection and run migrations.

  Args:
      state: Setup state

  Returns:
      True if database configured successfully, False otherwise
  """
  print_phase_header(2, 'Database Configuration')

  if state.is_phase_complete('database_configured'):
    console.print('[dim]✅ Database already configured (skipping)[/dim]')
    return True

  console.print('[cyan]Database configuration setup...[/cyan]')

  # Prompt for database credentials
  console.print('[bold]Enter database connection details:[/bold]')
  db_host = Prompt.ask('Database host', default='instance-6308e8f8-a992-4de7-a85c-7beb1fdc8d8a.database.cloud.databricks.com')
  db_port = Prompt.ask('Database port', default='5432')
  db_name = Prompt.ask('Database name', default='information_extractor')
  db_user = Prompt.ask('Database user', default='sanabil_app')
  db_password = Prompt.ask('Database password', password=True)

  # Test database connection
  from scripts.health_checks import test_database_connection

  if not test_database_connection(db_host, int(db_port), db_name, db_user, db_password):
    console.print('[red]❌ Database connection test failed[/red]')
    return False

  # Store database configuration to base.yaml BEFORE running migrations
  console.print('[cyan]Saving database configuration to base.yaml...[/cyan]')
  db_config = {
    'database': {
      'host': db_host,
      'port': int(db_port),
      'name': db_name,
      'user': db_user,
      'schema': 'information_extraction',
    }
  }
  if not update_base_config(db_config):
    console.print('[red]❌ Could not update config/base.yaml[/red]')
    return False

  # Update .env.local with password
  if not update_env_local(db_password):
    console.print('[yellow]⚠️  Could not update .env.local[/yellow]')

  console.print('[green]✅ Database configuration saved[/green]')

  # Run migrations (now that config is saved)
  console.print('[cyan]Running database migrations...[/cyan]')
  try:
    # Set DB_PASSWORD environment variable for migrations
    os.environ['DB_PASSWORD'] = db_password

    # Import and run create_tables from database.py
    import sys
    from pathlib import Path

    # Add server directory to path
    server_path = Path(__file__).parent.parent / 'server'
    sys.path.insert(0, str(server_path))

    from database import create_tables

    create_tables()
    console.print('[green]✅ Database migrations completed[/green]')

  except Exception as e:
    console.print(f'[red]❌ Database migrations failed: {e}[/red]')
    return False

  # Save database info to state
  state.set_data('database', db_config['database'])

  # Ask about creating Databricks secret
  if Confirm.ask('Create Databricks secret for database password?', default=True):
    from scripts.databricks_resources import create_secret

    # Prompt for secret scope and key
    console.print('[bold]Databricks Secret Configuration:[/bold]')
    scope = Prompt.ask('Secret scope name', default='information_extraction')
    key = Prompt.ask('Secret key name', default='lakebase_db_password')

    if create_secret(scope, key, db_password):
      console.print(f'[green]✅ Secret created: {scope}/{key}[/green]')

      # Save secret configuration to base.yaml
      secret_config = {
        'secrets': {
          'database_password': {
            'scope': scope,
            'key': key
          }
        }
      }
      if not update_base_config(secret_config):
        console.print('[yellow]⚠️  Could not update secret config in base.yaml[/yellow]')
    else:
      console.print(
        '[yellow]⚠️  Could not create secret (you can create it manually later)[/yellow]'
      )

  state.mark_phase_complete('database_configured')
  return True


def configure_catalog_and_volume(state: SetupState) -> bool:
  """Configure Unity Catalog, Schema, and Volume.

  Args:
      state: Setup state

  Returns:
      True if configured successfully, False otherwise
  """
  print_phase_header(3, 'Unity Catalog, Volume & Job Configuration')

  if state.is_phase_complete('catalog_configured') and state.is_phase_complete('volume_configured'):
    console.print('[dim]✅ Catalog and Volume already configured (skipping)[/dim]')
    return True

  # Get current user name for default catalog
  user_name = state.get_data('databricks_user') or 'user'
  first_name = user_name.split('@')[0].split('.')[0] if '@' in user_name else user_name

  # Ask for catalog.schema
  console.print('[bold]Unity Catalog and Schema Configuration:[/bold]')
  catalog_schema = Prompt.ask(
    'Unity Catalog.Schema to use',
    default=f'{first_name}_demos.information_extraction',
  )

  # Parse catalog and schema
  if '.' not in catalog_schema:
    console.print('[red]❌ Invalid format. Please use format: catalog.schema[/red]')
    return False

  catalog, schema = catalog_schema.split('.', 1)
  console.print(f'[green]Catalog: {catalog}[/green]')
  console.print(f'[green]Schema: {schema}[/green]')

  # Import resource management functions
  from scripts.databricks_resources import (
    check_catalog_exists,
    create_catalog,
    check_schema_exists,
    create_schema,
    check_volume_exists,
    create_volume,
    test_volume_write,
  )

  # Check if catalog exists
  console.print()
  console.print('[cyan]Checking if catalog exists...[/cyan]')
  if check_catalog_exists(catalog):
    console.print(f'[green]✅ Catalog exists: {catalog}[/green]')
  else:
    console.print(f'[yellow]⚠️  Catalog does not exist: {catalog}[/yellow]')

    if Confirm.ask('Create catalog?', default=True):
      if not create_catalog(catalog):
        console.print('[red]❌ Failed to create catalog[/red]')
        console.print(
          '[yellow]Please create the catalog manually or check your permissions[/yellow]'
        )
        return False
    else:
      console.print('[yellow]⚠️  Cannot proceed without catalog[/yellow]')
      return False

  # Check if schema exists
  console.print()
  console.print('[cyan]Checking if schema exists...[/cyan]')
  if check_schema_exists(catalog, schema):
    console.print(f'[green]✅ Schema exists: {catalog}.{schema}[/green]')
  else:
    console.print(f'[yellow]⚠️  Schema does not exist: {catalog}.{schema}[/yellow]')

    if Confirm.ask('Create schema?', default=True):
      if not create_schema(catalog, schema):
        console.print('[red]❌ Failed to create schema[/red]')
        console.print(
          '[yellow]Please create the schema manually or check your permissions[/yellow]'
        )
        return False
    else:
      console.print('[yellow]⚠️  Cannot proceed without schema[/yellow]')
      return False

  state.set_data('catalog', catalog)
  state.set_data('schema', schema)
  state.mark_phase_complete('catalog_configured')

  # Configure UC Volume
  console.print()
  console.print('[bold]Unity Catalog Volume Configuration:[/bold]')
  volume_path = Prompt.ask(
    'UC Volume path for documents',
    default=f'/Volumes/{catalog}/{schema}/sanabil_documents',
  )

  if check_volume_exists(volume_path):
    console.print(f'[green]✅ Volume exists: {volume_path}[/green]')
  else:
    console.print(f'[yellow]⚠️  Volume does not exist: {volume_path}[/yellow]')

    if Confirm.ask('Create volume?', default=True):
      # Parse volume name from path
      volume_name = volume_path.split('/')[-1]
      created_path = create_volume(catalog, schema, volume_name)

      if not created_path:
        console.print('[red]❌ Failed to create volume[/red]')
        return False

      volume_path = created_path

  # Test write permissions and clean up test file
  if not test_volume_write(volume_path):
    console.print('[red]❌ Volume write test failed[/red]')
    return False

  state.set_data('volume_path', volume_path)
  state.mark_phase_complete('volume_configured')

  # Configure output table
  console.print()
  console.print('[bold]Output Table Configuration:[/bold]')
  output_table = Prompt.ask(
    'Full table name for AI parse output',
    default=f'{catalog}.{schema}.ai_parse_document_output',
  )

  # Save output table to databricks section in base.yaml
  databricks_config = {
    'databricks': {
      'output_table': output_table
    }
  }
  if not update_base_config(databricks_config):
    console.print('[yellow]⚠️  Could not update output table config[/yellow]')
  else:
    console.print(f'[green]✅ Output table configured: {output_table}[/green]')

  state.set_data('output_table', output_table)

  # Update upload configuration with volume and defaults
  console.print()
  console.print('[cyan]Updating upload configuration...[/cyan]')
  upload_config = {
    'upload': {
      'base_path': volume_path,
      'max_size_mb': 50,
      'allowed_extensions': ['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.txt'],
    }
  }
  if not update_base_config(upload_config):
    console.print('[yellow]⚠️  Could not update upload config[/yellow]')
  else:
    console.print('[green]✅ Upload configuration saved[/green]')

  # Note: Job notebooks read directly from database/databricks/secrets sections
  console.print(
    '[dim]Note: Job notebooks read config from database/databricks/upload/secrets '
    'sections (no duplication!)[/dim]'
  )

  return True


def deploy_job(state: SetupState) -> bool:
  """Sync project to workspace and deploy job bundle.

  Args:
      state: Setup state

  Returns:
      True if job deployed successfully, False otherwise
  """
  print_phase_header(4, 'Workspace Sync & Job Bundle Deployment')

  if state.is_phase_complete('job_deployed'):
    console.print('[dim]✅ Job already deployed (skipping)[/dim]')
    return True

  # Get user info for default workspace path
  user_name = state.get_data('databricks_user') or 'user'

  # Ask for workspace path
  console.print('[bold]Workspace Configuration:[/bold]')
  workspace_path = Prompt.ask(
    'Workspace path for app files',
    default=f'/Workspace/Users/{user_name}/databricks-apps-resources/information-extraction-app/',
  )

  # Normalize workspace path (remove trailing slash)
  workspace_path = workspace_path.rstrip('/')
  state.set_data('workspace_path', workspace_path)

  # Sync project to workspace
  from scripts.databricks_resources import sync_project_to_workspace

  if not sync_project_to_workspace(workspace_path):
    console.print('[red]❌ Failed to sync project to workspace[/red]')
    return False

  # Update lakeflow-conf.yaml with workspace path
  console.print('[cyan]Updating lakeflow-conf.yaml...[/cyan]')
  from scripts.databricks_resources import update_lakeflow_config

  notebook_path = f'{workspace_path}/databricks-job-resources/information-extraction-main'

  if not update_lakeflow_config('databricks-job-resources/lakeflow-conf.yaml', notebook_path):
    console.print('[yellow]⚠️  Could not update lakeflow-conf.yaml[/yellow]')

  # Deploy job bundle
  from scripts.databricks_resources import deploy_job_bundle, check_job_exists

  result = deploy_job_bundle('databricks-job-resources')

  if not result or 'job_id' not in result:
    console.print('[red]❌ Failed to deploy job bundle[/red]')
    return False

  job_id = result['job_id']
  state.set_data('job_id', job_id)

  # Verify job exists
  if not check_job_exists(job_id):
    console.print(f'[red]❌ Could not verify job exists: {job_id}[/red]')
    return False

  # Update config/base.yaml with job_id
  job_config = {'databricks': {'job_id': job_id}}
  if not update_base_config(job_config):
    console.print('[yellow]⚠️  Could not update config/base.yaml with job_id[/yellow]')

  state.mark_phase_complete('job_deployed')
  return True


def configure_app_resources(state: SetupState) -> bool:
  """Configure Databricks App with resources.

  Args:
      state: Setup state

  Returns:
      True if app configured successfully, False otherwise
  """
  print_phase_header(5, 'Databricks App Resource Configuration')

  if state.is_phase_complete('app_deployed'):
    console.print('[dim]✅ App already deployed (skipping)[/dim]')
    return True

  # Update app.yaml with resource references
  console.print('[cyan]Updating app.yaml with resource references...[/cyan]')
  from scripts.config_manager import update_app_yaml_with_resources

  if update_app_yaml_with_resources():
    console.print('[green]✅ app.yaml updated with resource references[/green]')
  else:
    console.print('[yellow]⚠️  Could not update app.yaml (continuing anyway)[/yellow]')

  # Validate config consistency
  console.print('[cyan]Validating configuration consistency...[/cyan]')
  from scripts.config_manager import validate_config_consistency

  errors = validate_config_consistency()
  if errors:
    console.print('[yellow]⚠️  Configuration inconsistencies found:[/yellow]')
    for error in errors:
      console.print(f'  - {error}')
    console.print('[yellow]Please fix these issues manually in base.yaml or app.yaml[/yellow]')
  else:
    console.print('[green]✅ Configuration is consistent[/green]')

  # Get required data from state
  job_id = state.get_data('job_id')
  volume_path = state.get_data('volume_path')
  workspace_path = state.get_data('workspace_path')

  if not job_id or not volume_path or not workspace_path:
    console.print('[red]❌ Missing required data from previous phases[/red]')
    return False

  app_name = 'information-extraction-app'

  # ═══════════════════════════════════════════════════════════════════════
  # STEP 1: CREATE/UPDATE APP DEFINITION (not deployment)
  # This sets up the app with resources (job, volume, secrets) and permissions
  # ═══════════════════════════════════════════════════════════════════════
  console.print()
  console.print('[bold cyan]Step 1: App Definition & Resources[/bold cyan]')
  console.print('[cyan]Checking if app exists...[/cyan]')
  from scripts.databricks_resources import check_app_exists

  app_exists = check_app_exists(app_name)

  if not app_exists:
    # Create app with resources (app definition only, no source code yet)
    console.print(f'[cyan]Creating app definition: {app_name}[/cyan]')
    result = create_app_with_resources(app_name, job_id, volume_path)

    if not result:
      console.print('[red]❌ Failed to create app definition[/red]')
      return False

    console.print('[green]✅ App definition created (resources configured)[/green]')

    # Get service principal ID from the newly created app
    from scripts.databricks_resources import get_app_service_principal, grant_app_table_permissions
    service_principal_id = get_app_service_principal(app_name)

    if service_principal_id:
      catalog = state.get_data('catalog')
      schema = state.get_data('schema')

      if catalog and schema:
        console.print()
        if not grant_app_table_permissions(service_principal_id, catalog, schema):
          console.print('[yellow]⚠️  Could not grant table permissions (you may need to grant manually)[/yellow]')
      else:
        console.print('[yellow]⚠️  Missing catalog/schema - skipping permission grants[/yellow]')
    else:
      console.print('[yellow]⚠️  Could not get service principal ID - skipping permission grants[/yellow]')

  else:
    # App exists - update its resources to ensure they're current
    console.print(f'[green]✅ App definition already exists: {app_name}[/green]')
    console.print('[cyan]Updating app resources...[/cyan]')
    if not update_app_resources(app_name, job_id, volume_path):
      console.print('[yellow]⚠️  Failed to update app resources (continuing anyway)[/yellow]')
    else:
      console.print('[green]✅ App resources updated[/green]')

    # Grant permissions for existing app
    from scripts.databricks_resources import get_app_service_principal, grant_app_table_permissions
    service_principal_id = get_app_service_principal(app_name)

    if service_principal_id:
      catalog = state.get_data('catalog')
      schema = state.get_data('schema')

      if catalog and schema:
        console.print()
        if not grant_app_table_permissions(service_principal_id, catalog, schema):
          console.print('[yellow]⚠️  Could not grant table permissions (you may need to grant manually)[/yellow]')
      else:
        console.print('[yellow]⚠️  Missing catalog/schema - skipping permission grants[/yellow]')
    else:
      console.print('[yellow]⚠️  Could not get service principal ID - skipping permission grants[/yellow]')

  # ═══════════════════════════════════════════════════════════════════════
  # STEP 2: BUILD FRONTEND
  # Prepare the application code for deployment
  # ═══════════════════════════════════════════════════════════════════════
  console.print()
  console.print('[bold cyan]Step 2: Build Frontend[/bold cyan]')
  console.print('[cyan]Building frontend for deployment...[/cyan]')

  # Clean up any existing zombie processes before starting
  subprocess.run(['pkill', '-9', 'esbuild'], capture_output=True)
  subprocess.run(['pkill', '-9', 'vite'], capture_output=True)

  try:
    result = subprocess.run(
      ['npm', 'run', 'build'], cwd='client', capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
      console.print(f'[red]❌ Frontend build failed: {result.stderr}[/red]')
      # Clean up any zombie esbuild processes
      subprocess.run(['pkill', '-9', 'esbuild'], capture_output=True)
      return False

    console.print('[green]✅ Frontend built successfully[/green]')
  except subprocess.TimeoutExpired:
    console.print('[red]❌ Frontend build timed out after 300 seconds[/red]')
    # Clean up any zombie processes on timeout
    subprocess.run(['pkill', '-9', 'esbuild'], capture_output=True)
    subprocess.run(['pkill', '-9', 'vite'], capture_output=True)
    subprocess.run(['pkill', '-9', '-f', 'npm run build'], capture_output=True)
    return False
  except Exception as e:
    console.print(f'[red]❌ Frontend build failed: {e}[/red]')
    # Clean up any zombie processes on error
    subprocess.run(['pkill', '-9', 'esbuild'], capture_output=True)
    return False

  # ═══════════════════════════════════════════════════════════════════════
  # STEP 3: DEPLOY SOURCE CODE
  # Deploy the built application code to the app (separate from app creation)
  # ═══════════════════════════════════════════════════════════════════════
  console.print()
  console.print('[bold cyan]Step 3: Deploy Source Code[/bold cyan]')
  console.print('[cyan]Deploying source code to app...[/cyan]')
  cmd = build_databricks_cmd(
    ['databricks', 'apps', 'deploy', app_name, '--source-code-path', workspace_path]
  )
  result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

  if result.returncode != 0:
    console.print(f'[red]❌ Source code deployment failed: {result.stderr}[/red]')
    return False

  console.print('[green]✅ Source code deployed successfully[/green]')

  # Get app URL
  cmd = build_databricks_cmd(['databricks', 'apps', 'get', app_name, '--output', 'json'])
  result = subprocess.run(cmd, capture_output=True, text=True)

  if result.returncode == 0:
    try:
      app_data = json.loads(result.stdout)
      app_url = app_data.get('url')
      if app_url:
        state.set_data('app_url', app_url)
        console.print(f'[green]   App URL: {app_url}[/green]')
    except json.JSONDecodeError:
      pass

  state.mark_phase_complete('app_deployed')
  return True


def validate_setup(state: SetupState) -> bool:
  """Run validation and health checks.

  Args:
      state: Setup state

  Returns:
      True if validation passes, False otherwise
  """
  print_phase_header(6, 'Validation & Health Checks')

  console.print('[cyan]Running health checks...[/cyan]')

  # Test local server
  from scripts.health_checks import check_local_server

  console.print()
  console.print('[bold]Testing local development environment:[/bold]')
  if check_local_server(timeout=60):
    console.print('[green]✅ Local development environment working[/green]')
  else:
    console.print('[yellow]⚠️  Local server test failed (you can test manually later)[/yellow]')

  # Test deployed app if URL available
  app_url = state.get_data('app_url')
  if app_url:
    from scripts.health_checks import check_deployed_app

    console.print()
    console.print('[bold]Testing deployed app:[/bold]')
    if check_deployed_app(app_url):
      console.print('[green]✅ Deployed app working[/green]')
    else:
      console.print('[yellow]⚠️  Deployed app test failed[/yellow]')

  # Test job triggering
  job_id = state.get_data('job_id')
  if job_id:
    from scripts.health_checks import test_job_triggering

    console.print()
    console.print('[bold]Testing job triggering:[/bold]')
    if Confirm.ask('Test job triggering? (will start a job run)', default=False):
      if test_job_triggering(job_id, timeout=60):
        console.print('[green]✅ Job triggering working[/green]')
      else:
        console.print('[yellow]⚠️  Job triggering test failed[/yellow]')

  return True


def generate_report(state: SetupState) -> None:
  """Generate setup summary report.

  Args:
      state: Setup state
  """
  console.print()
  console.print('[bold cyan]═' * 60 + '[/bold cyan]')
  console.print('[bold cyan]Setup Summary[/bold cyan]')
  console.print('[bold cyan]═' * 60 + '[/bold cyan]')
  console.print()

  # Database
  db_config = state.get_data('database')
  if db_config:
    console.print(f'[cyan]Database:[/cyan] {db_config.get("host", "N/A")}')
    console.print(f'[cyan]Database Name:[/cyan] {db_config.get("name", "N/A")}')

  # Catalog & Schema
  catalog = state.get_data('catalog')
  schema = state.get_data('schema')
  if catalog and schema:
    console.print(f'[cyan]Catalog.Schema:[/cyan] {catalog}.{schema}')

  # Volume
  volume_path = state.get_data('volume_path')
  if volume_path:
    console.print(f'[cyan]Volume:[/cyan] {volume_path}')

  # Workspace
  workspace_path = state.get_data('workspace_path')
  if workspace_path:
    console.print(f'[cyan]Workspace Path:[/cyan] {workspace_path}')

  # Job
  job_id = state.get_data('job_id')
  if job_id:
    console.print(f'[cyan]Job ID:[/cyan] {job_id}')

  # App
  app_url = state.get_data('app_url')
  if app_url:
    console.print(f'[cyan]App URL:[/cyan] {app_url}')

  console.print()
  console.print('[bold cyan]Next Steps:[/bold cyan]')
  console.print('  1. Start local development:  [bold]./watch.sh[/bold]')
  console.print('  2. Access local app:         [bold]http://localhost:5173[/bold]')
  if app_url:
    console.print(f'  3. Access deployed app:      [bold]{app_url}[/bold]')
    console.print(
      f'  4. View app logs:            [bold]uv run python dba_logz.py {app_url}[/bold]'
    )
  console.print('  5. Deploy updates:           [bold]./deploy.sh[/bold]')
  console.print()
  console.print("[dim]💡 Tip: Run './setup.sh --help' to see all available options[/dim]")
  console.print()


def main():
  """Main setup wizard entry point."""
  print_header()

  # Parse command line arguments
  if '--help' in sys.argv:
    print_help()
    sys.exit(0)

  if '--reset' in sys.argv:
    state = SetupState()
    state.reset()
    console.print('[green]Setup state has been reset. Run ./setup.sh again to start fresh.[/green]')
    sys.exit(0)

  # Initialize state
  state = SetupState()

  # Check if there's existing progress
  if any(state.state['phases'].values()):
    console.print('[yellow]📋 Found existing setup progress:[/yellow]')
    table = Table(show_header=True)
    table.add_column('Phase', style='cyan')
    table.add_column('Status', style='green')

    phases = [
      ('Dependencies installed', 'dependencies_installed'),
      ('Databricks authenticated', 'databricks_authenticated'),
      ('Database configured', 'database_configured'),
      ('Catalog configured', 'catalog_configured'),
      ('Volume configured', 'volume_configured'),
      ('Job deployed', 'job_deployed'),
      ('App deployed', 'app_deployed'),
    ]

    for name, key in phases:
      status = '✅ Complete' if state.is_phase_complete(key) else '⏳ Pending'
      table.add_row(name, status)

    console.print(table)
    console.print()

    if not Confirm.ask('Resume from last checkpoint?', default=True):
      if Confirm.ask('Start fresh (reset all progress)?'):
        state.reset()

  # Run setup phases
  try:
    # Phase 1: Dependencies & Authentication
    if not check_dependencies(state):
      console.print('[red]❌ Dependency check failed[/red]')
      sys.exit(1)

    if not setup_databricks_auth(state):
      console.print('[red]❌ Authentication setup failed[/red]')
      sys.exit(1)

    # Phase 2: Database Configuration
    if not configure_database(state):
      console.print('[red]❌ Database configuration failed[/red]')
      sys.exit(1)

    # Phase 3: Catalog, Volume & Job Configuration
    if not configure_catalog_and_volume(state):
      console.print('[red]❌ Catalog and volume configuration failed[/red]')
      sys.exit(1)

    # Phase 4: Workspace Sync & Job Deployment
    if not deploy_job(state):
      console.print('[red]❌ Job deployment failed[/red]')
      sys.exit(1)

    # Phase 5: App Resource Configuration
    if not configure_app_resources(state):
      console.print('[red]❌ App resource configuration failed[/red]')
      sys.exit(1)

    # Phase 6: Validation & Health Checks
    if not validate_setup(state):
      console.print('[yellow]⚠️  Some health checks failed (setup still complete)[/yellow]')

    # Generate final report
    console.print()
    console.print(Panel.fit('[bold green]🎉 Setup Complete![/bold green]', border_style='green'))
    generate_report(state)

  except KeyboardInterrupt:
    console.print()
    console.print('[yellow]Setup interrupted. Progress has been saved.[/yellow]')
    console.print('[yellow]Run ./setup.sh again to resume.[/yellow]')
    sys.exit(130)
  except Exception as e:
    console.print()
    console.print(f'[red]❌ Unexpected error: {e}[/red]')
    console.print('[yellow]Progress has been saved. Run ./setup.sh again to resume.[/yellow]')
    sys.exit(1)


def print_help():
  """Print help message."""
  console.print('[bold cyan]Setup Wizard - Information Extraction App[/bold cyan]')
  console.print()
  console.print('[bold]Usage:[/bold]')
  console.print('  ./setup.sh [options]')
  console.print()
  console.print('[bold]Options:[/bold]')
  console.print('  --help          Show this help message')
  console.print('  --reset         Reset setup state and start fresh')
  console.print('  --verify-only   Only verify existing setup (TODO)')
  console.print('  --skip-deploy   Skip app deployment (TODO)')
  console.print()


if __name__ == '__main__':
  main()
