"""Settings API router."""
from fastapi import APIRouter
from app.api.deps import CurrentUser

router = APIRouter()


@router.get("/")
async def get_settings(current_user: CurrentUser):
    """Return non-sensitive settings for the current user."""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
    }
