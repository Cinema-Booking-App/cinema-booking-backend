from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.movie_service import *
from app.schemas.movie import MovieCreate
from fastapi import APIRouter

router = APIRouter()

@router.get("/movies")
def list_movies(db: Session = Depends(get_db)):
    return get_movies(db)

@router.get("/movies/{movie_id}")
def detail_movie(movie_id: int, db: Session = Depends(get_db)):
    return get_movie_by_id(db, movie_id)

@router.post("/movies")
def add_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    return create_movie(db, movie)

@router.delete("/movies/{movie_id}")
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    return delete_movie(db, movie_id)

@router.put("/movies/{movie_id}")
def edit_movie(movie_id: int, movie: MovieCreate, db: Session = Depends(get_db)):
    return update_movie(db, movie_id, movie)
