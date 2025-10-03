from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class MovieBase(BaseModel):
    title: str
    genre: Optional[str] = None
    duration: int
    year: Optional[int] = None
    age_rating: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[date] = None
    trailer_url: Optional[str] = None
    poster_url: Optional[str] = None
    status: Optional[str] = None
    director: Optional[str] = None
    actors: Optional[str] = None

class MovieCreate(MovieBase):
    pass

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    duration: Optional[int] = None
    year: Optional[int] = None
    age_rating: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[date] = None
    trailer_url: Optional[str] = None
    poster_url: Optional[str] = None
    status: Optional[str] = None
    director: Optional[str] = None
    actors: Optional[str] = None

class MovieResponse(MovieBase):
    movie_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True