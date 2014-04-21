import copy

class Canvas:
    def __init__(self, points, lines, triangles, delauny_points, data):
        self.composite_points = copy.deepcopy(points)
        self.composite_lines = copy.deepcopy(lines)
        # self.triangles = []
        # for t in triangles:
        #     points = []
        #     for p in t.points:
        #         points.append(self.composite_points[p.composite_point_index])
        #     self.triangles.append(geometry.Triangle(points = points))

        self.triangles = copy.deepcopy(triangles)
        self.delauny_points = copy.deepcopy(delauny_points)
        self.point_data = copy.deepcopy(data)