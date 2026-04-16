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

def onAppStart(app):
    #files
    app.file = None
    app.drawableDXF = None
    app.menu = True
    app.displayDXF = False
    #drawing
    app.width = 1600
    app.height = 900
    app.cx = app.width/2
    app.cy = app.height/2
    app.offsetX = 0
    app.offsetY = 0
    app.scale = 1
    app.showChecklist = False
    app.checklist = ['DISPLAY SETUP', 'MATERIAL PROPERTIES', 'MESHING', 
                     'BOUNDARY CONDITIONS', 'LOADS', 'SOLVE']
    app.currentStep = -1

def onAppRestart(app):
    #files
    app.file = None
    app.drawableDXF = None
    app.menu = True
    app.displayDXF = False
    #drawing
    app.cx = app.width/2
    app.cy = app.height/2
    app.offsetX = 0
    app.offsetY = 0
    app.scale = 1
    app.startingPointHold = (None, None)
    app.showChecklist = False
    app.currentStep = -1

def redrawAll(app):
    drawTitle(app)
    drawChecklist(app)
    if app.currentStep == -1:
        drawRect(app.width/2 - 200, app.height/2 - 75, 400, 150, 
                 fill='lightBlue', border='black')
        drawLabel('2D FEA SOLVER', app.width/2, app.height/2-33, size=30, 
                  bold=True)
        drawLabel('Click to select a DXF file',app.width/2, app.height/2 + 33, 
                  size=16)
    else:
        drawDXF(app)

def drawChecklist(app):
    if app.currentStep == -1: return
    drawRect(1250, 100, 300, 300, fill=None, border='black', borderWidth=4)
    drawLabel('CHECKLIST', 1400, 60, size=30, bold=True)
    for i in range(6):
        if i < app.currentStep: color = 'lightGreen'
        elif i == app.currentStep: color = 'lightYellow'
        else: color = None
        drawRect(1250, 100 + i * 50, 300, 50, border='black', fill=color)
        drawLabel(app.checklist[i], 1400, 125 + i * 50, size=16, bold=True)

def drawTitle(app):
    if app.currentStep == -1 or app.currentStep >= len(app.checklist):
        return
    else:
        drawLabel(app.checklist[app.currentStep], app.width/2, 30, size=24, 
                  bold=True)
        
#SOURCE: written by cursory
def drawDXF(app):
    if app.drawableDXF == None:
        return
    for entity in app.drawableDXF:
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            drawLine(start[0] * app.scale + app.cx + app.offsetX, 
                     start[1] * app.scale + app.cy + app.offsetY, 
                     end[0] * app.scale + app.cx + app.offsetX, 
                     end[1] * app.scale + app.cy + app.offsetY, fill='black')
        elif entity.dxftype() == 'ARC':
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            drawArc(center[0] * app.scale + app.cx + app.offsetX, 
                    center[1] * app.scale + app.cy + app.offsetY, 
                    radius * app.scale, radius * app.scale, 
                    start_angle, end_angle, fill=None, border='black')
            
def onKeyPress(app, key):
    if app.currentStep == 0:
        if key == 'up':
            app.scale *= 1.1
        elif key == 'down':
            app.scale /= 1.1

def onMousePress(app, mouseX, mouseY):
    if app.currentStep == -1:
        app.drawableDXF = getDXF()
        app.currentStep += 1
        app.showChecklist = True
    else:
        if hitsChecklistEntry(app, mouseX, mouseY):
            app.currentStep += 1
        if app.currentStep == 0:
            app.startingPointHold = (mouseX, mouseY)

def onMouseDrag(app, mouseX, mouseY):
    if app.currentStep == 0:
        startX, startY = app.startingPointHold
        app.offsetX = mouseX - startX
        app.offsetY = mouseY - startY

def onMouseRelease(app, mouseX, mouseY):
    if app.currentStep == 0:
        app.cx += app.offsetX
        app.cy += app.offsetY
        app.offsetX = 0
        app.offsetY = 0

def hitsChecklistEntry(app, mouseX, mouseY):
     if 1250 <= mouseX <= 1550 and 100 <= mouseY <= 400:
        index = (mouseY - 100) // 50
        if 0 <= index < len(app.checklist) and index == app.currentStep:
            return True

def main():
    runApp()

main()
