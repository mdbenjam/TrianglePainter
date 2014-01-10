__author__ = 'mdbenjam'

from OpenGL.GL import *
import math
import numpy as np

class Triangle:
    def __init__(self, points=None,file=None):
        if file == None:
            self.points = points
            self.centroid = getCentroid(self.points)
            self.color = []
            for p in self.points:
                self.color.append(p.get_current_color(self.centroid))
        else:
            self.load(file)

    def draw(self):
        for p in self.points:
            #print 'c'+str(color)
            glColor3f(self.color[0], self.color[1], self.color[2])
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
    def __init__(self, point=None, color_regions=None, file=None):
        if file == None:
            self.point = point
            self.color_regions = color_regions
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

def lineIntersection(self, p1, p2, p3, p4):
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