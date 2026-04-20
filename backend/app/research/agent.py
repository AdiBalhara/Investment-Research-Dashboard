import json
import time
import logging
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_json_chat_agent, AgentExecutor

from app.config import get_settings
from app.research.tools.stock_data import get_stock_data
from app.research.tools.news_search import search_news
from app.research.tools.vector_search import search_financial_documents
from app.research.schemas import ResearchResult, ResearchSection, ExecutionStep

logger = logging.getLogger(__name__)
settings = get_settings()


SYSTEM_PROMPT = """You are a financial research assistant. Use the tools to gather real data before answering.

The final output must be valid JSON matching the research schema.
Output keys must include: query, confidence, sections, and reasoning.
Each section must include type, render_as, title, data, source, and explanation.
Allowed section types: summary, company_overview, stock_performance, financial_comparison, news_sentiment, risk_analysis.
Allowed render modes: card_grid, table, line_chart, bar_chart, news_cards, text.

IMPORTANT TOOL USAGE RULES:
- For ANY query mentioning a company or ticker, ALWAYS call BOTH get_stock_data AND search_news — every time, no exceptions.
- For comparison queries (e.g. "Compare MSFT and GOOGL"), call get_stock_data for EACH ticker separately, then call search_news.
- Always include a news_sentiment section when search_news returns articles.
- If search_financial_documents fails or returns no results, continue — do NOT give up.
- Only omit a section if the required data tool ALSO failed.
- Never blame unavailable vector search for inability to answer — use get_stock_data and search_news instead.
"""

HUMAN_PROMPT = """TOOLS
------
{tools}

TOOLS AVAILABLE: {tool_names}

INSTRUCTIONS:
- Use tools whenever the user query asks for factual financial data.
- If you need a tool, respond with valid JSON containing a single action:
```json
{{
  "action": "<tool_name>",
  "action_input": "<tool input>"
}}
```
- When you are finished, respond with valid JSON containing a final answer action:
```json
{{
  "action": "Final Answer",
  "action_input": {{
    "query": "<user query>",
    "confidence": 0.8,
    "sections": [
      {{
        "type": "<section type>",
        "render_as": "<render mode>",
        "title": "<section title>",
        "data": {{ ... }},
        "source": "<source>",
        "explanation": "<brief explanation>"
      }}
    ],
    "reasoning": "<brief explanation>"
  }}
}}
```
- Do not include any extra text outside the JSON structure.
- Use the tools to ground numerical values and stock performance data.

USER'S INPUT
--------------------
{input}
"""


def _try_parse_json(text: str):
    if not isinstance(text, str):
        return None

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


ALLOWED_SECTION_TYPES = {
    "summary",
    "company_overview",
    "stock_performance",
    "financial_comparison",
    "news_sentiment",
    "risk_analysis",
}

ALLOWED_RENDER_MODES = {
    "card_grid",
    "table",
    "line_chart",
    "bar_chart",
    "news_cards",
    "text",
}


def _extract_tool_outputs(intermediate_steps: list) -> dict:
    tool_outputs: dict[str, list] = {}
    for step in intermediate_steps:
        if not step or not isinstance(step, (list, tuple)) or len(step) < 2:
            continue

        action = step[0]
        observation = step[1]
        tool_name = getattr(action, "tool", None) or "unknown"
        parsed = _try_parse_json(observation) if isinstance(observation, str) else observation
        tool_outputs.setdefault(tool_name, []).append(parsed)

    logger.info(f"Extracted tool outputs keys: {list(tool_outputs.keys())}")
    return tool_outputs


