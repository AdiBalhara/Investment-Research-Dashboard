"""Unit tests for research agent output validation and fallback behavior."""

import pytest
from app.research.schemas import ResearchSection, ResearchResult, ExecutionStep
from app.research.agent import (
    _validate_section,
    _validate_research_result,
    _build_stock_performance_section,
    _inject_actual_stock_performance,
)


class TestResearchSectionValidation:
    """Tests for individual section validation against tool outputs."""

    def test_company_overview_valid_with_tool_data(self):
        """Company overview should validate when data matches tool output."""
        tool_outputs = {
            "get_stock_data": [{
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "current_price": 175.50,
                "market_cap": 2_750_000_000_000,
                "revenue": 383_285_000_000,
                "pe_ratio": 28.5,
                "52_week_high": 199.62,
                "52_week_low": 164.08,
            }]
        }

        section = ResearchSection(
            type="company_overview",
            render_as="card_grid",
            title="Overview",
            data=[
                {"label": "Market Cap", "value": "$2.75T"},
                {"label": "P/E", "value": "28.5"},
                {"label": "Current Price", "value": "$175.50"},
            ],
            source="get_stock_data",
            explanation="Company metrics from stock data.",
        )

        assert _validate_section(section, tool_outputs) is True

    def test_company_overview_invalid_missing_tool_data(self):
        """Company overview should fail when tool data is missing."""
        tool_outputs = {"search_news": []}

        section = ResearchSection(
            type="company_overview",
            render_as="card_grid",
            title="Overview",
            data=[{"label": "P/E", "value": "28.5"}],
            source="get_stock_data",
            explanation="Company metrics.",
        )

        assert _validate_section(section, tool_outputs) is False

    def test_stock_performance_valid_with_historical_prices(self):
        """Stock performance should validate when chart uses actual historical prices."""
        tool_outputs = {
            "get_stock_data": [{
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "historical_prices": [
                    {"date": "2024-01-01", "close": 190.12},
                    {"date": "2024-01-02", "close": 192.53},
                    {"date": "2024-01-03", "close": 189.95},
                ]
            }]
        }

        section = ResearchSection(
            type="stock_performance",
            render_as="line_chart",
            title="Stock Performance",
            data={
                "labels": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "series": [{
                    "name": "Apple Inc. Stock Price",
                    "values": [190.12, 192.53, 189.95],
                }]
            },
            source="get_stock_data",
            explanation="Historical closing prices from stock data tool.",
        )

        assert _validate_section(section, tool_outputs) is True

    def test_stock_performance_invalid_hallucinated_prices(self):
        """Stock performance should fail when chart has hallucinated prices."""
        tool_outputs = {
            "get_stock_data": [{
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "historical_prices": [
                    {"date": "2024-01-01", "close": 190.12},
                    {"date": "2024-01-02", "close": 192.53},
                ]
            }]
        }

        section = ResearchSection(
            type="stock_performance",
            render_as="line_chart",
            title="Stock Performance",
            data={
                "labels": ["2024-01-01", "2024-01-02"],
                "series": [{
                    "name": "Apple Inc. Stock Price",
                    "values": [999.99, 1000.50],  # Hallucinated prices
                }]
            },
            source="get_stock_data",
            explanation="Stock prices.",
        )

        assert _validate_section(section, tool_outputs) is False

    def test_section_missing_source(self):
        """Section should fail validation if source is missing."""
        tool_outputs = {}

        section = ResearchSection(
            type="summary",
            render_as="text",
            title="Summary",
            data={"content": "Some text"},
            source=None,  # Missing source
            explanation="Summary of findings.",
        )

        assert _validate_section(section, tool_outputs) is False

    def test_section_missing_explanation(self):
        """Section should fail validation if explanation is missing."""
        tool_outputs = {}

        section = ResearchSection(
            type="summary",
            render_as="text",
            title="Summary",
            data={"content": "Some text"},
            source="manual",
            explanation="",  # Empty explanation
        )

        assert _validate_section(section, tool_outputs) is False

    def test_news_sentiment_valid_with_tool_titles(self):
        """News sentiment section should validate when articles come from search_news tool."""
        tool_outputs = {
            "search_news": [{
                "articles": [
                    {"title": "Apple Announces New Product", "source": "TechNews"},
                    {"title": "Apple Q4 Earnings Beat", "source": "FinanceDaily"},
                ]
            }]
        }

        section = ResearchSection(
            type="news_sentiment",
            render_as="news_cards",
            title="News Sentiment",
            data=[
                {
                    "title": "Apple Announces New Product",
                    "source": "TechNews",
                    "sentiment": "positive",
                    "summary": "Apple announced...",
                },
                {
                    "title": "Apple Q4 Earnings Beat",
                    "source": "FinanceDaily",
                    "sentiment": "positive",
                    "summary": "Q4 earnings...",
                },
            ],
            source="search_news",
            explanation="Recent news articles about the company.",
        )

        assert _validate_section(section, tool_outputs) is True

    def test_news_sentiment_invalid_hallucinated_titles(self):
        """News sentiment should fail when article titles don't match tool output."""
        tool_outputs = {
            "search_news": [{
                "articles": [
                    {"title": "Apple Announces New Product", "source": "TechNews"},
                ]
            }]
        }

        section = ResearchSection(
            type="news_sentiment",
            render_as="news_cards",
            title="News Sentiment",
            data=[
                {
                    "title": "Apple Invents Time Machine",  # Hallucinated title
                    "source": "FakeTech",
                    "sentiment": "positive",
                    "summary": "Made up news...",
                },
            ],
            source="search_news",
            explanation="News articles.",
        )

        assert _validate_section(section, tool_outputs) is False


