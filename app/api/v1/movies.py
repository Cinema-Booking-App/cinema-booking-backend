from fastapi import APIRouter
from app.services.movie_service import get_movies

router = APIRouter()


@router.get("/moives")
def list_movies():
    return get_movies();