def _build_stock_performance_section(stock_data: dict) -> dict:
    history = stock_data.get("historical_prices")
    if not isinstance(history, list) or len(history) == 0:
        return {}

    labels = [item.get("date") for item in history if isinstance(item, dict) and item.get("date")]
    values = [item.get("close") for item in history if isinstance(item, dict) and item.get("close") is not None]

    if not labels or not values or len(labels) != len(values):
        return {}

    return {
        "type": "stock_performance",
        "render_as": "line_chart",
        "title": "Stock Performance",
        "data": {
            "labels": labels,
            "series": [
                {
                    "name": f"{stock_data.get('company_name', stock_data.get('ticker', 'Stock'))} Stock Price",
                    "values": values,
                }
            ],
        },
        "source": "get_stock_data",
        "explanation": "This chart uses historical closing prices from the stock data tool.",
    }


def _inject_actual_stock_performance(data: dict, tool_outputs: dict[str, list]) -> dict:
    stock_data = _get_primary_stock_data(tool_outputs)
    if stock_data is None:
        return data

    actual_section = _build_stock_performance_section(stock_data)
    if not actual_section:
        return data

    sections = data.get("sections", []) or []
    replaced = False
    for idx, section in enumerate(sections):
        if isinstance(section, dict) and section.get("type") == "stock_performance":
            sections[idx] = actual_section
            replaced = True

    if not replaced:
        sections.append(actual_section)

    data["sections"] = sections
    return data


def _parse_numeric_value(value: str) -> float | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip().replace("$", "").replace(",", "").lower()
    multiplier = 1.0
    if normalized.endswith("t"):
        multiplier = 1_000_000_000_000
        normalized = normalized[:-1]
    elif normalized.endswith("b"):
        multiplier = 1_000_000_000
        normalized = normalized[:-1]
    elif normalized.endswith("m"):
        multiplier = 1_000_000
        normalized = normalized[:-1]
    elif normalized.endswith("k"):
        multiplier = 1_000
        normalized = normalized[:-1]

    try:
        value_float = float(normalized)
        return value_float * multiplier
    except ValueError:
        return None


def _numeric_matches_tool(value: str, actual: Any, tolerance: float = 0.05) -> bool:
    parsed = _parse_numeric_value(value)
    if parsed is None:
        try:
            parsed = float(value)
        except (ValueError, TypeError):
            return False

    if actual is None:
        return False

    try:
        actual_number = float(actual)
    except (ValueError, TypeError):
        return False

    if actual_number == 0:
        return abs(parsed) < 1e-6

    return abs(parsed - actual_number) <= abs(actual_number) * tolerance


def _get_primary_stock_data(tool_outputs: dict[str, list]) -> dict | None:
    for data in tool_outputs.get("get_stock_data", []):
        if isinstance(data, dict) and not data.get("error"):
            return data
    return None


def _get_news_titles(tool_outputs: dict[str, list]) -> set:
    titles = set()
    for data in tool_outputs.get("search_news", []):
        if isinstance(data, dict):
            for article in data.get("articles", []):
                if isinstance(article, dict) and article.get("title"):
                    titles.add(article.get("title"))
    return titles


def _get_news_articles_map(tool_outputs: dict[str, list]) -> dict:
    """Return a dict mapping article title -> full article dict from tool output."""
    articles_map: dict = {}
    for data in tool_outputs.get("search_news", []):
        if isinstance(data, dict):
            for article in data.get("articles", []):
                if isinstance(article, dict) and article.get("title"):
                    articles_map[article["title"]] = article
    return articles_map


def _get_known_company_names(tool_outputs: dict[str, list]) -> set:
    companies = set()
    # Collect from ALL stock data calls (supports multi-ticker comparison queries)
    for data in tool_outputs.get("get_stock_data", []):
        if isinstance(data, dict) and not data.get("error"):
            if data.get("company_name"):
                companies.add(data.get("company_name"))
            if data.get("ticker"):
                companies.add(data.get("ticker"))

    for data in tool_outputs.get("search_financial_documents", []):
        if isinstance(data, dict):
            metadata = data.get("metadata")
            if isinstance(metadata, dict) and metadata.get("company"):
                companies.add(metadata.get("company"))

    return {company.lower() for company in companies if isinstance(company, str)}


