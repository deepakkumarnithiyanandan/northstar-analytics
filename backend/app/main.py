import logging
import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.service import build_result, classify, enrich_answer
from app.config import MAX_UPLOAD_BYTES
from app.database import Base, engine, get_db
from app.models import AIQuery, Customer, Dataset, Product, Sale
from app.schemas import AskIn, AskOut, DashboardOut, DatasetOut, KPIOut, OptionsOut, SalesPage, UploadOut
from app.services.analytics import latest_dataset, sales_for_dataset, summarize
from app.services.csv_import import parse_sales_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Northstar Analytics API", version="1.0.0", description="Dataset-scoped sales analytics and safe natural-language queries.", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
def database_error_handler(_request, exc):
    logger.error("Database operation failed: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "The database is unavailable. Check the database connection and try again."})


def store_rows(db: Session, name: str, rows: list[dict]) -> Dataset:
    dataset = Dataset(name=name, row_count=len(rows))
    db.add(dataset)
    db.flush()
    products = {}
    customers = {}
    for row in rows:
        product_key = (row["product"], row["category"])
        if product_key not in products:
            item = Product(dataset_id=dataset.id, name=row["product"], category=row["category"])
            db.add(item)
            db.flush()
            products[product_key] = item.id
        if row["customer_id"] not in customers:
            customer = Customer(dataset_id=dataset.id, external_id=row["customer_id"])
            db.add(customer)
            db.flush()
            customers[row["customer_id"]] = customer.id
        db.add(Sale(
            dataset_id=dataset.id, order_id=row["order_id"], order_date=row["order_date"],
            customer_id=customers[row["customer_id"]], product_id=products[product_key],
            region=row["region"], quantity=row["quantity"], unit_price=row["unit_price"], revenue=row["revenue"],
        ))
    return dataset


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/datasets", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.uploaded_at.desc(), Dataset.id.desc()).all()


@app.post("/api/upload", response_model=UploadOut, status_code=201)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or Path(file.filename).suffix.casefold() != ".csv":
        raise HTTPException(status_code=415, detail="Upload a .csv file.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    rows, warnings = parse_sales_csv(content)
    dataset = store_rows(db, Path(file.filename).name, rows)
    db.commit()
    db.refresh(dataset)
    logger.info("Imported dataset %s with %s sales rows", dataset.id, dataset.row_count)
    return {"dataset": dataset, "warnings": warnings}


@app.post("/api/demo", response_model=DatasetOut, status_code=201)
def load_demo(db: Session = Depends(get_db)):
    sample_path = Path(__file__).resolve().parent.parent / "data" / "sample_sales.csv"
    if not sample_path.exists():
        raise HTTPException(status_code=503, detail="The bundled sample dataset is missing.")
    rows, _ = parse_sales_csv(sample_path.read_bytes())
    dataset = store_rows(db, "sample_sales.csv", rows)
    db.commit()
    db.refresh(dataset)
    return dataset


def validate_filters(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date.")


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(dataset_id: int | None = None, start_date: date | None = None,
              end_date: date | None = None, region: str | None = None,
              category: str | None = None, product: str | None = None, db: Session = Depends(get_db)):
    validate_filters(start_date, end_date)
    dataset = latest_dataset(db, dataset_id)
    rows = sales_for_dataset(db, dataset.id, start_date, end_date, region, category, product).all()
    summary = summarize(rows)
    return {
        "dataset": dataset,
        "kpis": {key: summary[key] for key in ("total_revenue", "total_orders", "average_order_value", "total_customers", "revenue_growth")},
        **{key: value for key, value in summary.items() if key not in ("total_revenue", "total_orders", "average_order_value", "total_customers", "revenue_growth")},
    }


@app.get("/api/kpis", response_model=KPIOut)
def kpis(dataset_id: int | None = None, start_date: date | None = None,
         end_date: date | None = None, region: str | None = None,
         category: str | None = None, product: str | None = None, db: Session = Depends(get_db)):
    validate_filters(start_date, end_date)
    dataset = latest_dataset(db, dataset_id)
    summary = summarize(sales_for_dataset(db, dataset.id, start_date, end_date, region, category, product).all())
    return {key: summary[key] for key in ("total_revenue", "total_orders", "average_order_value", "total_customers", "revenue_growth")}


@app.get("/api/sales", response_model=SalesPage)
def sales(dataset_id: int | None = None, start_date: date | None = None,
          end_date: date | None = None, region: str | None = None,
          category: str | None = None, product: str | None = None,
          limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    validate_filters(start_date, end_date)
    dataset = latest_dataset(db, dataset_id)
    query = sales_for_dataset(db, dataset.id, start_date, end_date, region, category, product)
    total = query.count()
    records = query.offset(offset).limit(limit).all()
    items = [{"id": sale.id, "order_id": sale.order_id, "order_date": sale.order_date,
              "customer_id": customer.external_id, "product": item.name, "category": item.category,
              "region": sale.region, "quantity": sale.quantity, "unit_price": sale.unit_price,
              "revenue": sale.revenue} for sale, item, customer in records]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/api/products", response_model=OptionsOut)
def products(dataset_id: int | None = None, db: Session = Depends(get_db)):
    dataset = latest_dataset(db, dataset_id)
    return {"items": [name for (name,) in db.query(Product.name).filter(Product.dataset_id == dataset.id).distinct().order_by(Product.name).all()]}


@app.get("/api/regions", response_model=OptionsOut)
def regions(dataset_id: int | None = None, db: Session = Depends(get_db)):
    dataset = latest_dataset(db, dataset_id)
    return {"items": [name for (name,) in db.query(Sale.region).filter(Sale.dataset_id == dataset.id).distinct().order_by(Sale.region).all()]}


@app.get("/api/categories", response_model=OptionsOut)
def categories(dataset_id: int | None = None, db: Session = Depends(get_db)):
    dataset = latest_dataset(db, dataset_id)
    return {"items": [name for (name,) in db.query(Product.category).filter(Product.dataset_id == dataset.id).distinct().order_by(Product.category).all()]}


@app.post("/api/ask", response_model=AskOut)
async def ask(payload: AskIn, dataset_id: int | None = None, db: Session = Depends(get_db)):
    question = payload.question.strip()
    if not question or len(question) > 1000:
        raise HTTPException(status_code=422, detail="Question must contain 1 to 1,000 characters.")
    dataset = latest_dataset(db, dataset_id)
    summary = summarize(sales_for_dataset(db, dataset.id).all())
    intent = classify(question)
    answer, metrics, visualization = build_result(intent, summary)
    answer = await enrich_answer(question, answer, metrics)
    record = AIQuery(dataset_id=dataset.id, question=question, intent=intent.value, answer=answer)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"answer": answer, "intent": intent.value, "metrics": metrics,
            "visualization": visualization, "query_id": record.id}