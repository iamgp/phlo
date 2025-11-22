# app.py - Flask dashboard hub for the Cascade Lakehouse platform
# Provides a web interface displaying all services, ports, and credentials
# in the data platform for easy navigation and monitoring

import os

from flask import Flask, render_template_string

app = Flask(__name__)

# HTML dashboard template embedded as string for simplicity
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cascade Lakehouse Hub</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 40px;
            font-size: 1.1em;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            color: white;
            font-size: 1.3em;
            margin-bottom: 15px;
            padding-left: 5px;
            border-left: 4px solid rgba(255,255,255,0.5);
        }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }
        .service-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        .service-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        .service-card.disabled {
            pointer-events: none;
            opacity: 0.6;
        }
        .service-card h2 {
            color: #667eea;
            margin-bottom: 8px;
            font-size: 1.5em;
        }
        .service-card p {
            color: #666;
            margin-bottom: 12px;
            line-height: 1.5;
        }
        .service-card .port {
            display: inline-block;
            background: #f0f0f0;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            color: #555;
            font-family: monospace;
        }
        .credentials {
            margin-top: 12px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            font-size: 0.85em;
            font-family: monospace;
        }
        .credentials div {
            margin: 4px 0;
            color: #555;
        }
        .status {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            margin-right: 8px;
        }
        .badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            margin-left: 8px;
            vertical-align: middle;
        }
        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Cascade Lakehouse Hub</h1>
        <div class="subtitle">Apache Iceberg + Nessie + Trino Architecture</div>

        <div class="section">
            <h3 class="section-title">Orchestration & Pipeline</h3>
            <div class="services-grid">
                <a href="http://localhost:{{ dagster_port }}" class="service-card" target="_blank">
                    <h2><span class="status"></span>Dagster</h2>
                    <p>Data pipeline orchestration with asset-based lineage and scheduling</p>
                    <span class="port">Port {{ dagster_port }}</span>
                </a>
            </div>
        </div>

        <div class="section">
            <h3 class="section-title">Query Engine & Catalog</h3>
            <div class="services-grid">
                <a href="http://localhost:{{ trino_port }}" class="service-card" target="_blank">
                    <h2><span class="status"></span>Trino</h2>
                    <p>Distributed SQL query engine for Iceberg tables and transformations</p>
                    <span class="port">Port {{ trino_port }}</span>
                </a>

                <a href="http://localhost:{{ nessie_port }}/api/v1" class="service-card" target="_blank">
                    <h2><span class="status"></span>Nessie</h2>
                    <p>Git-like catalog for Apache Iceberg with branching and versioning</p>
                    <span class="port">Port {{ nessie_port }}</span>
                </a>

                <a href="http://localhost:{{ minio_console_port }}" class="service-card" target="_blank">
                    <h2><span class="status"></span>MinIO Console</h2>
                    <p>S3-compatible object storage for Iceberg data files</p>
                    <span class="port">Port {{ minio_console_port }}</span>
                    <div class="credentials">
                        <div>User: {{ minio_user }}</div>
                        <div>Pass: {{ minio_pass }}</div>
                    </div>
                </a>

                <a href="http://localhost:{{ pgweb_port }}" class="service-card" target="_blank">
                    <h2><span class="status"></span>PGWeb</h2>
                    <p>Web-based PostgreSQL browser for marts and metadata</p>
                    <span class="port">Port {{ pgweb_port }}</span>
                </a>

                <a class="service-card disabled">
                    <h2><span class="status"></span>PostgreSQL</h2>
                    <p>Database for Nessie metadata and analytics marts</p>
                    <span class="port">Port {{ postgres_port }}</span>
                    <div class="credentials">
                        <div>User: {{ postgres_user }}</div>
                        <div>Pass: {{ postgres_pass }}</div>
                        <div>DB: {{ postgres_db }}</div>
                    </div>
                </a>
            </div>
        </div>

        <div class="section">
            <h3 class="section-title">API Layer</h3>
            <div class="services-grid">
                <a href="http://localhost:{{ api_port }}/docs" class="service-card" target="_blank">
                    <h2><span class="status"></span>FastAPI</h2>
                    <p>REST API for glucose analytics and Iceberg data access</p>
                    <span class="port">Port {{ api_port }}</span>
                    <div class="credentials">
                        <div>Admin: admin / admin123</div>
                        <div>Analyst: analyst / analyst123</div>
                    </div>
                </a>

                <a href="http://localhost:{{ hasura_port }}/console" class="service-card" target="_blank">
                    <h2><span class="status"></span>Hasura GraphQL</h2>
                    <p>Auto-generated GraphQL API from Postgres marts with real-time subscriptions</p>
                    <span class="port">Port {{ hasura_port }}</span>
                    <div class="credentials">
                        <div>Use JWT tokens from FastAPI</div>
                    </div>
                </a>
            </div>
        </div>

        <div class="section">
            <h3 class="section-title">Analytics & Visualization</h3>
            <div class="services-grid">
                <a href="http://localhost:{{ superset_port }}" class="service-card" target="_blank">
                    <h2><span class="status"></span>Superset</h2>
                    <p>Business intelligence dashboards and data exploration</p>
                    <span class="port">Port {{ superset_port }}</span>
                    <div class="credentials">
                        <div>User: {{ superset_user }}</div>
                        <div>Pass: {{ superset_pass }}</div>
                    </div>
                </a>

                <a href="http://localhost:{{ grafana_port }}" class="service-card" target="_blank">
                    <h2><span class="status"></span>Grafana</h2>
                    <p>Observability dashboards with metrics and logs visualization</p>
                    <span class="port">Port {{ grafana_port }}</span>
                    <div class="credentials">
                        <div>User: admin</div>
                        <div>Pass: admin</div>
                    </div>
                </a>
            </div>
        </div>

        <div class="section">
            <h3 class="section-title">Monitoring</h3>
            <div class="services-grid">
                <a href="http://localhost:{{ prometheus_port }}" class="service-card" target="_blank">
                    <h2><span class="status"></span>Prometheus</h2>
                    <p>Metrics collection and time-series database for service monitoring</p>
                    <span class="port">Port {{ prometheus_port }}</span>
                </a>
            </div>
        </div>

        <div class="footer">
            <p>Cascade Lakehouse Platform - Iceberg + Nessie + Trino</p>
            <p style="font-size: 0.9em; margin-top: 8px; opacity: 0.7;">
                Quick Start: make up-all &nbsp;|&nbsp; Docs: /docs &nbsp;|&nbsp; GitHub: /phlo
            </p>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
    HTML_TEMPLATE,
    dagster_port=os.getenv("DAGSTER_PORT", "10006"),
    trino_port=os.getenv("TRINO_PORT", "10005"),
    nessie_port=os.getenv("NESSIE_PORT", "10003"),
    minio_console_port=os.getenv("MINIO_CONSOLE_PORT", "10002"),
    minio_user=os.getenv("MINIO_ROOT_USER", "minio"),
    minio_pass=os.getenv("MINIO_ROOT_PASSWORD", "minio999"),
    pgweb_port=os.getenv("PGWEB_PORT", "10008"),
    postgres_port=os.getenv("POSTGRES_PORT", "10000"),
    postgres_user=os.getenv("POSTGRES_USER", "lake"),
    postgres_pass=os.getenv("POSTGRES_PASSWORD", "lakepass"),
    postgres_db=os.getenv("POSTGRES_DB", "lakehouse"),
    api_port=os.getenv("API_PORT", "10010"),
    hasura_port=os.getenv("HASURA_PORT", "10011"),
    superset_port=os.getenv("SUPERSET_PORT", "10007"),
    superset_user=os.getenv("SUPERSET_ADMIN_USER", "admin"),
    superset_pass=os.getenv("SUPERSET_ADMIN_PASSWORD", "admin123"),
    grafana_port=os.getenv("GRAFANA_PORT", "10016"),
    prometheus_port=os.getenv("PROMETHEUS_PORT", "10013"),
    )


if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", "10009"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
