from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    row_count: int
    uploaded_at: datetime


class UploadOut(BaseModel):
    dataset: DatasetOut
    warnings: list[str] = Field(default_factory=list)


class KPIOut(BaseModel):
    total_revenue: float
    total_orders: int
    average_order_value: float
    total_customers: int
    revenue_growth: float | None


class ChartPoint(BaseModel):
    label: str
    value: float


class DashboardOut(BaseModel):
    dataset: DatasetOut
    kpis: KPIOut
    revenue_over_time: list[ChartPoint]
    revenue_by_region: list[ChartPoint]
    revenue_by_category: list[ChartPoint]
    top_products: list[ChartPoint]
    order_trend: list[ChartPoint]
    insights: list[str]


class SaleOut(BaseModel):
    id: int
    order_id: str
    order_date: date
    customer_id: str
    product: str
    category: str
    region: str
    quantity: int
    unit_price: float
    revenue: float


class SalesPage(BaseModel):
    items: list[SaleOut]
    total: int
    limit: int
    offset: int


class OptionsOut(BaseModel):
    items: list[str]


class AskIn(BaseModel):
    question: str


class VisualizationOut(BaseModel):
    type: Literal["line", "bar", "pie", "table", "histogram"]
    title: str
    data: list[ChartPoint]


class AskOut(BaseModel):
    answer: str
    intent: str
    metrics: dict[str, Any]
    visualization: VisualizationOut
    query_id: int