"""
REST API Ingestion Template

This template shows how to create a Phlo ingestion asset for REST API data sources.

TODO: Customize this template:
1. Copy this file to src/phlo/defs/ingestion/YOUR_DOMAIN/YOUR_ASSET.py
2. Update the schema import to match your schema file
3. Configure the @phlo_ingestion decorator parameters
4. Configure the DLT rest_api source
5. Register domain in src/phlo/defs/ingestion/__init__.py
"""

from dlt.sources.rest_api import rest_api
from phlo.ingestion import phlo_ingestion
from phlo.schemas.example import RawExampleData

# TODO: Update this import to match your schema file
# Example: from phlo.schemas.weather import RawWeatherObservations


@phlo_ingestion(
    # TODO: Set the Iceberg table name (will be created in 'raw' schema)
    # Example: "weather_observations", "stripe_payments", "github_events"
    table_name="example_data",
    # TODO: Set the unique key field (must exist in your Pandera schema)
    # This field is used for deduplication - usually an ID or composite key
    # Example: "id", "transaction_id", "event_id"
    unique_key="id",
    # TODO: Set your Pandera schema for validation
    # This schema validates data BEFORE writing to Iceberg
    # Iceberg schema is AUTO-GENERATED from this Pandera schema
    validation_schema=RawExampleData,
    # TODO: Set the asset group (usually your domain name)
    # Groups help organize assets in Dagster UI
    # Example: "weather", "stripe", "github", "salesforce"
    group="example",
    # TODO: Set the cron schedule (when to run this ingestion)
    # Format: "minute hour day_of_month month day_of_week"
    # Examples:
    #   "0 */1 * * *"   - Every hour
    #   "*/15 * * * *"  - Every 15 minutes
    #   "0 0 * * *"     - Daily at midnight
    #   "0 9 * * MON"   - Every Monday at 9am
    # Test your cron: https://crontab.guru
    cron="0 */1 * * *",
    # TODO: Set freshness policy (warn_hours, fail_hours)
    # Example: (1, 24) means warn if data is >1 hour old, fail if >24 hours
    # Set based on your data update frequency
    freshness_hours=(1, 24),
    # Optional parameters (uncomment to use):
    # max_runtime_seconds=300,  # Timeout (default: 300)
    # max_retries=3,  # Retry attempts (default: 3)
    # retry_delay_seconds=30,  # Delay between retries (default: 30)
)
def example_data_ingestion(partition_date: str):
    """
    Ingest example data from REST API.

    TODO: Update this docstring to describe what this asset does.
    Example:
    \"\"\"
    Ingest weather observations from OpenWeather API.

    Fetches hourly weather data including temperature, humidity, and pressure
    for specified cities.

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Returns:
        DLT resource containing weather observations for the partition date
    \"\"\"

    Args:
        partition_date: Date partition in YYYY-MM-DD format (e.g., "2024-01-15")
                        Automatically provided by Dagster partitioning

    Returns:
        DLT source/resource containing the data to ingest
    """

    # TODO: Configure time range for partition
    # Most APIs use ISO 8601 format: YYYY-MM-DDTHH:MM:SS.SSSZ
    start_time = f"{partition_date}T00:00:00.000Z"
    end_time = f"{partition_date}T23:59:59.999Z"

    # TODO: Configure the DLT rest_api source
    # Documentation: https://dlthub.com/docs/dlt-ecosystem/verified-sources/rest_api
    source = rest_api(
        {
            "client": {
                # TODO: Set your API base URL
                # Example: "https://api.openweathermap.org/data/3.0"
                "base_url": "https://api.example.com/v1",
                # TODO: Configure authentication (uncomment one):
                # Option 1: Bearer token
                # "auth": {
                #     "token": os.getenv("YOUR_API_TOKEN"),  # Store in .env file
                # },
                # Option 2: API key in header
                # "headers": {
                #     "X-API-Key": os.getenv("YOUR_API_KEY"),
                # },
                # Option 3: Basic auth
                # "auth": {
                #     "type": "basic",
                #     "username": os.getenv("API_USERNAME"),
                #     "password": os.getenv("API_PASSWORD"),
                # },
                # Option 4: OAuth2 (more complex - see DLT docs)
                # "auth": {
                #     "type": "oauth2",
                #     "client_id": os.getenv("OAUTH_CLIENT_ID"),
                #     "client_secret": os.getenv("OAUTH_CLIENT_SECRET"),
                #     "token_url": "https://api.example.com/oauth/token",
                # },
            },
            # TODO: Configure resources (API endpoints to fetch)
            "resources": [
                {
                    # TODO: Set resource name (becomes table name in DLT staging)
                    # Example: "observations", "transactions", "events"
                    "name": "data",
                    "endpoint": {
                        # TODO: Set API endpoint path
                        # Example: "weather/observations", "charges", "events"
                        "path": "data",
                        # TODO: Configure query parameters
                        # These are added to the URL: /data?param1=value1&param2=value2
                        "params": {
                            # Date range parameters
                            "start_date": start_time,
                            "end_date": end_time,
                            # TODO: Add other parameters your API needs
                            # Examples:
                            # "limit": 1000,
                            # "offset": 0,
                            # "city": "London",
                            # "status": "active",
                        },
                    },
                    # TODO: Configure pagination if API supports it
                    # Uncomment and configure based on API pagination style:
                    # Style 1: Offset-based pagination
                    # "paginator": {
                    #     "type": "offset",
                    #     "limit": 1000,
                    #     "offset_param": "offset",
                    #     "limit_param": "limit",
                    #     "total_path": "response.total",  # JSON path to total count
                    # },
                    # Style 2: Page-based pagination
                    # "paginator": {
                    #     "type": "page_number",
                    #     "page_size": 100,
                    #     "page_param": "page",
                    #     "page_size_param": "per_page",
                    # },
                    # Style 3: Cursor-based pagination
                    # "paginator": {
                    #     "type": "cursor",
                    #     "cursor_path": "response.next_cursor",
                    #     "cursor_param": "cursor",
                    # },
                    # TODO: Configure data path if response is nested
                    # "data_selector": "response.data",  # Path to array in JSON response
                },
                # TODO: If you need multiple endpoints, add more resources:
                # {
                #     "name": "other_data",
                #     "endpoint": {
                #         "path": "other",
                #         "params": {...},
                #     },
                # },
            ],
        }
    )

    return source


