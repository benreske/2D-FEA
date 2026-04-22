from cmu_graphics import *
from cmu_cpcs_utils import *
import math
import random
import ezdxf
import sys
import tkinter as tk
from tkinter import filedialog

##SOURCE: claude.ai written code for tkinter
def getFilePath():
    root = tk.Tk()
    root.withdraw()
    filePath = filedialog.askopenfilename(title='Select a DXF file', 
                                          filetypes=[('DXF files', '*.dxf')])
    root.destroy()
    return filePath

##SOURCE: partially written by https://ezdxf.readthedocs.io/en/stable/tutorials/getting_data.html
def getDXF():
    filePath = getFilePath()
    if filePath == None:
        return None
    try:
        file = ezdxf.readfile(filePath)
        return file.modelspace()
    except IOError:
        print(f"Generic I/O error. Please check the file path and try again.")
        return None
    except ezdxf.DXFStructureError:
        print(f'''Invalid or corrupted DXF file. Please select a valid DXF file 
              and try again.''')
        return None

class Button:
    def __init__(self, left, top, width, height, label, color): 
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.label = label
        self.color = color
        self.clicked = False

    def isSelected(self, mouseX, mouseY):
        return (self.left <= mouseX <= self.left + self.width and 
                self.top <= mouseY <= self.top + self.height)

    def draw(self):
        drawRect(self.left, self.top, self.width, self.height, fill=self.color)
        drawLabel(self.label, self.left + self.width/2, self.top + 
                  self.height/2, fill='white', size=self.height/3, bold=True, 
                  font='Burger Crunchy')
    

def onAppStart(app):
    #files
    app.file = None
    app.drawableDXF = None
    #drawing
    app.width = 1600
    app.height = 900
    app.cx = app.width/2
    app.cy = app.height/2
    app.offsetX = 0
    app.offsetY = 0
    app.scale = 1
    app.buttons = []
    app.showChecklist = False
    app.buttons = createButtons(app)
    app.program = 0

def onAppRestart(app):
    #files
    app.file = None
    app.drawableDXF = None
    #program
    app.program = -1
    #drawing
    app.cx = app.width/2
    app.cy = app.height/2
    app.offsetX = 0
    app.offsetY = 0
    app.scale = 1
    app.startingPointHold = (None, None)
    app.showChecklist = False

def titleScreen_redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill=rgb(25, 25, 25))
    titleButton = Button(app.width/2 - 150, app.height/2 - 25, 300, 50, 
                         'CLICK TO START', fill='mediumSlateBlue')
    titleButton.draw()


def redrawAll(app):
    drawBackground(app)
    for button in app.buttons:
        button.draw()
    drawOutlines(app)
    if app.program == -1:
        drawRect(app.width/2 - 200, app.height/2 - 75, 400, 150, 
                 fill='lightBlue', border='black')
        drawLabel('2D FEA SOLVER', app.width/2, app.height/2-33, size=30, 
                  bold=True, font='Burger Crunchy')
        drawLabel('Click to select a DXF file',app.width/2, app.height/2 + 33, 
                  size=16)
    else:
        drawDXF(app)

def createButtons(app):
    programNames = ['Display Setup', 'Meshing', 'Material Properties', 
                     'Boundary Conditions', 'Loads', 'Solve']
    buttons = []
    for i in range(len(programNames)):
        button = Button(app.left + app.width - 300, 100 + i*50, 300, 50, 
                        programNames[i], rgb(30, 30, 30))
        buttons.append(button)
    return buttons

def drawBackground(app):
    drawRect(0, 0, app.width, app.height, fill=rgb(25, 25, 25))
    drawRect(app.left + app.width - 300, 0, 300, app.height, 
             fill=rgb(30, 30, 30))
    
def drawOutlines(app):
    drawRect(0, 0, app.width, app.height, fill=None, border=rgb(50, 50, 50), 
             borderWidth=1)
    drawRect(app.left + app.width - 300, 0, 300, app.height, fill=None, border=rgb(50, 50, 50), 
             borderWidth=1)
#SOURCE
def drawDXF(app):
    if app.drawableDXF == None:
        return
    edges = dict() #key: edge number; value: list of points that define polygon
    pointsToEdge = dict() #key: point; value: edge number that point belongs to
    for entity in app.drawableDXF:
        if entity.dxftype() == 'CIRCLE':
            center = entity.dxf.center
            pointsToEdge[center] = len(edges)
            radius = entity.dxf.radius
            drawCircle(app.cx + center[0] * app.scale, app.cy + center[1] 
                       * app.scale, radius * app.scale, border='black')
        elif isDrawable(entity):
            segments = getLineSegments(entity)
            for segment in segments:
                p1 = segment.start
                p2 = segment.end
                    
                

        
            
def isDrawable(entity):
    if entity.dxftype() in ['LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'SPLINE']:
        return True
    return False

def getEdgeNumber(segment):
    pass

def getEntityPoints(segment):
    pass

def solverScreen_onKeyPress(app, key):
    if app.program == 0:
        if key == 'up':
            app.scale *= 1.1
        elif key == 'down':
            app.scale /= 1.1

def titleScreen_onMousePress(app, mouseX, mouseY):
    #app.drawableDXF = getDXF()
    #app.program += 1
    #app.showChecklist = True
    pass

def solverScreen_onMousePress(app, mouseX, mouseY):
    if hitsChecklistEntry(app, mouseX, mouseY):
        app.program += 1
    if app.program == 0:
        app.startingPointHold = (mouseX, mouseY)

def solverScreen_onMouseDrag(app, mouseX, mouseY):
    if app.program == 0:
        startX, startY = app.startingPointHold
        app.offsetX = mouseX - startX
        app.offsetY = mouseY - startY

def solverScreen_onMouseRelease(app, mouseX, mouseY):
    if app.program == 0:
        app.cx += app.offsetX
        app.cy += app.offsetY
        app.offsetX = 0
        app.offsetY = 0

def solverScreen_onMouseMove(app, mouseX, mouseY):
    for button in app.buttons:
        if button.isSelected(mouseX, mouseY):
            button.color = rgb(50, 50, 50)
        else:
            button.color = rgb(30, 30, 30)

def main():
    runAppWithScreens(initialScreen='titleScreen')

main()