class TestResearchResultValidation:
    """Tests for complete research result validation."""

    def test_valid_research_result_with_all_sections(self):
        """Complete research result with valid sections should pass validation."""
        tool_outputs = {
            "get_stock_data": [{
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "current_price": 175.50,
                "market_cap": 2_750_000_000_000,
                "revenue": 383_285_000_000,
                "pe_ratio": 28.5,
                "52_week_high": 199.62,
                "52_week_low": 164.08,
                "historical_prices": [
                    {"date": "2024-01-01", "close": 190.12},
                    {"date": "2024-01-02", "close": 192.53},
                ]
            }],
            "search_news": [{
                "articles": [
                    {"title": "Apple News", "source": "TechNews"},
                ]
            }]
        }

        result = {
            "query": "Tell me about Apple",
            "confidence": 0.85,
            "sections": [
                {
                    "type": "summary",
                    "render_as": "text",
                    "title": "Summary",
                    "data": {"content": "Apple is a technology company."},
                    "source": "search_financial_documents",
                    "explanation": "Summary from documents.",
                },
                {
                    "type": "company_overview",
                    "render_as": "card_grid",
                    "title": "Overview",
                    "data": [
                        {"label": "P/E", "value": "28.5"},
                        {"label": "Market Cap", "value": "$2.75T"},
                    ],
                    "source": "get_stock_data",
                    "explanation": "Company metrics.",
                },
                {
                    "type": "stock_performance",
                    "render_as": "line_chart",
                    "title": "Performance",
                    "data": {
                        "labels": ["2024-01-01", "2024-01-02"],
                        "series": [{"name": "Apple Inc. Stock Price", "values": [190.12, 192.53]}]
                    },
                    "source": "get_stock_data",
                    "explanation": "Historical prices.",
                },
            ],
            "reasoning": "Used tool data.",
        }

        assert _validate_research_result(result, tool_outputs) is True

    def test_research_result_invalid_missing_sections(self):
        """Research result should fail if sections array is missing."""
        result = {
            "query": "Tell me about Apple",
            "confidence": 0.85,
            # Missing sections
            "reasoning": "Used tool data.",
        }

        assert _validate_research_result(result, {}) is False

    def test_research_result_invalid_section_type(self):
        """Research result should fail if a section has invalid type."""
        result = {
            "query": "Tell me about Apple",
            "confidence": 0.85,
            "sections": [
                {
                    "type": "invalid_section_type",  # Invalid
                    "render_as": "text",
                    "title": "Invalid",
                    "data": {"content": "Test"},
                    "source": "test",
                    "explanation": "Test explanation.",
                },
            ],
            "reasoning": "Used tool data.",
        }

        assert _validate_research_result(result, {}) is False


