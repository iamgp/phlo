# superset_config.py - Apache Superset configuration for Phlo dashboard
# Configures Superset settings for the lakehouse BI platform
# including database connections, security, and feature flags

import os

# --- Superset Configuration ---
# Core Superset settings for the BI dashboard platform
ROW_LIMIT = 5000

# --- Database Configuration ---
# Flask App Builder configuration
# Use SQLite for metadata, PostgreSQL for data connections
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

# --- Security Configuration ---
# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY", "")

# Allow embedding dashboards in iframes
HTTP_HEADERS = {"X-Frame-Options": "SAMEORIGIN"}

# --- Feature Flags ---
# Enable feature flags
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# --- Authentication Configuration ---
# Disable signup
AUTH_USER_REGISTRATION = False
