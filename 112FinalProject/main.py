from unittest import result

from cmu_graphics import *
from cmu_cpcs_utils import *
import math
import random
import ezdxf
import sys
import tkinter as tk
from tkinter import filedialog
import triangle as tr
from shapely.geometry import Polygon

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
    def __init__(self, left, top, width, height, label, color, id): 
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.label = label
        self.color = color
        self.id = id
        self.border = None
        self.textColor = 'white'
        self.opacity = 100
        self.isHovering = False

    def isSelected(self, mouseX, mouseY):
        return (self.left <= mouseX <= self.left + self.width and 
                self.top <= mouseY <= self.top + self.height)

    def draw(self):
        drawRect(self.left, self.top, self.width, self.height, fill=self.color,
                 border=self.border, opacity=self.opacity)
        if self.label != None:
            drawLabel(self.label, self.left + self.width/2, self.top + 
                      self.height/2, fill=self.textColor, size=self.height/3, 
                      bold=True, font='Burger Crunchy')

class Segment:
    def __init__(self, p1, p2):
        self.points = [p1, p2] # list of two tuples
        self.loadType = None
        self.loadMagnitude = 0
        self.edgeNumber = 0

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.onSegment = False
        self.segments = []

class Element:
    def __init__(self, node1, node2, node3):
        self.nodes = [node1, node2, node3]
        self.matrix = None
    
    def draw(self):
        points = self.unpackNodes(self.nodes)
        drawPolygon(*points, fill=None, border='cyan', borderWidth=1)
    
    @staticmethod
    def unpackNodes(nodes):
        result = []
        for node in nodes:
            result.extend([node.x, node.y])
        return result

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.displacementX = 0
        self.displacementY = 0

def onAppStart(app):
    #files
    app.file = None
    app.drawableDXF = None
    #drawing
    app.width = 1600
    app.height = 900
    #program
    app.program = 0

def onAppRestart(app):
    #files
    app.file = None
    app.drawableDXF = None
    #program
    app.program = 0

def titleScreen_onScreenActivate(app):
    app.titleButton = Button(app.width/2 - 350, app.height/2 - 50, 700, 100, 
                             'FEA 2D SOLVER: CLICK TO START', 'mediumSlateBlue', 
                             -1)

def solverScreen_onScreenActivate(app):
    #files
    app.drawableDXF = getDXF()
    #drawing
    app.buttons = createMenuButtons(app)
    createOtherButtons(app)
    app.cx = app.width/2
    app.cy = app.height/2
    app.offsetX = 0
    app.offsetY = 0
    app.scale = 1
    app.startingPoint = None
    app.meshElementCounter = None
    #data
    app.edges = dict() #key: edge number; value:  list of points
    app.allSegments = []
    app.nodes = []
    app.elements = []
    app.materials = []
    app.selectedMaterial = None
    app.fixedBoundaries = [] #list of fixed segments
    app.forceMagnitude = 0
    app.forceDirection = (0, 0)
    #collect data from dxf file and organize into edges and circles
    assembleEdges(app)
    #Program Manager
    app.isMeshed = False
    def allRequirementsReady():
        return (app.isMeshed and app.selectedMaterial != None and
                app.fixedBoundaries != [] and app.forceMagnitude != 0)
    app.programRequirements = {0: False,
                               1: app.isMeshed,
                               2: app.selectedMaterial != None,
                               3: app.fixedBoundaries != [],
                               4: app.forceMagnitude != 0,
                               5: allRequirementsReady()                
                              }
def titleScreen_redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill=rgb(25, 25, 25))
    app.titleButton.draw()

def solverScreen_redrawAll(app):
    drawBackground(app)
    drawDXF(app)
    drawSidebar(app)
    drawInstructions(app)
    drawUniqueFeatures(app)
    drawOutlines(app)

def createMenuButtons(app): #creates all buttons, returns main menu buttons
    programNames = ['Display Setup', 'Meshing', 'Material Properties', 
                     'Boundary Conditions', 'Loads', 'Solve']
    buttons = []
    for i in range(len(programNames)):
        button = Button(app.left + app.width - 300, i*50, 300, 50, 
                        programNames[i], rgb(30, 30, 30), i)
        buttons.append(button)
    return buttons

def createOtherButtons(app):
    app.meshButton = Button(app.left + app.width - 300, 800, 300, 50, 'MESH!',
                            'limeGreen', 6)
    app.sliderButton = Button(app.left + app.width - 510, 50, 20, 20, None,
                              rgb(75, 75, 75), 7)
    app.solveButton = Button(app.left + app.width - 300, 800, 300, 50, 'SOLVE!',
                            'limeGreen', 6)

def drawBackground(app):
    drawRect(0, 0, app.width, app.height, fill=rgb(25, 25, 25))

