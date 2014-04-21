__author__ = 'mdbenjam'

from OpenGL.GL import *
from OpenGL.GLUT import *
import math
import numpy as np
import orderedset
import collections

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
        self.centroid = getCentroid(self.points)
        self.color = None

class Grid:

    def convert_from_center(self, x, y):
        return (x - self.window.center_x + self.window.zoom_width/2, y - self.window.center_y + self.window.zoom_height/2)

    def convert_to_center(self, x, y):
        return (x + self.window.center_x - self.window.zoom_width/2, y + self.window.center_y - self.window.zoom_height/2)

    def __init__(self, cols, rows, window, triangles, is_triangle = False):
        self.cols = cols
        self.rows = rows
        self.window = window
        self.x_width = window.zoom_width / float(cols)
        self.y_height = window.zoom_height / float(rows)
        self.triangles = triangles
        self.is_triangle = is_triangle
        self.one_big_triangle = None

        self.grid = []

        for c in range(cols):
            self.grid.append([])
            for r in range(rows):
                self.grid[c].append([])

        for i, t in enumerate(triangles):


            if is_triangle:
                pts = t.points
                p = [pts[0].point, pts[1].point, pts[2].point]
            else:
                p = t

            if (pointInTriangle((self.window.center_x - self.window.zoom_width/2, self.window.center_y - self.window.zoom_height/2), p) and
                pointInTriangle((self.window.center_x - self.window.zoom_width/2, self.window.center_y + self.window.zoom_height/2), p) and
                pointInTriangle((self.window.center_x + self.window.zoom_width/2, self.window.center_y + self.window.zoom_height/2), p) and
                pointInTriangle((self.window.center_x + self.window.zoom_width/2, self.window.center_y - self.window.zoom_height/2), p)):
                self.one_big_triangle = t

            xs = [p[0][0], p[1][0], p[2][0]]
            ys = [p[0][1], p[1][1], p[2][1]]
            min_x, min_y = self.convert_from_center(min(xs), min(ys))
            max_x, max_y = self.convert_from_center(max(xs), max(ys))

            x1 = int(min_x / self.x_width)
            x2 = int(max_x / self.x_width)

            y1 = int(min_y / self.y_height)
            y2 = int(max_y / self.y_height)

            #if x1 < 0 and y1 < 0 and x2 > self.cols and y2 > self.rows:


            for x in range(max(0, x1), min(x2+1, self.cols)):
                for y in range(max(0, y1), min(y2+1, self.rows)):
                    self.grid[x][y].append(i)

            if not self.one_big_triangle is None:
                break

    def point_in_occupied_grid(self, p):
        x, y = self.convert_from_center(p[0], p[1])
        x = int(x/self.x_width)
        y = int(y/self.y_height)
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return len(self.grid[x][y]) != 0
        else:
            return False

    def point_in_triangle_acc(self, p):
        x, y = self.convert_from_center(p[0], p[1])
        x = int(x/self.x_width)
        y = int(y/self.y_height)
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return None

        for i in self.grid[x][y]:
            if self.is_triangle:
                pts = self.triangles[i].points
                if pointInTriangle(p, [pts[0].point, pts[1].point, pts[2].point]):
                    return self.triangles[i]
            else:
                if pointInTriangle(p, self.triangles[i]):
                    return self.triangles[i]

        return None

    def point_in_triangle_slow(self, p):
        for t in self.triangles:
            if self.is_triangle:
                pts = t.points
                if pointInTriangle(p, [pts[0].point, pts[1].point, pts[2].point]):
                    return t
            else:
                if pointInTriangle(p, t):
                    return t

        return None

    def triangle_intersection(self, tri):

        non_intersected_segments = orderedset.OrderedSet()
        counter = 0
        tried = orderedset.OrderedSet()
        bad_segs = orderedset.OrderedSet()
        ever_intersected = False

        pts = tri.points

        inside = []
        for p1 in pts:
            inside.append(self.point_in_triangle_acc(p1.point))
            if inside[-1]:
                ever_intersected = True

        """
        if ever_intersected:
            for index, p in enumerate(pts):
                index2 = (index + 1) % 3
                if inside[index] is None and inside[index2] is None:
                    non_intersected_segments.add((p.composite_point_index, tri.points[index2].composite_point_index))
        """

        if len(non_intersected_segments) == 0:

            p = [pts[0].point, pts[1].point, pts[2].point]

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
                    for i in self.grid[x][y]:
                        if i in tried:
                            break
                        tried.add(i)
                        # print counter
                        counter += 1
                        pts2 = self.triangles[i].points
                        intersected = False
                        segments = []

                        for index1, p1 in enumerate(pts):
                            index12 = (index1 + 1) % 3
                            for index2, p2 in enumerate(pts2):
                                index22 = (index2 + 1) % 3
                                if lineIntersection(p1.point, pts[index12].point, p2.point, pts2[index22].point):
                                    intersected = True
                                    ever_intersected = True
                                    seg = [(p1.composite_point_index, pts[index12].composite_point_index),
                                           (pts[index12].composite_point_index, p1.composite_point_index)]
                                    for j in range(len(seg)):
                                        bad_segs.add(seg[j])
                                        if seg[j] in non_intersected_segments:
                                            non_intersected_segments.remove(seg[j])
                                else:
                                    if inside[index1] or inside[index12]:
                                        seg = [(p1.composite_point_index, pts[index12].composite_point_index),
                                               (pts[index12].composite_point_index, p1.composite_point_index)]
                                        for j in range(len(seg)):
                                            bad_segs.add(seg[j])
                                            if seg[j] in non_intersected_segments:
                                                non_intersected_segments.remove(seg[j])
                                    else:
                                        seg = (p1.composite_point_index, pts[index12].composite_point_index)
                                        if not seg in bad_segs and not (pts[index12].composite_point_index, p1.composite_point_index) in segments:
                                            segments.append(seg)
                        if intersected:
                            non_intersected_segments.update(segments)
                        # else:
                        #     inside = True
                        #     triPts = [pts[0].point, pts[1].point, pts[2].point]
                        #     segments = []
                        #     for i, p in enumerate(pts2):
                        #         p2 = pts2[(i+1)%3]
                        #         segments.append((p.composite_point_index, p2.composite_point_index))
                        #         if not pointInTriangle(p, triPts):
                        #             inside = False
                        #             break
                        #     if inside:
                        #         non_intersected_segments.update(segments)
                        #         ever_intersected = True

        if ever_intersected == 0:
            return None
        else:
            return list(non_intersected_segments)

    def has_grid_line_intersection(self, p1, p2, p3):
        if self.point_in_occupied_grid(p1) or self.point_in_occupied_grid(p2):
            return True
        p1_convert = self.convert_from_center(p1[0], p1[1])
        p2_convert = self.convert_from_center(p2[0], p2[1])

        dy = float(p1_convert[1] - p2_convert[1])
        dx = float(p1_convert[0] - p2_convert[0])
        if dx == 0:
            dx = .001
        m = dy/dx
        b = p1_convert[1] - m*p1_convert[0]

        xs = [p1[0], p2[0]]
        ys = [p1[1], p2[1]]
        min_x, min_y = self.convert_from_center(min(xs), min(ys))
        max_x, max_y = self.convert_from_center(max(xs), max(ys))

        x1 = int(min_x / self.x_width)
        x2 = int(max_x / self.x_width)

        y1 = int(min_y / self.y_height)
        y2 = int(max_y / self.y_height)

        #for x in range(x1+1, x2+1):
        #    for y in range(y1+1, y2+1):
        #        if self.grid[x][y] > 0:
        #            if pointInTriangle((x, y), (p1, p2, p3)):
        #                return True

        for x in range(x1+1, x2+1):
            y = m * x * self.x_width + b
            y_grid = int(y / self.y_height)
            if 0 <= x < self.cols and 0 <= y_grid < self.rows:
                if y1 <= y_grid <= y2 and (len(self.grid[x-1][y_grid]) > 0 or len(self.grid[x][y_grid]) > 0):
                    # draw_point = self.convert_to_center(x*self.x_width, y)
                    # glColor3f(0, 0, 1)
                    # glBegin(GL_LINES)
                    # glVertex2f(p1[0], p1[1])
                    # glVertex2f(p2[0], p2[1])
                    # glEnd()
                    # glBegin(GL_POINTS)
                    # glVertex2f(draw_point[0], draw_point[1])
                    # glEnd()
                    return True

        if m == 0:
            return False

        for y in range(y1+1, y2+1):
            x = (y * self.y_height - b)/m
            x_grid = int(x / self.x_width)
            if 0 <= x_grid < self.cols and 0 <= y < self.rows:
                if x1 <= x_grid <= x2 and (len(self.grid[x_grid][y-1]) > 0 or len(self.grid[x_grid][y]) > 0):
                    # draw_point = self.convert_to_center(x, y*self.y_height)
                    # glColor3f(0, 1, 1)
                    # glBegin(GL_LINES)
                    # glVertex2f(p1[0], p1[1])
                    # glVertex2f(p2[0], p2[1])
                    # glEnd()
                    # glBegin(GL_POINTS)
                    # glVertex2f(draw_point[0], draw_point[1])
                    # glEnd()
                    return True

        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        glVertex2f(p1[0], p1[1])
        glVertex2f(p2[0], p2[1])
        glEnd()
        return False

    def get_number_triangles_part_of(self, p):
        x, y = self.convert_from_center(p.point[0], p.point[1])
        x = int(x/self.x_width)
        y = int(y/self.y_height)
        count = 0
        for k in self.grid[x][y]:
            if p in self.triangles[k].points:
                count += 1
        return count


    def get_unmodified_triangles(self, other, segment_graph):
        
        glPointSize(5)

        glColor3f(0, 0, 1)

        triangle_map = {}
        for t in other.triangles:
            for i in range(len(t.points)):
                p1 = t.points[i].composite_point_index
                p2 = t.points[(i+1)%3].composite_point_index
                if (p1, p2) in triangle_map:
                    triangle_map[(p1, p2)].append(t)
                else:
                    triangle_map[(p1, p2)] = [t]

                if (p2, p1) in triangle_map:
                    triangle_map[(p2, p1)].append(t)
                else:
                    triangle_map[(p2, p1)] = [t]

        triangles = orderedset.OrderedSet(other.triangles)
        points = orderedset.OrderedSet()
        added_segs = collections.OrderedDict()
        hole_points = orderedset.OrderedSet()
        opposite_segs = orderedset.OrderedSet()
        counter = 0
        if other.one_big_triangle is None:
            for i in range(self.cols):
                for j in range(self.rows):
                    if len(self.grid[i][j]) != 0:
                        for k in other.grid[i][j]:
                            tri = other.triangles[k]
                            if not tri in triangles:
                                continue
                            # print 'counter', counter
                            counter += 1

                            point_in_grid = []
                            at_least_one = False
                            for h, p in enumerate(tri.points):
                                h2 = (h+1)%3
                                h3 = (h+2)%3
                                point_in_grid.append(self.has_grid_line_intersection(p.point, tri.points[h2].point, tri.points[h3].point))
                                if point_in_grid[-1]:
                                    at_least_one = True

                            if at_least_one:
                                if tri in triangles:
                                    triangles.remove(tri)
                                for h, p in enumerate(tri.points):
                                    points.add(p)
                                    h2 = (h+1)%3
                                    # print 'point_in_grid', point_in_grid[h]
                                    if not point_in_grid[h]:#not point_in_grid[i] and not point_in_grid[i2] and point_in_grid[i3]:
                                        edge = (p.composite_point_index, tri.points[h2].composite_point_index)
                                        if not edge in opposite_segs:
                                            involved_triangles = triangle_map[edge]
                                            added_segs[edge] = None
                                            for involved_triangle in involved_triangles:
                                                if involved_triangle != tri:
                                                    added_segs[edge] = involved_triangle
                                                    break

                                            opposite_segs.add((edge[1], edge[0]))
        
        if len(opposite_segs) == 0:
            tri = self.triangles[0]
            p = tri.points[0]
            outerTri = other.point_in_triangle_acc(p.point)
            if outerTri is None:
                return [], [], [], []
            if outerTri in triangles:
                triangles.remove(outerTri)
            for h, p in enumerate(outerTri.points):
                points.add(p)
                h2 = (h+1)%3
                edge = (p.composite_point_index, outerTri.points[h2].composite_point_index)
                if not edge in opposite_segs:
                    involved_triangles = triangle_map[edge]
                    added_segs[edge] = None
                    for involved_triangle in involved_triangles:
                        if involved_triangle != outerTri:
                            added_segs[edge] = involved_triangle
                            break

            #glBegin(GL_TRIANGLES)
            #tri.draw_color((1, .5, 0))
            #glEnd()

            """
            if not intersection_edges is None:
                for p in tri.points:
                    points.add(p)
                for edge in intersection_edges:
                    if not edge in opposite_segs:
                        added_segs.add(edge)
                        opposite_segs.add((edge[1], edge[0]))
                if tri in triangles:
                    triangles.remove(tri)
            """
        """


        for i in range(self.cols):
            for j in range(self.rows):
                if len(self.grid[i][j]) != 0:
                    for k in other.grid[i][j]:
                        tri = other.triangles[k]

                        contains_one = False
                        inside_tri = []
                        for p in tri.points:
                            inside_tri.append(self.point_in_triangle_acc(p.point))
                            if not inside_tri[-1] is None:
                                contains_one = True
                            #if self.point_in_occupied_grid(p.point):

                        if contains_one:
                            for index, p in enumerate(tri.points):
                                index2 = (index + 1) % 3
                                if inside_tri[index] is None and inside_tri[index2] is None:
                                    added_segs.add((p.composite_point_index, tri.points[index2].composite_point_index))

                                points.add(p)
                            if tri in triangles:
                                triangles.remove(tri)
        """

        """
                if len(other.grid[i][j]) != 0:
                    for k in self.grid[i][j]:
                        tri = self.triangles[k]

                        contains_one = False
                        for p in tri.points:
                            inside_triangle = other.point_in_triangle_acc(p.point)
                            if not inside_triangle is None:
                                if inside_triangle in triangles:
                                    triangles.remove(inside_triangle)
                                for index, p2 in enumerate(inside_triangle.points):
                                    index2 = (index + 1) % 3
                                    points.add(p2)
                                    added_segs.append([p2.composite_point_index, inside_triangle.points[index2].composite_point_index])

                        for h in self.grid[i][j]:
                            tri2 = self.triangles[h]

                            contains_one = False
                            pts = tri.points
                            pts = [pts[0].point, pts[1].point, pts[2].point]
                            for p in tri2.points:
                                if pointInTriangle(p.point, pts):
                                    contains_one = True
                                    break

                            if contains_one:
                                #print 'adding contained triangle'
                                for p in tri.points:
                                    points.add(p)
                                if tri in triangles:
                                    triangles.remove(tri)
                        """
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
        glPointSize(1)
        """
        graph = {}
        for k,v in added_segs.iteritems():
            print k
            if k[0] in graph:
                graph[k[0]].append((k[1], v))
            else:
                graph[k[0]] = [(k[1], v)]

            if k[1] in graph:
                graph[k[1]].append((k[0], v))
            else:
                graph[k[1]] = [(k[0], v)]

        def remove_other_k(k):
            other_k = graph[k][0][0]
            graph[k] = []
            new_v = []
            for v in graph[other_k]:
                if v[0] != k:
                    new_v.append(v)
            graph[other_k] = new_v
            if len(new_v) == 1:
                remove_other_k(new_v[0][0])

        print 'graph 1', graph

        for k in graph.keys():
            v = graph[k]
            if len(v) == 1:
                print 'removing a point'
                #remove_other_k(k)

        print 'graph 2', graph

        added_segs_list = []
        hole_point_list = []
        for k, v in graph.iteritems():
            for k2 in v:
                added_segs_list.append((k, k2[0]))
                if not k2[1] is None:
                    hole_point_list.append(k2[1].centroid)
        """
        added_segs_list = []
        hole_point_list = []
        for k, v in added_segs.iteritems():
            added_segs_list.append(k)
            if not v is None:
                p = v.centroid
                tri_inside = other.point_in_triangle_acc(p)
                if tri_inside in triangles:
                    hole_point_list.append(p)


        return list(triangles), list(points), list(added_segs.keys()), hole_point_list

    def draw_grid(self, flag = False):
        if flag:
            glColor4f(0, 0, 1, 0.5)
        else:
            glColor4f(0.5, 1, 0.5, 1)
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

    def examine_grid(self, other):
        for i in range(self.cols):
            for j in range(self.rows):
                if len(self.grid[i][j]) > 0:
                    glClear(GL_COLOR_BUFFER_BIT)
                    for t in other.triangles:
                        glBegin(GL_LINE_LOOP)
                        t.draw_color((0,0,0))
                        glEnd()
                    glColor4f(0.5, 1, 0.5, 1)
                    x1, y1 = self.convert_to_center(i * self.x_width, j * self.y_height)
                    x2, y2 = self.convert_to_center((i+1) * self.x_width, (j+1) * self.y_height)
                    glBegin(GL_QUADS)
                    glVertex2f(x1, y1)
                    glVertex2f(x2, y1)
                    glVertex2f(x2, y2)
                    glVertex2f(x1, y2)
                    glEnd()
                    for k in other.grid[i][j]:
                        tri = other.triangles[k]
                        glBegin(GL_LINE_LOOP)
                        tri.draw_color((1, .5, 0))
                        glEnd()
                    glutSwapBuffers()
                    raw_input('press any key')

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
                else:
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
            self.fix_color_regions()
        else:
            self.load(file)

    def fix_color_regions(self):
        new_regions = []
        if len(self.color_regions) > 0 and isinstance(self.color_regions[0], list):
            for r in self.color_regions:
                for a in r:
                    new_regions.append(a)
            self.color_regions = new_regions

    def get_current_color(self, centroid):
        self.fix_color_regions()
        return get_color(self.color_regions, np.array([centroid[0]-self.point[0], centroid[1]-self.point[1]]))

    def composite_color(self, color):
        self.fix_color_regions()
        for r in self.color_regions:
            r.color = color_over(r.color, color)

    def save(self, f):
        f.write('%.16f' % (self.point[0])+','+'%.16f' % self.point[1])
        f.write(':')
        f.write(str(self.composite_point_index))
        f.write(':')
        f.write(str(len(self.color_regions)))
        f.write('\n')
        for c in self.color_regions:
            f.write(str(c.color[0])+','+
                        str(c.color[1])+','+
                        str(c.color[2])+','+
                        str(c.color[3])+','+
                        '%.16f' % c.start_angle[0]+','+
                        '%.16f' % c.start_angle[1]+','+
                        '%.16f' % c.end_angle[0]+','+
                        '%.16f' % c.end_angle[1]+'\n')


    def load(self, f):
        line = f.readline()
        s = line.split(':')
        point = s[0].split(',')
        self.composite_point_index = int(s[1])
        num = int(s[2])
        self.color_regions = []
        for i in range(num):
            c = f.readline().split(',')
            self.color_regions.append(ColorRegion([float(c[0]),
                                       float(c[1]),
                                       float(c[2]),
                                       float(c[3])],
                                       np.array([float(c[4]),
                                       float(c[5])]),
                                       np.array([float(c[6]),
                                        float(c[7])])))


        self.point = [float(point[0]), float(point[1])]

def cross(v1, v2):
    return v1[0]*v2[1] - v1[1]*v2[0]

def pointsOnSameSideOfLine(c, d, a, b):
    ab = [a[0]-b[0], a[1]-b[1]]
    ac = [a[0]-c[0], a[1]-c[1]]
    ad = [a[0]-d[0], a[1]-d[1]]
    c1 = cross(ab, ac)
    c2 = cross(ab, ad)
    return c1*c2 >= 0
    # return (((l1[1] - l2[1]) * (p1[0] - l1[0]) +
    #         (l2[0] - l1[0]) * (p1[1] - l1[1])) *
    #         ((l1[1] - l2[1]) * (p2[0] - l1[0]) +
    #         (l2[0] - l1[0]) * (p2[1] - l1[1]))) >= 0

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


def remove_triangles_with_holes(triangles, holes, boundaries, points, grid_x, grid_y, window, canvas):
    pointTriangleMap = collections.OrderedDict()

    for t in triangles:
        for p in t.points:
            if p in pointTriangleMap:
                pointTriangleMap[p].append(t)
            else:
                pointTriangleMap[p] = [t]

    pointBoundaryMap = collections.OrderedDict()

    for b in boundaries:
        p = points[b[0]]
        if p in pointBoundaryMap:
            pointBoundaryMap[p].append(b[1])
        else:
            pointBoundaryMap[p] = [b[1]]

        p = points[b[1]]
        if p in pointBoundaryMap:
           pointBoundaryMap[p].append(b[0])
        else:
            pointBoundaryMap[p] = [b[0]]

    notRemoveTriangles = orderedset.OrderedSet(triangles)
    boundarySet = orderedset.OrderedSet(boundaries)

    grid = Grid(grid_x, grid_y, window, triangles, True)

    for h in holes:
        # glClear(GL_COLOR_BUFFER_BIT)
        


        # glBegin(GL_TRIANGLES)
        # for t in triangles:
        #     t.draw_color((1, 0, 0))

        # for t in notRemoveTriangles:
        #     t.draw_color((0, 0, 1))
        # glEnd()

        # glColor3f(0, 0.5, 1)
        # glBegin(GL_LINES)
        # for r in boundaries:
        #     glVertex2f(points[r[0]].point[0], points[r[0]].point[1])
        #     glVertex2f(points[r[1]].point[0], points[r[1]].point[1])
        # glEnd()
        
        # glPointSize(5)
        # glColor3f(0, 0, 0)
        # glBegin(GL_POINTS)
        # glVertex2f(h[0], h[1])
        # glEnd()
        # glPointSize(1)

        # canvas.SwapBuffers()
        # raw_input('press any key')

        found = False
        # for t in triangles:
        #     if pointInTriangle(h, (t.points[0].point, t.points[1].point, t.points[2].point)):
        #         if t in notRemoveTriangles:
        #             found = True
        #         break
        # if not found:
        #     continue

        t = grid.point_in_triangle_acc(h)
        if not t is None:
            if t in notRemoveTriangles:
                found = True
        if not found:
            continue

        queue = collections.deque([t])
        notRemoveTriangles.remove(t)
        while len(queue) > 0:
            tri = queue.popleft()
            

            centroid = getCentroid(tri.points)
            trianglesToTry = []
            for i, p1 in enumerate(tri.points):
                p2 = tri.points[(i+1)%3]
                n1 = p1.composite_point_index
                n2 = p2.composite_point_index
                if not ((n1, n2) in boundarySet or (n2, n1) in boundarySet):
                    for t in pointTriangleMap[p1]:
                        if t in pointTriangleMap[p2]:
                            trianglesToTry.append(t)

                # if p in pointBoundaryMap:
                #     for p2 in pointBoundaryMap[p]:
                #         point1 = p#.point
                #         point2 = points[p2]#.point
                #         if not ((point1, point2) in lines or (point2, point1) in lines):
                #             lines.add((point1, point2))
                
            #for p in tri.points:
            for tri2 in trianglesToTry:
                if tri2 in notRemoveTriangles:
                    notRemoveTriangles.remove(tri2)
                    queue.append(tri2)

    return list(notRemoveTriangles)


