from fastapi import APIRouter, Depends
from ..dependencies import get_current_user

router = APIRouter()

@router.get("/meals")
def get_meals(current_user: str = Depends(get_current_user)):
    return {
        "message": "Protected meals data",
        "user": current_user
    }