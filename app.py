import os
import re
from pathlib import Path

import psycopg2
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)


def database_url():
    url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")
    if not url:
        env_path = Path(".env")
        if env_path.is_file():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not url:
        raise RuntimeError("DATABASE_URL is not set on the server")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if "sslmode=" not in url and ("rlwy.net" in url or "railway.app" in url):
        url += "&sslmode=require" if "?" in url else "?sslmode=require"
    return url


def public_error(exc):
    message = re.sub(r"://[^:\s]+:[^@\s]+@", "://***:***@", str(exc))
    return jsonify({"error": message}), 500


@app.get("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.get("/api/students")
def students():
    try:
        with psycopg2.connect(database_url()) as conn, conn.cursor() as cur:
            cur.execute("SELECT full_name FROM student ORDER BY full_name")
            return jsonify([name for (name,) in cur.fetchall()])
    except Exception as exc:
        return public_error(exc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
