#!/usr/bin/env python
# pyglet version of NeHe's OpenGL lesson06
# based on the pygame+PyOpenGL conversion by Paul Furber 2001 - m@verick.co.za
# Philip Bober 2007 pdbober@gmail.com

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
import os
import time
import copy
from collections import deque

import numpy as np
from scipy.spatial import Delaunay
import triangle


# Some api in the chain is translating the keystrokes to this octal string
# so instead of saying: ESCAPE = 27, we use the following.
ESCAPE = '\033'

window = 0

lastX = 0
lastY = 0

brushWidth = 10


class Triangle:
    def __init__(self, points, colors):
        self.points = points
        self.colors = colors

    def draw(self):
        for i in range(3):
            p = self.points[i]
            c = self.colors[i]
            if not(c[0] == 1 and c[1] == 1 and c[2] == 1):
                glColor3f(c[0], c[1], c[2])
                glVertex2f(p[0], p[1])

    def draw_color(self, color):
        for i in range(3):
            p = self.points[i]
            glColor3f(color[0], color[1], color[2])
            glVertex2f(p[0], p[1])



class Mouse:
    def __init__(self):
        self.mouseX = 0
        self.mouseY = 0
        self.mouseDown = False

class TrianglePoint:
    def __init__(self, point, prev=None, next=None, prev_on_side=None, next_on_side=None):
        self.point = point
        self.next = next
        self.prev = prev
        self.isValid = True
        self.next_on_side = next_on_side
        self.prev_on_side = prev_on_side

    def draw(self):
        if self.next != None and self.isValid and self.next.isValid:
            p1 = self.point
            p2 = self.next.point
            glVertex2f(p1[0], p1[1])
            glVertex2f(p2[0], p2[1])

        if (self.next_on_side != None and self.isValid and self.next_on_side.isValid
            and ((self.next == None or self.next_on_side.next == None)
                 or (self.prev == None or self.next_on_side.prev == None))):
            p1 = self.point
            p2 = self.next_on_side.point
            glVertex2f(p1[0], p1[1])
            glVertex2f(p2[0], p2[1])

        if (self.prev_on_side != None and self.isValid and self.prev_on_side.isValid
            and ((self.next == None or self.prev_on_side.next == None)
                 or (self.prev == None or self.prev_on_side.prev == None))):
            p1 = self.point
            p2 = self.prev_on_side.point
            glVertex2f(p1[0], p1[1])
            glVertex2f(p2[0], p2[1])


