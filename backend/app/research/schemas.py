from typing import Any, Optional
from pydantic import BaseModel, Field


class ResearchSection(BaseModel):
    """A single section of the AI research output."""
    type: str = Field(description="Section type: company_overview, financial_comparison, stock_performance, news_sentiment, risk_analysis, summary")
    render_as: str = Field(description="UI component to render: card_grid, table, line_chart, bar_chart, news_cards, text")
    title: str = Field(default="", description="Section title")
    data: Any = Field(description="Section data — structure depends on render_as type")
    source: Any = Field(default=None, description="Source attribution for this section, such as tool names or article sources")
    explanation: str = Field(default="", description="Why this section was included and how it was derived from tool output")


class ExecutionStep(BaseModel):
    """A single step in the AI agent's execution trace."""
    tool: str = Field(description="Name of the tool called")
    input: str = Field(description="Input passed to the tool")
    duration_ms: int = Field(default=0, description="Time taken in milliseconds")
    status: str = Field(default="success", description="Step status: success, error, skipped")


class ResearchResult(BaseModel):
    """Complete structured output from the AI research agent."""
    query: str = Field(description="Original user query")
    confidence: float = Field(default=0.75, description="AI confidence score 0-1")
    sections: list[ResearchSection] = Field(default_factory=list, description="Ordered list of result sections")
    execution_steps: list[ExecutionStep] = Field(default_factory=list, description="AI execution trace")
    reasoning: str = Field(default="", description="AI reasoning explanation for the results")


class ResearchRequest(BaseModel):
    """Request body for the research endpoint."""
    query: str = Field(min_length=1, description="Natural language research query")