def drawSidebar(app):
    drawRect(app.left + app.width - 300, 0, 300, app.height, 
             fill=rgb(30, 30, 30))
    for button in app.buttons:
        if button.id == app.program: #selected stage takes precedence
            button.color = 'yellow'
            button.opacity = 90
            button.textColor = 'black'
        elif app.programRequirements[button.id]: #finished requirements
            button.color = 'limeGreen'
            button.opacity = 90
            button.textColor = 'black'
        elif button.isHovering: #then highlight the hovering button
            button.color = rgb(50, 50, 50)
        else: #all other buttons
            button.color = rgb(30, 30, 30)
            button.opacity = 100
            button.textColor = 'white'
        if not app.isMeshed and button.id >= 2: #gray out buttons that aren't accessible
            button.textColor = rgb(90, 90, 90)
        button.draw()

def drawInstructions(app):
    textColor = 'lightSteelBlue'
    drawLabel('Instructions:', app.left + app.width - 150, 400, italic=True,
              fill=textColor, bold=True, size=27, font='Burger Crunchy')
    if app.program == 0:
        drawLabel('Drag and Resize Shape', app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)
        drawLabel('-/+ to change size', app.left + app.width - 150, 490, 
                  fill=textColor, font='Burger Crunchy', size=22)
    elif app.program == 1:
        drawLabel('Drag slider to change', app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)
        drawLabel('element size', app.left + app.width - 150, 490, 
                  fill=textColor, font='Burger Crunchy', size=22)
        drawLabel("Press 'mesh' when ready", app.left + app.width - 150, 530,
                  fill=textColor, font='Burger Crunchy', size=22)
    elif app.program == 2:
        drawLabel('Select type of Material', app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)
    elif app.program == 3:
        drawLabel('Click or drag to select', app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)
        drawLabel('fixed edges', app.left + app.width - 150, 490, 
                  fill=textColor, font='Burger Crunchy', size=22)
    elif app.program == 4:
        drawLabel("Press 'solve' when ready", app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)

def drawUniqueFeatures(app):
    if app.program == 1:
        app.meshButton.draw()
        drawRect(app.left + app.width - 600, 50, 200, 20, fill=rgb(150, 150, 
                 150))
        app.sliderButton.draw()

def drawOutlines(app):
    drawRect(0, 0, app.width, app.height, fill=None, border=rgb(50, 50, 50), 
             borderWidth=1)
    drawRect(app.left + app.width - 300, 0, 300, app.height, fill=None, border=rgb(50, 50, 50), 
             borderWidth=1)
##Start of drawing DXF code
def assembleEdges(app):
    if app.drawableDXF == None: #no dxf file selected
        return
    point_index = dict() #key: point; value: edge # that includes points
    for entity in app.drawableDXF:
        segments = getSegments(app, entity) #also adds segments to app.segments
        if segments != None:
            for segment in segments:
                p1, p2 = segment.points
                addSegment(roundPoint(p1), roundPoint(p2), app.edges, 
                           point_index) #adds segments to edges and point_index dicts
    
def drawDXF(app):
    for edge in app.edges:
        points = flattenEdges(app, app.edges[edge])
        drawEdge(points)
        
def flattenEdges(app, points):
    result = []
    for x, y in points:
        result.extend([x * app.scale + app.offsetX + app.cx, y * app.scale + 
                       app.offsetY + app.cy])
    return result

def drawEdge(points):
    drawPolygon(*points, fill=None, border='white', borderWidth=2)
#Source, written by claude.ai
def roundPoint(p, decimals=3):
    scale = 10 ** decimals
    return (math.floor(p[0] * scale) / scale, math.floor(p[1] * scale) / scale)
#Source: written by claude.ai with modifications
def addSegment(p1, p2, edges, point_index):
    edgeA = point_index.get(p1)
    edgeB = point_index.get(p2)
    if edgeA is None and edgeB is None:
        # Brand new edge
        edgeID = len(edges)
        edges[edgeID] = [p1, p2]
        point_index[p1] = edgeID
        point_index[p2] = edgeID
    elif edgeA is not None and edgeB is None:
        # p1 connects to an existing edge, append p2
        edges[edgeA].append(p2)
        point_index[p2] = edgeA
    elif edgeA is None and edgeB is not None:
        # p2 on existing edge, insert p1 at the beginning
        edges[edgeB].insert(0, p1)
        point_index[p1] = edgeB
    elif edgeA != edgeB:
        # merge the two edges
        listA = edges[edgeA]
        listB = edges[edgeB]
        
        # make sure p1 is at the end of edgeA and p2 at start of edgeB
        if listA[-1] != p1:
            listA.reverse()
        if listB[0] != p2:
            listB.reverse()
        
        edges[edgeA] = listA + listB
        for p in listB:
            point_index[p] = edgeA
        del edges[edgeB]
                 
