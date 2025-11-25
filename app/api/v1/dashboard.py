# dashboard.py
# API cho dashboard thống kê hệ thống
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Trả về thống kê tổng quan hệ thống: số lượng user, vé, doanh thu, v.v.
    """
    from app.models.users import Users
    from app.models.tickets import Tickets
    from app.models.showtimes import Showtimes
    from app.models.movies import Movies
    from sqlalchemy import func

    user_count = db.query(Users).count()
    ticket_count = db.query(Tickets).count()
    total_revenue = db.query(func.sum(Tickets.price)).scalar() or 0

    # Doanh thu từng phim (top movies)
    top_movies = (
        db.query(
            Movies.movie_id,
            Movies.title,
            func.sum(Tickets.price).label("revenue"),
            func.count(Tickets.ticket_id).label("tickets")
        )
        .join(Showtimes, Showtimes.showtime_id == Tickets.showtime_id)
        .join(Movies, Movies.movie_id == Showtimes.movie_id)
        .group_by(Movies.movie_id, Movies.title)
        .order_by(func.sum(Tickets.price).desc())
        .limit(3)
        .all()
    )

    return {
        "user_count": user_count,
        "ticket_count": ticket_count,
        "total_revenue": int(total_revenue),
        "top_movies": [
            {
                "movie_id": m.movie_id,
                "title": m.title,
                "revenue": int(m.revenue),
                "tickets": m.tickets
            }
            for m in top_movies
        ]
    }
