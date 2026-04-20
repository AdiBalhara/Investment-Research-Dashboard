from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.database import get_db
from app.auth.dependencies import get_current_user, CurrentUser
from app.reports.models import Report
from app.reports.schemas import ReportCreate, ReportResponse, ReportListItem

router = APIRouter()


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def save_report(
    request: ReportCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a research result as a report."""
    report = Report(
        org_id=current_user.org_id,
        user_id=current_user.user_id,
        query=request.query,
        result=request.result,
        confidence=request.confidence,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


@router.get("", response_model=list[ReportListItem])
async def list_reports(
    search: Optional[str] = Query(None, description="Search reports by query text"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all reports for the current user's organization."""
    stmt = (
        select(Report)
        .where(Report.org_id == current_user.org_id)
        .order_by(desc(Report.created_at))
    )

    if search:
        stmt = stmt.where(Report.query.ilike(f"%{search}%"))

    result = await db.execute(stmt)
    reports = result.scalars().all()
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single report by ID (must belong to user's org)."""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.org_id == current_user.org_id,
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report (must belong to user's org)."""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.org_id == current_user.org_id,
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    await db.delete(report)
