import csv

from cluster_model import predict_cluster

SKILL_COLUMNS = (
    "skill_programming",
    "skill_data_stats",
    "skill_frontend_design",
    "skill_business_pitch",
)


def assign_groups(students, n_groups=8):
    by_cluster = {}
    for student in students:
        skills = [student[column] for column in SKILL_COLUMNS]
        cluster = predict_cluster(skills)
        by_cluster.setdefault(cluster, []).append(student["id"])

    clusters = sorted(by_cluster, key=lambda cluster: (-len(by_cluster[cluster]), cluster))
    group_of = {}
    cluster_of = {}
    seat = 0
    for cluster in clusters:
        for student_id in sorted(by_cluster[cluster]):
            group_of[student_id] = (seat % n_groups) + 1
            cluster_of[student_id] = cluster
            seat += 1

    return [
        {
            "id": student["id"],
            "cluster": cluster_of[student["id"]],
            "group": group_of[student["id"]],
        }
        for student in students
    ]


def load_students(path):
    students = []
    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            student = {"id": row["netid"]}
            for column in SKILL_COLUMNS:
                student[column] = float(row[column])
            students.append(student)
    return students


def main():
    n_groups = 8
    assignments = assign_groups(load_students("class_dataset.csv"), n_groups)
    clusters = sorted({student["cluster"] for student in assignments})
    by_group = {group: [] for group in range(1, n_groups + 1)}
    for student in assignments:
        by_group[student["group"]].append(student)

    missing = 0
    for group in range(1, n_groups + 1):
        members = by_group[group]
        counts = {cluster: 0 for cluster in clusters}
        for student in members:
            counts[student["cluster"]] += 1
        breakdown = ", ".join(
            f"cluster {cluster}: {counts[cluster]}" for cluster in clusters
        )
        print(f"group {group}: {len(members)} students ({breakdown})")
        if any(count == 0 for count in counts.values()):
            missing += 1
    print(f"groups missing a cluster: {missing}")


if __name__ == "__main__":
    main()