# Example: Weather API Ingestion
# ==============================
#
# @phlo_ingestion(
#     table_name="weather_observations",
#     unique_key="observation_id",
#     validation_schema=RawWeatherData,
#     group="weather",
#     cron="0 */1 * * *",
#     freshness_hours=(2, 24),
# )
# def weather_observations(partition_date: str):
#     \"\"\"Ingest hourly weather observations.\"\"\"
#
#     source = rest_api({
#         "client": {
#             "base_url": "https://api.openweathermap.org/data/3.0",
#             "auth": {"token": os.getenv("OPENWEATHER_API_KEY")},
#         },
#         "resources": [{
#             "name": "observations",
#             "endpoint": {
#                 "path": "onecall/timemachine",
#                 "params": {
#                     "lat": "51.5074",
#                     "lon": "-0.1278",
#                     "dt": partition_date,
#                 },
#             },
#         }],
#     })
#
#     return source


# Example: Stripe Payments Ingestion
# ===================================
#
# @phlo_ingestion(
#     table_name="stripe_charges",
#     unique_key="id",
#     validation_schema=RawStripeCharges,
#     group="stripe",
#     cron="*/15 * * * *",
#     freshness_hours=(1, 6),
# )
# def stripe_charges(partition_date: str):
#     \"\"\"Ingest Stripe payment charges.\"\"\"
#
#     # Stripe uses Unix timestamps
#     import time
#     from datetime import datetime
#
#     date_obj = datetime.strptime(partition_date, "%Y-%m-%d")
#     start_timestamp = int(date_obj.timestamp())
#     end_timestamp = start_timestamp + 86400  # +24 hours
#
#     source = rest_api({
#         "client": {
#             "base_url": "https://api.stripe.com/v1",
#             "auth": {
#                 "type": "basic",
#                 "username": os.getenv("STRIPE_API_KEY"),
#                 "password": "",  # Stripe uses key as username, blank password
#             },
#         },
#         "resources": [{
#             "name": "charges",
#             "endpoint": {
#                 "path": "charges",
#                 "params": {
#                     "created[gte]": start_timestamp,
#                     "created[lt]": end_timestamp,
#                     "limit": 100,
#                 },
#             },
#             "paginator": {
#                 "type": "cursor",
#                 "cursor_path": "next_page",
#                 "cursor_param": "starting_after",
#             },
#         }],
#     })
#
#     return source


# Next Steps:
# ===========
#
# 1. Copy this template to your domain directory:
#    cp templates/ingestion/rest_api.py src/phlo/defs/ingestion/YOUR_DOMAIN/YOUR_ASSET.py
#
# 2. Create corresponding schema:
#    cp templates/schemas/example_schema.py src/phlo/schemas/YOUR_DOMAIN.py
#
# 3. Edit both files and replace all TODOs
#
# 4. Register domain in src/phlo/defs/ingestion/__init__.py:
#    from phlo.defs.ingestion import YOUR_DOMAIN  # noqa: F401
#
# 5. Restart Dagster:
#    docker restart dagster-webserver
#
# 6. Test in Dagster UI:
#    http://localhost:3000 → Assets → YOUR_ASSET → Materialize
#
# 7. Check data in Trino:
#    docker exec -it trino trino --catalog iceberg_dev --schema raw
#    SELECT * FROM YOUR_TABLE LIMIT 10;