class Window:
    def __init__(self, width = None, height = None, zoom_width = None, zoom_height = None, 
                 center_x = None, center_y = None, loadFile = None):
        if not loadFile is None:
            self.load(loadFile)
        else:
            self.width = width
            self.height = height
            self.zoom_width = zoom_width
            self.zoom_height = zoom_height
            self.original_width = width
            self.original_height = height
            self.center_x = center_x
            self.center_y = center_y

    def to_world_coords(self, x, y):
        return ((float(x)/self.width - .5) * self.zoom_width + self.center_x, (.5 - float(y)/self.height) * self.zoom_height + self.center_y)

    def to_window_coords(self, x, y):
        return (((float(x) - self.center_x)/self.zoom_width + .5)*self.width, (.5 - (float(y) - self.center_y)/self.zoom_height)*self.height)

    def save(self, f):
        f.write(str(self.width)+','+str(self.height)+','+
                str(self.zoom_width)+','+str(self.zoom_height)+','+
                str(self.original_width)+','+str(self.original_height)+','+
                str(self.center_x)+','+str(self.center_y)+'\n')

    def load(self, f):
        params = f.readline().split(',')
        self.width = int(params[0])
        self.height = int(params[1])
        self.zoom_width = float(params[2])
        self.zoom_height = float(params[3])
        self.original_width = float(params[4])
        self.original_height = float(params[5])
        self.center_x = float(params[6])
        self.center_y = float(params[7])

class Mouse:
    def __init__(self, loadFile = None):
        if not loadFile is None:
            self.load(loadFile)
        else:
            self.mouseX = 0
            self.mouseY = 0
            self.mouseDown = False

    def save(self, f):
        f.write(str(self.mouseX)+','+str(self.mouseY)+'\n')

    def load(self, f):
        params = f.readline().split(',')
        self.mouseX = int(float(params[0]))
        self.mouseY = int(float(params[1]))



    