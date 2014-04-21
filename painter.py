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
#import cProfile

import numpy as np
import brush
import threading
import geometry
import random
import time

import wx
try:
    from wx import glcanvas
    haveGLCanvas = True
except ImportError:
    haveGLCanvas = False
    print 'FAILED TO IMPORT'


# Some api in the chain is translating the keystrokes to this octal string
# so instead of saying: ESCAPE = 27, we use the following.
ESCAPE = '\033'

window = 0


brushWidth = 10

out_name = ""



class Painter:

    def __init__(self, window):
        self.mouse = geometry.Mouse()
        self.window = window
        
        self.eccentricity = 1
        self.angle = 0
        self.hardness = .5
        self.size = 50
        self.opacity = .5
        self.color = (0, 0, 0, self.opacity)

        self.brush = brush.Brush(self.size, 100, window, self.color, self.hardness)
        self.next_clear_stroke = False
        self.draw_outlines = False
        self.currentScale = 1
        self.center = (0, 0)
        self.zooming = False
        self.panning = False
        self.panningStarted = False
        self.width = 0
        self.height = 0
        self.zoomLevel = 1

        self.recordIndex = 0



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


    def checkWindowDimensions(self):
        if (self.window.center_x - self.window.zoom_width/2 < -self.window.original_width/2):
            self.window.center_x = -self.window.original_width/2 + self.window.zoom_width/2
        if (self.window.center_x + self.window.zoom_width/2 > self.window.original_width/2):
            self.window.center_x = self.window.original_width/2 - self.window.zoom_width/2
        if (self.window.center_y - self.window.zoom_height/2 < -self.window.original_height/2):
            self.window.center_y = -self.window.original_height/2 + self.window.zoom_height/2
        if (self.window.center_y + self.window.zoom_height/2 > self.window.original_height/2):
            self.window.center_y = self.window.original_height/2 - self.window.zoom_height/2

    def zoom(self, z, x, y):
        if not self.mouse.mouseDown:
            x = float(x) / self.window.width - .5
            y = float(y) / self.window.height - .5
            preX = x * self.window.zoom_width
            preY = y * self.window.zoom_width
            self.window.zoom_width = self.window.zoom_width / z
            self.window.zoom_height = self.window.zoom_height / z
            postX = x * self.window.zoom_width
            postY = y * self.window.zoom_width
            self.window.center_x = self.window.center_x + preX - postX
            self.window.center_y = self.window.center_y - preY + postY

            self.checkWindowDimensions()

            if (self.window.zoom_width > self.window.original_width or 
                self.window.zoom_height > self.window.original_height):
                self.window.zoom_width = self.window.original_width
                self.window.zoom_height = self.window.original_height
                self.window.center_x = 0
                self.window.center_y = 0

            self.zoomLevel = self.window.original_width / self.window.zoom_width
            self.brush.set_size(self.size, self.hardness, self.zoomLevel)

    def pan(self, x, y):
        self.window.center_x -= x/self.zoomLevel
        self.window.center_y += y/self.zoomLevel

        self.checkWindowDimensions()

    def draw_triangles(self, canvas):
        self.canvas = canvas
        # texID = glGenTextures(1)
        # glBindTexture(GL_TEXTURE_2D, texID)
        # glTexImage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGBA8, self.window.width, self.window.height, False )

        # fboID = glGenFramebuffers(1)
        # glBindFramebuffer(GL_FRAMEBUFFER, fboID)
        # glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, texID, 0)



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
        # glEnable(GL_MULTISAMPLE)
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
        self.brush.draw_triangles(self.draw_outlines)
        self.brush.draw_stroke()
        if self.next_clear_stroke:
            canvas.SwapBuffers()
            self.brush.clear_stroke(self.window, canvas)
            self.next_clear_stroke = False
            self.draw_triangles(canvas)
            return

        #glPushMatrix()
        #glTranslated(-self.window.center_x, -self.window.center_y, 0)

        #glPopMatrix()
        self.brush.draw_cursor(self.mouse, self.window)

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
  
        # glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        # glBindFramebuffer(GL_READ_FRAMEBUFFER, fboID)
        # glDrawBuffer(GL_BACK)
        # glBlitFramebuffer(0, 0, self.window.width, self.window.height, 0, 0, self.window.width, self.window.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        canvas.SwapBuffers()
        # glDisable(GL_MULTISAMPLE)

    # The function called whenever a key is pressed. Note the use of Python tuples to pass in: (key, x, y)  
    def keyPressed(self, evt):
        upperCaseShift = ord('a')-ord('A')
        # If escape is pressed, kill everything.
        code = evt.GetKeyCode()
        # if not evt.ShiftDown() and 65 <= code <= 90:
        #     code += 32
        # key = chr(code)

        # if key == ESCAPE:
        #     sys.exit()
        # if key == 'o':
        #     out_name = raw_input('Open File: ')
        #     if os.path.exists(out_name):
        #         self.brush.load(out_name, self.window)
        # if key == 's':
        #     out_name = raw_input('Save File: ')
        #     self.brush.save(out_name)

        # if key == 'a':
        #     out_name = 'last_stroke.txt'
        #     if os.path.exists(out_name):
        #         self.brush.load(out_name, self.window)

        # if key == 'S':
        #     shutil.move('hold.txt', 'last_stroke_action.txt')

        # if key == 'A':
        #     out_name = 'last_stroke_action.txt'
        #     if os.path.exists(out_name):
        #         self.brush.load_action(out_name, self.window)

        # if key == ']':
        #     new_size = self.brush.get_size()+5
        #     #self.brush.set_size(new_size, new_size*2*self.fuzzy)
        # if key == '[':
        #     new_size = self.brush.get_size()-5
        #     #self.brush.set_size(new_size, new_size*2*self.fuzzy)

        # if key == 'r':
        #     self.brush.change_color((1,0,0,self.opacity))
        # if key == 'g':
        #     self.brush.change_color((0,1,0,self.opacity))
        # if key == 'b':
        #     self.brush.change_color((0,0,1,self.opacity))
        # if key == 'l':
        #     self.brush.change_color((0,0,0,self.opacity))
        # if key == 't':
        #     if self.opacity < 1:
        #         self.opacity = 1
        #     else:
        #         self.opacity = .5
        #     self.brush.change_color([self.brush.color[0], self.brush.color[1], self.brush.color[2], self.opacity])
        # if key == 'c':
        #     self.brush.cycle(1)
        # if key == 'x':
        #     self.brush.cycle(-1)
        
        if code == ord('z')-upperCaseShift:
            self.zooming = True

        # if code == ord('s')-upperCaseShift:
        #     self.brush.saveImage('testImage', self.window, self.draw_outlines)

        if code == ord('p')-upperCaseShift:
            self.panning = True

        if code == wx.WXK_BACK and evt.CmdDown():
            self.brush.clear(self.window)

        if code == ord('r')-upperCaseShift and evt.CmdDown():
            self.randomStroke()
        # if key == 'q':
        #     self.brush.simplify()

        # if key == 'f':
        #     if self.fuzzy == 0:
        #         self.fuzzy = 1
        #     else:
        #         self.fuzzy = 0
        #     size = self.brush.get_size()
        #     self.brush.set_size(size, size*2*self.fuzzy)

    def randomStroke(self):
        denom = 0
        while denom == 0:
            startX = random.randint(0, self.window.width)
            startY = random.randint(0, self.window.height)
            endX = random.randint(0, self.window.width)
            endY = random.randint(0, self.window.height)

            if startX > endX:
                startX, endX = endX, startX
            denom = (startX - endX)


        startX = self.window.width/4
        endX = self.window.width*3/4
        startY = self.window.height/4
        endY = self.window.height*3/4
        denom = (startX - endX)
        # z = random.random()*10.0
        # self.zoom(z, random.randint(0, self.window.width), random.randint(0, self.window.height))

        slope = float((startY - endY))/denom
        y = float(startY)
        self.mouse.mouseX = startX
        self.mouse.mouseY = startY

        self.brush.new_stroke(self.mouse, self.window)
        for x in range(startX+40, endX, 40):
            y += slope*40
            self.mouse.mouseX = x
            self.mouse.mouseY = y
            self.brush.stamp (self.mouse, self.window)
            #time.sleep(.01)
            self.draw_triangles(self.canvas)
            
        self.next_clear_stroke = True
        self.draw_triangles(self.canvas)
        # self.zoom(1/z/2.0, random.randint(0, self.window.width), random.randint(0, self.window.height))

    def randomStrokes50(self):
        for i in range(50):
            self.randomStroke()

    def setColor(self, color, integer=True):
        if integer:
            self.color = (color[0]/255.0, color[1]/255.0, color[2]/255.0, self.opacity)
        else:
            self.color = (color[0], color[1], color[2], self.opacity)

        self.brush.change_color(self.color)

    def setShape(self, numSides):
        self.brush.set_sides(numSides, self.zoomLevel)

    def setSize(self, size):
        self.size = size
        self.brush.set_size(self.size, self.hardness, self.zoomLevel)

    def setHardness(self, size):
        self.hardness = size
        self.brush.set_size(self.size, self.hardness, self.zoomLevel)

    def setAngle(self, angle):
        self.angle = angle
        self.brush.set_angle(angle, self.zoomLevel)

    def setEccentricity(self, e):
        self.eccentricity = e
        self.brush.set_eccentricity(e, self.zoomLevel)

    def setOpacity(self, opacity):
        self.opacity = opacity
        self.color = (self.color[0], self.color[1], self.color[2], self.opacity)
        self.brush.change_color(self.color)

    def playRecord(self, canvas):
        self.brush.play_record(self.recordIndex, canvas)
        self.recordIndex += 1

    def playAllRecords(self, canvas):
        while self.recordIndex < self.brush.get_strokes_in_record()-1:
            self.brush.play_record(self.recordIndex, canvas)
            self.recordIndex += 1

    def recover(self):
        if os.path.isfile('recoveryCanvas.art'):
            self.loadFile('recoveryCanvas.art')

    def loadRecord(self, name):
        self.brush.open_record(name)

    def saveAll(self, name):
        self.brush.saveAll(name)

    def saveImage(self, name):
        self.brush.saveImage(name, self.window, self.draw_outlines)

    def loadFile(self, name):
        self.brush.load(name)

    def undo(self):
        self.brush.undo()

    def redo(self):
        self.brush.undo(redo = 1)

    def keyReleased(self, evt):
        upperCaseShift = ord('a')-ord('A')
        key = evt.GetKeyCode()
        if key == ord('z')-upperCaseShift:
            self.zooming = False
        if key == ord('p')-upperCaseShift:
            self.panning = False

    # The function called whenever the mouse is pressed. Note the use of Python tuples to pass in: (key, x, y)
    def mousePressed(self, evt):
        x, y = evt.GetPosition()

        if evt.AltDown():
            if evt.LeftUp():
                self.zoom(2., x, y)
            if evt.RightUp():
                self.zoom(.5, x, y)
        elif evt.CmdDown() or self.panningStarted:
            if evt.LeftDown():
                self.lastX = x
                self.lastY = y
                self.mouse.mouseDown = True
                self.panningStarted = True
            if evt.LeftUp():
                self.mouse.mouseDown = False
                self.panningStarted = False

            if evt.CmdDown():
                if evt.RightDown():
                    self.brush.pick_color(x, y, self.window)
        else:
            if evt.LeftDown():
                self.lastX = x
                self.lastY = y
                self.mouse.mouseDown = True
                self.brush.new_stroke(self.mouse, self.window)
            if evt.LeftUp():
                self.next_clear_stroke = True
                self.mouse.mouseDown = False

            if evt.RightDown():
                self.draw_outlines = not self.draw_outlines


    def mouseWheel(self, evt):
        direction = evt.GetWheelRotation()
        x = evt.GetX()
        y = evt.GetY()
        if direction > 0:
            # Scroll Up
            self.zoom(1.25, x, y)

        if direction < 0:
            # Scroll Down
            self.zoom(.8, x, y)

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
    def mouseMoved(self, evt):
        x, y = evt.GetPosition()

        if self.panningStarted:
            self.pan(x - self.lastX, y - self.lastY)
            self.lastX = x
            self.lastY = y
        else:
            if self.mouse.mouseDown:
                diffX = x - self.lastX
                diffY = y - self.lastY
                if abs(diffX) + abs(diffY) > 5:
                    self.brush.stamp (self.mouse, self.window)
                    self.lastX = x
                    self.lastY = y
        self.mouse.mouseX = x
        self.mouse.mouseY = y


class ButtonPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)



        box = wx.BoxSizer(wx.VERTICAL)
        box.Add((20, 30))

        frame = wx.Frame(None, -1, "Canvas", size=(1280,750), pos=(200, 200), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        self.paintCanvas = PaintCanvas(frame, self) # CubeCanvas(frame) or ConeCanvas(frame); frame passed to MyCanvasBase
        self.paintCanvas.Bind(wx.EVT_MOUSEWHEEL, self.paintCanvas.OnMouseWheel)
        #self.paintCanvas.InitGL()

        self.colorPanel = wx.Panel(self, -1, size=(100, 100))
        box.Add(self.colorPanel, 0, wx.ALIGN_CENTER|wx.ALL, 15)
        self.colorPanel.Bind(wx.EVT_LEFT_DOWN, self.OnColorButton)

        self.lastColor = (0, 0, 0)
        self.colorPanel.SetBackgroundColour(self.lastColor)

        triangleImage = wx.Image("triangleIcon.jpg", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.triangleButton = wx.BitmapButton(self, 1, bitmap = triangleImage, size=(50, 50))
        sqaureImage = wx.Image("squareIcon.jpg", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.squareButton = wx.BitmapButton(self, 2, bitmap = sqaureImage, size=(50, 50))
        circleImage = wx.Image("circleIcon.jpg", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.circleButton = wx.BitmapButton(self, 3, bitmap = circleImage, size=(50, 50))

        shapeButtonBox = wx.BoxSizer(wx.HORIZONTAL)

        shapeButtonBox.Add(self.triangleButton, -1, wx.ALIGN_CENTER)
        shapeButtonBox.Add(self.squareButton, -1, wx.ALIGN_CENTER)
        shapeButtonBox.Add(self.circleButton, -1, wx.ALIGN_CENTER)
        
        self.triangleButton.Bind(wx.EVT_BUTTON, self.paintCanvas.OnChangeShape, id=1)
        self.squareButton.Bind(wx.EVT_BUTTON, self.paintCanvas.OnChangeShape, id=2)
        self.circleButton.Bind(wx.EVT_BUTTON, self.paintCanvas.OnChangeShape, id=3)

        box.Add(shapeButtonBox, -1, wx.EXPAND)


        
        self.eccentricitySlider = wx.Slider(self, 10, 10, 10, 50)
        self.eccentricityText = wx.StaticText(self, -1, 'Eccentricity: '+str(self.eccentricitySlider.GetValue()))
        # self.paintCanvas.setOpacity(self.opacitySlider.GetValue())
        
        self.eccentricitySlider.Bind(wx.EVT_SLIDER, self.OnChangeEccentricity, id=10)
        box.Add(self.eccentricityText, -1, wx.ALIGN_CENTER)
        box.Add(self.eccentricitySlider)

        
        self.angleSlider = wx.Slider(self, 11, 0, 0, 100)
        self.angleText = wx.StaticText(self, -1, 'Angle: '+str(self.angleSlider.GetValue()))
        # self.paintCanvas.setOpacity(self.opacitySlider.GetValue())
        
        self.angleSlider.Bind(wx.EVT_SLIDER, self.OnChangeAngle, id=11)
        box.Add(self.angleText, -1, wx.ALIGN_CENTER)
        box.Add(self.angleSlider)


        
        self.opacitySlider = wx.Slider(self, 6, 50, 0, 100)
        self.opacityText = wx.StaticText(self, -1, 'Opacity: '+str(self.opacitySlider.GetValue()))
        # self.paintCanvas.setOpacity(self.opacitySlider.GetValue())
        
        self.opacitySlider.Bind(wx.EVT_SLIDER, self.OnChangeOpacity, id=6)
        box.Add(self.opacityText, -1, wx.ALIGN_CENTER)
        box.Add(self.opacitySlider)


        self.sizeSlider = wx.Slider(self, 4, 50, 5, 100)
        self.sizeText = wx.StaticText(self, -1, 'Size: '+str(self.sizeSlider.GetValue()))
        # self.paintCanvas.setSize(self.sizeSlider.GetValue())

        self.sizeSlider.Bind(wx.EVT_SLIDER, self.OnChangeSize, id=4)
        box.Add(self.sizeText, -1, wx.ALIGN_CENTER)
        box.Add(self.sizeSlider)


        self.hardnessSlider = wx.Slider(self, 5, 50, 10, 100)
        self.hardnessText = wx.StaticText(self, -1, 'Hardness: '+str(self.hardnessSlider.GetValue()))
        # self.paintCanvas.setHardnessSize(self.hardnessSizeSlider.GetValue())
        
        self.hardnessSlider.Bind(wx.EVT_SLIDER, self.OnChangeHardness, id=5)
        box.Add(self.hardnessText, -1, wx.ALIGN_CENTER)
        box.Add(self.hardnessSlider)




        self.playRecord = wx.Button(self, 7, label = 'Play Record')
        self.playRecord.Bind(wx.EVT_BUTTON, self.paintCanvas.PlayRecord, id=7)
        
        self.playAllRecords = wx.Button(self, 8, label = 'Play All')
        self.playAllRecords.Bind(wx.EVT_BUTTON, self.paintCanvas.PlayAllRecords, id=8)
        
        self.recover = wx.Button(self, 9, label = 'Recover')
        self.recover.Bind(wx.EVT_BUTTON, self.paintCanvas.Recover, id=9)

        playBox = wx.BoxSizer(wx.HORIZONTAL)
        playBox.Add(self.playRecord, 0, wx.ALIGN_CENTER)
        playBox.Add(self.playAllRecords, 0, wx.ALIGN_CENTER)
        
        box.Add(playBox)
        box.Add(self.recover, 0, wx.ALIGN_CENTER)

        self.SetAutoLayout(True)
        self.SetSizer(box)

        
        frame.Show(True)
        self.lastColor = None

    def OnKeyDown(self, evt):
        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnColorButton(evt)
        else:
            self.paintCanvas.OnKeyDown(evt)

    def OnColorButton(self, evt):
        if not self.lastColor is None:
            data = wx.ColourData()
            data.SetColour(wx.Colour(self.lastColor[0], self.lastColor[1], self.lastColor[2]))
            dlg = wx.ColourDialog(self, data)
        else:
            dlg = wx.ColourDialog(self)

        # Ensure the full colour dialog is displayed, 
        # not the abbreviated version.
        dlg.GetColourData().SetChooseFull(True)
 
        if dlg.ShowModal() == wx.ID_OK:
            self.lastColor = dlg.GetColourData().GetColour().Get()
            print 'data', self.lastColor
            self.paintCanvas.setColor(self.lastColor)
            self.colorPanel.SetBackgroundColour(self.lastColor)
            self.Refresh()
 
        dlg.Destroy()

    def OnChangeAngle(self, evt):
        self.paintCanvas.setAngle(self.angleSlider.GetValue())
        self.angleText.SetLabel('Angle: '+str(self.angleSlider.GetValue()))

    def OnChangeEccentricity(self, evt):
        self.paintCanvas.setEccentricity(self.eccentricitySlider.GetValue())
        self.eccentricityText.SetLabel('Eccentricity: '+str(self.eccentricitySlider.GetValue()))

    def OnChangeSize(self, evt):
        self.paintCanvas.setSize(self.sizeSlider.GetValue())
        self.sizeText.SetLabel('Size: '+str(self.sizeSlider.GetValue()))

    def OnChangeHardness(self, evt):
        self.paintCanvas.setHardness(self.hardnessSlider.GetValue())
        self.hardnessText.SetLabel('Hardness: '+str(self.hardnessSlider.GetValue()))

    def OnChangeOpacity(self, evt):
        self.paintCanvas.setOpacity(self.opacitySlider.GetValue())
        self.opacityText.SetLabel('Opacity: '+str(self.opacitySlider.GetValue()))

    def OnLoadRecordFile(self, evt):
        openFileDialog = wx.FileDialog(self, "Open Record", "", "",
                       "Record Files (*.rec)|*.rec", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        self.paintCanvas.LoadRecord(openFileDialog.GetPath())

    def OnSaveImage(self, evt):
        saveFileDialog = wx.FileDialog(self, "Save Image", "", "",
                       "Image Files (*.png)|*.png", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if saveFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        self.paintCanvas.SaveImage(saveFileDialog.GetPath())

    def OnLoadFile(self, evt):
        openFileDialog = wx.FileDialog(self, "Open Art", "", "",
                       "Art Files (*.art)|*.art", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        self.paintCanvas.LoadFile(openFileDialog.GetPath())

    def OnSaveAll(self, evt):
        saveFileDialog = wx.FileDialog(self, "Save", "", "",
                       "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if saveFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        self.paintCanvas.SaveAll(saveFileDialog.GetPath())

    def OnUndo(self, evt):
        self.paintCanvas.Undo()

    def OnRedo(self, evt):
        self.paintCanvas.Redo()

class MyCanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent, panel):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.InitGL()
        self.init = True
        self.context = glcanvas.GLContext(self)

        
        # initial mouse position
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_IDLE, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_KEY_DOWN, panel.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnSize(event)

    def DoSetViewport(self):
        if not self.init:
            self.InitGL()
            self.init = True
        size = self.size = self.GetClientSize()
        self.SetCurrent(self.context)
        glViewport(0, 0, size.width, size.height)
        
    def OnPaint(self, event):
        graphicsContext = wx.GraphicsContext.Create(self)
        #print 'antialiasing: ', graphicsContext.SetAntialiasMode(wx.ANTIALIAS_DEFAULT)
        #self.SetCurrent(graphicsContext)
        self.SetCurrent(self.context)
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()

    def OnMouseDown(self, evt):
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnMouseDown(evt)

    def OnMouseUp(self, evt):
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnMouseUp(evt)

    def OnMouseMotion(self, evt):
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnMouseMotion(evt)

    def OnKeyUp(self, evt):
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnKeyUp(evt)

    def OnKeyDown(self, evt):
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnKeyDown(evt)

class PaintCanvas(MyCanvasBase):
    def InitGL(self):
        # Select type of Display mode:   
        #  Double buffer 
        #  RGBA color
        # Alpha components supported 
        # glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_MULTISAMPLE)

        # # get a 640 x 480 window 
        # glutInitWindowSize(window_width, window_height)

        # # the window starts at the upper left corner of the screen 
        # glutInitWindowPosition(0, 0)

        # # Okay, like the C version we retain the window id to use when closing, but for those of you new
        # # to Python (like myself), remember this assignment would make the variable local and not global
        # # if it weren't for the global declaration at the start of main.
        # window = glutCreateWindow("Painter")


        # # Uncomment this line to get full screen.
        # #glutFullScreen()

        # # Register the function called when the keyboard is pressed.  
        # glutKeyboardFunc (painter.keyPressed)
        # glutKeyboardUpFunc (painter.keyReleased)
        window_width = 1280
        window_height = 750
        window_params = geometry.Window(window_width, window_height, window_width, window_height, 0, 0)

        out_name = "last_stroke.txt"#raw_input("FileName: ")
        self.painter = Painter(window_params)
        self.painter.init()

    def setColor(self, color):
        print color
        self.painter.setColor(color)

    def OnChangeShape(self, evt):
        print 'id', evt.GetId()
        if evt.GetId() == 1:
            self.painter.setShape(3)
        elif evt.GetId() == 2:
            self.painter.setShape(4)
        elif evt.GetId() == 3:
            self.painter.setShape(100)

    def setSize(self, size):
        self.painter.setSize(size)

    def setHardness(self, size):
        self.painter.setHardness(size/100.0)

    def setOpacity(self, opacity):
        self.painter.setOpacity(opacity/100.0)

    def setEccentricity(self, e):
        self.painter.setEccentricity(e/10.0)

    def setAngle(self, a):
        self.painter.setAngle(a/50.0*math.pi)

    def PlayRecord(self, evt):
        self.painter.playRecord(self)

    def PlayAllRecords(self, evt):
        self.painter.playAllRecords(self)

    def Recover(self, evt):
        self.painter.recover()

    def LoadRecord(self, name):
        self.painter.loadRecord(name)

    def SaveAll(self, name):
        self.painter.saveAll(name)
    
    def LoadFile(self, name):
        self.painter.loadFile(name)
    
    def SaveImage(self, name):
        self.painter.saveImage(name)

    def Undo(self):
        self.painter.undo()

    def Redo(self):
        self.painter.redo()

    def OnDraw(self):
        self.painter.draw_triangles(self)

    def OnMouseDown(self, evt):
        self.painter.mousePressed(evt)

    def OnMouseUp(self, evt):
        self.painter.mousePressed(evt)

    def OnMouseMotion(self, evt):
        self.painter.mouseMoved(evt)

    def OnMouseWheel(self, evt):
        self.painter.mouseWheel(evt)
    
    def OnSize(self, evt):
        width, height = evt.GetSize()
        self.painter.resize(width, height)

    def OnKeyUp(self, evt):
        self.painter.keyReleased(evt)

    def OnKeyDown(self, evt):
        self.painter.keyPressed(evt)

class RunDemoApp(wx.App):
    def __init__(self):
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        frame = wx.Frame(None, -1, "Triangle Painter", pos=(30,100),
                        style=wx.DEFAULT_FRAME_STYLE, name="run a sample")
        frame.CreateStatusBar()

        menuBar = wx.MenuBar()
        menu = wx.Menu()

        loadItem = menu.Append(wx.ID_OPEN)
        saveAll = menu.Append(wx.ID_SAVE)
        loadRecordItem = menu.Append(-1, "Load Record", "Load File")
        saveImage = menu.Append(-1, "Save Image", "Save File")
        exitItem = menu.Append(wx.ID_CANCEL, "E&xit\tCtrl-Q", "Exit Painter")
        
        menuBar.Append(menu, "&File")

        editMenu = wx.Menu()
        undoItem = editMenu.Append(wx.ID_UNDO)
        redoItem = editMenu.Append(wx.ID_REDO)
        
        menuBar.Append(editMenu, "&Edit")
        
        frame.SetMenuBar(menuBar)
        frame.Show(True)
        frame.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

        win = ButtonPanel(frame)

        # set the frame to a good size for showing the two buttons
        frame.SetSize((150, 500))
        win.SetFocus()
        self.window = win
        frect = frame.GetRect()

        self.SetTopWindow(frame)
        self.frame = frame

        self.Bind(wx.EVT_MENU, win.OnLoadFile, loadItem)
        self.Bind(wx.EVT_MENU, win.OnSaveAll, saveAll)
        self.Bind(wx.EVT_MENU, win.OnLoadRecordFile, loadRecordItem)
        self.Bind(wx.EVT_MENU, win.OnSaveImage, saveImage)

        self.Bind(wx.EVT_MENU, self.OnExitApp, exitItem)

        self.Bind(wx.EVT_MENU, win.OnUndo, undoItem)
        self.Bind(wx.EVT_MENU, win.OnRedo, redoItem)

        return True
        
    def OnExitApp(self, evt):
        self.frame.Close(True)

    def OnCloseFrame(self, evt):
        sys.exit(0)
        evt.Skip()

app = RunDemoApp()
app.MainLoop()

#main()

