from app.core.database import SessionLocal
from app.models.movie import Movie
from fastapi import APIRouter
from app.schemas.movie import MovieOut

router = APIRouter()


def get_movies():
    db = SessionLocal();
    movies = db.query(Movie).all();
    return [MovieOut.from_orm(m) for m in movies]
