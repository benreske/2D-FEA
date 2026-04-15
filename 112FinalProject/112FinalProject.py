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
    app.width = 1600
    app.height = 900
    app.dxfData = None
    app.menu = True

def onAppRestart(app):
    app.dxfData = None
    app.menu = True
    app.displayDXF = False

def redrawAll(app):
    if app.menu:
        drawRect(app.width/2 - 200, app.height/2 - 75, 400, 150, 
                 fill='lightBlue', border='black')
        drawLabel('2D FEA SOLVER', app.width/2, app.height/2-33, size=30, 
                  bold=True)
        drawLabel('Click to select a DXF file',app.width/2, app.height/2 + 33, 
                  size=16)
    elif app.displayDXF:
        drawDXF(app)


def onMousePress(app, mouseX, mouseY):
    if app.menu:
        app.dxfData = getDXF()
        app.menu = False
        app.displayDXF = True



#SOURCE: written by cursory
def drawDXF(app):
    if app.dxfData == None:
        return
    for entity in app.dxfData:
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            drawLine(start[0] + app.width/2, start[1] + app.height/2, end[0] + 
                     app.width/2, end[1] + app.height/2, fill='black')
        elif entity.dxftype() == 'CIRCLE':
            center = entity.dxf.center
            radius = entity.dxf.radius
            drawCircle(center[0] + app.width/2, center[1] + app.height/2, 
                       radius, fill=None, border='black')
        elif entity.dxftype() == 'ARC':
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            drawArc(center[0] + app.width/2, center[1] + app.height/2, radius, 
                    start_angle, end_angle, fill=None, border='black')
    

def main():
    runApp()

main()