def _format_large_number(value) -> str:
    """Format a large number into a human-readable string."""
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return str(value)
    if v >= 1_000_000_000_000:
        return f"${v / 1_000_000_000_000:.2f}T"
    if v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.2f}B"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.2f}M"
    return f"${v:,.2f}"


def _build_company_overview_items(stock_data: dict) -> list:
    """Build a validated list of label/value dicts from stock tool data."""
    items = []
    if stock_data.get("company_name"):
        items.append({"label": "Company", "value": stock_data["company_name"]})
    if stock_data.get("ticker"):
        items.append({"label": "Ticker", "value": stock_data["ticker"]})
    if stock_data.get("current_price") is not None:
        items.append({"label": "Current Price", "value": f"${stock_data['current_price']}"})
    if stock_data.get("market_cap") is not None:
        items.append({"label": "Market Cap", "value": _format_large_number(stock_data["market_cap"])})
    if stock_data.get("pe_ratio") is not None:
        items.append({"label": "P/E Ratio", "value": str(round(float(stock_data["pe_ratio"]), 2))})
    if stock_data.get("forward_pe") is not None:
        items.append({"label": "Forward P/E", "value": str(round(float(stock_data["forward_pe"]), 2))})
    if stock_data.get("52_week_high") is not None:
        items.append({"label": "52 Week High", "value": f"${stock_data['52_week_high']}"})
    if stock_data.get("52_week_low") is not None:
        items.append({"label": "52 Week Low", "value": f"${stock_data['52_week_low']}"})
    if stock_data.get("sector"):
        items.append({"label": "Sector", "value": stock_data["sector"]})
    if stock_data.get("industry"):
        items.append({"label": "Industry", "value": stock_data["industry"]})
    if stock_data.get("dividend_yield") is not None:
        items.append({"label": "Dividend Yield", "value": f"{round(float(stock_data['dividend_yield']) * 100, 2)}%"})
    return items