class Brush:
    def __init__(self, brushRadius, numSides):
        self.brushPoints = []
        self.currentQuads = []
        self.triangle_points = []
        self.last_points = deque([])
        self.last_removed = None
        self.triangles = []
        self.lastMouse = None
        self.stroke_over = False


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
        if self.stroke_over:
            glColor3f(.5,.5,.5)
        else:
            glColor3f(0,0,0)

        for q in self.currentQuads:
            for p in q:
                glVertex2f(p[0], p[1])

        glEnd()

    def draw_triangles(self, flag):
        glBegin(GL_TRIANGLES)

        """
        for t in self.triangles:
            t.draw()
        """

        glEnd()

        if flag:
            for t in self.triangles:
                glBegin(GL_LINE_LOOP)
                t.draw_color((1,0,0))
                glEnd()

            glLineWidth(3.0)
            glBegin(GL_LINES)
            glColor3f(0,0,1)
            for t in self.triangle_points:
                t.draw()

            glEnd()
            glLineWidth(1.0)

            glPointSize(3.0)
            glBegin(GL_POINTS)
            glColor3f(1,0.5,0)
            for t in self.triangle_points:
                glVertex2f(t.point[0], t.point[1])

            glEnd()
            glPointSize(1.0)


    def new_stroke(self, mouse):
        self.triangles = []
        self.triangle_points = []
        self.last_points = deque([])
        self.currentQuads = []
        self.currentPolys = []
        self.stroke_over = False
        points = []
        count = 0
        for p in self.brushPoints:
            count = count + 1
            point = (mouse.mouseX + p[0], mouse.mouseY + p[1])
            self.addNotCoveredPoint(point, count==len(self.brushPoints))
            points.append(point)
        self.currentQuads.append(points)

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

    def pointInAnyQuad(self, p):
        for q in self.currentQuads:
            if self.pointInQuad(p, q):
                return True
        return False

    def addNotCoveredPoint(self, p, last):
        prev = None
        if len(self.last_points) >= len(self.brushPoints):
            prev = self.last_points.popleft()

            #while prev != None and not prev.isValid:
            #    prev = prev.prev
        #if prev == None:
        #    if len(self.last_points) > 0:
        #        prev = self.last_points[-1]

        if last:
            point = TrianglePoint(p, prev, None, None, self.last_points[0])
            self.last_points[0].prev_on_side = point
        else:
            point = TrianglePoint(p, prev, None, None, None)

        if len(self.last_points) > 0:
            if self.last_points[-1].next_on_side == None:
                self.last_points[-1].next_on_side = point
                point.prev_on_side = self.last_points[-1]

        point.isValid = not self.pointInAnyQuad(p)

        self.triangle_points.append(point)
        if prev != None and point.isValid:
            prev.next = point
        self.last_points.append(point)

        self.last_removed = prev
        return point

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

    def checkIntersections(self, quad, tpoint):
        if tpoint.prev == None and tpoint.next == None:
            return

        for j in range(4):
            v1 = quad[j]
            v2 = quad[(j+1)%4]
            if tpoint.prev != None and tpoint.prev.isValid:
                intersection = self.lineIntersection(v1, v2, tpoint.point, tpoint.prev.point)
                if intersection != None:
                    # TODO: May need to check if inside... Not sure, don't think so
                    if not self.pointInAnyQuad(intersection):
                        point = TrianglePoint(intersection, tpoint.prev, None)
                        self.triangle_points.append(point)
                        tpoint.prev.next = point
                        tpoint.prev = point

                        point2 = TrianglePoint(v1, None, point)
                        if not self.pointInAnyQuad(v1):
                            self.triangle_points.append(point2)

                        point2 = TrianglePoint(v2, None, point)
                        if not self.pointInAnyQuad(v2):
                            self.triangle_points.append(point2)

            if tpoint.next != None and tpoint.next.isValid:
                intersection = self.lineIntersection(v1, v2, tpoint.point, tpoint.next.point)
                if intersection != None:
                    # TODO: May need to check if inside... Not sure, don't think so
                    if not self.pointInAnyQuad(intersection):
                        point = TrianglePoint(intersection, None, tpoint.next)
                        self.triangle_points.append(point)
                        tpoint.next.prev = point
                        tpoint.next = point

                        point2 = TrianglePoint(v1, None, point)
                        if not self.pointInAnyQuad(v1):
                            self.triangle_points.append(point2)

                        point2 = TrianglePoint(v2, None, point)
                        if not self.pointInAnyQuad(v2):
                            self.triangle_points.append(point2)



    def removeCoverdPoint(self, q):
        new_triangle_points = []
        for t in self.triangle_points:
            if t.isValid:
                if self.pointInQuad(t.point, q):
                    self.checkIntersections(q, t)
                    if t.prev != None:
                        if t.next == None or t.next.prev == t:
                            t.prev.next = t.next
                    if t.next != None:
                        if t.prev == None or t.prev.next == t:
                            t.next.prev = t.prev
                    t.isValid = False
                else:
                    new_triangle_points.append(t)
        self.triangle_points  = new_triangle_points

    def stamp(self, mouse):
        if self.lastMouse != None:
            quad = []

            for i in range(len(self.brushPoints)):
                nextI = (i + 1) % len(self.brushPoints)
                x1 = self.brushPoints[i][0]
                y1 = self.brushPoints[i][1]
                point = (mouse.mouseX + x1, mouse.mouseY + y1)
                self.addNotCoveredPoint(point, i == len(self.brushPoints)-1)

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
                self.currentQuads.append(points)
                self.removeCoverdPoint(points)

            #TODO: Make this general for any poly brush
            points = []
            for i in range(len(self.brushPoints)):
                points.append((mouse.mouseX + self.brushPoints[i][0], mouse.mouseY + self.brushPoints[i][1]))
            self.currentQuads.append(points)
            self.removeCoverdPoint(points)

        self.lastMouse = copy.deepcopy(mouse)

    def clear_stroke(self):
        self.stroke_over = True
        width = 640
        height = 480

        points = []
        if self.lastMouse != None:
            count = 0
            for p in self.brushPoints:
                count = count + 1
                point = (self.lastMouse.mouseX + p[0], self.lastMouse.mouseY + p[1])
                self.addNotCoveredPoint(point, count == len(self.brushPoints))
                points.append(point)
            self.removeCoverdPoint(points)

        self.lastMouse = None

        #self.triangle_points = []
        lines = []

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

        array = np.empty([len(self.triangle_points), 2])
        i = 0
        for t in self.triangle_points:
            if t.isValid:
                array[i, 0] = int(t.point[0])
                array[i, 1] = int(t.point[1])
                i = i + 1

        A = dict(vertices = array[0:i]) #, segments = line_array)
        delauny_points = array[triangle.triangulate (A)['triangles']]
        for t in delauny_points:
            sum_x = 0
            sum_y = 0
            for p in t:
                sum_x = sum_x + p[0]
                sum_y = sum_y + p[1]

            # TODO: ELIMINATE 480!
            colors = glReadPixels(sum_x/3, 479 - sum_y/3, 1, 1, GL_RGBA, GL_FLOAT)

            self.triangles.append(Triangle(t, [colors[0][0], colors[0][0], colors[0][0]]))