class TestStockPerformanceGrounding:
    """Tests for stock performance chart grounding with actual historical data."""

    def test_build_stock_performance_section_with_valid_history(self):
        """Should build a valid stock performance section from historical prices."""
        stock_data = {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "historical_prices": [
                {"date": "2024-01-01", "close": 190.12},
                {"date": "2024-01-02", "close": 192.53},
                {"date": "2024-01-03", "close": 189.95},
            ]
        }

        section = _build_stock_performance_section(stock_data)

        assert section.get("type") == "stock_performance"
        assert section.get("render_as") == "line_chart"
        assert section.get("source") == "get_stock_data"
        assert section["data"]["labels"] == ["2024-01-01", "2024-01-02", "2024-01-03"]
        assert section["data"]["series"][0]["values"] == [190.12, 192.53, 189.95]

    def test_build_stock_performance_section_with_empty_history(self):
        """Should return empty dict when historical prices are missing or empty."""
        stock_data = {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "historical_prices": []  # Empty
        }

        section = _build_stock_performance_section(stock_data)

        assert section == {}

    def test_inject_actual_stock_performance_replaces_hallucinacored_chart(self):
        """Should replace hallucinated stock chart with real data from get_stock_data."""
        tool_outputs = {
            "get_stock_data": [{
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "historical_prices": [
                    {"date": "2024-01-01", "close": 190.12},
                    {"date": "2024-01-02", "close": 192.53},
                ]
            }]
        }

        data = {
            "query": "Apple stock",
            "sections": [
                {
                    "type": "stock_performance",
                    "render_as": "line_chart",
                    "title": "Performance",
                    "data": {
                        "labels": ["2024-01-01", "2024-01-02"],
                        "series": [{"name": "Apple Inc. Stock Price", "values": [999.99, 1000.50]}]  # Hallucinated
                    },
                    "source": "get_stock_data",
                    "explanation": "Chart.",
                },
            ]
        }

        result = _inject_actual_stock_performance(data, tool_outputs)

        # Should have replaced with real data
        stock_chart = result["sections"][0]
        assert stock_chart["data"]["series"][0]["values"] == [190.12, 192.53]

    def test_inject_actual_stock_performance_appends_if_missing(self):
        """Should append a stock performance section if none exists."""
        tool_outputs = {
            "get_stock_data": [{
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "historical_prices": [
                    {"date": "2024-01-01", "close": 190.12},
                ]
            }]
        }

        data = {
            "query": "Apple stock",
            "sections": [
                {
                    "type": "summary",
                    "render_as": "text",
                    "title": "Summary",
                    "data": {"content": "Summary"},
                    "source": "manual",
                    "explanation": "Summary.",
                },
            ]
        }

        result = _inject_actual_stock_performance(data, tool_outputs)

        # Should have appended stock_performance section
        assert len(result["sections"]) == 2
        assert result["sections"][1]["type"] == "stock_performance"

    def test_inject_actual_stock_performance_handles_missing_stock_data(self):
        """Should not modify data if stock tool data is not available."""
        tool_outputs = {}  # No stock data

        original_data = {
            "query": "Apple stock",
            "sections": [
                {
                    "type": "summary",
                    "render_as": "text",
                    "title": "Summary",
                    "data": {"content": "Summary"},
                    "source": "manual",
                    "explanation": "Summary.",
                },
            ]
        }

        result = _inject_actual_stock_performance(original_data, tool_outputs)

        # Should be unchanged
        assert result == original_data
