__author__ = 'mdbenjam'

from collections import deque
import numpy as np
import triangle
import marchingsquares
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
import copy
import math
import sys
import geometry
#from profilehooks import profile
import time
import random
import threading
import shutil
import os.path
import stroke
import canvas as triangleCanvas

debug = True

def debug_print(msg):
    if 0:
        for m in msg:
            print m,
        print

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
        self.composite_points = []
        self.delauny_points = []
        self.composite_lines = []
        self.current_quads = []
        self.fall_off_current_quads = []
        self.current_poly = []
        self.fall_off_current_poly = []
        self.color = color
        self.brush_radius = brush_radius
        self.hardness = fall_off_radius
        self.num_sides = num_sides
        self.colored_points = []
        self.point_data = []
        
        self.whereInUndoStack = 0
        self.undoData = deque()

        self.triangle_vertices_vbo = None
        self.minXValue = 0
        self.maxXValue = 0
        self.minYValue = 0
        self.maxYValue = 0

        self.renderLock = threading.Lock()

        self.show_index = 0

        self.update_brushes()

        self.window = window

        range = [geometry.ColorRegion((1, 1, 1, 1), [1, 0], [1, 0])]

        self.composite_points.append(geometry.TrianglePoint([window.center_x-window.zoom_width/2, window.center_y-window.zoom_height/2], range, 0))
        self.composite_points.append(geometry.TrianglePoint([window.center_x+window.zoom_width/2-1, window.center_y-window.zoom_height/2], range, 1))
        self.composite_points.append(geometry.TrianglePoint([window.center_x+window.zoom_width/2-1, window.center_y+window.zoom_height/2-1], range, 2))
        self.composite_points.append(geometry.TrianglePoint([window.center_x-window.zoom_width/2, window.center_y+window.zoom_height/2-1], range, 3))

        self.composite_lines.append((0, 1))
        self.composite_lines.append((1, 2))
        self.composite_lines.append((2, 3))
        self.composite_lines.append((3, 0))

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
        self.delauny_points.extend(delauny_points)

        for indices in tri_indicies:
            t = []
            for i in indices:
                t.append(self.composite_points[i])
            self.triangles.append(geometry.Triangle(t))

        self.setup_vbo()

        self.undoData.append(triangleCanvas.Canvas(self.composite_points, self.composite_lines, self.triangles, self.delauny_points, self.point_data))

        if os.path.isfile('out_record.rec'):
            shutil.move('out_record.rec', 'current_record.rec')
        if os.path.isfile('current_record.rec'):
            self.open_record('current_record.rec')

    def update_brushes(self):
        self.brushPoints, extremes2 = self.make_brush(self.num_sides, self.hardness*self.brush_radius)
        self.fall_off_brush_points, extremes = self.make_brush(self.num_sides, self.brush_radius)

        self.minXValue = extremes[0]
        self.maxXValue = extremes[1]
        self.minYValue = extremes[2]
        self.maxYValue = extremes[3]

    def make_brush(self, num_sides, brush_radius):
        brushPoints = []
        deltaAngle = 2*np.pi/num_sides
        angle = np.pi/4.0
        if num_sides % 2 == 1:
            angle = -np.pi/2.0

        minX = sys.maxint
        minY = sys.maxint
        maxX = - sys.maxint
        maxY = - sys.maxint
        for i in range(num_sides):
            x, y = (np.cos(angle)*brush_radius, np.sin(angle)*brush_radius)
            if x < minX:
                minX = x
            if x > maxX:
                maxX = x
            if y < minY:
                minY = y
            if y > maxY:
                maxY = y
            brushPoints.append((x, y))
            angle = angle + deltaAngle

        return brushPoints, (minX, maxX, minY, maxY)

    def undo(self, redo = -1):
        self.whereInUndoStack += redo

        if self.whereInUndoStack < 0:
            self.whereInUndoStack = 0
        if self.whereInUndoStack >= len(self.undoData):
            self.whereInUndoStack = len(self.undoData) - 1

        debug_print(['where in undo stack', self.whereInUndoStack])

        currentCanvas = self.undoData[self.whereInUndoStack]
        self.composite_points = currentCanvas.composite_points
        self.composite_lines = currentCanvas.composite_lines
        self.triangles = currentCanvas.triangles
        self.delauny_points = currentCanvas.delauny_points
        self.point_data = currentCanvas.point_data
        debug_print(['points', self.composite_points])
        self.setup_vbo()

    def change_color(self,color):
        self.color = color

    def get_size(self):
        return self.brush_radius

    def set_size(self, brush_radius, hardness):
        self.brush_radius = brush_radius
        self.hardness = hardness
        self.update_brushes()

    def set_sides(self, num_sides):
        self.num_sides = num_sides
        debug_print(['num_sides', self.num_sides])
        self.update_brushes()

    def validateBrushLocation(self, (x, y), window):
        if x + self.maxXValue > window.center_x + window.zoom_width/2 - 1:
            x = window.center_x + window.zoom_width/2 - self.maxXValue - 1
        if x + self.minXValue < window.center_x - window.zoom_width/2 + 1:
            x = window.center_x - window.zoom_width/2 - self.minXValue + 1
        if y + self.maxYValue > window.center_y + window.zoom_height/2 - 1:
            y = window.center_y + window.zoom_height/2 - self.maxYValue - 1
        if y + self.minYValue < window.center_y - window.zoom_height/2 + 1:
            y = window.center_y - window.zoom_height/2 - self.minYValue + 1
        return (x, y)

    def draw_cursor(self, mouse, window):
        (x, y) = window.to_world_coords(float(mouse.mouseX), float(mouse.mouseY))
        (x, y) = self.validateBrushLocation((x, y), window)

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
        if self.hardness < 1:
            glBegin(GL_QUADS)
            if black:
                glColor4f(.5,.5,.5,1)
            else:
                glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])

            for q in self.fall_off_current_quads:
                for p in q:
                    glVertex2f(p[0], p[1])
            glEnd()
            glBegin(GL_POLYGON)

            for q in self.fall_off_current_poly:
                for p in q:
                    glVertex2f(p[0], p[1])

            glEnd()

        glBegin(GL_QUADS)

        if black:
            glColor4f(0,0,0,1)
        else:
            glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])

        for q in self.current_quads:
            for p in q:
                glVertex2f(p[0], p[1])

        glEnd()
        glBegin(GL_POLYGON)

        for q in self.current_poly:
            for p in q:
                glVertex2f(p[0], p[1])

        glEnd()

    def cycle(self, amount):
        self.show_index = (self.show_index + amount) % len(self.composite_points)
        index = self.show_index % len(self.colored_points)
        if index < len(self.colored_points):
            h = self.colored_points[index]
            debug_print([h[4], h[5], h[6]])
            for r in self.composite_points[h[7]].color_regions:
                debug_print([r.start_angle, r.end_angle, r.color])
            debug_print([self.point_data[h[7]]])
            debug_print(['----'])
        debug_print([self.show_index])

    def draw_and_wait(self, triangles):
        glClear(GL_COLOR_BUFFER_BIT)
        glBegin(GL_TRIANGLES)
        glColor3f(1,0,1)
        for t in triangles:
            t.draw()

        glEnd()
        glutSwapBuffers()
        #raw_input('press any key')

    def draw_triangles(self, flag):
        if not (self.triangle_vertices_vbo is None):
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_COLOR_ARRAY)
            self.triangle_vertices_vbo.bind()

            try:
                glVertexPointer(2, GL_FLOAT, 20, self.triangle_vertices_vbo)
                glColorPointer(3, GL_FLOAT, 20, self.triangle_vertices_vbo+8)
                glDrawArrays(GL_TRIANGLES, 0, len(self.triangles)*3)
            finally:
                self.triangle_vertices_vbo.unbind()
                glDisableClientState(GL_VERTEX_ARRAY)
                glDisableClientState(GL_COLOR_ARRAY)

        #glBegin(GL_TRIANGLES)
        #for t in self.triangles:
        #    t.draw()
        #glEnd()


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

            glColor3f(0,0,1)
            glBegin(GL_LINES)
            for s in self.composite_lines:
                p1 = self.composite_points[s[0]].point
                p2 = self.composite_points[s[1]].point
                glVertex2f(p1[0], p1[1])
                glVertex2f(p2[0], p2[1])

            glColor3f(0,1,0)
            p1 = self.composite_points[self.composite_lines[-1][0]].point
            p2 = self.composite_points[self.composite_lines[-1][1]].point
            glVertex2f(p1[0], p1[1])
            glVertex2f(p2[0], p2[1])
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
                    glVertex2f(t.point[0]+angle1[0]*length, t.point[1]+angle1[1]*length)
                    glVertex2f(t.point[0], t.point[1])
                    glVertex2f(t.point[0]+angle2[0]*length, t.point[1]+angle2[1]*length)
                    glEnd()
                    glLineWidth(1)
                    glBegin(GL_POINTS)
                    glColor3f(0,0,1)
                glVertex2f(t.point[0], t.point[1])
                index = index + 1

            glEnd()
            glPointSize(1.0)



            """
            glPointSize(3.0)
            glBegin(GL_POINTS)
            index = 1#self.show_index % len(self.colored_points)
            if index < len(self.colored_points):
                h = self.colored_points[index]
                glColor3f(1,.5,0)
                glVertex2f(h[0][0], h[0][1])
                glVertex2f(h[1][0], h[1][1])
                glColor3f(0,1,1)
                glVertex2f(h[2][0], h[2][1])
                glVertex2f(h[3][0], h[3][1])

            glEnd()
            glPointSize(1.0)
            """


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
        self.renderLock.acquire()

        #self.triangles = []
        self.triangle_points = []
        self.last_points = deque([])
        self.current_quads = []
        self.fall_off_current_quads = []
        self.current_poly = []
        self.fall_off_current_poly = []
        self.stroke_over = False
        points = []
        count = 0
        zoom = window.width/window.zoom_width
        safeMouseX, safeMouseY = self.validateBrushLocation(window.to_world_coords(mouse.mouseX, mouse.mouseY), window)
        for p in self.brushPoints:
            count = count + 1
            point = (safeMouseX + p[0], safeMouseY + p[1])
            #self.addNotCoveredPoint(point, count==len(self.brushPoints))
            points.append(point)
        self.current_poly.append(points)

        points = []
        count = 0
        if self.hardness < 1:
            for p in self.fall_off_brush_points:
                count = count + 1
                point = (safeMouseX + p[0], safeMouseY + p[1])
                #self.addNotCoveredPoint(point, count==len(self.brushPoints))
                points.append(point)
            self.fall_off_current_poly.append(points)
        
        self.lastMouse = copy.deepcopy(mouse)
        self.renderLock.release()




    def stamp(self, mouse, window):
        self.renderLock.acquire()
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
                safeMouseX, safeMouseY = self.validateBrushLocation(window.to_world_coords(mouse.mouseX, mouse.mouseY), window)
                safeOldMouseX, safeOldMouseY = self.validateBrushLocation(window.to_world_coords(self.lastMouse.mouseX, self.lastMouse.mouseY), window)
                for i in range(len(self.brushPoints)):
                    nextI = (i + 1) % len(brush_points)
                    x1 = brush_points[i][0]
                    y1 = brush_points[i][1]
                    x2 = brush_points[nextI][0]
                    y2 = brush_points[nextI][1]
                    points = [(safeOldMouseX + x1, safeOldMouseY + y1),
                                (safeMouseX + x1, safeMouseY + y1),
                                (safeMouseX + x2, safeMouseY + y2),
                                (safeOldMouseX + x2, safeOldMouseY + y2)]
                    current_quads.append(points)

            make_quads(self.brushPoints, self.current_quads)
            if self.hardness < 1:
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
        self.renderLock.release()



    def timer_start(self):
        self.start_time = time.clock()

    def timer_end(self):
        debug_print([time.clock() - self.start_time])

    #@profile
    def clear_stroke(self, window, canvas):
        self.renderLock.acquire()

        grid_x = 50
        grid_y = 50
        self.timer_start()
        #fbo = glGenFramebuffers(1)
        #glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        #glDisable(GL_DEPTH_TEST)
        #glClearColor(1.0, 1.0, 1.0, 1.0)
        #TODO: REMOVE 480
        #glViewport(0, 0, 640, 480)
        if debug:
            self.save_action('hold.txt')
        self.append_record('out_record.rec')


        width = window.width
        height = window.height

        self.lastMouse = None
        lines = []

        def draw_and_read():
            glClear(GL_COLOR_BUFFER_BIT)
            self.timer_start()
            glEnable( GL_MULTISAMPLE )
            self.draw_stroke(black=True)
            glDisable( GL_MULTISAMPLE )
            self.timer_end()
            debug_print(['^ draw time'])
            self.timer_start()
            array = glReadPixels(0, 0, width, width, GL_RGBA, GL_FLOAT)
            self.timer_end()
            debug_print(['^ read time'])

            return array

        self.timer_end()
        values = draw_and_read()

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

        self.timer_start()

        def prune_points(contour):
            for i in range(len(contour)):
                for j in range(len(contour[i])):
                    (contour[i][j][0], contour[i][j][1]) = window.to_world_coords(contour[i][j][1], window.height - contour[i][j][0])


            def iterate_pruning():
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
                    USE_EVERY = 20


                    current_count = 0
                    last_points = []
                    last_five_points = []
                    iterations = 0
                    for p in c[1:-1]:
                        current_count = current_count + 1
                        last_five_points.append(p)

                        if current_count >= USE_EVERY:
                            last_points.append(p)
                            n = np.array([last_p[0]-p[0], last_p[1]-p[1]])
                            n = n/np.linalg.norm(n)
                            line_test_failed = False
                            """
                            for p2 in last_five_points:
                                iterations += 1
                                vec_to_p = np.array([p[0]-p2[0], p[1]-p2[1]])
                                if np.linalg.norm(vec_to_p-(np.dot(vec_to_p,n)*n)) > DIST_THRESHOLD:
                                    line_test_failed = True
                                    break
                            """
                            if not line_test_failed:
                                last_points_length = len(last_points)
                                if last_points_length < 5:
                                    point_list = last_points
                                else:
                                    point_list = []
                                    for index in range(5):
                                        point_list.append(last_points[random.randint(0, last_points_length-1)])
                                for p2 in point_list:
                                    iterations += 1
                                    vec_to_p = np.array([p[0]-p2[0], p[1]-p2[1]])
                                    if np.linalg.norm(vec_to_p-(np.dot(vec_to_p,n)*n)) > DIST_THRESHOLD:
                                        line_test_failed = True
                                        break

                            if line_test_failed:
                                self.triangle_points.append((last_points[-1][0], last_points[-1][1]))
                                index = len(self.triangle_points)-1
                                lines.append([index - 1, index])
                                first_angle = None
                                last_angle = None
                                last_p = last_points[-1]
                                current_count = 0
                                last_points = []
                            last_five_points = []

                        if False: #current_count >= USE_EVERY:


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
                    #print 'iterations', iterations, len(c)
            iterate_pruning()

        def convert_pointset_to_contour(cont):
            contours = []
            for c in cont:
                point_map = {}
                index = 0
                
                for i in range(0, len(c), 2):
                    p1 = (c[i][0], c[i][1])
                    p2 = (c[i+1][0], c[i+1][1])

                    if p1 in point_map:
                        if not p2 in point_map[p1]:
                            point_map[p1].append(p2)
                        # if len(point_map[p1]) > 1:
                        #     print 'too many: ', len(point_map[p1])
                        #     for a in point_map[p1]:
                        #         print a
                        #     print p2
                    else:
                        point_map[p1] = [p2]

                    if p2 in point_map:
                        if not p1 in point_map[p2]:
                            point_map[p2].append(p1)
                        # if len(point_map[p2]) > 1:
                        #     print 'too many: ', len(point_map[p2]), p2
                        #     for a in point_map[p2]:
                        #         print a
                        #     print p1
                    else:
                        point_map[p2] = [p1]

                used_points = set()
                contour = []
                p = (c[0][0], c[0][1])
                used_points.add(p)

                atLeastOne = True
                while atLeastOne:
                    nextP = point_map[p]
                    atLeastOne = False
                    for point in nextP:
                        if not point in used_points:
                            atLeastOne = True
                            break
                    if atLeastOne:
                        contour.append(p)
                        used_points.add(p)
                        p = point
                contours.append(contour)
            return np.array(contours)

        if self.hardness == 1:
            # self.contours = measure.find_contours(rvalues[:,:], .5)
            self.contours = np.array([marchingsquares.isocontour(np.swapaxes(rvalues[:,:], 0, 1), .5)])
            self.contours = convert_pointset_to_contour(self.contours)
            prune_points(self.contours)
            size_of_core = len(self.triangle_points)
        else:

            self.contours = np.array([marchingsquares.isocontour(np.swapaxes(rvalues[:,:], 0, 1), .25)])
            self.contours = convert_pointset_to_contour(self.contours)
            prune_points(self.contours)

            size_of_core = len(self.triangle_points)
            
            self.contours2 = np.array([marchingsquares.isocontour(np.swapaxes(rvalues[:,:], 0, 1), .75)])
            self.contours2 = convert_pointset_to_contour(self.contours2)
            prune_points(self.contours2)

        self.timer_end()
        self.timer_start()





        def create_triangulation_arrays():
            line_array = np.empty([len(lines), 2])
            i = 0
            for l in lines:
                line_array[i, 0] = l[0]
                line_array[i, 1] = l[1]
                i = i + 1

            array = np.empty([len(self.triangle_points), 2])
            i = 0
            for t in self.triangle_points:
                array[i, 0] = t[0]
                array[i, 1] = t[1]
                i = i + 1

            self.boundary = line_array
            self.arrayPoints = array

        create_triangulation_arrays()

        def triangulation_one():
            A = dict(vertices = self.arrayPoints, segments = self.boundary)
            return triangle.triangulate(A, 'p')

        first_triangulation = triangulation_one()
        first_triangle_indicies = first_triangulation['triangles']
        debug_print(['fti', first_triangle_indicies])

        starting_value = len(self.composite_points)



        def add_points_to_composite():
            angles = np.empty([len(self.triangle_points), 2, 2])
            for l in lines:
                p1 = self.triangle_points[l[0]]
                p2 = self.triangle_points[l[1]]
                angle = np.array([p1[0]-p2[0], p1[1]-p2[1]])
                angle = angle / np.linalg.norm(angle)
                angles[l[0], 1, :] = -1*angle
                angles[l[1], 0, :] = angle


            index = 0
            transparent_color = [self.color[0], self.color[1], self.color[2], 0]
            for p in self.triangle_points:

                if self.hardness == 1:
                    regions = [geometry.ColorRegion(transparent_color, angles[index,0], angles[index,1]),
                               geometry.ColorRegion(self.color, angles[index,1], angles[index,0])]
                else:
                    if index < size_of_core:
                        regions = [geometry.ColorRegion(self.color, angles[index,0], angles[index,0])]
                                   #geometry.ColorRegion(self.color, angles[index,1], angles[index,0])]
                    else:
                        regions = [geometry.ColorRegion(transparent_color, angles[index,0], angles[index,0])]
                                   #geometry.ColorRegion(transparent_color, angles[index,1], angles[index,0])]

                t = geometry.TrianglePoint(p,regions, composite_point_index=len(self.composite_points))
                self.composite_points.append(t)
                index = index + 1
            debug_print(['added this many indicies to composite', index])

        add_points_to_composite()


        grid_old = geometry.Grid(grid_x, grid_y, window, self.triangles, True)
        first_triangles = []
        for i in first_triangle_indicies:
            t = first_triangulation['vertices'][i]
            t2 = []
            for j in range(len(i)):
                debug_print(['trying to access', i[j]])
                t2.append(self.composite_points[starting_value+i[j]])
            first_triangles.append(geometry.Triangle(t2))

        grid_new = geometry.Grid(grid_x, grid_y, window, first_triangles, True)

        mapping = {}
        index = 0



        glClear(GL_COLOR_BUFFER_BIT)
        grid_old.draw_grid()



        graph = []
        for i in range(len(self.composite_points)):
            graph.append([])

        for s in self.composite_lines:
            graph[s[0]].append(s[1])
            graph[s[1]].append(s[0])


        #if len(self.triangles) > 5:
        #    grid_new.examine_grid(grid_old)
        """
        glClear(GL_COLOR_BUFFER_BIT)
        grid_new.draw_grid()


        for t in self.triangles:
            glBegin(GL_LINE_LOOP)
            t.draw_color((1,0,0))
            glEnd()
        glutSwapBuffers()
        #raw_input('press any key')
        """

        old_triangles, redo_points, extra_segments, hole_points = grid_new.get_unmodified_triangles(grid_old, graph)

        boundary_points = set()
        for es in extra_segments:
            boundary_points.add(es[0])
            boundary_points.add(es[1])


        debug_print(['length of old_triangles', len(old_triangles)])
        for p in redo_points:
            mapping[p.composite_point_index] = index
            index += 1

        debug_print(['using:', len(redo_points), 'out of', len(self.composite_points)])

        redo_segments = []
        seg_set = set(self.composite_lines)
        for l in self.composite_lines:
            if l[0] in mapping and l[1] in mapping:
                index1 = mapping[l[0]]
                index2 = mapping[l[1]]
                redo_segments.append((index1, index2))
                # TODO: Maybe causing bad topology crashes
                if not (l[0] in boundary_points and l[1] in boundary_points):
                    debug_print(['maybe made bad topology!'])
                    seg_set.remove(l)

        redo_starting_value = len(redo_points)




        """
        glClear(GL_COLOR_BUFFER_BIT)

        glColor3f(1, 0, 1)
        glBegin(GL_LINES)
        for r in self.composite_lines:
            glVertex2f(self.composite_points[r[0]].point[0], self.composite_points[r[0]].point[1])
            glVertex2f(self.composite_points[r[1]].point[0], self.composite_points[r[1]].point[1])
        glEnd()

        glPointSize(3)
        glColor3f(0, 1, 1)
        glBegin(GL_POINTS)
        for r in self.composite_points:
            glVertex2f(r.point[0], r.point[1])
        glEnd()
        glPointSize(1)

        glutSwapBuffers()
        #raw_input('press any key')
        """

        def triangulation_two():
            for l in lines:
                #seg1 = [l[0]+starting_value,l[1]+starting_value]
                #self.composite_lines.append(seg1)
                seg2 = [l[0]+redo_starting_value,l[1]+redo_starting_value]
                redo_segments.append(seg2)

            verts = np.empty([len(redo_points)+len(self.composite_points)-starting_value, 2])
            i = 0
            for t in redo_points:
                verts[i, 0] = t.point[0]
                verts[i, 1] = t.point[1]

                i = i + 1

            for t in self.composite_points[starting_value:]:
                verts[i, 0] = t.point[0]
                verts[i, 1] = t.point[1]

                i = i + 1


            debug_print(['extra_segments',])
            for es in extra_segments:
                if not es in seg_set and not (es[1], es[0]) in seg_set:
                    debug_print([es])
                    redo_segments.append([mapping[es[0]], mapping[es[1]]])

            #print
            debug_print(['redo_segments', redo_segments])

            pre_extra_seg_length = len(redo_segments)

            """
            glClear(GL_COLOR_BUFFER_BIT)
            grid_new.draw_grid()


            #for t in self.triangles:
            #    glBegin(GL_LINE_LOOP)
            #    t.draw_color((0,0,0))
            #    glEnd()

            glColor3f(1, 0, 1)
            glBegin(GL_LINES)
            for r in extra_segments:
                glVertex2f(verts[mapping[r[0]]][0], verts[mapping[r[0]]][1])
                glVertex2f(verts[mapping[r[1]]][0], verts[mapping[r[1]]][1])
            glEnd()

            glPointSize(3)

            glColor3f(1, 0, 0)
            glBegin(GL_POINTS)
            for r in self.composite_points:
                glVertex2f(r.point[0], r.point[1])
            glEnd()

            glColor3f(0, 1, 1)
            glBegin(GL_POINTS)
            for r in redo_points:
                glVertex2f(r.point[0], r.point[1])
            glEnd()

            glColor3f(0, 0, 0)
            glBegin(GL_POINTS)
            for r in hole_points:
                glVertex2f(r[0], r[1])
            glEnd()

            glPointSize(1)



            glutSwapBuffers()
            raw_input('press any key')
            """

            line_array = np.empty([len(redo_segments), 2])
            i = 0
            for l in redo_segments:
                line_array[i, 0] = l[0]
                line_array[i, 1] = l[1]
                i = i + 1

            hole_array = np.empty([len(hole_points), 2])
            i = 0
            for p in hole_points:
                hole_array[i, 0] = p[0]
                hole_array[i, 1] = p[1]
                i = i + 1

            # print 'hole_array', hole_array

            debug_print(['before triangulation'])
            if i == 0:
                A = dict(vertices = verts, segments = line_array)#, holes = hole_array)
            else:
                A = dict(vertices = verts, segments = line_array, holes = hole_array)
            # print self.composite_points
            # print self.composite_lines
            ret = triangle.triangulate(A, 'p'), pre_extra_seg_length
            debug_print(['after triangulation'])
            return ret

        triangulation, pre_extra_seg_length = triangulation_two()
        tri_indicies = triangulation['triangles']
        delauny_points = triangulation['vertices']
        segments = triangulation['segments']



        def convert_redo_point_to_composite(index):
            if index < redo_starting_value:
                return redo_points[index].composite_point_index
            else:
                return index + starting_value - redo_starting_value

        pts_length = len(redo_points)
        for s in segments:
            #if s[0] < pts_length or s[1] < pts_length:
            index1 = s[0]
            index2 = s[1]
            seg_set.add((convert_redo_point_to_composite(index1), convert_redo_point_to_composite(index2)))

        original_segments_set = set(self.composite_lines)

        for e in extra_segments:
            s = (e[0], e[1])
            s2 = (e[1], e[0])
            if not s in original_segments_set and not s2 in original_segments_set:
                if s in seg_set:
                    seg_set.remove(s)
                if s2 in seg_set:
                    seg_set.remove(s2)

        self.composite_lines = list(seg_set)

        new_tri_indicies = []
        for indicies in tri_indicies:
            new_indicies = []
            for i in indicies:
                new_indicies.append(convert_redo_point_to_composite(i))
            new_tri_indicies.append(new_indicies)

        tri_indicies = new_tri_indicies

        self.delauny_points.extend(delauny_points[redo_starting_value:])
        delauny_points = self.delauny_points

        debug_print(['delauny_length', len(delauny_points), 'composite', len(self.composite_points)])

        graph = []
        marked = []
        all_points = []
        self.point_data = []

        for i in range(len(delauny_points)):
            graph.append([])
            self.point_data.append([])
            if i < len(self.composite_points):
                all_points.append(self.composite_points[i])
                marked.append(True)
            else:
                all_points.append(None)
                marked.append(False)



        for s in self.composite_lines:
            graph[s[0]].append(s[1])
            graph[s[1]].append(s[0])



        draw_point_coloring = False
        def color_index(index):
            if marked[index]:
                return
            visited = set()
            marked[index] = True
            color_regions = []
            angles = []
            p1 = delauny_points[index]
            for s in graph[index]:

                if draw_point_coloring:
                    p = p1
                    glMatrixMode(GL_PROJECTION)
                    glLoadIdentity()
                    glOrtho(p[0] - 200, p[0] + 200, p[1] - 200, p[1] + 200,
                            -1,
                            1)

                    glMatrixMode(GL_MODELVIEW)
                    glLoadIdentity()

                    glClear(GL_COLOR_BUFFER_BIT)

                    for t in self.triangles:
                        glBegin(GL_LINE_LOOP)
                        t.draw_color((1,0,0))
                        glEnd()

                    glPointSize(3)

                    glColor3f(1, 0.5, 0)
                    glBegin(GL_POINTS)
                    for r in self.composite_points:
                        glVertex2f(r.point[0], r.point[1])
                    glEnd()



                    glPointSize(10)
                    glBegin(GL_POINTS)
                    glColor3f(0, 1, 1)
                    glVertex2f(p[0], p[1])

                    glColor3f(1, 0, 1)
                    p = delauny_points[s]
                    glVertex2f(p[0], p[1])
                    glEnd()
                    glPointSize(1)

                    glutSwapBuffers()
                    raw_input('press any key')

                p2 = delauny_points[s]

                angle = np.array([p2[0]-p1[0], p2[1]-p1[1]])
                norm = np.linalg.norm(angle)
                if norm == 0:
                    continue
                angle = angle/norm
                i = s
                last_i = i
                while i >= len(self.composite_points):
                    visited.add(i)

                    angle2 = []
                    for b in graph[i]:
                        if b in visited:
                            angle2.append(-1)
                            continue
                        p2 = delauny_points[b]
                        hold = np.array([p2[0]-p1[0], p2[1]-p1[1]])
                        norm = np.linalg.norm(hold)
                        if norm == 0:
                            angle2.append(-1)
                            continue
                        hold = hold/norm
                        angle2.append(np.dot(hold, angle))
                    if not graph[i][0] in visited:
                        max_dot = angle2[0]
                        max_index = 0
                    else:
                        max_dot = angle2[1]
                        max_index = 1
                    for a in range(1,len(angle2)):
                        if angle2[a] > max_dot and not graph[i][a] in visited:
                            max_dot = angle2[a]
                            max_index = a
                    last_i = i
                    p2 = delauny_points[max_index]
                    hold = np.array([p2[0]-p1[0], p2[1]-p1[1]])

                    i = graph[i][max_index]

                p2 = delauny_points[i]

                angles.append((angle, all_points[i], (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2, delauny_points[i], i))

                def gen_color_range(angle1, angle2, p, index):
                    """
                    c_r1 = angle1[1].color_regions
                    c_r2 = angle2[1].color_regions
                    minimum = 1
                    min_index = 0
                    for i in range(len(c_r1)):
                        r = c_r1[i]
                        hold = abs(r.end_angle - angle1[0])
                        if hold < minimum:
                            minimum = hold
                            min_index = i
                    c1 = c_r1[min_index].color

                    minimum = 1
                    min_index = 0
                    for i in range(len(c_r2)):
                        r = c_r2[i]
                        hold = abs(r.start_angle - angle2[0])
                        if hold < minimum:
                            minimum = hold
                            min_index = i
                    c2 = c_r2[min_index].color
                    """

                    # TODO: Figure out a more stable approach. The /1000 is needed to avoid crossing a boundary when
                    # dealing with really small triangles!
                    dx = angle1[0][0]/1000.0
                    dy = angle1[0][1]/1000.0
                    p2 = [p[0]-dy, p[1]+dx]
                    centroid1 = geometry.getCentroidPoints([p, p2, angle1[1].point])
                    centroid2 = geometry.getCentroidPoints([p, p2, angle2[1].point])
                    #c1 = geometry.get_color(angle1[1].color_regions, [-dy, dx])#(p2)#geometry.get_color(c_r1, angle1[0] + math.pi/2.0)
                    c1 = angle1[1].get_current_color(p2)#geometry.get_color(c_r2, angle1[0] + math.pi/2.0)
                    c2 = angle2[1].get_current_color(p2)#geometry.get_color(c_r2, angle1[0] + math.pi/2.0)

                    dist = math.sqrt ((angle1[1].point[0] - angle2[1].point[0])**2
                                      + (angle1[1].point[1] - angle2[1].point[1])**2)
                    d1 = math.sqrt (angle1[2])
                    d2 = math.sqrt (angle2[2])
                    if dist == 0:
                        r1 = .5
                        r2 = .5
                    else:
                        r1 = d2/dist
                        r2 = d1/dist
                    color = [c1[0] * r1 + c2[0] * r2, c1[1] * r1 + c2[1] * r2, c1[2] * r1 + c2[2] * r2, c1[3] * r1 + c2[3] * r2]
                    self.colored_points.append([p, p2, angle1[1].point, angle2[1].point, c1, c2, color, index])
                    return geometry.ColorRegion(color, angle1[0], angle2[0])

                def get_other_range(other_indices, range1, p, index):
                    if len(other_indicies) == 2:
                        range2 = [gen_color_range(angles[other_indicies[0]], angles[other_indicies[1]], p, index),
                                  gen_color_range(angles[other_indicies[1]], angles[other_indicies[0]], p, index)]
                        self.point_data[index].append(True)
                        if angles[other_indicies[0]][4] < starting_value:
                            return geometry.composite_ranges(range2, range1)
                        else:
                            return geometry.composite_ranges(range1, range2)

                    else:
                        self.point_data[index].append(False)
                        return [range1]

            flag = False
            min_val = 1
            min_index = -1
            for i in range(1,len(angles)):
                a = angles[i]

                if draw_point_coloring:
                    p = delauny_points[index]

                    glMatrixMode(GL_PROJECTION)
                    glLoadIdentity()
                    glOrtho(p[0] - 200, p[0] + 200, p[1] - 200, p[1] + 200,
                            -1,
                            1)

                    glMatrixMode(GL_MODELVIEW)
                    glLoadIdentity()

                    glClear(GL_COLOR_BUFFER_BIT)

                    for t in self.triangles:
                        glBegin(GL_LINE_LOOP)
                        t.draw_color((1,0,0))
                        glEnd()

                    glPointSize(3)

                    glColor3f(0, 0, 1)
                    glBegin(GL_POINTS)
                    for r in self.composite_points:
                        glVertex2f(r.point[0], r.point[1])
                    glEnd()



                    glPointSize(10)
                    glBegin(GL_POINTS)
                    glColor3f(0, 1, 1)
                    glVertex2f(p[0], p[1])

                    glColor3f(1, 0, 1)
                    p = a[1]
                    glVertex2f(p.point[0], p.point[1])
                    glEnd()
                    glPointSize(1)

                    glutSwapBuffers()
                    raw_input('press any key')

                other_indicies = range(1, len(angles))

                dot_prod = np.dot(a[0], angles[0][0])
                if dot_prod < min_val:
                    min_index = i
                    min_val = dot_prod

            i = min_index
            if i > 0:
                a = angles[i]

                range1 = [gen_color_range(angles[0], a, p1, index), gen_color_range(a, angles[0], p1, index)]
                other_indicies.remove(i)
                color_regions = get_other_range(other_indicies, range1, p1, index)
                flag = True


            if len(angles) == 1:
                color_regions = angles[0][1].color_regions
            else:
                if not flag:
                    debug_print(['FAILED When determining color range order'])
                    debug_print([angles])

            all_points[index] = geometry.TrianglePoint(p1, color_regions, composite_point_index=index)


        for i in range(len(self.composite_points), len(all_points)):
            color_index(i)

        pixel_colors = []

        #glClear(GL_COLOR_BUFFER_BIT)
        #self.draw_triangles(False)

        #read_pixels = glReadPixels(0, 0, width, height, GL_RGBA, GL_FLOAT)

        def determine_final_colors():


            for p in self.composite_points[starting_value:]:
                pixel_color = [1, 1, 1, 0]
                t = grid_old.point_in_triangle_acc(p.point)

                if not t is None:
                    pixel_color = t.get_color_at_point(p.point)
                pixel_colors.append(pixel_color)




            for p in self.composite_points[0:starting_value]:
                    tri = grid_new.point_in_triangle_acc(p.point)
                    if not tri is None:
                        p.composite_color(tri.get_color_at_point(p.point))


            for p,p_c in zip(self.composite_points[starting_value:], pixel_colors):
                index = 0
                for r in p.color_regions:
                    r.color = geometry.color_over(p_c, r.color)
                    index = index + 1

        determine_final_colors()

        self.composite_points = all_points
        #self.composite_lines = []
        #for s in segments:
        #    self.composite_lines.append(s)


        hold = len(self.triangles)
        self.triangles = []
        debug_print(['out of:', hold, 'using', len(self.triangles)])

        for indices in tri_indicies:
            t = []
            for i in indices:
                t.append(all_points[i])

            self.triangles.append(geometry.Triangle(t))
        self.triangles.extend(old_triangles)

        debug_print(["tri: " + str(len(self.triangles))])
        debug_print(["quad: " + str(len(self.current_quads))])



        self.setup_vbo()

        self.current_quads = []
        self.fall_off_current_quads = []
        self.current_poly = []
        self.fall_off_current_poly = []
        if debug:
            self.save('last_stroke.txt')
        

        #self.simplify()

        #glBindFramebuffer(GL_FRAMEBUFFER, 0)
        #glDeleteFramebuffers(1, fbo)
        self.timer_end()

        self.whereInUndoStack += 1

        dequeSize = len(self.undoData)
        for i in range(self.whereInUndoStack, dequeSize):
            self.undoData.pop()
        self.undoData.append(triangleCanvas.Canvas(self.composite_points, self.composite_lines, self.triangles, self.delauny_points, self.point_data))

        self.renderLock.release()


    def setup_vbo(self):
        if not self.triangle_vertices_vbo is None:
            self.triangle_vertices_vbo.delete()
        np_vbo = np.empty((len(self.triangles)*3, 5), dtype=np.float32)

        for index in range(len(self.triangles)):
            points = self.triangles[index].points
            # speed this up by using old information
            colors = self.triangles[index].get_colors()
            np_vbo[index*3, 0:2] = points[0].point
            np_vbo[index*3, 2:5] = colors[0][0:3]
            np_vbo[index*3+1, 0:2] = points[1].point
            np_vbo[index*3+1, 2:5] = colors[1][0:3]
            np_vbo[index*3+2, 0:2] = points[2].point
            np_vbo[index*3+2, 2:5] = colors[2][0:3]

        # Try to do async
        self.triangle_vertices_vbo = vbo.VBO(np_vbo)

    def simplify(self):
        def get_lab_color(c):
            coeff = np.array([[0.4360747, 0.3850649, 0.1430804, 0], [0.2225045, 0.7168786, 0.0606169, 0], [0.0139322, 0.0971045, 0.7141733, 0]])
            rgb = np.array(c)
            xyz = np.dot(coeff, rgb)
            X = xyz[0]
            Y = xyz[1]
            Z = xyz[2]
            sqrtY = np.sqrt(Y)
            L = 100*sqrtY
            if sqrtY == 0:
                sqrtY = .001
            a = 172.30*(X-Y)/sqrtY
            b = 67.20*(Y-Z)/sqrtY
            return np.array([L,a,b])

        def deltaE(c1, c2):
            return np.linalg.norm(c1-c2)

        def combine_arcs():
            for p in self.composite_points:
                i = 0

                regions = [p.color_regions[i]]
                i = i + 1
                flag = False
                while i < len(p.color_regions) and not flag:
                    flag = True
                    for j in range(len(p.color_regions)):
                        if np.dot(p.color_regions[j].start_angle, regions[i-1].end_angle) > .99:
                            regions.append(p.color_regions[j])
                            i = i + 1
                            flag = False
                            break
                if flag:
                    continue

                i = 0

                while i < len(regions) and len(regions) > 1:
                    j = (i + 1) % len(regions)
                    r1 = regions[i]
                    r2 = regions[j]
                    if deltaE(get_lab_color(r1.color), get_lab_color(r2.color)) < 1:
                        new_color_region = (geometry.ColorRegion(r1.color, r1.start_angle, r2.end_angle))
                        if i < j:
                            regions.pop(j)
                            regions.pop(i)
                        else:
                            regions.pop(i)
                            regions.pop(j)
                        regions.append(new_color_region)
                        i = 0
                    else:
                        i = i + 1

                p.color_regions = regions

        def remove_edges():
            graph = []
            for i in range(len(self.composite_points)):
                graph.append([])

            for s in self.composite_lines:
                graph[s[0]].append(s[1])
                graph[s[1]].append(s[0])

            new_points = []
            keep_seg = []

            rem = 0
            rem_partial_sum = []
            for i in range(len(self.composite_points)):
                p = self.composite_points[i]
                new_points.append(p)
                keep_seg.append(True)
                rem_partial_sum.append(rem)
                if len(p.color_regions) == 1:
                    p2 = None
                    if len(graph[i]) > 0:
                        p2_index = graph[i][0]
                        p2 = self.composite_points[p2_index]
                    """
                    for j in graph[i]:
                        if len(self.composite_points[j].color_regions) == 1:
                            p2 = self.composite_points[j]
                            p2_index = j
                            break
                    """
                    if not p2 is None:

                        new_points.pop()
                        keep_seg[i] = False
                        rem = rem + 1

                        for j in graph[i]:
                            graph[j].remove(i)

            self.composite_points = new_points
            segs = []

            for i in range(len(keep_seg)):
                if keep_seg[i]:
                    for j in graph[i]:
                        if keep_seg[j]:
                            segs.append([i-rem_partial_sum[i], j-rem_partial_sum[j]])

            self.composite_lines = segs


        #combine_arcs()
        #remove_edges()

        def edge_collapses():
            triangle_graph = []
            for i in range(len(self.composite_points)):
                triangle_graph.append([])

            for t in self.triangles:
                for p in t.points:
                    triangle_graph[p.composite_point_index].append(t)


            graph = []
            for i in range(len(self.composite_points)):
                graph.append([])

            for s in self.composite_lines:
                graph[s[0]].append(s[1])
                graph[s[1]].append(s[0])

            def try_edge_collapse(e):
                connected0 = list(graph[e[0]])
                connected1 = list(graph[e[1]])

                def collapse(point_from, point_to):
                    set(graph[point_from])
                    for p in graph[point_from]:
                        if p in graph[point_to] and p != point_to:
                            graph[point_to].append(p)
                        if p != point_to:
                            graph[p].append(point_to)

                        graph[p].remove(point_from)

                    graph[point_from] = []

                    for t in triangle_graph[point_from]:
                        new_triangle_points = [self.composite_points[point_to]]
                        for p in t.points:
                            if p.composite_point_index != point_to and p.composite_point_index != point_from:
                                new_triangle_points.append(self.composite_points[p.composite_point_index])

                        if len(new_triangle_points) == 3:
                            new_t = geometry.Triangle(points=new_triangle_points)
                            triangle_graph[point_to].append(new_t)

                        for p in t.points:
                            if p.composite_point_index != point_from:
                                debug_print(['beta adf'])
                                triangle_graph[p.composite_point_index].remove(t)
                                if len(new_triangle_points) == 3:
                                    triangle_graph[p.composite_point_index].append(new_t)
                            else:
                                debug_print(['alpha adf'])

                    triangle_graph[point_from] = []
                    self.composite_points[point_from] = None

                collapse(e[0], e[1])

            #for e in self.composite_lines:
            #    try_edge_collapse(e)
            try_edge_collapse(self.composite_lines[-1])

            mapping = []
            new_points = []
            index = 0
            for i, p in enumerate(self.composite_points):
                if p is None:
                    mapping.append(None)
                else:
                    mapping.append(index)
                    debug_print(['check index', p.composite_point_index, i])
                    p.composite_point_index = index
                    new_points.append(p)
                    index += 1

            self.composite_points = new_points

            triangles = set()
            for graphs in triangle_graph:
                for t in graphs:
                    triangles.add(t)
            self.triangles = list(triangles)

            lines = set()
            reverse_lines = set()
            for i, g in enumerate(graph):
                for p in g:
                    l0 = (mapping[i], mapping[p])
                    l1 = (mapping[p], mapping[i])
                    if not l0 in reverse_lines:
                        lines.add(l0)
                        reverse_lines.add(l1)
                        reverse_lines.add(l1)

            self.composite_lines = list(lines)

            self.delauny_points = []
            for p in self.composite_points:
                self.delauny_points.append(p.point)

        edge_collapses()
        self.setup_vbo()
        debug_print(['triangles', len(self.triangles), 'lines', len(self.composite_lines), 'points', len(self.composite_points)])


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

    def load_helper(self, f):
        self.composite_points = []
        self.composite_lines = []
        self.triangles = []
        self.delauny_points = []
        num_points = int(f.readline())
        for i in range(num_points):
            self.composite_points.append(geometry.TrianglePoint(file=f))

        num_lines = int(f.readline())
        for i in range(num_lines):
            line = f.readline()
            s = line.split(',')
            self.composite_lines.append((int(s[0]),int(s[1])))

        num_triangles = int(f.readline())
        for i in range(num_triangles):
            self.triangles.append(geometry.Triangle(file=f))

        for d in self.composite_points:
            self.delauny_points.append(d.point)

        #self.stroke_over = False
        #self.clear_stroke(window)
        #self.stroke_over = True
        self.setup_vbo()

    def load(self, in_name):
        f = open(in_name, 'r')
        self.load_helper(f)

        f.close()
        debug_print(['lines', self.composite_lines])
        debug_print([len(self.composite_points)])
        debug_print(['points'])
        for i, p in enumerate(self.composite_points):
            debug_print([p.composite_point_index])
        
    def append_record(self, out_name):

        f = open(out_name, 'a')

        f.write("$\n")
        f.write(str(len(self.current_quads))+'\n')
        f.write(str(self.color[0])+','+str(self.color[1])+','+str(self.color[2])+','+str(self.color[3])+'\n')
        for q in self.current_quads:
            for p in q:
                f.write(str(p[0]) + ',' + str(p[1])+'\n')

        f.write(str(len(self.fall_off_current_quads))+'\n')
        f.write(str(self.color[0])+','+str(self.color[1])+','+str(self.color[2])+','+str(0)+'\n')
        for q in self.fall_off_current_quads:
            for p in q:
                f.write(str(p[0]) + ',' + str(p[1])+'\n')
        f.close()

    def save_record(self, name):
        if os.path.isfile('out_record.rec'):
            shutil.move('out_record.rec', name)

    def open_record(self, in_name):
        f = open(in_name, 'r')
        self.strokes = []

        while '$' in f.readline():
            nextStroke = stroke.Stroke()
            nextStroke.load(f)
            self.strokes.append(nextStroke)
        f.close()

    def play_record(self, index, canvas):
        self.color = self.strokes[index].color
        self.current_quads = self.strokes[index].quads
        self.fall_off_current_quads = self.strokes[index].fallOffQuads

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.window.center_x - (self.window.zoom_width / 2.0),
                self.window.center_x + (self.window.zoom_width / 2.0),
                self.window.center_y - (self.window.zoom_height / 2.0),
                self.window.center_y + (self.window.zoom_height / 2.0),
                -1,
                1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.stroke_over = False
        self.clear_stroke(self.window, canvas)
        self.stroke_over = True

    def save_action(self, out_name):
        self.save(out_name)

        f = open(out_name, 'a')
        f.write(str(len(self.current_quads))+'\n')
        f.write(str(self.color[0])+','+str(self.color[1])+','+str(self.color[2])+','+str(self.color[3])+'\n')
        for q in self.current_quads:
            for p in q:
                f.write(str(p[0]) + ',' + str(p[1])+'\n')

        f.write(str(len(self.fall_off_current_quads))+'\n')
        f.write(str(self.color[0])+','+str(self.color[1])+','+str(self.color[2])+','+str(0)+'\n')
        for q in self.fall_off_current_quads:
            for p in q:
                f.write(str(p[0]) + ',' + str(p[1])+'\n')
        f.close()

    def load_action(self, in_name, window):
        f = open(in_name, 'r')
        self.composite_points = []
        self.composite_lines = []
        self.triangles = []
        self.current_quads = []
        self.fall_off_current_quads = []

        self.load_helper(f)

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

        num_quads = int(f.readline())
        color = f.readline().split(',')
        #self.color = [float(color[0]), float(color[1]), float(color[2]), float(color[3])]
        for i in range(num_quads):
            q = []
            for j in range(4):
                line = f.readline()
                s = line.split(',')
                q.append([float(s[0]), float(s[1])])
            self.fall_off_current_quads.append(q)

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