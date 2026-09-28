import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException

from app.config import MAX_UPLOAD_BYTES, MAX_UPLOAD_ROWS


REQUIRED_COLUMNS = {
    "order_id", "order_date", "customer_id", "product", "category", "region", "quantity", "unit_price"
}


def parse_sales_csv(content: bytes) -> tuple[list[dict], list[str]]:
    if not content:
        raise HTTPException(status_code=422, detail="The CSV file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"CSV files must be smaller than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Use a UTF-8 encoded CSV file.") from exc

    reader = csv.DictReader(io.StringIO(text))
    headers = [header.strip().lower() for header in (reader.fieldnames or []) if header]
    if not headers:
        raise HTTPException(status_code=422, detail="The CSV needs a header row.")
    if len(headers) != len(set(headers)):
        raise HTTPException(status_code=422, detail="Column names must be unique.")
    missing = sorted(REQUIRED_COLUMNS - set(headers))
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required columns: {', '.join(missing)}.")

    rows = []
    errors = []
    for row_number, raw in enumerate(reader, start=2):
        if row_number > MAX_UPLOAD_ROWS + 1:
            raise HTTPException(status_code=413, detail=f"CSV files may contain at most {MAX_UPLOAD_ROWS:,} rows.")
        values = {key.strip().lower(): (value or "").strip() for key, value in raw.items() if key}
        try:
            required_values = [values.get(name, "") for name in REQUIRED_COLUMNS]
            if any(not value for value in required_values):
                raise ValueError("required fields cannot be blank")
            order_date = date.fromisoformat(values["order_date"])
            quantity_decimal = Decimal(values["quantity"])
            price = Decimal(values["unit_price"])
            revenue = Decimal(values["revenue"]) if values.get("revenue") else quantity_decimal * price
            if not all(value.is_finite() for value in (quantity_decimal, price, revenue)):
                raise ValueError("numeric fields must contain finite values")
            if quantity_decimal != quantity_decimal.to_integral_value() or quantity_decimal <= 0:
                raise ValueError("quantity must be a positive whole number")
            if price < 0 or revenue < 0:
                raise ValueError("unit_price and revenue cannot be negative")
            rows.append({
                "order_id": values["order_id"], "order_date": order_date,
                "customer_id": values["customer_id"], "product": values["product"],
                "category": values["category"], "region": values["region"],
                "quantity": int(quantity_decimal), "unit_price": float(price), "revenue": float(revenue),
            })
        except (KeyError, InvalidOperation, ValueError) as exc:
            errors.append(f"Row {row_number}: {exc if str(exc) else 'invalid date or numeric value'}")
            if len(errors) == 20:
                break
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Some rows could not be imported.", "errors": errors})
    if not rows:
        raise HTTPException(status_code=422, detail="The CSV has a header but no sales rows.")
    return rows, []