class Painter:

    def __init__(self):
        self.mouse = Mouse()
        self.brush = Brush(50, 4)
        self.next_clear_stroke = False
        self.draw_outlines = False

    def resize(self, width, height):
        if height==0:
            height=1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, 0, 1)
        glMatrixMode(GL_MODELVIEW)

    def init(self):
        glDisable(GL_DEPTH_TEST)
        glutSetCursor(GLUT_CURSOR_NONE)
        glClearColor(1.0, 1.0, 1.0, 1.0)

    def draw_triangles(self):

        glClear(GL_COLOR_BUFFER_BIT)
        """
        glBegin(GL_TRIANGLES)
        glColor3f(0,0,0)

        for tri in triangles:
            glVertex2f(tri[0,0], tri[0,1])
            glVertex2f(tri[1,0], tri[1,1])
            glVertex2f(tri[2,0], tri[2,1])

        glEnd()

        for tri in triangles:
            glBegin(GL_LINE_LOOP)
            glColor3f(1,0,0)
            glVertex2f(tri[0,0], tri[0,1])
            glVertex2f(tri[1,0], tri[1,1])
            glVertex2f(tri[2,0], tri[2,1])

            glEnd()
        """

        self.brush.draw_cursor(self.mouse)
        if self.next_clear_stroke:
            self.brush.draw_stroke()
            self.brush.clear_stroke()
            self.next_clear_stroke = False
            glClear(GL_COLOR_BUFFER_BIT)
        self.brush.draw_stroke()
        self.brush.draw_triangles(self.draw_outlines)

        glutSwapBuffers()

    # The function called whenever a key is pressed. Note the use of Python tuples to pass in: (key, x, y)  
    def keyPressed(self, *args):
        # If escape is pressed, kill everything.
        if args[0] == ESCAPE:
            glutDestroyWindow(window)
            sys.exit()

    # The function called whenever the mouse is pressed. Note the use of Python tuples to pass in: (key, x, y)  
    def mousePressed(self, button, state, x, y):

        global lastX
        global lastY

        if button == GLUT_LEFT_BUTTON:
            if(state == GLUT_DOWN):
                lastX = x
                lastY = y
                self.mouse.mouseDown = True
                self.brush.new_stroke(self.mouse)
            else:
                self.next_clear_stroke = True
                self.mouse.mouseDown = False

        if button == GLUT_RIGHT_BUTTON:
            if(state == GLUT_DOWN):
                self.draw_outlines = not self.draw_outlines

    def removelines(self, points, lines, removeNumber):
        points = np.delete(points, removeNumber)
        indices = []
        i = len(lines)-4
        while i < len(lines):
            if lines[i,0] == removeNumber or lines[i,1] == removeNumber:
                np.delete(lines, i) 
            else:
                i = i + 1
        return points, lines

    # The function called whenever a key is pressed. Note the use of Python tuples to pass in: (key, x, y)  
    def mouseMoved(self, x, y):

        global lastX
        global lastY
        if self.mouse.mouseDown:
            diffX = x - lastX
            diffY = y - lastY
            if abs(diffX) + abs(diffY) > 50:
                self.brush.stamp (self.mouse)
                lastX = x
                lastY = y
        self.mouse.mouseX = x
        self.mouse.mouseY = y

def main():
    global window
    painter = Painter()

    glutInit(())

    window_width = 640
    window_height = 480

    # Select type of Display mode:   
    #  Double buffer 
    #  RGBA color
    # Alpha components supported 
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA)

    # get a 640 x 480 window 
    glutInitWindowSize(window_width, window_height)

    # the window starts at the upper left corner of the screen 
    glutInitWindowPosition(0, 0)

    # Okay, like the C version we retain the window id to use when closing, but for those of you new
    # to Python (like myself), remember this assignment would make the variable local and not global
    # if it weren't for the global declaration at the start of main.
    window = glutCreateWindow("Painter")

    glutDisplayFunc (painter.draw_triangles)

    # Uncomment this line to get full screen.
    #glutFullScreen()

    # When we are doing nothing, redraw the scene.
    glutIdleFunc(painter.draw_triangles)

    # Register the function called when our window is resized.
    glutReshapeFunc (painter.resize)

    # Register the function called when the keyboard is pressed.  
    glutKeyboardFunc (painter.keyPressed)

    # Register the function called when the mouse is pressed.  
    glutMouseFunc (painter.mousePressed)

    # Register the function called when the mouse is moved while pressed
    glutMotionFunc (painter.mouseMoved)

    # Register the function called when the mouse is moved.  
    glutPassiveMotionFunc (painter.mouseMoved)

    painter.init()

    # Initialize our window. 
    painter.resize (window_width, window_height)

    # Start Event Processing Engine	
    glutMainLoop()

# Print message to console, and kick off the main to get it rolling.
print "Hit ESC key to quit."
main()

