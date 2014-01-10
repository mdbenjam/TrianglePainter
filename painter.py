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
import math
import shutil
import cProfile

import numpy as np
import brush


# Some api in the chain is translating the keystrokes to this octal string
# so instead of saying: ESCAPE = 27, we use the following.
ESCAPE = '\033'

window = 0

lastX = 0
lastY = 0

brushWidth = 10

out_name = ""

class Window:
    def __init__(self, width, height, zoom_width, zoom_height, center_x, center_y):
        self.width = width
        self.height = height
        self.zoom_width = zoom_width
        self.zoom_height = zoom_height
        self.center_x = center_x
        self.center_y = center_y

    def to_world_coords(self, x, y):
        return ((float(x)/self.width - .5) * self.zoom_width + self.center_x, (.5 - float(y)/self.height) * self.zoom_height + self.center_y)

    def to_window_coords(self, x, y):
        return (((float(x) - self.center_x)/self.zoom_width + .5)*self.width, (.5 - (float(y) - self.center_y)/self.zoom_height)*self.height)

class Mouse:
    def __init__(self):
        self.mouseX = 0
        self.mouseY = 0
        self.mouseDown = False

class Painter:

    def __init__(self, window):
        self.mouse = Mouse()
        self.window = window
        self.brush = brush.Brush(50, 100, window, (0,0,1,0.5), 100)
        self.next_clear_stroke = False
        self.draw_outlines = False
        self.currentScale = 1
        self.center = (0, 0)
        self.zooming = False
        self.width = 0
        self.height = 0
        self.fuzzy = 1

    def output(self, x, y, text):
        glRasterPos2f(x, y, 0)
        glColor3f(0, 0, 0)
        glDisable(GL_TEXTURE_2D)
        for p in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, c_int(ord(p)))

    def resize(self, width, height):
        if height==0:
            height=1
        self.window.width = width
        self.window.height = height
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, 0, 1)
        glMatrixMode(GL_MODELVIEW)

    def init(self):
        glDisable(GL_DEPTH_TEST)
        glutSetCursor(GLUT_CURSOR_NONE)
        glEnable (GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(1.0, 1.0, 1.0, 1.0)

    def zoom(self, z, x, y):
        x = float(x) / self.window.width - .5
        y = float(y) / self.window.height - .5
        preX = x * self.window.zoom_width
        preY = y * self.window.zoom_width
        self.window.zoom_width = self.window.zoom_width / z
        self.window.zoom_height = self.window.zoom_height / z
        postX = x * self.window.zoom_width
        postY = y * self.window.zoom_width
        self.window.center_x = self.window.center_x + preX
        self.window.center_y = self.window.center_y - preY




    def draw_triangles(self):

        glClear(GL_COLOR_BUFFER_BIT)



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

        if self.next_clear_stroke:
            self.brush.clear_stroke(self.window)
            self.next_clear_stroke = False

        #glPushMatrix()
        #glTranslated(-self.window.center_x, -self.window.center_y, 0)
        self.brush.draw_triangles(self.draw_outlines)
        #glPopMatrix()
        self.brush.draw_cursor(self.mouse, self.window)
        self.brush.draw_stroke()
        #self.brush.draw_contours()


        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.window.width, 0, self.window.height,
                -1,
                1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        (xcoord, ycoord) = self.window.to_world_coords(self.mouse.mouseX, self.mouse.mouseY)
        self.output(10, 10, 'X, Y: '+str(xcoord)+' '+str(ycoord))

        glutSwapBuffers()

    # The function called whenever a key is pressed. Note the use of Python tuples to pass in: (key, x, y)  
    def keyPressed(self, *args):
        # If escape is pressed, kill everything.
        if args[0] == ESCAPE:
            glutDestroyWindow(window)
            sys.exit()
        if args[0] == 'o':
            out_name = raw_input('Open File: ')
            if os.path.exists(out_name):
                self.brush.load(out_name, self.window)
        if args[0] == 's':
            out_name = raw_input('Save File: ')
            self.brush.save(out_name)

        if args[0] == 'a':
            out_name = 'last_stroke.txt'
            if os.path.exists(out_name):
                self.brush.load(out_name, self.window)

        if args[0] == 'S':
            shutil.move('hold.txt', 'last_stroke_action.txt')

        if args[0] == 'A':
            out_name = 'last_stroke_action.txt'
            if os.path.exists(out_name):
                self.brush.load_action(out_name, self.window)

        if args[0] == ']':
            new_size = self.brush.get_size()+5
            self.brush.set_size(new_size, new_size*2*self.fuzzy)
        if args[0] == '[':
            new_size = self.brush.get_size()-5
            self.brush.set_size(new_size, new_size*2*self.fuzzy)

        if args[0] == 'r':
            self.brush.change_color((1,0,0,0.5))
        if args[0] == 'g':
            self.brush.change_color((0,1,0,0.5))
        if args[0] == 'b':
            self.brush.change_color((0,0,1,0.5))
        if args[0] == 'l':
            self.brush.change_color((0,0,0,0.5))
        if args[0] == 'c':
            self.brush.cycle(1)
        if args[0] == 'x':
            self.brush.cycle(-1)
        if args[0] == 'z':
            self.zooming = True
        if args[0] == 'f':
            if self.fuzzy == 0:
                self.fuzzy = 1
            else:
                self.fuzzy = 0
            size = self.brush.get_size()
            self.brush.set_size(size, size*2*self.fuzzy)

    def keyReleased(self, *args):
        if args[0] == 'z':
            self.zooming = False

    # The function called whenever the mouse is pressed. Note the use of Python tuples to pass in: (key, x, y)
    def mousePressed(self, button, state, x, y):

        global lastX
        global lastY

        if self.zooming:
            if button == GLUT_LEFT_BUTTON:
                if(state == GLUT_UP):
                    self.zoom(2, x, y)
            if button == GLUT_RIGHT_BUTTON:
                if(state == GLUT_UP):
                    self.zoom(.5, x, y)
        else:
            if button == GLUT_LEFT_BUTTON:
                if(state == GLUT_DOWN):
                    lastX = x
                    lastY = y
                    self.mouse.mouseDown = True
                    self.brush.new_stroke(self.mouse, self.window)
                else:
                    self.next_clear_stroke = True
                    self.mouse.mouseDown = False

            if button == GLUT_RIGHT_BUTTON:
                if(state == GLUT_DOWN):
                    self.draw_outlines = not self.draw_outlines


    def mouseWheel(self, button, dir, x, y):
        if dir > 0:
            # Scroll Up
            self.zoom(2)

        if dir < 0:
            # Scroll Down
            self.zoom(.5)

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
            if abs(diffX) + abs(diffY) > 5:
                self.brush.stamp (self.mouse, self.window)
                lastX = x
                lastY = y
        self.mouse.mouseX = x
        self.mouse.mouseY = y

def main():
    global window
    global out_name

    glutInit(())

    window_width = 640
    window_height = 480
    window_params = Window(window_width, window_height, window_width, window_height, 0, 0)

    out_name = "last_stroke.txt"#raw_input("FileName: ")

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

    painter = Painter(window_params)
    glutDisplayFunc (painter.draw_triangles)

    # Uncomment this line to get full screen.
    #glutFullScreen()

    # When we are doing nothing, redraw the scene.
    glutIdleFunc(painter.draw_triangles)

    # Register the function called when our window is resized.
    glutReshapeFunc (painter.resize)

    # Register the function called when the keyboard is pressed.  
    glutKeyboardFunc (painter.keyPressed)
    glutKeyboardUpFunc (painter.keyReleased)

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

