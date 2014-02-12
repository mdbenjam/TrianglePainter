__author__ = 'mdbenjam'

from OpenGL.GL import *
from OpenGL.GLUT import *
import math
import numpy as np
import copy

class Triangle:
    def __init__(self, points=None,file=None):
        if file == None:
            self.points = points
            self.centroid = getCentroid(self.points)
            self.color = None
        else:
            self.load(file)

    def get_colors(self):
        if self.color is None:
            self.color = []
            for p in self.points:
                self.color.append(p.get_current_color(self.centroid))
        return self.color


    def draw(self):
        color = self.get_colors()
        for p, c in zip(self.points, color):
            #print 'c'+str(color)
            glColor3f(c[0], c[1], c[2])
            glVertex2f(p.point[0], p.point[1])

    def draw_color(self, color):
        for p in self.points:
            glColor3f(color[0], color[1], color[2])
            glVertex2f(p.point[0], p.point[1])

    # TODO: optimize if all the colors are the same
    def get_color_at_point(self, point):
        color = [0,0,0,0]
        coeff_array = np.array([[self.points[0].point[0], self.points[0].point[1], 1],
                                [self.points[1].point[0], self.points[1].point[1], 1],
                                [self.points[2].point[0], self.points[2].point[1], 1]])
        point_colors = []
        index = 0
        for p in self.points:

            point_colors.append(p.get_current_color(self.centroid))
            index = index + 1

        total_area = triangle_area(self.points[0].point, self.points[1].point, self.points[2].point)
        for i in range(3):
            j = (i+1)%3
            k = (i+2)%3
            area = triangle_area(point, self.points[j].point, self.points[k].point)

            for h in range(4):
                color[h] += area/total_area * point_colors[i][h]
        """
        for i in range(4):
            color_array = np.array([point_colors[0][i], point_colors[1][i], point_colors[2][i]])
            try:
                results = np.linalg.solve(coeff_array, color_array)
                color[i] = results[0]*point[0] + results[1]*point[1] + results[2]
            except np.linalg.linalg.LinAlgError:
                print 'Color system degenerate. Linalg Error.'
                color[i] = color_array[0]
        """

        return color

    def save(self, f):
        for p in self.points:
            p.save(f)

    def load(self, f):
        self.points = []
        for i in range(3):
            self.points.append(TrianglePoint(file=f))

class Grid:

    def convert_from_center(self, x, y):
        return (x + self.window.center_x + self.window.zoom_width/2, y + self.window.center_y + self.window.zoom_height/2)

    def convert_to_center(self, x, y):
        return (x - self.window.center_x - self.window.zoom_width/2, y - self.window.center_y - self.window.zoom_height/2)

    def __init__(self, cols, rows, window, triangles, points, segments, is_triangle = False):
        self.cols = cols
        self.rows = rows
        self.window = window
        self.x_width = window.zoom_width / float(cols)
        self.y_height = window.zoom_height / float(rows)
        self.triangles = triangles
        self.is_triangle = is_triangle
        self.points = points
        self.segments = segments
        self.graph = []

        for i in range(len(points)):
            self.graph.append([])

        for s in segments:
            self.graph[s[0]].append(s[1])
            self.graph[s[1]].append(s[0])

        self.grid = []
        self.seg_grid = []
        for c in range(cols):
            self.grid.append([])
            self.seg_grid.append([])
            for r in range(rows):
                self.grid[c].append([])
                self.seg_grid[c].append([])

        for i, t in enumerate(triangles):
            if is_triangle:
                pts = t.points
                p = [pts[0].point, pts[1].point, pts[2].point]
            else:
                p = t

            xs = [p[0][0], p[1][0], p[2][0]]
            ys = [p[0][1], p[1][1], p[2][1]]
            min_x, min_y = self.convert_from_center(min(xs), min(ys))
            max_x, max_y = self.convert_from_center(max(xs), max(ys))

            x1 = int(min_x / self.x_width)
            x2 = int(max_x / self.x_width)

            y1 = int(min_y / self.y_height)
            y2 = int(max_y / self.y_height)


            for x in range(x1, x2+1):
                for y in range(y1, y2+1):
                    self.grid[x][y].append(i)

        for i, s in enumerate(segments):
            p = [points[s[0]].point, points[s[1]].point]

            xs = [p[0][0], p[1][0]]
            ys = [p[0][1], p[1][1]]
            min_x, min_y = self.convert_from_center(min(xs), min(ys))
            max_x, max_y = self.convert_from_center(max(xs), max(ys))

            x1 = int(min_x / self.x_width)
            x2 = int(max_x / self.x_width)

            y1 = int(min_y / self.y_height)
            y2 = int(max_y / self.y_height)

            for x in range(x1, x2+1):
                for y in range(y1, y2+1):
                    self.seg_grid[x][y].append(i)

    def point_in_occupied_grid(self, p):
        x, y = self.convert_from_center(p[0], p[1])
        x = int(x/self.x_width)
        y = int(y/self.y_height)
        return len(self.grid[x][y]) != 0

    def point_in_triangle_acc(self, p):
        x, y = self.convert_from_center(p[0], p[1])
        x = int(x/self.x_width)
        y = int(y/self.y_height)
        for i in self.grid[x][y]:
            if self.is_triangle:
                pts = self.triangles[i].points
                if pointInTriangle(p, [pts[0].point, pts[1].point, pts[2].point]):
                    return self.triangles[i]
            else:
                if pointInTriangle(p, self.triangles[i]):
                    return self.triangles[i]

        return None

    def get_number_triangles_part_of(self, p):
        x, y = self.convert_from_center(p.point[0], p.point[1])
        x = int(x/self.x_width)
        y = int(y/self.y_height)
        count = 0
        for k in self.grid[x][y]:
            if p in self.triangles[k].points:
                count += 1
        return count


    def get_unmodified_triangles(self, other):
        triangles = set(other.triangles)
        points = set()
        added_segs = []
        for i in range(self.cols):
            for j in range(self.rows):
                if len(self.grid[i][j]) != 0:
                    for k in other.grid[i][j]:
                        tri = other.triangles[k]

                        added_a_point = 0
                        for p in tri.points:
                            #if self.point_in_occupied_grid(p.point):
                            if self.point_in_triangle_acc(p.point):
                                added_a_point += 1
                                points.add(p)

                        if added_a_point == 3 and tri in triangles:
                            triangles.remove(tri)

        added_points = []
        added_segments = []
        replace_points_graph = []
        remove_seg_graph = []
        for i in range(len(self.points)):
            remove_seg_graph.append([])
            replace_points_graph.append(None)

        index = len(self.points)
        added_index = 0
        already_intersected = set()
        for p in self.points:
            for i2 in self.graph[p.composite_point_index]:
                p2 = self.points[i2]
                if p.composite_point_index >= p2.composite_point_index:
                    continue
                x, y = self.convert_from_center(p.point[0], p.point[1])
                x = int(x/self.x_width)
                y = int(y/self.y_height)

                x2, y2 = self.convert_from_center(p2.point[0], p2.point[1])
                x2 = int(x2/self.x_width)
                y2 = int(y2/self.y_height)

                xmin = min(x, x2)
                xmax = max(x, x2)

                ymin = min(y, y2)
                ymax = max(y, y2)

                for x in range(xmin, xmax+1):
                    for y in range(ymin, ymax+1):
                        for k in other.seg_grid[x][y]:
                            print 'k', k
                            seg = other.segments[k]
                            if (p == other.points[seg[0]] or p2 == other.points[seg[0]] or
                                p == other.points[seg[1]] or p2 == other.points[seg[1]]):
                                continue

                            other_nums = [p.composite_point_index, p2.composite_point_index, other.points[seg[0]].composite_point_index, other.points[seg[1]].composite_point_index]
                            other_nums = sorted(other_nums)
                            point_numbers = (other_nums[0], other_nums[1], other_nums[2], other_nums[3])

                            if point_numbers in already_intersected:
                                continue

                            intersection = lineIntersection(p.point, p2.point, other.points[seg[0]].point, other.points[seg[1]].point)
                            if not intersection is None:
                                added_points.append(TrianglePoint([intersection[0], intersection[1]], composite_point_index = index))
                                added_segments.append([index, p.composite_point_index])
                                added_segments.append([index, p2.composite_point_index])
                                added_segments.append([index, other.points[seg[0]].composite_point_index])
                                added_segments.append([index, other.points[seg[1]].composite_point_index])
                                remove_seg_graph[p.composite_point_index].append(p2.composite_point_index)
                                remove_seg_graph[p2.composite_point_index].append(p.composite_point_index)
                                remove_seg_graph[other.points[seg[0]].composite_point_index].append(other.points[seg[1]].composite_point_index)
                                remove_seg_graph[other.points[seg[1]].composite_point_index].append(other.points[seg[0]].composite_point_index)
                                replace_points_graph[p.composite_point_index] = added_index

                                index += 1
                                added_index += 1


                                already_intersected.add(point_numbers)




        """
        new_triangles = set()
        for tri in triangles:
            remove = False
            for i, p in enumerate(tri.points):
                p1 = tri.points[(i+1)%3]
                p2 = tri.points[(i+2)%3]
                count = 0
                for index in segment_graph[p.composite_point_index]:
                    if (index == p1.composite_point_index or index == p2.composite_point_index) and p1 in points and p2 in points:
                        count += 1
                if count == 2:
                    for p3 in tri.points:
                        points.add(p3)
                    remove = True
                    break
            if not remove:
                new_triangles.add(tri)
        triangles = new_triangles
        for t in other.triangles:
            for i, p in enumerate(t.points):
                p1 = t.points[(i+1)%3]
                p2 = t.points[(i+2)%3]
                bool1 = p1 in points
                bool2 = p2 in points
                bool3 = p in points
                if not bool3 and bool1 and bool2:
                    added_segs.append([p1.composite_point_index, p2.composite_point_index])
        """
        """
        for t in other.triangles:
            for i, p in enumerate(t.points):
                replace = replace_points_graph[p.composite_point_index]
                if not replace is None:
                    t.points[i] = added_points[replace]
        """
        triangle_list = sorted(list(triangles), key=lambda tri: max(tri.points[0].composite_point_index, tri.points[1].composite_point_index, tri.points[2].composite_point_index))



        return triangle_list, list(points), added_points, added_segments, remove_seg_graph

    def draw_grid(self):
        glColor3f(0.5, 1, 0.5)
        for i in range(self.cols):
            for j in range(self.rows):
                x1, y1 = self.convert_to_center(i * self.x_width, j * self.y_height)
                x2, y2 = self.convert_to_center((i+1) * self.x_width, (j+1) * self.y_height)
                if len(self.grid[i][j]) == 0:
                    glBegin(GL_LINE_LOOP)
                else:
                    glBegin(GL_QUADS)
                glVertex2f(x1, y1)
                glVertex2f(x2, y1)
                glVertex2f(x2, y2)
                glVertex2f(x1, y2)
                glEnd()



class ColorRegion:
    def __init__(self, color, start_angle, end_angle):
        self.color = color
        self.start_angle = start_angle
        self.end_angle = end_angle

def composite_ranges(bottom_range, top_range):
    color_ranges = []

    for t in top_range:
        for b in bottom_range:
            if angle_between(b.start_angle, t.start_angle, b.end_angle):
                if angle_between(b.start_angle, t.end_angle, b.end_angle):
                    color_ranges.append(ColorRegion(color_over(b.color, t.color), t.start_angle, t.end_angle))
                color_ranges.append(ColorRegion(color_over(b.color, t.color), t.start_angle, b.end_angle))
            elif angle_between(b.start_angle, t.end_angle, b.end_angle):
                color_ranges.append(ColorRegion(color_over(b.color, t.color), b.start_angle, t.end_angle))
            elif (angle_between(t.start_angle, b.start_angle, t.end_angle) and
                angle_between(t.start_angle, b.end_angle, t.end_angle)):
                color_ranges.append(ColorRegion(color_over(b.color, t.color), b.start_angle, b.end_angle))

    return color_ranges


def getCentroid(tri):
    centroid = [0, 0]
    for p in tri:
        centroid[0] = centroid[0] + p.point[0]
        centroid[1] = centroid[1] + p.point[1]

    return [centroid[0]/3.0, centroid[1]/3.0]

def getCentroidPoints(tri):
    centroid = [0, 0]
    for p in tri:
        centroid[0] = centroid[0] + p[0]
        centroid[1] = centroid[1] + p[1]

    return [centroid[0]/3.0, centroid[1]/3.0]

"""
Is angle b between a and c
"""
def angle_between(a, b, c):
    s_cross_e = np.cross(a, c)
    if s_cross_e < 0:
        mid = -(a+c)/2.0
        return angle_between(a, b, mid) or angle_between(mid, b, c)
    return (np.cross(a, b) >= 0 and np.cross(b,c) >= 0)

def get_color(regions, angle):
    for r in regions:
        if angle_between(r.start_angle, angle, r.end_angle):
            return r.color
    return regions[0].color

def colors_equal(c1, c2):
    return (abs(c1[0]-c2[0]) < .01 and
            abs(c1[1]-c2[1]) < .01 and
            abs(c1[2]-c2[2]) < .01)

def color_over(color_bottom, color_top):
    alpha = color_top[3]
    composite_color = [color_top[0]*alpha + color_bottom[0]*(1-alpha),
                       color_top[1]*alpha + color_bottom[1]*(1-alpha),
                       color_top[2]*alpha + color_bottom[2]*(1-alpha),
                       1]
    return composite_color

class TrianglePoint:
    def __init__(self, point=None, color_regions=None, composite_point_index = None, file=None):
        if file == None:
            self.point = point
            self.color_regions = color_regions
            self.composite_point_index = composite_point_index
        else:
            self.load(file)

    def get_current_color(self, centroid):
        return get_color(self.color_regions, np.array([centroid[0]-self.point[0], centroid[1]-self.point[1]]))

    def composite_color(self, color):
        for r in self.color_regions:
            r.color = color_over(r.color, color)

    def save(self, f):
        f.write(str(self.point[0])+','+str(self.point[1]))
        f.write(':')
        f.write(str(len(self.color_regions)))
        f.write('\n')
        for c in self.color_regions:
            f.write(str(c.color[0])+','+
                        str(c.color[1])+','+
                        str(c.color[2])+','+
                        str(c.color[3])+','+
                        str(c.start_angle)+','+
                        str(c.end_angle)+'\n')


    def load(self, f):
        line = f.readline()
        s = line.split(':')
        point = s[0].split(',')
        num = int(s[1])
        self.color_regions = []
        for i in range(num):
            c = f.readline().split(',')
            self.color_regions.append(ColorRegion([float(c[0]),
                                       float(c[1]),
                                       float(c[2]),
                                       float(c[3])],
                                       float(c[4]),
                                       float(c[5])))


        self.point = [float(point[0]), float(point[1])]

def cross(v1, v2):
    return v1[0]*v2[1] - v1[1]*v2[0]

def pointInTriangle(p, tri):

    def sameSide(p, p1, p2, p3):
        side = [p1[0]-p2[0], p1[1]-p2[1]]
        to_point = [p[0]-p2[0], p[1]-p2[1]]
        to_tip = [p3[0]-p2[0], p3[1]-p2[1]]
        return cross(side, to_point)*cross(side, to_tip) >= 0

    return sameSide(p, tri[0], tri[1], tri[2]) and sameSide(p, tri[1], tri[2], tri[0]) and sameSide(p, tri[2], tri[0], tri[1])

def pointInQuad(p, quad):
    flag = 0
    for j in range(4):
        v1 = quad[j]
        v2 = quad[(j+1)%4]
        ev = (v1[0]-v2[0], v1[1]-v2[1])
        pv = (p[0]-v2[0], p[1]-v2[1])
        cross = ev[0]*pv[1]-ev[1]*pv[0]
        if cross < -.0001:
            if flag == 0:
                flag = 1
            elif flag == 2:
                return False
        elif cross > .0001:
            if flag == 0:
                flag = 2
            elif flag == 1:
                return False
        else:
            return False
    return True

def lineIntersection(p1, p2, p3, p4):
    if max(p1[0], p2[0]) < min(p3[0], p4[0]):
        return None

    dx = p1[0]-p2[0]
    if (dx == 0):
        m1 = None
    else:
        m1 = (p1[1]-p2[1])/dx

    dx = p3[0]-p4[0]
    if (dx == 0):
        m2 = None
    else:
        m2 = (p3[1]-p4[1])/dx

    if m1 == m2:
        return None

    if m1 == None:
        b2 = p3[1]-m2*p3[0]
        x = p1[0]
        y = m2*p1[0]+b2
        if x > min(p3[0],p4[0]) and x < max(p3[0], p4[0]) and y > min(p1[1], p2[1]) and y < max(p1[1], p2[1]):
            return (x,y)
        else:
            return None
    elif m2 == None:
        b1 = p1[1]-m1*p1[0]
        x = p3[0]
        y = m1*p3[0]+b1
        if x > min(p1[0],p2[0]) and x < max(p1[0], p2[0]) and y > min(p3[1], p4[1]) and y < max(p3[1], p4[1]):
            return (x,y)
        else:
            return None
    else:
        b1 = p1[1]-m1*p1[0]
        b2 = p3[1]-m2*p3[0]
        x = (b2-b1)/(m1-m2)
        y = m1*x+b1

    if (x < max(min(p1[0], p2[0]), min(p3[0],p4[0]))) or (x > min(max(p1[0], p2[0]), max(p3[0], p4[0]))):
        return None
    else:
        return (x,y)

def triangle_area(p1, p2, p3):
    x1 = p1[0]
    y1 = p1[1]
    x2 = p2[0]
    y2 = p2[1]
    x3 = p3[0]
    y3 = p3[1]
    return abs(.5*(-x2*y1 + x3*y1 + x1*y2 - x3*y2 - x1*y3 + x2*y3))