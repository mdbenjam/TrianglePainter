__author__ = 'mdbenjam'

from collections import deque
import numpy as np
import triangle
from skimage import measure
from OpenGL.GL import *
from OpenGL.GLUT import *
import copy
import math
import sys
import geometry

class Brush:

    def __init__(self, brush_radius, num_sides, color=(0,0,0,1)):
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
        self.composite_lines = []
        self.brushPoints = []
        self.current_quads = []
        self.color = color
        self.brush_radius = brush_radius
        self.num_sides = num_sides

        self.show_index = 0

        self.make_brush()


    def make_brush(self):
        self.brushPoints = []
        deltaAngle = 2*np.pi/self.num_sides
        angle = np.pi/4.0
        if self.num_sides % 2 == 1:
            angle = -np.pi/2.0

        for i in range(self.num_sides):
            self.brushPoints.append((np.cos(angle)*self.brush_radius, np.sin(angle)*self.brush_radius))
            angle = angle + deltaAngle

    def change_color(self,color):
        self.color = color

    def get_size(self):
        return self.brush_radius

    def set_size(self, brush_radius):
        self.brush_radius = brush_radius
        self.make_brush()

    def draw_cursor(self, mouse):
        glBegin(GL_POLYGON)
        glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])

        for p in self.brushPoints:
            glVertex2f(mouse.mouseX + p[0], mouse.mouseY + p[1])

        glEnd()

    def draw_stroke(self, black=False):
        glBegin(GL_QUADS)
        if black:
            glColor4f(0,0,0,1)
        else:
            glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])

        for q in self.current_quads:
            for p in q:
                glVertex2f(p[0], p[1])

        glEnd()

    def cycle(self, amount):
        self.show_index = (self.show_index + amount) % len(self.composite_points)

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
            index = 0
            for t in self.composite_points:
                if self.show_index == index:
                    glColor3f(0,.4,0)
                    glEnd()
                    glLineWidth(3)
                    glBegin(GL_LINES)
                    length = 10
                    angle1 = t.color_regions[0].start_angle
                    angle2 = t.color_regions[0].end_angle
                    glVertex2f(t.point[0], t.point[1])
                    glVertex2f(t.point[0]+math.cos(angle1)*length, t.point[1]+math.sin(angle1)*length)
                    glVertex2f(t.point[0], t.point[1])
                    glVertex2f(t.point[0]+math.cos(angle2)*length, t.point[1]+math.sin(angle2)*length)
                    glEnd()
                    glLineWidth(1)
                    glBegin(GL_POINTS)
                    glColor3f(0,0,1)
                glVertex2f(t.point[0], t.point[1])
                index = index + 1

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
        self.draw_stroke(black=True)

        width = 640
        height = 480


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

        lines = []
        holes = []
        MAX_ANGLE_DEVIATION = math.pi*25.0/180.0
        DIST_THRESHOLD = .5
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
            last_five_points = []

            for p in c[1:-1]:

                current_count = current_count + 1
                last_points.append(p)
                last_five_points.append(p)
                n = np.array([last_p[0]-p[0], last_p[1]-p[1]])
                n = n/np.linalg.norm(n)
                line_test_failed = False
                for p2 in last_points:
                    vec_to_p = np.array([p[0]-p2[0], p[1]-p2[1]])
                    if np.linalg.norm(vec_to_p-(np.dot(vec_to_p,n)*n)) > DIST_THRESHOLD:
                        line_test_failed = True


                if line_test_failed:
                    self.triangle_points.append((last_points[-1][1], 480-last_points[-1][0]))
                    index = len(self.triangle_points)-1
                    lines.append([index - 1, index])
                    first_angle = None
                    last_angle = None
                    last_p = last_points[-1]
                    current_count = 0
                    last_five_points = []
                    last_points = []


                if current_count >= USE_EVERY:
                    dy = p[1]-last_p[1]
                    dx = p[0]-last_p[0]
                    angle = math.atan2(dy, dx)
                    if first_angle == None:
                        first_angle = angle
                        last_angle = angle
                    else:
                        if ((abs(angle-last_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-last_angle)-2*math.pi) > MAX_ANGLE_DEVIATION) or
                                (abs(angle-first_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-first_angle)-2*math.pi) > MAX_ANGLE_DEVIATION)):
                            for p2 in last_five_points[::2]:
                                dy = p2[1]-last_p[1]
                                dx = p2[0]-last_p[0]
                                angle = math.atan2(dy, dx)
                                if ((abs(angle-last_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-last_angle)-2*math.pi) > MAX_ANGLE_DEVIATION) or
                                        (abs(angle-first_angle) > MAX_ANGLE_DEVIATION and abs(abs(angle-first_angle)-2*math.pi) > MAX_ANGLE_DEVIATION)):
                                    self.triangle_points.append((p2[1], 480-p2[0]))
                                    index = len(self.triangle_points)-1
                                    lines.append([index - 1, index])
                                    if contour_hole == False:
                                        holes.append([(last_p[1]+p2[1])/2.0+math.sin(angle-math.pi/2.0)*r, 480-((last_p[0]+p2[0])/2.0+math.cos(angle-math.pi/2.0)*r)])
                                        contour_hole = True

                            first_angle = None
                            last_angle = None
                    last_p = p
                    current_count = 0
                    last_five_points = []
                    last_points = []
            lines.append([len(self.triangle_points)-1, first_index])


        """
        for p in self.composite_points:
            pixel_color = glReadPixels(p.point[0], 479 - p.point[1], 1, 1, GL_RGBA, GL_FLOAT)
            if pixel_color[0][0][0] == 0:
                p.add_color(self.color)
        """

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

        self.holes = holes_array

        """
        A = dict(vertices = array, segments = line_array, holes = holes_array)
        triangulation = triangle.triangulate(A, 'p')
        delauny_points = triangulation['vertices'][triangulation['triangles']]
        """
        #delauny_points = array[triangle.triangulate (A, 'p q')['triangles']]

        #old_triangles = copy.deepcopy(self.triangle_points)

        starting_value = len(self.composite_points)

        #glutSwapBuffers()
        #glClear(GL_COLOR_BUFFER_BIT)
        #self.draw_triangles(False)

        #glutSwapBuffers()


        #glutSwapBuffers()


        angles = np.empty([len(self.triangle_points), 2])
        for l in lines:
            p1 = self.triangle_points[l[0]]
            p2 = self.triangle_points[l[1]]
            angle = math.atan2(p1[1]-p2[1], p1[0]-p2[0])
            angles[l[0], 0] = (angle + math.pi) % (2*math.pi)
            if angles[l[0], 0] > math.pi:
                angles[l[0], 0] = angles[l[0], 0] - 2*math.pi
            angles[l[1], 1] = angle


        index = 0
        for p in self.triangle_points:
            #pixel_color = glReadPixels(p[0], 479 - p[1], 1, 1, GL_RGBA, GL_FLOAT)[0][0]
            pixel_color = [1, 1, 1, 1]
            for t in self.triangles:
                pts = t.points
                tri = [pts[0].point, pts[1].point, pts[2].point]
                if geometry.pointInTriangle(p, tri):
                    pixel_color = pts[0].get_current_color(geometry.getCentroid(t.points))
                    break
            alpha = self.color[3]
            composite_color = [self.color[0]*alpha + pixel_color[0]*(1-alpha),
                               self.color[1]*alpha + pixel_color[1]*(1-alpha),
                               self.color[2]*alpha + pixel_color[2]*(1-alpha),
                               1]
            regions = [geometry.ColorRegion(composite_color, angles[index,0], angles[index,1]),
                       geometry.ColorRegion(pixel_color, angles[index,1], angles[index,0])]
            t = geometry.TrianglePoint(p,regions)
            self.composite_points.append(t)
            index = index + 1

        for p in self.composite_points[0:starting_value]:
            pixel_color = glReadPixels(p.point[0], 479 - p.point[1], 1, 1, GL_RGBA, GL_FLOAT)[0][0]
            if pixel_color[0] == 0:
                p.composite_color(self.color)

        for l in lines:
            self.composite_lines.append([l[0]+starting_value,l[1]+starting_value])

        verts = np.empty([len(self.composite_points), 2])
        i = 0
        for t in self.composite_points:
            verts[i, 0] = t.point[0]
            verts[i, 1] = t.point[1]

            i = i + 1



        line_array = np.empty([len(self.composite_lines), 2])
        i = 0
        for l in self.composite_lines:
            line_array[i, 0] = l[0]
            line_array[i, 1] = l[1]
            i = i + 1

        A = dict(vertices = verts, segments = line_array, holes = [0, 0])
        triangulation = triangle.triangulate(A, 'p')
        tri_indicies = triangulation['triangles']
        delauny_points = triangulation['vertices']
        segments = triangulation['segments']

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


        #self.draw_stroke()
        self.triangles = []

        graph = []
        marked = []
        all_points = []
        for i in range(len(delauny_points)):
            graph.append([])
            if i < len(self.composite_points):
                all_points.append(self.composite_points[i])
                marked.append(True)
            else:
                all_points.append(None)
                marked.append(False)



        for s in segments:
            graph[s[0]].append(s[1])
            graph[s[1]].append(s[0])


        def color_index(index):
            if marked[index]:
                return

            marked[index] = True
            color_regions = []
            angles = []
            p1 = delauny_points[index]
            for s in graph[index]:
                # Unclear if this is always True. i.e. we might need to search until we find a
                # point that isn't new. It may not always be a point's first neighbor.
                color_reg = []

                p2 = delauny_points[s]

                angles.append((math.atan2(p2[1]-p1[1], p2[0]-p1[0]), all_points[s], (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2, p2))

            print "before ", angles
            angles = sorted(angles, key = lambda a: a[0])
            print "after ", angles

            for i in range(len(angles)):
                i2 = (i + 1) % len(angles)
                if i2 == 0:
                    average = (angles[i][0] + angles[i2][0] + 2*math.pi)/2.0
                    if average > math.pi:
                        average = average - 2*math.pi
                else:
                    average = (angles[i][0] + angles[i2][0])/2.0

                if angles[i][2] > angles[i2][2]:
                    if angles[i][1] is None:
                        point_to_use = angles[i2][1]
                    else:
                        point_to_use = angles[i][1]
                else:
                    if angles[i2][1] is None:
                        point_to_use = angles[i][1]
                    else:
                        point_to_use = angles[i2][1]

                centroid = geometry.getCentroidPoints([p1, angles[i][3], angles[i2][3]])

                color_regions.append(geometry.ColorRegion(point_to_use.get_current_color(centroid), angles[i][0], angles[i2][0]))

                #color_reg.extend(all_points[s].color_regions)
                #print "segs", 0, s
                #for c in color_reg:
                #    print c.color

                #color_regions.extend(color_reg)
            #print len(color_regions)
            #for c in color_regions:
            #    print c.color
            all_points[index] = geometry.TrianglePoint(p1, color_regions)


        for i in range(len(all_points)):
                color_index(i)

        for indices in tri_indicies:
            t = []
            for i in indices:
                t.append(all_points[i])

            self.triangles.append(geometry.Triangle(t))


        print "tri: " + str(len(self.triangles))
        print "quad: " + str(len(self.current_quads))

        self.current_quads = []
        self.save('last_stroke.txt')

        #glBindFramebuffer(GL_FRAMEBUFFER, 0)
        #glDeleteFramebuffers(1, fbo)

    def save(self, out_name):

        f = open(out_name, 'w')
        f.write(str(len(self.composite_points))+'\n')
        for p in self.composite_points:
            p.save(f)

        f.write(str(len(self.composite_lines))+'\n')
        for l in self.composite_lines:
            f.write(str(l[0])+','+str(l[1])+'\n')

        f.write(str(len(self.triangles))+'\n')
        for t in self.triangles:
            t.save(f)
        f.close()

    def load(self, in_name):
        f = open(in_name, 'r')
        self.composite_points = []
        self.composite_lines = []
        self.triangles = []
        num_points = int(f.readline())
        for i in range(num_points):
            self.composite_points.append(geometry.TrianglePoint(file=f))

        num_lines = int(f.readline())
        for i in range(num_lines):
            line = f.readline()
            s = line.split(',')
            self.composite_lines.append([int(s[0]),int(s[1])])

        num_triangles = int(f.readline())
        for i in range(num_triangles):
            self.triangles.append(geometry.Triangle(file=f))

        self.stroke_over = False
        self.clear_stroke()
        self.stroke_over = True
        f.close()
