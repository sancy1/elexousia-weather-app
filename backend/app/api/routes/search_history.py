"""
FILE: backend/app/api/routes/search_history.py
API routes for search history management
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.api.dependencies import get_current_user
from app.infrastructure.repositories.search_history_repository import (
    add_search_history,
    get_search_history,
    delete_search_history,
    clear_search_history,
    cleanup_old_search_history
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search-history", tags=["search-history"])


class SearchHistoryRequest(BaseModel):
    city_name: str
    country_code: str = ""
    temperature: Optional[float] = None
    condition: Optional[str] = None


class SearchHistoryResponse(BaseModel):
    id: int
    user_id: int
    city_name: str
    country_code: str
    searched_at: str
    temperature: Optional[float] = None
    condition: Optional[str] = None


@router.get("", response_model=List[SearchHistoryResponse])
async def get_search_history_endpoint(
    limit: int = 50,
    user = Depends(get_current_user)
):
    """
    Get search history for the current user
    """
    try:
        history = await get_search_history(user.id, limit)
        return history
    except Exception as e:
        logger.error(f"Failed to get search history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search history")


@router.post("", response_model=SearchHistoryResponse)
async def add_search_history_endpoint(
    body: SearchHistoryRequest,
    user = Depends(get_current_user)
):
    """
    Add a new search history entry
    """
    try:
        result = await add_search_history(
            user_id=user.id,
            city_name=body.city_name,
            country_code=body.country_code,
            temperature=body.temperature,
            condition=body.condition
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to add search history")
        return result
    except Exception as e:
        logger.error(f"Failed to add search history: {e}")
        raise HTTPException(status_code=500, detail="Failed to add search history")


@router.delete("/{history_id}")
async def delete_search_history_endpoint(
    history_id: int,
    user = Depends(get_current_user)
):
    """
    Delete a search history entry
    """
    try:
        success = await delete_search_history(history_id, user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Search history entry not found")
        return {"message": "Search history entry deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete search history: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete search history")


@router.delete("")
async def clear_search_history_endpoint(
    user = Depends(get_current_user)
):
    """
    Clear all search history for the current user
    """
    try:
        success = await clear_search_history(user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear search history")
        return {"message": "Search history cleared"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear search history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear search history")
