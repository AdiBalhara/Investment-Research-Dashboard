from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user, CurrentUser
from app.research.schemas import ResearchRequest, ResearchResult
from app.research.agent import run_research

router = APIRouter()


@router.post("", response_model=ResearchResult)
async def research(
    request: ResearchRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Run an AI-powered financial research query.
    The agent will dynamically select tools and return structured insights.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    result = await run_research(request.query)
    return result
