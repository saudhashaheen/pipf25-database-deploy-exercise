import os
import re
from pathlib import Path

import psycopg2
from flask import Flask, jsonify, send_from_directory

from assignment_rules import assign_groups
from cluster_model import CENTROIDS

app = Flask(__name__)

N_GROUPS = 8


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


def group_payload(rows):
    names = {}
    students = []
    for submitted_id, full_name, programming, data_stats, frontend, pitch in rows:
        names[submitted_id] = full_name
        students.append(
            {
                "id": submitted_id,
                "skill_programming": programming,
                "skill_data_stats": data_stats,
                "skill_frontend_design": frontend,
                "skill_business_pitch": pitch,
            }
        )

    assignments = assign_groups(students)
    labels = sorted({item["cluster"] for item in assignments})
    by_group = {group: [] for group in range(1, N_GROUPS + 1)}
    for item in assignments:
        by_group[item["group"]].append(item)

    groups = []
    missing = 0
    for group in range(1, N_GROUPS + 1):
        counts = {label: 0 for label in labels}
        for item in by_group[group]:
            counts[item["cluster"]] += 1
        if any(count == 0 for count in counts.values()):
            missing += 1
        groups.append(
            {
                "group": group,
                "members": [names[item["id"]] for item in by_group[group]],
                "cluster_counts": counts,
            }
        )

    return {
        "n_groups": N_GROUPS,
        "groups": groups,
        "clusters": [
            {
                "cluster": label,
                "students": sum(item["cluster"] == label for item in assignments),
                "centroid": list(CENTROIDS[label]),
            }
            for label in labels
        ],
        "groups_missing_a_cluster": missing,
    }


@app.get("/api/groups")
def groups():
    try:
        with psycopg2.connect(database_url()) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT submitted_id, full_name,
                       skill_programming, skill_data_stats,
                       skill_frontend_design, skill_business_pitch
                FROM student
                ORDER BY submitted_id
                """
            )
            return jsonify(group_payload(cur.fetchall()))
    except Exception as exc:
        return public_error(exc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
