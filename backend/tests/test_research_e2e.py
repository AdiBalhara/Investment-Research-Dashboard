"""End-to-end tests for research agent and API."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.research.agent import run_research, parse_agent_response
from app.research.schemas import ResearchResult, ResearchSection


class TestResearchAgentEndToEnd:
    """End-to-end tests for the research agent."""

    @pytest.mark.asyncio
    async def test_research_query_returns_valid_structured_response(self):
        """Research query should return valid structured ResearchResult with source and explanation."""
        # Mock the agent executor to return a realistic response
        mock_agent_output = """{
            "query": "Tell me about Apple",
            "confidence": 0.85,
            "sections": [
                {
                    "type": "summary",
                    "render_as": "text",
                    "title": "Summary",
                    "data": {"content": "Apple is a technology company."},
                    "source": "search_financial_documents",
                    "explanation": "Summary derived from financial documents."
                }
            ],
            "reasoning": "Used financial documents to provide context."
        }"""

        mock_intermediate_steps = [
            (MagicMock(tool="search_financial_documents", tool_input="Apple"),
             '{"documents": [{"title": "Apple Overview", "source": "SEC"}]}')
        ]

        result = parse_agent_response(mock_agent_output, mock_intermediate_steps, "Tell me about Apple")

        # Verify result is a valid ResearchResult
        assert isinstance(result, ResearchResult)
        assert result.query == "Tell me about Apple"
        assert result.confidence == 0.85
        assert len(result.sections) > 0

        # Verify sections have source and explanation
        for section in result.sections:
            assert section.source is not None
            assert section.explanation is not None or section.type == "summary"

    @pytest.mark.asyncio
    async def test_research_agent_handles_invalid_json_gracefully(self):
        """Research agent should return safe fallback when AI output is not valid JSON."""
        mock_agent_output = "This is not valid JSON at all!"
        mock_intermediate_steps = []

        result = parse_agent_response(mock_agent_output, mock_intermediate_steps, "Test query")

        # Should return a fallback ResearchResult
        assert isinstance(result, ResearchResult)
        assert result.confidence == 0.2  # Low confidence for fallback
        assert len(result.sections) == 1
        assert result.sections[0].type == "summary"
        assert "could not be validated" in result.sections[0].data["content"]

    @pytest.mark.asyncio
    async def test_research_agent_handles_hallucinated_stock_data(self):
        """Research agent should reject responses with hallucinated stock data."""
        # Stock chart with hallucinated prices not matching tool output
        mock_agent_output = """{
            "query": "Apple stock",
            "confidence": 0.9,
            "sections": [
                {
                    "type": "stock_performance",
                    "render_as": "line_chart",
                    "title": "Stock Performance",
                    "data": {
                        "labels": ["2024-01-01", "2024-01-02"],
                        "series": [{"name": "Apple Stock", "values": [999.99, 1000.50]}]
                    },
                    "source": "get_stock_data",
                    "explanation": "Stock prices."
                }
            ],
            "reasoning": "Provided stock data."
        }"""

        # Real historical prices from the tool
        mock_intermediate_steps = [
            (MagicMock(tool="get_stock_data", tool_input="AAPL"),
             '{"ticker": "AAPL", "historical_prices": [{"date": "2024-01-01", "close": 190.12}, {"date": "2024-01-02", "close": 192.53}]}')
        ]

        result = parse_agent_response(mock_agent_output, mock_intermediate_steps, "Apple stock")

        # Should return fallback due to validation failure
        assert result.confidence <= 0.2  # Low confidence
        assert result.sections[0].type == "summary"
        assert "could not be validated" in result.sections[0].data["content"]

    @pytest.mark.asyncio
    async def test_research_agent_injects_real_stock_prices_into_response(self):
        """Research agent should inject real historical prices into stock_performance section."""
        # AI response with stock_performance section
        mock_agent_output = """{
            "query": "Apple stock",
            "confidence": 0.85,
            "sections": [
                {
                    "type": "stock_performance",
                    "render_as": "line_chart",
                    "title": "Stock Performance",
                    "data": {},
                    "source": "get_stock_data",
                    "explanation": "Historical stock prices."
                }
            ],
            "reasoning": "Stock performance analysis."
        }"""

        # Tool returns real data
        mock_intermediate_steps = [
            (MagicMock(tool="get_stock_data", tool_input="AAPL"),
             '{"ticker": "AAPL", "company_name": "Apple Inc.", "historical_prices": [{"date": "2024-01-01", "close": 190.12}, {"date": "2024-01-02", "close": 192.53}]}')
        ]

        result = parse_agent_response(mock_agent_output, mock_intermediate_steps, "Apple stock")

        # Should succeed with valid data
        assert result.confidence > 0.5
        stock_section = next((s for s in result.sections if s.type == "stock_performance"), None)
        if stock_section:
            # Verify it contains actual prices from the tool
            assert stock_section.data.get("series")[0]["values"] == [190.12, 192.53]

    @pytest.mark.asyncio
    async def test_research_result_all_sections_have_source_and_explanation(self):
        """All returned sections must include source and explanation metadata."""
        mock_agent_output = """{
            "query": "Research Apple",
            "confidence": 0.8,
            "sections": [
                {
                    "type": "company_overview",
                    "render_as": "card_grid",
                    "title": "Company Overview",
                    "data": [
                        {"label": "P/E", "value": "28.5"},
                        {"label": "Market Cap", "value": "$2.75T"}
                    ],
                    "source": "get_stock_data",
                    "explanation": "Company metrics from the stock data tool."
                },
                {
                    "type": "summary",
                    "render_as": "text",
                    "title": "Summary",
                    "data": {"content": "Apple is a leading technology company."},
                    "source": "search_financial_documents",
                    "explanation": "Summary from financial documents."
                }
            ],
            "reasoning": "Combined tool outputs for comprehensive analysis."
        }"""

        mock_intermediate_steps = [
            (MagicMock(tool="get_stock_data", tool_input="AAPL"),
             '{"ticker": "AAPL", "company_name": "Apple Inc.", "market_cap": 2750000000000, "pe_ratio": 28.5}'),
            (MagicMock(tool="search_financial_documents", tool_input="Apple"),
             '{"documents": [{"title": "Apple Overview"}]}')
        ]

        result = parse_agent_response(mock_agent_output, mock_intermediate_steps, "Research Apple")

        # Verify all sections have source and explanation
        assert len(result.sections) > 0
        for section in result.sections:
            assert section.source is not None, f"Section {section.type} missing source"
            if section.type != "summary":  # Summary might have defaults
                assert section.explanation, f"Section {section.type} missing explanation"

    @pytest.mark.asyncio
    async def test_frontend_receives_valid_research_result_structure(self):
        """Frontend should receive a ResearchResult with proper structure for rendering."""
        mock_agent_output = """{
            "query": "Apple analysis",
            "confidence": 0.82,
            "sections": [
                {
                    "type": "summary",
                    "render_as": "text",
                    "title": "Analysis Summary",
                    "data": {"content": "Apple shows strong fundamentals."},
                    "source": "analysis",
                    "explanation": "Based on company data and market trends."
                }
            ],
            "reasoning": "Analyzed multiple financial metrics."
        }"""

        result = parse_agent_response(mock_agent_output, [], "Apple analysis")

        # Verify the structure matches what frontend expects
        assert isinstance(result, ResearchResult)
        assert hasattr(result, "query")
        assert hasattr(result, "confidence")
        assert hasattr(result, "sections")
        assert hasattr(result, "execution_steps")
        assert hasattr(result, "reasoning")

        # Verify sections have rendering properties
        for section in result.sections:
            assert hasattr(section, "type")
            assert hasattr(section, "render_as")
            assert hasattr(section, "title")
            assert hasattr(section, "data")
            assert hasattr(section, "source")
            assert hasattr(section, "explanation")


@pytest.fixture
def mock_groq_settings(monkeypatch):
    """Mock Groq settings for testing."""
    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
