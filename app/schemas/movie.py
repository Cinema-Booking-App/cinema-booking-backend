from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class MovieOut(BaseModel):
    movie_id: int
    title: str
    genre: Optional[str] = None
    duration: int
    year: Optional[int] = None
    age_rating: Optional[str] = None
    language: Optional[str] = None
    format: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[date] = None
    trailer_url: Optional[str] = None
    poster_url: Optional[str] = None
    status: Optional[str] = None
    director: Optional[str] = None
    actors: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True