def _filter_valid_sections(data: dict, tool_outputs: dict[str, list]) -> dict:
    """Remove sections that cannot be validated due to missing tool data."""
    sections = data.get("sections", []) or []
    filtered_sections = []
    stock_data = _get_primary_stock_data(tool_outputs)
    news_titles = _get_news_titles(tool_outputs)

    for section_data in sections:
        if not isinstance(section_data, dict):
            continue

        section_type = section_data.get("type", "")
        render_as = section_data.get("render_as", "")

        # Skip stock_performance if no valid stock data
        if section_type == "stock_performance" and stock_data is None:
            logger.debug("Skipping stock_performance section: no valid stock data available")
            continue

        # Skip company_overview if no stock data
        if section_type == "company_overview" and stock_data is None:
            logger.debug("Skipping company_overview section: no valid stock data available")
            continue

        # Normalize company_overview: always rebuild from tool data so validation passes
        if section_type == "company_overview" and stock_data is not None:
            items = _build_company_overview_items(stock_data)
            if not items:
                continue
            section_data = dict(
                section_data,
                data=items,
                source=stock_data.get("source", "get_stock_data"),
            )

        # Skip news_sentiment if no news data
        if section_type == "news_sentiment" and not news_titles:
            logger.debug("Skipping news_sentiment section: no news data available")
            continue

        # Normalize news_sentiment: enrich items with summary/url from tool output
        if section_type == "news_sentiment":
            articles_map = _get_news_articles_map(tool_outputs)
            raw_items = section_data.get("data", [])
            if isinstance(raw_items, list):
                normalized_items = []
                for item in raw_items:
                    if not isinstance(item, dict):
                        continue
                    title = item.get("title", "")
                    tool_article = articles_map.get(title, {})
                    normalized_items.append({
                        "title": title,
                        "source": item.get("source") or tool_article.get("source", ""),
                        "sentiment": item.get("sentiment") or tool_article.get("sentiment", "neutral"),
                        "summary": item.get("summary") or tool_article.get("description", "") or "",
                        "url": item.get("url") or tool_article.get("url", ""),
                    })
                section_data = dict(section_data, data=normalized_items)

        # Skip financial_comparison if no company data
        if section_type == "financial_comparison" and stock_data is None:
            logger.debug("Skipping financial_comparison section: no company data available")
            continue

        # Normalize financial_comparison: agent may return a dict-of-dicts instead
        # of the required {headers: [...], rows: [[...]]} table format.
        if section_type == "financial_comparison":
            sec_data = section_data.get("data", {})
            if isinstance(sec_data, dict) and "headers" not in sec_data and "rows" not in sec_data:
                # Convert {"MSFT": {"price": ..., "pe": ...}, "GOOGL": {...}} → table
                companies = list(sec_data.keys())
                if companies and isinstance(sec_data[companies[0]], dict):
                    field_keys = list(sec_data[companies[0]].keys())
                    headers = ["Company"] + [k.replace("_", " ").title() for k in field_keys]
                    rows = []
                    for company, metrics in sec_data.items():
                        if isinstance(metrics, dict):
                            row = [company] + [str(metrics.get(k, "N/A")) for k in field_keys]
                            rows.append(row)
                    section_data = dict(section_data, data={"headers": headers, "rows": rows})
            elif isinstance(sec_data, list) and sec_data and isinstance(sec_data[0], dict):
                # Convert list-of-dicts format if the LLM uses that
                field_keys = list(sec_data[0].keys())
                headers = [k.replace("_", " ").title() for k in field_keys]
                rows = [[str(item.get(k, "N/A")) for k in field_keys] for item in sec_data if isinstance(item, dict)]
                section_data = dict(section_data, data={"headers": headers, "rows": rows})

            # If normalization didn't produce a valid table, drop the section
            normalized = section_data.get("data", {})
            if not isinstance(normalized, dict) or "headers" not in normalized or "rows" not in normalized or not normalized["rows"]:
                logger.debug("Skipping financial_comparison: could not normalize to table format")
                continue

        # Keep summary and risk_analysis as they don't require tool data
        # Normalize text sections: ensure data has a "content" key
        if section_type in ("summary", "risk_analysis"):
            sec_data = section_data.get("data")
            if isinstance(sec_data, dict) and "content" not in sec_data:
                # Pick the first string value found, or stringify the whole dict
                text = next(
                    (v for v in sec_data.values() if isinstance(v, str) and v.strip()),
                    str(sec_data),
                )
                section_data = dict(section_data, data={"content": text})
            elif isinstance(sec_data, str):
                section_data = dict(section_data, data={"content": sec_data})

        filtered_sections.append(section_data)

    data["sections"] = filtered_sections
    return data


def _build_fallback_response(agent_output: str, tool_outputs: dict[str, list]) -> str:
    """Build a fallback response using available tool outputs."""
    stock_data = _get_primary_stock_data(tool_outputs)
    news_data = tool_outputs.get("search_news", [])

    parts = []

    if stock_data:
        ticker = stock_data.get("ticker", "unknown")
        company = stock_data.get("company_name", ticker)
        price = stock_data.get("current_price", "N/A")
        parts.append(f"Stock Information for {company} ({ticker}): Current price is ${price}.")
    else:
        # Check if there was a stock data error
        stock_errors = tool_outputs.get("get_stock_data", [])
        if stock_errors and isinstance(stock_errors[0], dict) and stock_errors[0].get("error"):
            parts.append(f"Stock data unavailable: {stock_errors[0].get('message', 'Unable to fetch stock data.')}")

    if news_data and isinstance(news_data[0], dict) and "articles" in news_data[0]:
        articles = news_data[0].get("articles", [])[:3]  # First 3 articles
        if articles:
            parts.append("\nRecent News:")
            for article in articles:
                title = article.get("title", "Unknown")
                source = article.get("source", "Unknown")
                parts.append(f"- {title} ({source})")

    if not parts:
        parts.append("Research completed, but no validated data could be displayed. Please try again or refine your query.")

    return "\n".join(parts)





