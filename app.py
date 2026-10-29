from pathlib import Path

import psycopg2
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)


def database_url():
    for line in Path(".env").read_text().splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL is missing from .env")


@app.get("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.get("/api/students")
def students():
    with psycopg2.connect(database_url()) as conn, conn.cursor() as cur:
        cur.execute("SELECT full_name FROM student ORDER BY full_name")
        return jsonify([name for (name,) in cur.fetchall()])


if __name__ == "__main__":
    app.run(port=8000)
