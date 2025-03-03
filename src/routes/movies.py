from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas.movies import MovieDetailResponseSchema, MovieListResponseSchema

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema
)
async def read_movies(
    page: int = Query(1, ge=1, description="The actual page number."),
    per_page: int = Query(
        10, ge=1, le=20, description="Count movies on page"
    ),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = (
        await db.execute(select(MovieModel).offset(offset).limit(per_page))
    )
    movies = result.scalars().all()

    prev_page = (
        f"/theater/movies/?page={page-1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page+1}&per_page={per_page}"
        if page < total_pages else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema
)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = (
        await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie
