class Canvas:
    def __init__(self, points, lines, triangles, delauny_points, data):
        self.composite_points = points[:]
        self.composite_lines = lines[:]
        self.triangles = triangles[:]
        self.delauny_points = delauny_points[:]
        self.point_data = data[:]