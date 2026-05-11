"""
FILE: backend/app/api/routes/saved_locations.py
Saved locations endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Path
from pydantic import BaseModel
from typing import Optional

from app.agent.tools.city_resolver import resolve_city
from app.infrastructure.repositories.location_repository import (
    add_saved_location,
    get_saved_locations,
    update_saved_location,
    set_default_location,
    delete_saved_location
)
from app.api.dependencies import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/saved-locations", tags=["Saved Locations"])


class SaveLocationRequest(BaseModel):
    city_name: str
    country_code: str
    label: str


class UpdateLocationRequest(BaseModel):
    label: Optional[str] = None
    display_order: Optional[int] = None


@router.get("")
async def list_saved_locations(user = Depends(get_current_user)):
    """
    Get user's saved locations ordered by display_order
    """
    user_id = user.id
    
    try:
        locations = await get_saved_locations(user_id)
        return {"locations": locations}
    except Exception as e:
        logger.error(f"Failed to get saved locations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve saved locations")


@router.post("")
async def create_saved_location(body: SaveLocationRequest, user = Depends(get_current_user)):
    """
    Add a new saved location
    """
    user_id = user.id
    
    logger.info(f"Creating saved location: user_id={user_id}, city_name={body.city_name}, label={body.label}")
    
    # Resolve city to get exact coordinates
    try:
        logger.info(f"Resolving city: {body.city_name}")
        loc = await resolve_city(body.city_name)
        logger.info(f"City resolved: {loc}")
        if not loc:
            raise HTTPException(status_code=404, detail=f"City '{body.city_name}' not found")
    except Exception as e:
        logger.error(f"City resolution failed: {e}")
        raise HTTPException(status_code=404, detail=f"City '{body.city_name}' not found: {str(e)}")
    
    # Use resolved location data
    latitude = float(loc["latitude"])
    longitude = float(loc["longitude"])
    timezone = loc.get("timezone", "UTC")
    country_code = loc.get("country_code", body.country_code)
    city_name = loc.get("city_name", body.city_name)
    
    logger.info(f"Adding to database: city_name={city_name}, country_code={country_code}, label={body.label}, lat={latitude}, lon={longitude}, timezone={timezone}")
    
    try:
        location = await add_saved_location(
            user_id=user_id,
            city_name=city_name,
            country_code=country_code,
            label=body.label,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone
        )
        
        logger.info(f"Location saved successfully: {location}")
        if location:
            return location
        else:
            logger.error("add_saved_location returned None")
            raise HTTPException(status_code=500, detail="Failed to save location: Database returned None")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create saved location: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save location: {str(e)}")


@router.patch("/{location_id}")
async def update_location(
    location_id: int = Path(..., description="Location ID"),
    body: UpdateLocationRequest = None,
    user = Depends(get_current_user)
):
    """
    Update label or display_order for a saved location
    """
    user_id = user.id
    
    if body is None:
        body = UpdateLocationRequest()
    
    try:
        success = await update_saved_location(
            location_id=location_id,
            user_id=user_id,
            label=body.label,
            display_order=body.display_order
        )
        
        if success:
            return {"message": "Location updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Location not found or not owned by user")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update location: {e}")
        raise HTTPException(status_code=500, detail="Failed to update location")


@router.patch("/{location_id}/default")
async def set_default(
    location_id: int = Path(..., description="Location ID"),
    user = Depends(get_current_user)
):
    """
    Set this location as default (shown on load)
    """
    user_id = user.id
    
    try:
        success = await set_default_location(location_id, user_id)
        
        if success:
            return {"message": "Location set as default"}
        else:
            raise HTTPException(status_code=404, detail="Location not found or not owned by user")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default location: {e}")
        raise HTTPException(status_code=500, detail="Failed to set default location")


@router.delete("/{location_id}")
async def delete_location(
    location_id: int = Path(..., description="Location ID"),
    user = Depends(get_current_user)
):
    """
    Remove a saved location
    """
    user_id = user.id
    
    try:
        success = await delete_saved_location(location_id, user_id)
        
        if success:
            return {"message": "Location deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Location not found or not owned by user")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete location: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete location")
