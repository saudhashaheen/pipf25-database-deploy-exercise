CENTROIDS = (
    (2.923076923076923, 3.0769230769230766, 2.8461538461538463, 4.0),
    (3.0, 3.6, 1.4, 1.5999999999999996),
    (4.2, 4.6, 4.0, 4.6),
)


def predict_cluster(skills):
    nearest = 0
    nearest_distance = None
    for label, centroid in enumerate(CENTROIDS):
        distance = 0.0
        for value, center in zip(skills, centroid):
            difference = value - center
            distance += difference * difference
        if nearest_distance is None or distance < nearest_distance:
            nearest = label
            nearest_distance = distance
    return nearest
