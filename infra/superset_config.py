import os

# Superset specific config
ROW_LIMIT = 5000

# Flask App Builder configuration
# Use SQLite for metadata, PostgreSQL for data connections
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY", "")

# Allow embedding dashboards in iframes
HTTP_HEADERS = {"X-Frame-Options": "SAMEORIGIN"}

# Enable feature flags
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# Disable signup
AUTH_USER_REGISTRATION = False