def _validate_section(section: ResearchSection, tool_outputs: dict[str, list]) -> bool:
    if section.type not in ALLOWED_SECTION_TYPES:
        return False
    if section.render_as not in ALLOWED_RENDER_MODES:
        return False
    if not isinstance(section.explanation, str) or not section.explanation.strip():
        return False
    if section.source is None:
        return False
    if not isinstance(section.source, (str, list, dict)):
        return False

    data = section.data

    # Structural-only validation. Normalization in _filter_valid_sections already
    # rebuilt each section using actual tool output data, so we only need to
    # check that the shape is correct for the frontend to render safely.

    if section.type == "company_overview":
        if not isinstance(data, list) or len(data) == 0:
            return False
        for item in data:
            if not isinstance(item, dict) or "label" not in item or "value" not in item:
                return False
        return True

    if section.type == "stock_performance":
        if not isinstance(data, dict):
            return False
        labels = data.get("labels")
        series = data.get("series")
        if not isinstance(labels, list) or not isinstance(series, list) or len(series) == 0:
            return False
        first_series = series[0]
        if not isinstance(first_series, dict) or not isinstance(first_series.get("values"), list):
            return False
        return True

    if section.type == "financial_comparison":
        if not isinstance(data, dict):
            return False
        if not isinstance(data.get("headers"), list) or not isinstance(data.get("rows"), list):
            return False
        if len(data["headers"]) == 0 or len(data["rows"]) == 0:
            return False
        return True

    if section.type == "news_sentiment":
        if not isinstance(data, list) or len(data) == 0:
            return False
        for item in data:
            if not isinstance(item, dict):
                return False
            if not all(field in item for field in ("title", "source", "sentiment")):
                return False
            if item.get("title") not in titles:
                return False

        return True

    if section.type == "summary":
        return isinstance(data, dict) and isinstance(data.get("content"), str)

    if section.type == "risk_analysis":
        return isinstance(data, dict) and isinstance(data.get("content"), str)

    return False


def _validate_research_result(data: dict, tool_outputs: dict[str, list]) -> bool:
    if not isinstance(data, dict):
        return False
    if "sections" not in data or not isinstance(data["sections"], list):
        return False

    for section_data in data["sections"]:
        if not isinstance(section_data, dict):
            return False

        section = ResearchSection(
            type=section_data.get("type", ""),
            render_as=section_data.get("render_as", ""),
            title=section_data.get("title", ""),
            data=section_data.get("data", {}),
            source=section_data.get("source"),
            explanation=section_data.get("explanation", ""),
        )

        if not _validate_section(section, tool_outputs):
            logger.warning(f"Section failed validation: type={section.type} render_as={section.render_as} data_keys={list(section.data.keys()) if isinstance(section.data, dict) else type(section.data).__name__}")
            return False

    return True


def create_agent():
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=settings.GROQ_API_KEY,
        temperature=0.0,
        max_tokens=2000,
    )

    tools = [get_stock_data, search_news, search_financial_documents]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_json_chat_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )

    return agent_executor


