__author__ = 'mdbenjam'

from collections import deque
import numpy as np
import triangle
from skimage import measure
from OpenGL.GL import *
import copy
import math
import sys
import geometry

class Brush:

    def __init__(self, brushRadius, numSides):
        self.triangle_points = []
        self.last_points = deque([])
        self.last_removed = None
        self.triangles = []
        self.lastMouse = None
        self.stroke_over = False
        self.contours = []
        self.boundary = None
        self.arrayPoints = None
        self.holes = None
        self.composite_points = []
        self.brushPoints = []
        self.current_quads = []


        deltaAngle = 2*np.pi/numSides
        angle = np.pi/4.0
        if numSides % 2 == 1:
            angle = -np.pi/2.0

        for i in range(numSides):
            self.brushPoints.append((np.cos(angle)*brushRadius, np.sin(angle)*brushRadius))
            angle = angle + deltaAngle

    def draw_cursor(self, mouse):
        glBegin(GL_POLYGON)
        glColor3f(0,0,0)

        for p in self.brushPoints:
            glVertex2f(mouse.mouseX + p[0], mouse.mouseY + p[1])

        glEnd()

    def draw_stroke(self):
        glBegin(GL_QUADS)
        if not self.stroke_over:
            glColor3f(0,0,0)

        for q in self.current_quads:
            for p in q:
                glVertex2f(p[0], p[1])

        glEnd()

    def draw_triangles(self, flag):
        glBegin(GL_TRIANGLES)
        for t in self.triangles:
            t.draw()
        glEnd()

        if flag:
            """
            glLineWidth(3.0)
            glBegin(GL_LINES)
            glColor3f(0,0,1)
            for t in self.triangle_points:
                t.draw()

            glEnd()
            glLineWidth(1.0)
            """

            for t in self.triangles:
                glBegin(GL_LINE_LOOP)
                t.draw_color((1,0,0))
                glEnd()



            glPointSize(3.0)
            glBegin(GL_POINTS)
            glColor3f(0,0,1)
            for t in self.triangle_points:
                glVertex2f(t[0], t[1])

            glEnd()
            glPointSize(1.0)

            glPointSize(3.0)
            glBegin(GL_POINTS)
            glColor3f(1,0,1)
            for h in self.holes:
                glVertex2f(h[0], h[1])
            glEnd()
            glPointSize(1.0)

            """
            glPointSize(3.0)
            glBegin(GL_POINTS)
            glColor3f(0,0,1)
            for p in self.arrayPoints:
                glVertex2f(p[0], p[1])
            glEnd()
            glPointSize(1.0)

            glLineWidth(3.0)
            glBegin(GL_LINES)
            glColor3f(1,0,0)
            for b in self.boundary:
                p1 = self.arrayPoints[b[0]]
                p2 = self.arrayPoints[b[1]]
                glVertex2f(p1[0], p1[1])
                glVertex2f(p2[0], p2[1])

            glEnd()
            glLineWidth(1.0)
            """

    def draw_contours(self):
        glPointSize(3.0)
        glBegin(GL_POINTS)
        glColor3f(1,0,0)
        for c in self.contours:
            for p in c:
                #TODO CHANGE 480
                glVertex2f(p[1], 480-p[0])

        glEnd()
        glPointSize(1.0)

    def new_stroke(self, mouse):
        #self.triangles = []
        self.triangle_points = []
        self.last_points = deque([])
        self.current_quads = []
        self.currentPolys = []
        self.stroke_over = False
        points = []
        count = 0
        for p in self.brushPoints:
            count = count + 1
            point = (mouse.mouseX + p[0], mouse.mouseY + p[1])
            #self.addNotCoveredPoint(point, count==len(self.brushPoints))
            points.append(point)
        self.current_quads.append(points)
        self.lastMouse = copy.deepcopy(mouse)



    def stamp(self, mouse):
        if self.lastMouse != None:
            quad = []

            """
            for i in range(len(self.brushPoints)):
                nextI = (i + 1) % len(self.brushPoints)
                x1 = self.brushPoints[i][0]
                y1 = self.brushPoints[i][1]
                point = (mouse.mouseX + x1, mouse.mouseY + y1)
                self.addNotCoveredPoint(point, i == len(self.brushPoints)-1)
            """

            for i in range(len(self.brushPoints)):
                nextI = (i + 1) % len(self.brushPoints)
                x1 = self.brushPoints[i][0]
                y1 = self.brushPoints[i][1]
                x2 = self.brushPoints[nextI][0]
                y2 = self.brushPoints[nextI][1]
                points = [(self.lastMouse.mouseX + x1, self.lastMouse.mouseY + y1),
                            (mouse.mouseX + x1, mouse.mouseY + y1),
                            (mouse.mouseX + x2, mouse.mouseY + y2),
                            (self.lastMouse.mouseX + x2, self.lastMouse.mouseY + y2)]
                self.current_quads.append(points)

            #TODO: Make this general for any poly brush
            """
            points = []
            for i in range(len(self.brushPoints)):
                points.append((mouse.mouseX + self.brushPoints[i][0], mouse.mouseY + self.brushPoints[i][1]))
            self.current_quads.append(points)
            self.removeCoverdPoint(points)
            """

        self.lastMouse = copy.deepcopy(mouse)


    def clear_stroke(self):

        #fbo = glGenFramebuffers(1)
        #glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        #glDisable(GL_DEPTH_TEST)
        #glClearColor(1.0, 1.0, 1.0, 1.0)
        #TODO: REMOVE 480
        #glViewport(0, 0, 640, 480)
        glClear(GL_COLOR_BUFFER_BIT)
        self.draw_stroke()

        width = 640
        height = 480

        """
        points = []
        if self.lastMouse != None:
            count = 0
            for p in self.brushPoints:
                count = count + 1
                point = (self.lastMouse.mouseX + p[0], self.lastMouse.mouseY + p[1])
                self.addNotCoveredPoint(point, count == len(self.brushPoints))
                points.append(point)
            self.removeCoverdPoint(points)
        """

        self.lastMouse = None

        #self.triangle_points = []
        lines = []


        values = glReadPixels(0, 0, width, width, GL_RGBA, GL_FLOAT)
        rvalues = np.ones([height, width])
        for i in range(height):
            for j in range(width):
                rvalues[i, j] = values[i, j, 0]
        #print self.values.shape
        self.contours = measure.find_contours(rvalues[:,:], .5)
        self.triangle_points = []
        """
        lines = []
        MAX_ANGLE_DEVIATION = math.pi*20.0/180.0
        for c in self.contours:
            if len(c) < 2:
                continue
            self.triangle_points.append(c[0])
            last_p = c[0]
            last_angle = None
            first_angle = None
            #TODO: REMOVE 480
            self.triangle_points.append((last_p[1], 480-last_p[0]))
            first_index = len(self.triangle_points)

            #TODO: Check for closed
            for p in c[1:-1]:
                dy = p[1]-last_p[1]
                dx = p[0]-last_p[0]
                angle = math.atan2(dy, dx)
                if first_angle == None:
                    first_angle = angle
                    last_angle = angle
                else:
                    if ((abs(angle-last_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-last_angle)-2*math.pi) > MAX_ANGLE_DEVIATION) or
                            (abs(angle-first_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-first_angle)-2*math.pi) > MAX_ANGLE_DEVIATION)):
                        first_angle = None
                        last_angle = None
                        self.triangle_points.append((p[1], 480-p[0]))
                        index = len(self.triangle_points)
                        lines.append([index - 1, index])
                last_p = p
            lines.append([len(self.triangle_points), first_index])
        """
        lines = []
        holes = []
        MAX_ANGLE_DEVIATION = math.pi*5.0/180.0
        for c in self.contours:
            if len(c) < 2:
                continue
            last_p = c[0]

            r = .5
            contour_hole = False

            last_angle = None
            first_angle = None
            #TODO: REMOVE 480
            self.triangle_points.append((last_p[1], 480-last_p[0]))
            first_index = len(self.triangle_points)-1

            #TODO: Check for closed
            USE_EVERY = 5
            current_count = 0
            last_points = []
            for p in c[1:-1]:

                current_count = current_count + 1
                last_points.append(p)
                if current_count >= 5:
                    dy = p[1]-last_p[1]
                    dx = p[0]-last_p[0]
                    angle = math.atan2(dy, dx)
                    if first_angle == None:
                        first_angle = angle
                        last_angle = angle
                    else:
                        if ((abs(angle-last_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-last_angle)-2*math.pi) > MAX_ANGLE_DEVIATION) or
                                (abs(angle-first_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-first_angle)-2*math.pi) > MAX_ANGLE_DEVIATION)):
                            for p2 in last_points[::2]:
                                dy = p2[1]-last_p[1]
                                dx = p2[0]-last_p[0]
                                angle = math.atan2(dy, dx)
                                if ((abs(angle-last_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-last_angle)-2*math.pi) > MAX_ANGLE_DEVIATION) or
                                        (abs(angle-first_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-first_angle)-2*math.pi) > MAX_ANGLE_DEVIATION)):
                                    self.triangle_points.append((p2[1], 480-p2[0]))
                                    index = len(self.triangle_points)-1
                                    lines.append([index - 1, index])
                                    if contour_hole == False:
                                        print "sin "+str(math.sin(angle-math.pi/2.0))
                                        holes.append([(last_p[1]+p2[1])/2.0+math.sin(angle-math.pi/2.0)*r, 480-((last_p[0]+p2[0])/2.0+math.cos(angle-math.pi/2.0)*r)])
                                        contour_hole = True

                            first_angle = None
                            last_angle = None
                    last_p = p
                    current_count = 0
                    last_points = []
            lines.append([len(self.triangle_points)-1, first_index])


        #print self.contours
        #x, y = np.ogrid[-np.pi:np.pi:480j, -np.pi:np.pi:480j]
        #self.values = np.sin(np.exp((np.sin(x)**3 + np.cos(y)**2)))
        #print self.values.shape

        # Find contours at a constant value of 0.8
        #self.contours = measure.find_contours(self.values, 0.8)

        """
        lastT = None
        for t in self.triangle_points:
            if t.isValid and lastT != None and lastT.isValid:
                if t.next == None and lastT.prev == None:
                    t.next = lastT
                    lastT.prev = t
                if t.prev == None and lastT.next == None:
                    t.prev = lastT
                    lastT.next = t
            lastT = t

        """

        line_array = np.empty([len(lines), 2])
        i = 0
        for l in lines:
            line_array[i, 0] = l[0]
            line_array[i, 1] = l[1]
            i = i + 1


        holes_array = np.empty([len(holes), 2])
        i = 0
        for h in holes:
            holes_array[i, 0] = h[0]
            holes_array[i, 1] = h[1]
            i = i + 1

        array = np.empty([len(self.triangle_points), 2])
        i = 0
        for t in self.triangle_points:
            array[i, 0] = t[0]
            array[i, 1] = t[1]
            i = i + 1

        self.boundary = line_array
        self.arrayPoints = array

        print holes_array
        self.holes = holes_array

        A = dict(vertices = array, segments = line_array, holes = holes_array)
        triangulation = triangle.triangulate(A, 'p')
        delauny_points = triangulation['vertices'][triangulation['triangles']]
        #delauny_points = array[triangle.triangulate (A, 'p q')['triangles']]
        for t in delauny_points:
            sum_x = 0
            sum_y = 0
            for p in t:
                sum_x = sum_x + p[0]
                sum_y = sum_y + p[1]
            # TODO: ELIMINATE 480!
            colors = glReadPixels(sum_x/3, 479 - sum_y/3, 1, 1, GL_RGBA, GL_FLOAT)
            print colors[0][0]

            for p in t:
                self.composite_points.append(geometry.TrianglePoint(p,colors[0][0]))

        verts = np.empty([len(self.composite_points), 2])
        colors = np.empty([len(self.composite_points), 4])
        i = 0
        for t in self.composite_points:
            verts[i, 0] = t.point[0]
            verts[i, 1] = t.point[1]
            colors[i, 0] = t.color[0]
            colors[i, 1] = t.color[1]
            colors[i, 2] = t.color[2]
            colors[i, 3] = t.color[3]
            i = i + 1

        A = dict(vertices = verts)
        triangulation = triangle.triangulate(A)
        delauny_points = verts[triangulation['triangles']]
        delauny_colors = colors[triangulation['triangles']]
        """
        for t in delauny_points:
            sum_x = 0
            sum_y = 0
            for p in t:
                sum_x = sum_x + p[0]
                sum_y = sum_y + p[1]

            # TODO: ELIMINATE 480!
            colors = glReadPixels(sum_x/3, 479 - sum_y/3, 1, 1, GL_RGBA, GL_FLOAT)

            self.triangles.append(Triangle(t, [[0,0,0],[0,0,0],[0,0,0]]))#[colors[0][0], colors[0][0], colors[0][0]]))
        """
        self.triangles = []
        print "Here1"
        for t, tc in zip(delauny_points,delauny_colors):
            sum_x = 0
            sum_y = 0
            for p in t:
                sum_x = sum_x + p[0]
                sum_y = sum_y + p[1]


            # TODO: ELIMINATE 480!
            colors = glReadPixels(sum_x/3, 479 - sum_y/3, 1, 1, GL_RGBA, GL_FLOAT)
            tri = []
            for p, c in zip(t,tc):
                tri.append(geometry.TrianglePoint(p,c))

            self.triangles.append(geometry.Triangle(tri))


        print "tri: " + str(len(self.triangles))
        print "quad: " + str(len(self.current_quads))

        #glBindFramebuffer(GL_FRAMEBUFFER, 0)
        #glDeleteFramebuffers(1, fbo)

    def save(self, f):
        for q in self.current_quads:
            for p in q:
                f.write(str(p[0])+':'+str(p[1])+', ')
            f.write('\n')

    def load(self, f):
        self.current_quads = []
        self.triangles = []
        for l in f:
            s = l.split(',')
            points = []
            count = 0
            for p in s:
                count = count + 1
                if count > 4:
                    break
                i = p.split(':')
                print i
                points.append((float(i[0]), float(i[1])))
            self.current_quads.append(points)

        glClear(GL_COLOR_BUFFER_BIT)
        self.stroke_over = False
        self.draw_stroke()
        self.clear_stroke()
        self.stroke_over = True
