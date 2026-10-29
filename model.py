"""Reads the placeholder student table and summarizes competency scores."""

import csv
from pathlib import Path

STUDENTS = Path(__file__).resolve().parent / "database" / "student.csv"

COMPETENCIES = (
    ("skill_programming", "Programming"),
    ("skill_data_stats", "Data and stats"),
    ("skill_frontend_design", "Frontend design"),
    ("skill_business_pitch", "Business pitch"),
)


def _rows():
    with STUDENTS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def list_students():
    return [
        {
            "student_id": int(row["student_id"]),
            "full_name": row["full_name"].strip(),
        }
        for row in _rows()
    ]


def average_competencies():
    rows = _rows()
    count = len(rows)
    averages = []
    for key, label in COMPETENCIES:
        total = sum(int(row[key]) for row in rows)
        average = round(total / count, 2) if count else None
        averages.append({"key": key, "label": label, "average": average})
    return {"student_count": count, "averages": averages}
