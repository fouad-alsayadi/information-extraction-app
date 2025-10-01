"""Authentication dependencies for extracting user context from Databricks Apps."""

import logging
from typing import Dict, Optional

from fastapi import Request

from server.services.user_service import UserService

logger = logging.getLogger(__name__)


async def get_current_user_context(request: Request) -> Dict[str, Optional[str]]:
  """Extract user context from Databricks Apps authentication headers.
  If headers are not available, fallback to workspace client.

  Databricks Apps automatically injects user information via HTTP headers
  when on-behalf-of-user authentication is enabled.

  Returns:
      Dict containing user information from headers or workspace client
  """
  headers = request.headers

  # Try to get user info from headers first
  user_context = {
    'user_id': headers.get('X-Forwarded-User'),
    'email': headers.get('X-Forwarded-Email'),
    'username': headers.get('X-Forwarded-Preferred-Username'),
    'real_ip': headers.get('X-Real-Ip'),
    'request_id': headers.get('X-Request-Id'),
  }

  # Check if we have any user information from headers
  has_user_info = any([user_context['user_id'], user_context['email'], user_context['username']])

  # If no user info from headers, fallback to user service
  if not has_user_info:
    try:
      user_service = UserService()
      current_user = user_service.get_current_user()

      user_context.update(
        {
          'user_id': str(current_user.id) if current_user.id else None,
          'email': current_user.emails[0].value if current_user.emails else None,
          'username': current_user.user_name,
          'display_name': current_user.display_name,
        }
      )

      logger.info(f'Fallback to user service for user: {user_context.get("email", "Unknown")}')

    except Exception as e:
      logger.warning(f'Failed to get user from user service: {str(e)}')
      # Keep the original empty context, will fallback to 'System' in get_user_for_logging

  # Set display_name if we have email
  if user_context.get('email') and not user_context.get('display_name'):
    user_context['display_name'] = user_context['email'].split('@')[0]

  return user_context


def get_user_for_logging(user_context: Dict[str, Optional[str]]) -> str:
  """Get a user identifier for logging purposes.

  Prioritizes email, then username, then user_id, falls back to 'System'.
  """
  return (
    user_context.get('email')
    or user_context.get('username')
    or user_context.get('user_id')
    or 'System'
  )


def get_user_display_name(user_context: Dict[str, Optional[str]]) -> str:
  """Get a user display name for UI purposes.

  Extracts name from email or uses username.
  """
  email = user_context.get('email')
  if email and '@' in email:
    return email.split('@')[0].replace('.', ' ').title()

  return user_context.get('username') or user_context.get('display_name') or 'Unknown User'
