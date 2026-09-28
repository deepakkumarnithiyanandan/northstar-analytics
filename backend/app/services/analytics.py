from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.models import Customer, Dataset, Product, Sale


def latest_dataset(db: Session, dataset_id: int | None) -> Dataset:
    dataset = db.get(Dataset, dataset_id) if dataset_id else db.query(Dataset).order_by(Dataset.uploaded_at.desc(), Dataset.id.desc()).first()
    if dataset is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="No dataset is available. Upload a CSV or load the sample dataset.")
    return dataset


def sales_for_dataset(db: Session, dataset_id: int, start_date: date | None = None, end_date: date | None = None,
                      region: str | None = None, category: str | None = None, product: str | None = None):
    query = db.query(Sale, Product, Customer).join(Product, Sale.product_id == Product.id).join(Customer, Sale.customer_id == Customer.id)
    query = query.filter(Sale.dataset_id == dataset_id)
    if start_date:
        query = query.filter(Sale.order_date >= start_date)
    if end_date:
        query = query.filter(Sale.order_date <= end_date)
    if region:
        query = query.filter(Sale.region == region)
    if category:
        query = query.filter(Product.category == category)
    if product:
        query = query.filter(Product.name == product)
    return query.order_by(Sale.order_date.desc(), Sale.id.desc())


def summarize(rows):
    if not rows:
        return {
            "total_revenue": 0.0, "total_orders": 0, "average_order_value": 0.0,
            "total_customers": 0, "revenue_growth": None,
            "revenue_over_time": [], "revenue_by_region": [], "revenue_by_category": [],
            "regional_change": [], "category_change": [], "top_products": [],
            "lowest_products": [], "order_trend": [], "insights": [],
        }

    monthly = defaultdict(float)
    regions = defaultdict(float)
    categories = defaultdict(float)
    products = defaultdict(float)
    monthly_by_region = defaultdict(float)
    monthly_by_category = defaultdict(float)
    orders_by_month = defaultdict(set)
    order_revenue = defaultdict(float)
    customers = set()
    total_revenue = 0.0
    for sale, item, customer in rows:
        month = sale.order_date.strftime("%Y-%m")
        total_revenue += sale.revenue
        monthly[month] += sale.revenue
        regions[sale.region] += sale.revenue
        categories[item.category] += sale.revenue
        products[item.name] += sale.revenue
        monthly_by_region[(sale.region, month)] += sale.revenue
        monthly_by_category[(item.category, month)] += sale.revenue
        orders_by_month[month].add(sale.order_id)
        order_revenue[sale.order_id] += sale.revenue
        customers.add(customer.external_id)
    order_count = len(order_revenue)
    month_keys = sorted(monthly)
    growth = None
    if len(month_keys) >= 2 and monthly[month_keys[-2]]:
        growth = (monthly[month_keys[-1]] - monthly[month_keys[-2]]) / monthly[month_keys[-2]] * 100
    regional_change = []
    category_change = []
    if len(month_keys) >= 2:
        previous_month, latest_month = month_keys[-2:]
        regional_change = [
            {"label": name, "value": round((monthly_by_region[(name, latest_month)] - monthly_by_region[(name, previous_month)]) / monthly_by_region[(name, previous_month)] * 100, 2)}
            for name in regions if monthly_by_region[(name, previous_month)]
        ]
        category_change = [
            {"label": name, "value": round((monthly_by_category[(name, latest_month)] - monthly_by_category[(name, previous_month)]) / monthly_by_category[(name, previous_month)] * 100, 2)}
            for name in categories if monthly_by_category[(name, previous_month)]
        ]
    insights = []
    if month_keys:
        insights.append(f"{month_keys[-1]} is the latest month in this view with {monthly[month_keys[-1]]:,.0f} in revenue.")
    if regions:
        leader = max(regions, key=regions.get)
        insights.append(f"{leader} leads regions with {regions[leader]:,.0f} in revenue.")
    if growth is not None:
        direction = "up" if growth >= 0 else "down"
        insights.append(f"Revenue is {direction} {abs(growth):.1f}% versus the previous month in this dataset.")
    return {
        "total_revenue": round(total_revenue, 2), "total_orders": order_count,
        "average_order_value": round(total_revenue / order_count, 2) if order_count else 0.0,
        "total_customers": len(customers), "revenue_growth": round(growth, 2) if growth is not None else None,
        "revenue_over_time": [{"label": key, "value": round(monthly[key], 2)} for key in month_keys],
        "revenue_by_region": [{"label": key, "value": round(value, 2)} for key, value in sorted(regions.items(), key=lambda pair: pair[1], reverse=True)],
        "regional_change": sorted(regional_change, key=lambda item: item["value"], reverse=True),
        "category_change": sorted(category_change, key=lambda item: item["value"]),
        "revenue_by_category": [{"label": key, "value": round(value, 2)} for key, value in sorted(categories.items(), key=lambda pair: pair[1], reverse=True)],
        "top_products": [{"label": key, "value": round(value, 2)} for key, value in sorted(products.items(), key=lambda pair: pair[1], reverse=True)[:8]],
        "lowest_products": [{"label": key, "value": round(value, 2)} for key, value in sorted(products.items(), key=lambda pair: pair[1])[:5]],
        "order_trend": [{"label": key, "value": len(orders_by_month[key])} for key in month_keys],
        "insights": insights,
    }