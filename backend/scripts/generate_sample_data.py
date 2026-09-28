import csv
import random
from datetime import date, timedelta
from pathlib import Path


random.seed(42)
output = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"
output.parent.mkdir(parents=True, exist_ok=True)

catalog = [
    ("Arc Desk Lamp", "Lighting", 78),
    ("Halo Floor Lamp", "Lighting", 164),
    ("Task Lamp Mini", "Lighting", 42),
    ("Studio Desk", "Furniture", 425),
    ("Form Task Chair", "Furniture", 289),
    ("Oak Side Table", "Furniture", 138),
    ("Wireless Keyboard", "Accessories", 89),
    ("Precision Mouse", "Accessories", 54),
    ("Canvas Tote", "Accessories", 24),
    ("Notebook Set", "Stationery", 18),
    ("Desk Organizer", "Stationery", 36),
    ("Felt Pen Pack", "Stationery", 14),
]
regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
weights = [1.0, 1.1, 0.9, 0.82, 1.16, 0.75, 1.25, 1.35, 1.4, 1.55, 1.18, 1.12]
start = date(2025, 1, 1)
end = date(2026, 6, 30)
days = (end - start).days

with output.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["order_id", "order_date", "customer_id", "product", "category", "region", "quantity", "unit_price", "revenue"])
    for index in range(1, 1201):
        order_date = start + timedelta(days=random.randint(0, days))
        product_index = random.choices(range(len(catalog)), weights=weights, k=1)[0]
        product, category, list_price = catalog[product_index]
        quantity = random.choices([1, 2, 3, 4], weights=[70, 22, 6, 2], k=1)[0]
        unit_price = round(list_price * random.uniform(0.92, 1.08), 2)
        revenue = round(quantity * unit_price, 2)
        customer_number = random.randint(1, 335)
        region = random.choices(regions, weights=[1.05, 1.14, 0.92, 0.87, 1.18], k=1)[0]
        writer.writerow([
            f"ORD-{order_date:%y%m}-{index:05d}", order_date.isoformat(), f"C-{customer_number:04d}",
            product, category, region, quantity, f"{unit_price:.2f}", f"{revenue:.2f}",
        ])

print(f"Wrote 1,200 sales rows to {output}")