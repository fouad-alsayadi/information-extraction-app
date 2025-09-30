"""User router for Databricks user information."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.services.user_service import UserService

router = APIRouter()


class UserInfo(BaseModel):
  """Databricks user information."""

  email: str  # User's email address
  displayName: str  # Name to display
  active: bool


class UserWorkspaceInfo(BaseModel):
  """User and workspace information."""

  user: UserInfo
  workspace: dict


@router.get('/me', response_model=UserInfo)
async def get_current_user():
  """Get current user information from Databricks."""
  try:
    service = UserService()
    user_info = service.get_user_info()

    return UserInfo(
      email=user_info['email'],  # email from service
      displayName=user_info['displayName'],
      active=user_info['active'],
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to fetch user info: {str(e)}')


@router.get('/me/workspace', response_model=UserWorkspaceInfo)
async def get_user_workspace_info():
  """Get user information along with workspace details."""
  try:
    service = UserService()
    info = service.get_user_workspace_info()

    return UserWorkspaceInfo(
      user=UserInfo(
        email=info['user']['email'],  # email from service
        displayName=info['user']['displayName'],
        active=info['user']['active'],
      ),
      workspace=info['workspace'],
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to fetch workspace info: {str(e)}')
