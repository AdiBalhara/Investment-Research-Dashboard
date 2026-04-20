from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.auth.dependencies import get_current_user, CurrentUser
from app.watchlist.models import WatchlistItem
from app.watchlist.schemas import WatchlistAdd, WatchlistItemResponse

router = APIRouter()


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    request: WatchlistAdd,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a company to the user's watchlist."""
    item = WatchlistItem(
        org_id=current_user.org_id,
        user_id=current_user.user_id,
        ticker=request.ticker.upper(),
        company_name=request.company_name,
    )
    db.add(item)

    try:
        await db.flush()
        await db.refresh(item)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already in watchlist",
        )

    return item


@router.get("", response_model=list[WatchlistItemResponse])
async def list_watchlist(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all watchlist items for the current user's organization."""
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.org_id == current_user.org_id)
        .order_by(WatchlistItem.added_at.desc())
    )
    items = result.scalars().all()
    return items


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    item_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a company from the watchlist."""
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == item_id,
            WatchlistItem.org_id == current_user.org_id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found")

    await db.delete(item)
