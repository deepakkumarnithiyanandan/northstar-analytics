import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


CSV = b"order_id,order_date,customer_id,product,category,region,quantity,unit_price,revenue\n"
CSV += b"o-1,2025-01-03,c-1,Desk,Office,West,2,10,20\n"
CSV += b"o-1,2025-01-03,c-1,Chair,Office,West,1,30,30\n"
CSV += b"o-2,2025-02-03,c-2,Lamp,Lighting,East,1,50,50\n"


def test_upload_dashboard_and_filtered_sales(client):
    response = client.post("/api/upload", files={"file": ("sales.csv", CSV, "text/csv")})
    assert response.status_code == 201
    dataset_id = response.json()["dataset"]["id"]

    dashboard = client.get("/api/dashboard", params={"dataset_id": dataset_id}).json()
    assert dashboard["kpis"]["total_revenue"] == 100
    assert dashboard["kpis"]["total_orders"] == 2
    assert dashboard["kpis"]["average_order_value"] == 50
    assert dashboard["kpis"]["total_customers"] == 2
    assert len(dashboard["revenue_over_time"]) == 2

    sales = client.get("/api/sales", params={"dataset_id": dataset_id, "region": "East"}).json()
    assert sales["total"] == 1
    assert sales["items"][0]["product"] == "Lamp"


def test_upload_rejects_missing_columns_and_bad_values(client):
    missing = client.post("/api/upload", files={"file": ("bad.csv", b"order_id,product\no-1,Desk\n", "text/csv")})
    assert missing.status_code == 422
    assert "Missing required columns" in missing.json()["detail"]

    invalid = CSV.replace(b"2025-01-03", b"not-a-date", 1)
    response = client.post("/api/upload", files={"file": ("bad.csv", invalid, "text/csv")})
    assert response.status_code == 422
    assert "Row 2" in response.json()["detail"]["errors"][0]
    assert client.get("/api/datasets").json() == []


def test_ask_returns_computed_metrics_and_recommended_chart(client):
    upload = client.post("/api/upload", files={"file": ("sales.csv", CSV, "text/csv")})
    dataset_id = upload.json()["dataset"]["id"]
    response = client.post("/api/ask", params={"dataset_id": dataset_id}, json={"question": "What are the top products by revenue?"})

    assert response.status_code == 200
    result = response.json()
    assert result["intent"] == "top_products"
    assert result["visualization"]["type"] == "bar"
    assert result["visualization"]["data"][0]["label"] == "Lamp"
    assert result["query_id"] == 1


def test_ask_compares_regional_monthly_growth_not_total_revenue(client):
    regional_csv = b"order_id,order_date,customer_id,product,category,region,quantity,unit_price,revenue\n"
    regional_csv += b"jan-west,2025-01-05,c-1,Desk,Office,West,1,100,100\n"
    regional_csv += b"jan-east,2025-01-06,c-2,Lamp,Lighting,East,1,100,100\n"
    regional_csv += b"feb-west,2025-02-05,c-1,Desk,Office,West,1,150,150\n"
    regional_csv += b"feb-east,2025-02-06,c-2,Lamp,Lighting,East,1,50,50\n"
    uploaded = client.post("/api/upload", files={"file": ("regional.csv", regional_csv, "text/csv")})
    dataset_id = uploaded.json()["dataset"]["id"]

    fastest = client.post("/api/ask", params={"dataset_id": dataset_id}, json={"question": "Which region grew fastest?"}).json()
    biggest_decline = client.post("/api/ask", params={"dataset_id": dataset_id}, json={"question": "Which region had the biggest revenue decline?"}).json()

    assert fastest["intent"] == "regional_growth"
    assert "West" in fastest["answer"] and "+50.0%" in fastest["answer"]
    assert biggest_decline["intent"] == "regional_decline"
    assert "East" in biggest_decline["answer"] and "-50.0%" in biggest_decline["answer"]


def test_dashboard_requires_a_dataset(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 404


def test_bundled_sample_dataset_loads(client):
    response = client.post("/api/demo")
    assert response.status_code == 201
    assert response.json()["row_count"] == 1200

    dashboard = client.get("/api/dashboard", params={"dataset_id": response.json()["id"]}).json()
    assert dashboard["kpis"]["total_orders"] == 1200
    assert dashboard["revenue_over_time"]