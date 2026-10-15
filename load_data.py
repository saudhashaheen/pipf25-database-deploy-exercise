"""Create the intake schema and load class_dataset.csv into Postgres."""

import csv
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent
PERIODS = {"Weekday", "Weekend"}
TIMES = {"mornings", "afternoons", "evenings"}
TABLES = (
    "student",
    "tool",
    "student_tool",
    "availability_slot",
    "student_availability",
)


def database_url():
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            return value.strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL is missing from .env")


def csv_path():
    for path in (ROOT / "data" / "class_dataset.csv", ROOT / "class_dataset.csv"):
        if path.is_file():
            return path
    raise SystemExit("class_dataset.csv was not found in data/ or the project root")


def split_list(value):
    if not value or not value.strip():
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def parse_slot(label):
    period, separator, time_of_day = label.partition(" ")
    if separator and period in PERIODS and time_of_day in TIMES:
        return period, time_of_day
    raise SystemExit(f"Unrecognized availability value: {label!r}")


def blank_to_none(value):
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def load(conn, path):
    with path.open(newline="", encoding="utf-8") as handle, conn.cursor() as cur:
        for row in csv.DictReader(handle):
            cur.execute(
                """
                INSERT INTO student (
                    submitted_id, full_name, school_year, intro_programming,
                    skill_programming, skill_data_stats, skill_frontend_design,
                    skill_business_pitch, working_style, interests, semester_goal,
                    submitted_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING student_id
                """,
                (
                    row["netid"].strip(),
                    row["name"].strip(),
                    row["school_year"].strip(),
                    row["intro_programming"].strip(),
                    int(row["skill_programming"]),
                    int(row["skill_data_stats"]),
                    int(row["skill_frontend_design"]),
                    int(row["skill_business_pitch"]),
                    blank_to_none(row["working_style"]),
                    blank_to_none(row["interests"]),
                    blank_to_none(row["semester_goal"]),
                    row["submitted_at"].strip(),
                ),
            )
            student_id = cur.fetchone()[0]

            for position, name in enumerate(split_list(row["tools"]), start=1):
                cur.execute(
                    """
                    INSERT INTO tool (name) VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING tool_id
                    """,
                    (name,),
                )
                tool_id = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO student_tool (student_id, tool_id, position)
                    VALUES (%s, %s, %s)
                    """,
                    (student_id, tool_id, position),
                )

            for position, label in enumerate(split_list(row["availability"]), start=1):
                period, time_of_day = parse_slot(label)
                cur.execute(
                    """
                    INSERT INTO student_availability (
                        student_id, period, time_of_day, position
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    (student_id, period, time_of_day, position),
                )


def main():
    schema_sql = (ROOT / "schema.sql").read_text()
    conn = psycopg2.connect(database_url())
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.autocommit = False
        load(conn, csv_path())
        conn.commit()
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                print(f"{table}: {cur.fetchone()[0]}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
