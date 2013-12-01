__author__ = 'mdbenjam'

from OpenGL.GL import *

class Triangle:
    def __init__(self, points=None,file=None):
        if file == None:
            self.points = points
        else:
            self.load(file)

    def draw(self):
        for p in self.points:
            color = p.get_current_color()
            #print 'c'+str(color)
            glColor3f(color[0], color[1], color[2])
            glVertex2f(p.point[0], p.point[1])

    def draw_color(self, color):
        for p in self.points:
            glColor3f(color[0], color[1], color[2])
            glVertex2f(p.point[0], p.point[1])

    def save(self, f):
        for p in self.points:
            p.save(f)

    def load(self, f):
        self.points = []
        for i in range(3):
            self.points.append(TrianglePoint(file=f))

class TrianglePoint:
    def __init__(self, point=None, colors=None, file=None):
        if file == None:
            self.point = point
            self.colors = []
            if len(colors[0]) == 1:
                self.colors.append([colors])
            else:
                self.colors.append(colors[0])
                for c in colors[1:]:
                    self.add_color(c)
        else:
            self.load(file)



    def add_color(self, color):
        final_color = [0, 0, 0, 0]
        alpha2 = color[3]
        for i in range(3):
            final_color[i] = self.colors[-1][i]*(1-alpha2) + color[i]*alpha2
        final_color[3] = 1

        self.colors.append(color)
        self.colors.append(final_color)

    def get_current_color(self):
        return self.colors[-1]

    def save(self, f):
        f.write(str(self.point[0])+','+str(self.point[1]))
        f.write(':')
        f.write(str(self.colors[0, 0])+','+
                    str(self.colors[0, 1])+','+
                    str(self.colors[0, 2])+','+
                    str(self.colors[0, 3]))
        f.write('\n')

    def load(self, f):
        line = f.readline()
        s = line.split(':')
        point = s[0].split(',')
        color = s[1].split(',')
        self.point = [float(point[0]), float(point[1])]
        self.colors = []
        self.colors.append([float(color[0]), float(color[1]), float(color[2]), float(color[3])])

def pointInQuad(self, p, quad):
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