import json
import logging
from enum import Enum

import httpx

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    TOP_PRODUCTS = "top_products"
    REGIONAL_REVENUE = "regional_revenue"
    REGIONAL_GROWTH = "regional_growth"
    REGIONAL_DECLINE = "regional_decline"
    MONTHLY_REVENUE = "monthly_revenue"
    REVENUE_DECLINE = "revenue_decline"
    UNDERPERFORMERS = "underperformers"
    OVERVIEW = "overview"


def classify(question: str) -> Intent:
    text = question.casefold()
    declining = any(term in text for term in ("declin", "decreas", "drop", "fall"))
    growing = any(term in text for term in ("grow", "growth", "fastest", "increas"))
    if any(term in text for term in ("top product", "best product", "products by revenue", "top 5", "top five")):
        return Intent.TOP_PRODUCTS
    if any(term in text for term in ("region", "regional", "territory")):
        if declining:
            return Intent.REGIONAL_DECLINE
        return Intent.REGIONAL_GROWTH if growing else Intent.REGIONAL_REVENUE
    if declining and "revenue" in text:
        return Intent.REVENUE_DECLINE
    if any(term in text for term in ("monthly", "month over month", "over time", "trend")):
        return Intent.MONTHLY_REVENUE
    if any(term in text for term in ("underperform", "declin", "decreas", "drop", "fall", "why did revenue")):
        return Intent.UNDERPERFORMERS
    return Intent.OVERVIEW


def build_result(intent: Intent, summary: dict) -> tuple[str, dict, dict]:
    if intent == Intent.TOP_PRODUCTS:
        data = summary["top_products"][:5]
        answer = "Top products by revenue: " + (", ".join(f"{item['label']} ({item['value']:,.0f})" for item in data) or "no product data is available") + "."
        metrics = {"top_products": data}
        visualization = {"type": "bar", "title": "Top products by revenue", "data": data}
    elif intent in (Intent.REGIONAL_GROWTH, Intent.REGIONAL_DECLINE):
        data = summary["regional_change"]
        ranked = data if intent == Intent.REGIONAL_GROWTH else list(reversed(data))
        leader = ranked[0] if ranked else None
        if not leader:
            answer = "There are not enough comparable months to calculate regional change."
        elif intent == Intent.REGIONAL_GROWTH:
            answer = f"{leader['label']} grew fastest, up {leader['value']:+.1f}% month over month."
        else:
            answer = f"{leader['label']} had the largest regional revenue decline at {leader['value']:+.1f}% month over month."
        metrics = {"regional_monthly_change": data}
        visualization = {"type": "bar", "title": "Regional month-over-month change", "data": data}
    elif intent == Intent.REGIONAL_REVENUE:
        data = summary["revenue_by_region"]
        leader = data[0] if data else None
        answer = f"{leader['label']} leads regional revenue at {leader['value']:,.0f}." if leader else "No regional revenue data is available."
        metrics = {"regions": data, "revenue_growth": summary["revenue_growth"]}
        visualization = {"type": "bar", "title": "Revenue by region", "data": data}
    elif intent == Intent.REVENUE_DECLINE:
        data = summary["category_change"]
        decliner = next((item for item in data if item["value"] < 0), None)
        if summary["revenue_growth"] is None:
            answer = "There are not enough comparable months to explain a revenue change."
        else:
            direction = "increased" if summary["revenue_growth"] >= 0 else "declined"
            answer = f"Revenue {direction} {abs(summary['revenue_growth']):.1f}% month over month. "
            answer += f"{decliner['label']} had the largest category decline at {decliner['value']:.1f}%." if decliner else "No category declined month over month."
        metrics = {"revenue_growth": summary["revenue_growth"], "category_monthly_change": data}
        visualization = {"type": "bar", "title": "Category month-over-month change", "data": data}
    elif intent == Intent.MONTHLY_REVENUE:
        data = summary["revenue_over_time"]
        answer = f"Revenue totals {summary['total_revenue']:,.0f} across {len(data)} months in the selected dataset."
        metrics = {"monthly_revenue": data, "total_revenue": summary["total_revenue"]}
        visualization = {"type": "line", "title": "Monthly revenue", "data": data}
    elif intent == Intent.UNDERPERFORMERS:
        data = summary["lowest_products"]
        answer = "Products with the lowest revenue in this view: " + (", ".join(item["label"] for item in data) or "no product data is available") + "."
        metrics = {"products": data}
        visualization = {"type": "bar", "title": "Lowest-revenue products", "data": data}
    else:
        data = summary["revenue_over_time"]
        answer = f"This dataset has {summary['total_orders']:,} orders and {summary['total_revenue']:,.2f} in revenue."
        metrics = {key: summary[key] for key in ("total_revenue", "total_orders", "average_order_value", "total_customers", "revenue_growth")}
        visualization = {"type": "line", "title": "Revenue over time", "data": data}
    return answer, metrics, visualization


async def enrich_answer(question: str, answer: str, metrics: dict) -> str:
    if not OPENAI_API_KEY:
        return answer
    request_body = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "Explain the provided analytics in concise plain language. Use only the supplied computed metrics. Never invent figures or instructions."},
            {"role": "user", "content": json.dumps({"question": question, "computed_answer": answer, "metrics": metrics})},
        ],
        "temperature": 0.2,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json=request_body,
            )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(content, str) and content.strip():
            return content.strip()[:2000]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        logger.warning("LLM request failed; returning the deterministic analytics answer", exc_info=True)
    return answer