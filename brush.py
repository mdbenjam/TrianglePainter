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

    def __init__(self, brush_radius, num_sides, window, color=(0,0,0,1), fall_off_radius=0):
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
        self.current_quads = []
        self.fall_off_current_quads = []
        self.color = color
        self.brush_radius = brush_radius
        self.fall_off_radius = fall_off_radius
        self.num_sides = num_sides
        self.bad_points = []

        self.show_index = 0

        self.brushPoints = self.make_brush(self.num_sides, self.brush_radius)
        self.fall_off_brush_points = self.make_brush(self.num_sides, self.fall_off_radius)

        self.window = window


    def make_brush(self, num_sides, brush_radius):
        brushPoints = []
        deltaAngle = 2*np.pi/num_sides
        angle = np.pi/4.0
        if num_sides % 2 == 1:
            angle = -np.pi/2.0

        for i in range(num_sides):
            brushPoints.append((np.cos(angle)*brush_radius, np.sin(angle)*brush_radius))
            angle = angle + deltaAngle

        return brushPoints

    def change_color(self,color):
        self.color = color

    def get_size(self):
        return self.brush_radius

    def set_size(self, brush_radius, fall_off_radius):
        self.brush_radius = brush_radius
        self.fall_off_radius = fall_off_radius
        self.brushPoints = self.make_brush(self.num_sides, self.brush_radius)
        self.fall_off_brush_points = self.make_brush(self.num_sides, self.fall_off_radius)

    def draw_cursor(self, mouse, window):
        (x, y) = window.to_world_coords(float(mouse.mouseX), float(mouse.mouseY))
        glBegin(GL_POLYGON)
        glColor4f(self.color[0]*2, self.color[1]*2, self.color[2]*2, self.color[3])
        for p in self.fall_off_brush_points:
            glVertex2f(x + p[0], y + p[1])

        glEnd()

        glBegin(GL_POLYGON)
        glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])

        for p in self.brushPoints:
            glVertex2f(x + p[0], y + p[1])
        glEnd()



    def draw_stroke(self, black=False):
        glBegin(GL_QUADS)
        if black:
            glColor4f(.5,.5,.5,1)
        else:
            glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])

        for q in self.fall_off_current_quads:
            for p in q:
                glVertex2f(p[0], p[1])

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
        print self.show_index

    def draw_triangles(self, flag):
        glBegin(GL_TRIANGLES)
        for t in self.triangles:
            t.draw()
        glEnd()

        glPointSize(3.0)
        glBegin(GL_POINTS)
        glColor3f(1,0,0)
        for p in self.bad_points:
            glVertex2f(p[0], p[1])
        glEnd()
        glPointSize(1.0)

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

    def new_stroke(self, mouse, window):
        #self.triangles = []
        self.triangle_points = []
        self.last_points = deque([])
        self.current_quads = []
        self.fall_off_current_quads = []
        self.currentPolys = []
        self.stroke_over = False
        points = []
        count = 0
        zoom = window.width/window.zoom_width
        for p in self.brushPoints:
            count = count + 1
            point = window.to_world_coords(mouse.mouseX + p[0]*zoom, mouse.mouseY + p[1]*zoom)
            #self.addNotCoveredPoint(point, count==len(self.brushPoints))
            points.append(point)
        self.current_quads.append(points)
        self.lastMouse = copy.deepcopy(mouse)



    def stamp(self, mouse, window):
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
            zoom = window.width/window.zoom_width

            def make_quads(brush_points, current_quads):
                for i in range(len(self.brushPoints)):
                    nextI = (i + 1) % len(brush_points)
                    x1 = brush_points[i][0]*zoom
                    y1 = brush_points[i][1]*zoom
                    x2 = brush_points[nextI][0]*zoom
                    y2 = brush_points[nextI][1]*zoom
                    points = [window.to_world_coords(self.lastMouse.mouseX + x1, self.lastMouse.mouseY + y1),
                                window.to_world_coords(mouse.mouseX + x1, mouse.mouseY + y1),
                                window.to_world_coords(mouse.mouseX + x2, mouse.mouseY + y2),
                                window.to_world_coords(self.lastMouse.mouseX + x2, self.lastMouse.mouseY + y2)]
                    current_quads.append(points)

            make_quads(self.brushPoints, self.current_quads)
            make_quads(self.fall_off_brush_points, self.fall_off_current_quads)

            #TODO: Make this general for any poly brush
            """
            points = []
            for i in range(len(self.brushPoints)):
                points.append((mouse.mouseX + self.brushPoints[i][0], mouse.mouseY + self.brushPoints[i][1]))
            self.current_quads.append(points)
            self.removeCoverdPoint(points)
            """

        self.lastMouse = copy.deepcopy(mouse)




    def clear_stroke(self, window):

        #fbo = glGenFramebuffers(1)
        #glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        #glDisable(GL_DEPTH_TEST)
        #glClearColor(1.0, 1.0, 1.0, 1.0)
        #TODO: REMOVE 480
        #glViewport(0, 0, 640, 480)
        self.save_action('hold.txt')
        glClear(GL_COLOR_BUFFER_BIT)
        self.draw_stroke(black=True)

        width = window.width
        height = window.height

        self.lastMouse = None

        #self.triangle_points = []
        lines = []


        values = glReadPixels(0, 0, width, width, GL_RGBA, GL_FLOAT)
        rvalues = np.ones([height, width])
        for i in range(height):
            for j in range(width):
                rvalues[i, j] = values[i, j, 0]
        #print self.values.shape
        self.triangle_points = []

        lines = []
        holes = []
        MAX_ANGLE_DEVIATION = math.pi*25.0/180.0
        DIST_THRESHOLD = .5

        def prune_points(contour):
            for i in range(len(contour)):
                for j in range(len(contour[i])):
                    (contour[i][j][0], contour[i][j][1]) = window.to_world_coords(contour[i][j][1], window.height - contour[i][j][0])


            for c in contour:
                if len(c) < 2:
                    continue
                last_p = c[0]

                r = .5
                contour_hole = False

                last_angle = None
                first_angle = None
                #TODO: REMOVE 480
                self.triangle_points.append((last_p[0], last_p[1]))
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
                        self.triangle_points.append((last_points[-1][0], last_points[-1][1]))
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
                                        self.triangle_points.append((p2[0], p2[1]))
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

        if self.fall_off_radius == 0:
            self.contours = measure.find_contours(rvalues[:,:], .5)
            prune_points(self.contours)
        else:
            self.contours = measure.find_contours(rvalues[:,:], .25)
            prune_points(self.contours)
            size_of_core = len(self.triangle_points)
            self.contours = (measure.find_contours(rvalues[:,:], .75))
            prune_points(self.contours)

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

        A = dict(vertices = array, segments = line_array)#, holes = holes_array)
        triangulation = triangle.triangulate(A, 'p')
        first_triangle_indicies = triangulation['triangles']
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
            angles[l[0], 1] = (angle + math.pi) % (2*math.pi)
            if angles[l[0], 1] > math.pi:
                angles[l[0], 1] = angles[l[0], 1] - 2*math.pi
            angles[l[1], 0] = angle


        index = 0
        for p in self.triangle_points:
            #pixel_color = glReadPixels(p[0], 479 - p[1], 1, 1, GL_RGBA, GL_FLOAT)[0][0]
            pixel_color = [1, 1, 1, 0]
            for t in self.triangles:
                pts = t.points
                tri = [pts[0].point, pts[1].point, pts[2].point]
                if geometry.pointInTriangle(p, tri):
                    pixel_color = t.get_color_at_point(p)
                    break
            alpha = self.color[3]

            composite_color = [self.color[0]*alpha + pixel_color[0]*(1-alpha),
                               self.color[1]*alpha + pixel_color[1]*(1-alpha),
                               self.color[2]*alpha + pixel_color[2]*(1-alpha),
                               1]

            if self.fall_off_radius == 0:
                regions = [geometry.ColorRegion(composite_color, angles[index,0], angles[index,1]),
                           geometry.ColorRegion(pixel_color, angles[index,1], angles[index,0])]
            else:
                if index < size_of_core:
                    regions = [geometry.ColorRegion(composite_color, 0, 2*math.pi)]
                else:
                    regions = [geometry.ColorRegion(pixel_color, 0, 2*math.pi)]

            t = geometry.TrianglePoint(p,regions)
            self.composite_points.append(t)
            index = index + 1

        glClear(GL_COLOR_BUFFER_BIT)
        glBegin(GL_TRIANGLES)
        glColor4f(0,0,0,1)

        for t in triangulation['vertices'][first_triangle_indicies]:
            for p in t:
                glVertex2f(p[0], p[1])

        glEnd()

        for p in self.composite_points[0:starting_value]:
            (windowx, windowy) = window.to_window_coords(p.point[0], p.point[1])
            pixel_color = glReadPixels(windowx-1.5, height - 1.5 - windowy , 3, 3, GL_RGBA, GL_FLOAT)
            sum = 0
            for i in range(3):
                for j in range(3):
                    sum += pixel_color[i][j][0]
            if sum == 0:
                p.composite_color(self.color)
            else:
                if sum < 9:
                    for i in first_triangle_indicies:
                        t = triangulation['vertices'][i]
                        if geometry.pointInTriangle(p.point, t):
                            t2 = []
                            for j in range(len(i)):
                                t2.append(self.composite_points[starting_value+i[j]])
                            tri = geometry.Triangle(t2)
                            #p.composite_color(tri.get_color_at_point(p.point))
                            p.composite_color(self.color)
                            """
                            centroid = geometry.getCentroidPoints(t)
                            angle = math.atan2(centroid[1]-t[0][1], centroid[0]-t[0][0])
                            r = self.composite_points[starting_value+i[0]].color_regions[0]
                            if (r.start_angle <= angle <= r.end_angle or
                                (r.end_angle < r.start_angle and
                                (r.start_angle <= angle+2*math.pi <= r.end_angle+2*math.pi or
                                 r.start_angle <= angle <= r.end_angle+2*math.pi))):
                            #if (glReadPixels(centroid[0], height - centroid[1], 1, 1, GL_RGBA, GL_FLOAT)[0][0][0] == 0):
                                p.composite_color(self.color)
                                break
                            """


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

        A = dict(vertices = verts, segments = line_array)
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



        """
        for s in segments:
            graph[s[0]].append(s[1])
            graph[s[1]].append(s[0])


        bad_points = []

        def color_index(index):
            if marked[index]:
                return

            marked[index] = True
            color_regions = []
            angles = []
            p1 = delauny_points[index]
            for s in graph[index]:

                color_reg = []

                p2 = delauny_points[s]

                angle = math.atan2(p2[1]-p1[1], p2[0]-p1[0])
                print 'first_angle', angle
                i = s
                while all_points[i] is None:
                    angle2 = []
                    for b in graph[i]:
                        p3 = delauny_points[b]
                        hold = math.atan2(p3[1]-p1[1], p3[0]-p1[0])
                        print 'next_angle', hold
                        angle2.append(abs(hold-angle))
                    min_angle = angle2[0]
                    min_index = 0
                    for a in range(1,len(angle2)):
                        if angle2[a] < min_angle:
                            min_angle = angle2[a]
                            min_index = a
                    i = min_index
                    print 'chose', i

                angles.append((angle, all_points[i], (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2, delauny_points[i], i))

            angles = sorted(angles, key = lambda a: a[0])

            for i in range(len(angles)):
                i2 = (i + 1) % len(angles)
                if i2 == 0:
                    average = (angles[i][0] + angles[i2][0] + 2*math.pi)/2.0
                    if average > math.pi:
                        average = average - 2*math.pi
                else:
                    average = (angles[i][0] + angles[i2][0])/2.0


                centroid = geometry.getCentroidPoints([p1, angles[i][3], angles[i2][3]])#[(p1[0] + other_point[0])/2.0, (p1[1]+other_point[1])/2.0]
                #print 1,p1, angles[i][3], angles[i2][3]
                #print 2,centroid, point_to_use.point
                #print 3,point_to_use.get_current_color(centroid)

                color_regions.append(geometry.ColorRegion(angles[i][1].get_current_color(centroid), angles[i][0], angles[i2][0]))

                #color_reg.extend(all_points[s].color_regions)
                #print "segs", 0, s
                #for c in color_reg:
                #    print c.color

                #color_regions.extend(color_reg)
            #print len(color_regions)
            #for c in color_regions:
            #    print c.color
            all_points[index] = geometry.TrianglePoint(p1, color_regions)
            print "index", index
        """
        for t in tri_indicies:
            graph[t[0]].append(t[1])
            graph[t[0]].append(t[2])
            graph[t[1]].append(t[0])
            graph[t[1]].append(t[2])
            graph[t[2]].append(t[1])
            graph[t[2]].append(t[0])


        bad_points = []

        def color_index(index):
            if marked[index]:
                return

            marked[index] = True
            color_regions = []
            angles = []
            p1 = delauny_points[index]
            for s in graph[index]:

                color_reg = []

                p2 = delauny_points[s]

                angles.append((math.atan2(p2[1]-p1[1], p2[0]-p1[0]), all_points[s], (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2, p2, p2))

            angles = sorted(angles, key = lambda a: a[0])

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
                        other_point = angles[i][3]
                    else:
                        point_to_use = angles[i][1]
                        other_point = angles[i2][3]
                else:
                    if angles[i2][1] is None:
                        point_to_use = angles[i][1]
                        other_point = angles[i2][3]
                    else:
                        point_to_use = angles[i2][1]
                        other_point = angles[i][3]

                if point_to_use is None:
                    print "FAILURE HERE", angles[i2][1], angles[i][1]
                    bad_points.append(p1)
                    continue

                centroid = geometry.getCentroidPoints([p1, angles[i][3], angles[i2][3]])#[(p1[0] + other_point[0])/2.0, (p1[1]+other_point[1])/2.0]
                #print 1,p1, angles[i][3], angles[i2][3]
                #print 2,centroid, point_to_use.point
                #print 3,point_to_use.get_current_color(centroid)

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


        for i in range(len(self.composite_points), len(all_points)):
                color_index(i)

        self.bad_points = bad_points

        for indices in tri_indicies:
            t = []
            for i in indices:
                t.append(all_points[i])

            self.triangles.append(geometry.Triangle(t))

        #self.composite_points = all_points

        print "tri: " + str(len(self.triangles))
        print "quad: " + str(len(self.current_quads))

        self.current_quads = []
        self.fall_off_current_quads = []
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

    def load(self, in_name, window):
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
        self.clear_stroke(window)
        self.stroke_over = True
        f.close()

    def save_action(self, out_name):
        self.save(out_name)

        f = open(out_name, 'a')
        f.write(str(len(self.current_quads))+'\n')
        f.write(str(self.color[0])+','+str(self.color[1])+','+str(self.color[2])+','+str(self.color[3])+'\n')
        for q in self.current_quads:
            for p in q:
                f.write(str(p[0]) + ',' + str(p[1])+'\n')

        f.close()

    def load_action(self, in_name, window):
        f = open(in_name, 'r')
        self.composite_points = []
        self.composite_lines = []
        self.triangles = []
        self.current_quads = []
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

        num_quads = int(f.readline())
        color = f.readline().split(',')
        self.color = [float(color[0]), float(color[1]), float(color[2]), float(color[3])]
        for i in range(num_quads):
            q = []
            for j in range(4):
                line = f.readline()
                s = line.split(',')
                q.append([float(s[0]), float(s[1])])
            self.current_quads.append(q)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(window.center_x - (window.zoom_width / 2.0),
                window.center_x + (window.zoom_width / 2.0),
                window.center_y - (window.zoom_height / 2.0),
                window.center_y + (window.zoom_height / 2.0),
                -1,
                1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.stroke_over = False
        self.clear_stroke(window)
        self.stroke_over = True
        f.close()