from fastapi import APIRouter

router = APIRouter(prefix="/saved-locations", tags=["Saved Locations"])

@router.get("/")
async def list_saved_locations():
    """List saved locations - to be implemented in Phase 4"""
    return {"message": "Saved locations - Phase 4"}