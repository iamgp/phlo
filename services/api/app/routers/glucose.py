# glucose.py - FastAPI router for glucose analytics endpoints
# Provides REST API access to diabetes glucose data from PostgreSQL marts
# with caching, authentication, and query optimization

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query

from app.auth.dependencies import CurrentUser
from app.config import settings
from app.connectors.postgres import postgres_connector
from app.middleware.cache import cached

# --- Router Configuration ---
# API router for glucose-related endpoints
router = APIRouter(prefix="/glucose", tags=["Glucose Analytics"])


# --- Glucose Analytics Endpoints ---
# REST API endpoints for diabetes data analysis
@router.get("/readings", summary="Get glucose readings")
@cached(ttl=settings.cache_glucose_readings_ttl)
async def get_glucose_readings(
    current_user: CurrentUser,
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, le=10000, description="Maximum number of readings"),
) -> dict[str, Any]:
    """
    Get glucose readings from the marts layer.

    Cached for 1 hour. Queries the Postgres marts for fast access.
    """
    readings = postgres_connector.get_glucose_readings(
        start_date=start_date, end_date=end_date, limit=limit
    )

    return {
        "data": readings,
        "count": len(readings),
        "source": "postgres_marts",
        "cached": True,
    }


@router.get("/daily-summary", summary="Get daily glucose summary")
@cached(ttl=settings.cache_glucose_readings_ttl)
async def get_daily_summary(
    current_user: CurrentUser,
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
):
    """
    Get glucose summary for a specific day.

    Cached for 1 hour. Fast query from Postgres marts.
    """
    readings = postgres_connector.get_glucose_readings(
        start_date=date, end_date=date, limit=1
    )

    if not readings:
        return {
            "date": datetime.strptime(date, "%Y-%m-%d").date().isoformat(),
            "avg_glucose": None,
            "min_glucose": None,
            "max_glucose": None,
            "readings_count": 0,
        }

    reading = readings[0]
    return {
        "date": reading.get("date"),
        "avg_glucose": reading.get("avg_glucose"),
        "min_glucose": reading.get("min_glucose"),
        "max_glucose": reading.get("max_glucose"),
        "readings_count": reading.get("readings_count"),
        "time_in_range_percent": reading.get("time_in_range_percent"),
    }


@router.get("/hourly-patterns", summary="Get hourly patterns")
@cached(ttl=settings.cache_hourly_patterns_ttl)
async def get_hourly_patterns(
    current_user: CurrentUser,
):
    """
    Get hourly glucose patterns across all data.

    Cached for 6 hours (slow-changing aggregates). Queries Postgres marts.
    """
    patterns = postgres_connector.get_hourly_patterns()

    return [
        {
            "hour_of_day": p["hour_of_day"],
            "avg_glucose": p.get("avg_glucose"),
            "readings_count": p.get("readings_count"),
        }
        for p in patterns
    ]


@router.get("/statistics", summary="Get glucose statistics")
@cached(ttl=settings.cache_glucose_readings_ttl)
async def get_statistics(
    current_user: CurrentUser,
    period: str = Query("7d", regex="^(7d|30d|90d)$", description="Time period: 7d, 30d, or 90d"),
) -> dict[str, Any]:
    """
    Get glucose statistics for a time period.

    Cached for 1 hour. Aggregates from Postgres marts.
    """
    # Calculate date range
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map[period]
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    readings = postgres_connector.get_glucose_readings(
        start_date=str(start_date), end_date=str(end_date), limit=10000
    )

    if not readings:
        return {
            "period": period,
            "days": days,
            "readings_count": 0,
            "statistics": None,
        }

    # Calculate statistics
    glucose_values = [r["avg_glucose"] for r in readings if r.get("avg_glucose")]

    if not glucose_values:
        return {
            "period": period,
            "days": days,
            "readings_count": len(readings),
            "statistics": None,
        }

    return {
        "period": period,
        "days": days,
        "readings_count": len(readings),
        "statistics": {
            "avg_glucose": sum(glucose_values) / len(glucose_values),
            "min_glucose": min(glucose_values),
            "max_glucose": max(glucose_values),
        },
    }
