"""Run starter queries, or your own SQL, against the intake database.

The connection is read-only. Start it with no arguments for the menu, or pass
a starter number to run that query and exit: python query.py 2
"""

import sys

import psycopg2

from load_data import database_url

QUERIES = [
    (
        "Roster and skill ratings",
        """
        SELECT full_name,
               school_year,
               intro_programming,
               skill_programming AS programming,
               skill_data_stats AS data_stats,
               skill_frontend_design AS frontend,
               skill_business_pitch AS pitch
        FROM student
        ORDER BY CASE school_year
                     WHEN 'First-year' THEN 1
                     WHEN 'Sophomore' THEN 2
                     WHEN 'Junior' THEN 3
                     WHEN 'Senior' THEN 4
                 END,
                 full_name
        """,
    ),
    (
        "Tools in the order each student listed them",
        """
        SELECT s.full_name,
               string_agg(t.name, ', ' ORDER BY st.position) AS tools
        FROM student s
        JOIN student_tool st ON st.student_id = s.student_id
        JOIN tool t ON t.tool_id = st.tool_id
        GROUP BY s.student_id, s.full_name
        ORDER BY s.full_name
        """,
    ),
    (
        "How many students listed each tool",
        """
        SELECT t.name AS tool, COUNT(*) AS students
        FROM tool t
        JOIN student_tool st ON st.tool_id = t.tool_id
        GROUP BY t.name
        ORDER BY students DESC, tool
        """,
    ),
    (
        "Students free on weekend mornings",
        """
        SELECT s.full_name,
               s.school_year,
               s.skill_programming AS programming,
               sa.position AS listed_at
        FROM student s
        JOIN student_availability sa ON sa.student_id = s.student_id
        WHERE sa.period = 'Weekend'
          AND sa.time_of_day = 'mornings'
        ORDER BY sa.position, s.full_name
        """,
    ),
    (
        "Pairs who share the most free slots",
        """
        SELECT a.full_name AS student_a,
               b.full_name AS student_b,
               COUNT(*) AS shared_slots
        FROM student_availability sa
        JOIN student_availability sb
          ON sa.period = sb.period
         AND sa.time_of_day = sb.time_of_day
         AND sa.student_id < sb.student_id
        JOIN student a ON a.student_id = sa.student_id
        JOIN student b ON b.student_id = sb.student_id
        GROUP BY a.full_name, b.full_name
        ORDER BY shared_slots DESC, student_a, student_b
        LIMIT 15
        """,
    ),
]


def print_menu():
    print("\nStarter queries")
    for number, (title, _) in enumerate(QUERIES, start=1):
        print(f"  {number}. {title}")
    print("  sql. Type a query")
    print("  q. Quit")


def prompt_sql():
    print("SQL, ending with a semicolon:")
    lines = []
    while True:
        line = input("sql> " if not lines else "...> ")
        lines.append(line)
        if line.strip().endswith(";"):
            return "\n".join(lines)


def cell(value):
    if value is None:
        return ""
    text = str(value).replace("\n", " ")
    if len(text) <= 40:
        return text
    return text[:37] + "..."


def print_result(cursor):
    if cursor.description is None:
        print("(no rows returned)")
        return
    rows = cursor.fetchall()
    headers = [column.name for column in cursor.description]
    rendered = [[cell(value) for value in row] for row in rows]
    widths = [
        max([len(header), *(len(row[index]) for row in rendered)], default=len(header))
        for index, header in enumerate(headers)
    ]
    header_line = "  ".join(header.ljust(width) for header, width in zip(headers, widths))
    print(header_line)
    print("  ".join("-" * width for width in widths))
    for row in rendered:
        print("  ".join(value.ljust(width) for value, width in zip(row, widths)))
    print(f"\n{len(rows)} row(s)")


def run(connection, sql):
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql)
        except psycopg2.Error as error:
            print(error.pgerror.strip() if error.pgerror else error)
            return
        print_result(cursor)


def main():
    connection = psycopg2.connect(database_url())
    connection.set_session(readonly=True, autocommit=True)
    try:
        if len(sys.argv) > 1:
            number = int(sys.argv[1])
            title, sql = QUERIES[number - 1]
            print(title)
            run(connection, sql)
            return
        while True:
            print_menu()
            choice = input("\nChoice: ").strip().lower()
            if choice in {"q", "quit", "exit"}:
                break
            if choice == "sql":
                run(connection, prompt_sql())
                continue
            if choice.isdigit() and 1 <= int(choice) <= len(QUERIES):
                title, sql = QUERIES[int(choice) - 1]
                print(f"\n{title}")
                run(connection, sql)
                continue
            print("Enter a number from the list, sql, or q.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
