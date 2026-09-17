from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset
from app.services import analytics_service
from app.services.dataset_service import load_cleaned_dataframe

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _get_filtered_df(dataset_id: int, db: Session, product_id: str | None, region: str | None, category: str | None):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    df = load_cleaned_dataframe(dataset)
    if product_id:
        df = df.loc[df["product_id"] == product_id]
    if region and "region" in df.columns:
        df = df.loc[df["region"] == region]
    if category and "category" in df.columns:
        df = df.loc[df["category"] == category]
    if df.empty:
        raise HTTPException(status_code=404, detail="No data matches the selected filters.")
    return df


@router.get("/summary")
def analytics_summary(
    dataset_id: int,
    product_id: str | None = None,
    region: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    df = _get_filtered_df(dataset_id, db, product_id, region, category)
    return analytics_service.summary_kpis(df)


@router.get("/trends")
def analytics_trends(
    dataset_id: int,
    freq: str = Query("D", pattern="^(D|W|M)$"),
    product_id: str | None = None,
    region: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    df = _get_filtered_df(dataset_id, db, product_id, region, category)
    return {"trend": analytics_service.revenue_trend(df, freq=freq)}


@router.get("/top-products")
def analytics_top_products(dataset_id: int, limit: int = 10, region: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    df = _get_filtered_df(dataset_id, db, None, region, category)
    return {"top_products": analytics_service.top_products(df, n=limit)}


@router.get("/regions")
def analytics_regions(dataset_id: int, db: Session = Depends(get_db)):
    df = _get_filtered_df(dataset_id, db, None, None, None)
    return {"regions": analytics_service.regional_performance(df)}


@router.get("/categories")
def analytics_categories(dataset_id: int, db: Session = Depends(get_db)):
    df = _get_filtered_df(dataset_id, db, None, None, None)
    return {"categories": analytics_service.category_performance(df)}


@router.get("/filters")
def analytics_filters(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    df = load_cleaned_dataframe(dataset)
    return {
        "products": analytics_service.list_products(df),
        "regions": analytics_service.list_regions(df),
        "categories": sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else [],
    }