def parse_agent_response(output: str, intermediate_steps: list, query: str) -> ResearchResult:
    """Parse the agent's output into a structured ResearchResult."""
    # Extract execution steps from intermediate steps
    execution_steps = []
    for step in intermediate_steps:
        if not step or not isinstance(step, (list, tuple)) or len(step) == 0:
            continue
        action = step[0]
        tool_name = action.tool if hasattr(action, "tool") else "unknown"
        tool_input = str(action.tool_input) if hasattr(action, "tool_input") else ""
        execution_steps.append(ExecutionStep(
            tool=tool_name,
            input=tool_input[:200],  # Truncate long inputs
            status="success",
        ))

    # Try to parse the output - could be JSON, dict, or raw text
    try:
        tool_outputs = _extract_tool_outputs(intermediate_steps)

        # Try JSON parsing first
        try:
            # Handle case where output is already a dict (create_json_chat_agent returns parsed dict)
            if isinstance(output, dict):
                data = output
            else:
                cleaned = output.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
                data = json.loads(cleaned)

            data = _inject_actual_stock_performance(data, tool_outputs)
            data = _filter_valid_sections(data, tool_outputs)

            if not _validate_research_result(data, tool_outputs):
                logger.warning("Agent output failed validation against tool output and schema.")
                raise ValueError("Structured output failed validation")

            sections = []
            for section_data in data.get("sections", []):
                sections.append(ResearchSection(
                    type=section_data.get("type", "summary"),
                    render_as=section_data.get("render_as", "text"),
                    title=section_data.get("title", ""),
                    data=section_data.get("data", {}),
                    source=section_data.get("source"),
                    explanation=section_data.get("explanation", ""),
                ))

            return ResearchResult(
                query=query,
                confidence=data.get("confidence", 0.7),
                sections=sections,
                execution_steps=execution_steps,
                reasoning=data.get("reasoning", ""),
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, treat the output as raw text and create a summary
            logger.debug("Output is not JSON, treating as raw text")
            fallback_content = _build_fallback_response(output, tool_outputs)
            return ResearchResult(
                query=query,
                confidence=0.4 if tool_outputs else 0.2,
                sections=[
                    ResearchSection(
                        type="summary",
                        render_as="text",
                        title="Research Results",
                        data={"content": fallback_content},
                        source="agent_output",
                        explanation="Agent output converted to summary.",
                    )
                ],
                execution_steps=execution_steps,
                reasoning="Raw agent output processed as text.",
            )

    except Exception as e:
        logger.warning(f"Failed to parse agent response: {e}")
        tool_outputs = _extract_tool_outputs(intermediate_steps)
        fallback_content = _build_fallback_response(output, tool_outputs)
        
        return ResearchResult(
            query=query,
            confidence=0.2,
            sections=[
                ResearchSection(
                    type="summary",
                    render_as="text",
                    title="Research Results",
                    data={"content": fallback_content},
                    source="fallback",
                    explanation="Processing error - showing available data.",
                )
            ],
            execution_steps=execution_steps,
            reasoning="Error processing response.",
        )


async def run_research(query: str) -> ResearchResult:
    """Run the AI research agent on a user query."""
    start_time = time.time()

    try:
        agent = create_agent()
        result = await agent.ainvoke({"input": query})

        output = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])
        
        logger.info(f"Agent output type: {type(output)}")
        logger.info(f"Agent output: {str(output)[:500]}")
        logger.info(f"Intermediate steps count: {len(intermediate_steps)}")

        research_result = parse_agent_response(output, intermediate_steps, query)

        # Update execution step durations
        total_time = int((time.time() - start_time) * 1000)
        if research_result.execution_steps:
            per_step = total_time // len(research_result.execution_steps)
            for step in research_result.execution_steps:
                step.duration_ms = per_step

        return research_result

    except Exception as e:
        logger.error(f"Research agent failed: {e}", exc_info=True)
        total_time = int((time.time() - start_time) * 1000)
        return ResearchResult(
            query=query,
            confidence=0.2,
            sections=[
                ResearchSection(
                    type="summary",
                    render_as="text",
                    title="Error",
                    data={"content": f"An error occurred while processing your query: {str(e)}. Please try again."},
                )
            ],
            execution_steps=[ExecutionStep(tool="agent", input=query, duration_ms=total_time, status="error")],
            reasoning="The AI agent encountered an error during processing.",
        )
