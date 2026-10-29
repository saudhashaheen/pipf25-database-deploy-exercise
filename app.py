import os
from pathlib import Path

import psycopg2
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)


def database_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env_path = Path(".env")
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL is missing")


@app.get("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.get("/api/students")
def students():
    with psycopg2.connect(database_url()) as conn, conn.cursor() as cur:
        cur.execute("SELECT full_name FROM student ORDER BY full_name")
        return jsonify([name for (name,) in cur.fetchall()])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
