import os

from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lakehouse Services Hub</title>
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
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
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
        <h1>Data Lakehouse Services Hub</h1>
        <div class="services-grid">
            <a href="http://localhost:{{ dagster_port }}" class="service-card" target="_blank">
                <h2><span class="status"></span>Dagster</h2>
                <p>Orchestration platform for data pipelines, asset management, and scheduling</p>
                <span class="port">Port {{ dagster_port }}</span>
            </a>

            <a href="http://localhost:{{ superset_port }}" class="service-card" target="_blank">
                <h2><span class="status"></span>Superset</h2>
                <p>Business intelligence and data visualization dashboards</p>
                <span class="port">Port {{ superset_port }}</span>
                <div class="credentials">
                    <div>User: {{ superset_user }}</div>
                    <div>Pass: {{ superset_pass }}</div>
                </div>
            </a>

            <a href="http://localhost:{{ minio_console_port }}" class="service-card" target="_blank">
                <h2><span class="status"></span>MinIO Console</h2>
                <p>Object storage browser for data lake files (S3-compatible)</p>
                <span class="port">Port {{ minio_console_port }}</span>
                <div class="credentials">
                    <div>User: {{ minio_user }}</div>
                    <div>Pass: {{ minio_pass }}</div>
                </div>
            </a>

            <a href="http://localhost:{{ datahub_port }}" class="service-card" target="_blank">
                <h2><span class="status"></span>DataHub</h2>
                <p>Metadata catalog and data lineage tracking</p>
                <span class="port">Port {{ datahub_port }}</span>
            </a>

            <a href="http://localhost:{{ airbyte_port }}" class="service-card" target="_blank">
                <h2><span class="status"></span>Airbyte</h2>
                <p>Data ingestion and ELT connector platform</p>
                <span class="port">Port {{ airbyte_port }}</span>
            </a>

            <a href="http://localhost:{{ postgres_port }}" class="service-card" style="pointer-events: none; opacity: 0.7;">
                <h2><span class="status"></span>PostgreSQL</h2>
                <p>Database for metadata and analytics marts</p>
                <span class="port">Port {{ postgres_port }}</span>
                <div class="credentials">
                    <div>User: {{ postgres_user }}</div>
                    <div>Pass: {{ postgres_pass }}</div>
                    <div>DB: {{ postgres_db }}</div>
                </div>
            </a>
        </div>
        <div class="footer">
            <p>Data Lakehouse Platform</p>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        dagster_port=os.getenv("DAGSTER_PORT", "3000"),
        superset_port=os.getenv("SUPERSET_PORT", "8088"),
        superset_user=os.getenv("SUPERSET_ADMIN_USER", "admin"),
        superset_pass=os.getenv("SUPERSET_ADMIN_PASSWORD", "admin123"),
        minio_console_port=os.getenv("MINIO_CONSOLE_PORT", "9001"),
        minio_user=os.getenv("MINIO_ROOT_USER", "minio"),
        minio_pass=os.getenv("MINIO_ROOT_PASSWORD", "minio999"),
        datahub_port="9002",
        airbyte_port=os.getenv("AIRBYTE_WEB_PORT", "8000"),
        postgres_port=os.getenv("POSTGRES_PORT", "5432"),
        postgres_user=os.getenv("POSTGRES_USER", "lake"),
        postgres_pass=os.getenv("POSTGRES_PASSWORD", "lakepass"),
        postgres_db=os.getenv("POSTGRES_DB", "lakehouse"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=54321, debug=True)
