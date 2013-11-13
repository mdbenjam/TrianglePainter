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
    def __init__(self, width, height):
        self.width = width
        self.height = height


class Mouse:
    def __init__(self):
        self.mouseX = 0
        self.mouseY = 0
        self.mouseDown = False

class Painter:

    def __init__(self):
        self.mouse = Mouse()
        self.brush = brush.Brush(50, 4, (0,0,1,1))
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

        if self.next_clear_stroke:
            self.brush.clear_stroke()
            self.next_clear_stroke = False

        self.brush.draw_triangles(self.draw_outlines)
        self.brush.draw_cursor(self.mouse)
        self.brush.draw_stroke()
        #self.brush.draw_contours()

        glutSwapBuffers()

    # The function called whenever a key is pressed. Note the use of Python tuples to pass in: (key, x, y)  
    def keyPressed(self, *args):
        # If escape is pressed, kill everything.
        if args[0] == ESCAPE:
            glutDestroyWindow(window)
            sys.exit()
        if args[0] == 'a':
            if os.path.exists(out_name):
                f = open(out_name, 'r')
                self.brush.load(f)
                f.close()
            else:
                f = open(out_name, 'w')
                self.brush.save(f)
                f.close()
        if args[0] == 'r':
            self.brush.change_color((1,0,0,1))
        if args[0] == 'g':
            self.brush.change_color((0,1,0,1))
        if args[0] == 'b':
            self.brush.change_color((0,0,1,1))
        if args[0] == 'l':
            self.brush.change_color((0,0,0,1))

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
            if abs(diffX) + abs(diffY) > 5:
                self.brush.stamp (self.mouse)
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
    window_params = Window(window_width, window_height)

    out_name = "out1.txt"#raw_input("FileName: ")

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

    painter = Painter()
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