def getSegments(app, entity): #returns list of segments, adds segments to app.segments
    entitySegments = []
    if entity.dxftype() == 'LINE':
        p1 = (entity.dxf.start[0], entity.dxf.start[1])
        p2 = (entity.dxf.end[0], entity.dxf.end[1])
        segment = Segment(p1, p2)
        entitySegments.append(segment)
        app.allSegments.append(segment)
    elif entity.dxftype() == 'ARC':
        segments = arcToSegments(entity)
        entitySegments.extend(segments)
        app.allSegments.extend(segments)
    elif entity.dxftype() == 'LWPOLYLINE':
        segments = lwPolylineToSegments(entity)
        entitySegments.extend(segments)
        app.allSegments.extend(segments)
    elif entity.dxftype() == 'POLYLINE':
        segments = polylineToSegments(entity)
        entitySegments.extend(segments)
        app.allSegments.extend(segments)
    elif entity.dxftype() == 'SPLINE':
        segments = splineToSegments(entity)
        entitySegments.extend(segments)
        app.allSegments.extend(segments)
    elif entity.dxftype() == 'ELLIPSE':
        segments = ellipseToSegments(entity)
        entitySegments.extend(segments)
        app.allSegments.extend(segments)
    elif entity.dxftype() == 'CIRCLE':
        segments = circleToEdges(entity)
        entitySegments.extend(segments)
        app.allSegments.extend(segments)
    return entitySegments

def isDrawable(entity):
    if entity.dxftype() in ['LINE', 'ARC', 'POLYLINE', 'LWPOLYLINE', 'SPLINE', 
                            'ELLIPSE']:
        return True
    return False
#Source: written by claude.ai (EXEMPT)
def arcToSegments(entity):
    cx = entity.dxf.center.x
    cy = entity.dxf.center.y
    r = entity.dxf.radius
    start_angle = math.radians(entity.dxf.start_angle)
    end_angle = math.radians(entity.dxf.end_angle)
    
    # handle wrap-around (e.g. 270 -> 90)
    if end_angle < start_angle:
        end_angle += 2 * math.pi
    
    arcSpan = end_angle - start_angle
    steps = max(6, int(arcSpan / (math.pi / 12)))

    angles = [start_angle + (end_angle - start_angle) * i / steps for i in range(steps + 1)]
    points = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]
    
    return [Segment(points[i], points[i+1]) for i in range(steps)]
#Source: written by claude.ai
def lwPolylineToSegments(entity):
    pts = [p[:2] for p in entity.get_points()]
    segments = [Segment(pts[i], pts[i+1]) for i in range(len(pts)-1)]
    if entity.is_closed:
        segments.append(Segment(pts[-1], pts[0]))
    return segments
#Source: written by claude.ai
def polylineToSegments(entity):
    pts = [p[:2] for p in entity.points()]
    segments = [Segment(pts[i], pts[i+1]) for i in range(len(pts)-1)]
    if entity.is_closed:
        segments.append(Segment(pts[-1], pts[0]))
    return segments
#Source: written by claude.ai (EXEMPT)
def splineToSegments(entity):
    pts = [p[:2] for p in entity.flattening(0.1)]
    if len(pts) > 51:
        # resample down to max_segs evenly spaced points
        indices = [int(i * (len(pts)-1) / 50) for i in range(51)]
        pts = [pts[i] for i in indices]
    return [Segment(pts[i], pts[i+1]) for i in range(len(pts)-1)]
#Source: written by claude.ai (EXEMPT)
def ellipseToSegments(entity):
    import math
    
    cx, cy = entity.dxf.center.x, entity.dxf.center.y
    major = entity.dxf.major_axis
    ratio = entity.dxf.ratio
    rx = math.hypot(major.x, major.y)
    ry = rx * ratio
    rotation = math.atan2(major.y, major.x)
    start_angle = entity.dxf.start_param
    end_angle = entity.dxf.end_param

    if end_angle < start_angle:
        end_angle += 2 * math.pi

    steps = 6
    angles = [start_angle + (end_angle - start_angle) * i / steps for i in range(steps + 1)]
    points = [(cx + rx * math.cos(a) * math.cos(rotation) - ry * math.sin(a) * math.sin(rotation),
               cy + rx * math.cos(a) * math.sin(rotation) + ry * math.sin(a) * math.cos(rotation))
              for a in angles]

    return [Segment(points[i], points[i+1]) for i in range(steps)]

def circleToEdges(entity):
    segments = []
    cx = entity.dxf.center.x
    cy = entity.dxf.center.y
    r = entity.dxf.radius
    points = 16
    for i in range(points):
        angle1 = 2 * math.pi * (i/points) #step size
        angle2 = 2 * math.pi * ((i+1)/points) #1 step over
        p1 = getRadiusEndpoint(cx, cy, r, angle1)
        p2 = getRadiusEndpoint(cx, cy, r, angle2)
        segments.append(Segment(p1, p2))
    return segments
#Source: CS academy
def getRadiusEndpoint(cx, cy, r, theta):
    return (cx + r*math.cos(theta),
            cy - r*math.sin(theta))
#end of drawing DXF code
#Meshing code
#Source: claude.ai, general info: https://www.cs.cmu.edu/~quake/triangle.html
def createMesh(app):

    meshDict = dict()
    boundaryEdges = []
    holeEdges = []
    for edge in app.edges:
        if isHoleEdge(app, app.edges[edge]):
            holeEdges.append(edge)
        else:
            boundaryEdges.append(edge)
    
    meshDict['vertices'] = boundaryEdges
    meshDict['holes'] = holeEdges

    nodesList, trianglesList = tr.triangulate(meshDict, 'pq30a0.5')
    for points in nodesList:
        node = Node(points[0], points[1])
        app.nodes.append(node)
    for triangle in trianglesList:
        node1 = app.nodes[triangle[0]]
        node2 = app.nodes[triangle[1]]
        node3 = app.nodes[triangle[2]]
        element = Element(node1, node2, node3)
        app.elements.append(element)

def isHoleEdge(app, edge1):
    for edge in app.edges:
        if edge != edge1 and edge.contains(edge1):
            return True
    return False

#end of meshing code
def titleScreen_onMouseMove(app, mouseX, mouseY):
    if app.titleButton.isSelected(mouseX, mouseY):
        app.titleButton.color = 'mediumPurple'
        setLargeButtonSize(app)
    else:
        app.titleButton.color = 'mediumSlateBlue'
        setDefaultButtonSize(app)

def titleScreen_onMousePress(app, mouseX, mouseY):
    if app.titleButton.isSelected(mouseX, mouseY):
        app.titleButton.color = 'limeGreen'

def setDefaultButtonSize(app):
    app.titleButton.left = app.width/2 - 350
    app.titleButton.top = app.height/2 - 50
    app.titleButton.width = 700
    app.titleButton.height = 100

def setLargeButtonSize(app):
    app.titleButton.left = app.width/2 - 360
    app.titleButton.top = app.height/2 - 60
    app.titleButton.width = 720
    app.titleButton.height = 120

def titleScreen_onMouseRelease(app, mouseX, mouseY):
    if app.titleButton.isSelected(mouseX, mouseY):
        setActiveScreen('solverScreen')
    else:
        app.titleButton.color = 'mediumSlateBlue'
        setDefaultButtonSize(app)

def solverScreen_onKeyPress(app, key):
    if app.program == 0 and not app.isMeshed:
        if key == '+' or key == '=':
            app.scale *= 1.1
        elif key == '-' or key == '_':
            app.scale /= 1.1

def solverScreen_onMousePress(app, mouseX, mouseY):
    for button in app.buttons:
        if button.isSelected(mouseX, mouseY) and button.id != app.program:
            app.programRequirements[0] = True #make first button green
            if not app.isMeshed and button.id < 2:
                app.program = button.id
            elif app.isMeshed:
                app.program = button.id
    #drawing setup
    if app.program == 0 and not app.isMeshed:
        app.startingPoint = mouseX, mouseY
    #mesh
    elif app.program == 1:
        if app.sliderButton.isSelected(mouseX, mouseY):
            app.sliderButton.isHovering = True #used like isDragging for the slider button
        elif app.meshButton.isSelected(mouseX, mouseY):
            createMesh(app)

def solverScreen_onMouseDrag(app, mouseX, mouseY):
    if app.program == 0 and not app.isMeshed:
        startX, startY =app.startingPoint
        app.offsetX = mouseX - startX
        app.offsetY = mouseY - startY
    if app.program == 1:
        if app.sliderButton.isHovering:
            if mouseX < 1000:
                app.sliderButton.left = 1000
            elif mouseX > 1190:
                app.sliderButton.left = 1180
            else:
                app.sliderButton.left = mouseX - 10

def solverScreen_onMouseRelease(app, mouseX, mouseY):
    if app.program == 0 and not app.isMeshed:
        app.cx += app.offsetX
        app.cy += app.offsetY
        app.offsetX = 0
        app.offsetY = 0
    if app.program == 1:
        app.sliderButton.isHovering = False
    
def solverScreen_onMouseMove(app, mouseX, mouseY):
    for button in app.buttons:
        if button.isSelected(mouseX, mouseY) and button.id != app.program:
            if not app.isMeshed and button.id < 2:
                button.isHovering = True
            elif app.isMeshed:
                button.isHovering = True
        else:
            button.isHovering = False

def main():
    runAppWithScreens(initialScreen='titleScreen')

main()
