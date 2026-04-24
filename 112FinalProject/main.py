from cmu_graphics import *
from cmu_cpcs_utils import *
import math
import ezdxf
import sys
import tkinter as tk
from tkinter import filedialog
import triangle as tr
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

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
        self.color = 'yellow'
        self.width = 3

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
    
    def draw(self, app):
        initialPoints = [(self.nodes[0].x, self.nodes[0].y), (self.nodes[1].x, 
                        self.nodes[1].y), (self.nodes[2].x, self.nodes[2].y)]
        points = flattenDraw(app, initialPoints)
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

#Source: partially helped by claude.ai

def onAppStart(app):
    #files
    app.file = None
    app.drawableDXF = None
    #drawing
    app.width = 1600
    app.height = 900
    #program
    app.program = 0

def restartApp(app):
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
    #program 0: draw
    app.cx = app.width/2
    app.cy = app.height/2
    app.offsetX = 0
    app.offsetY = 0
    app.scale = 1
    app.startingPoint = None
    app.edges = dict() #key: edge number; value:  list of points
    #program 1: mesh
    app.meshElementCounter = None
    app.allSegments = []
    app.nodes = []
    app.elements = []
    app.isMeshed = False
    #program 2: material selection
    app.materials = []
    app.materialMenuOpen = False
    app.materialButtons = []
    app.selectedMaterial = None
    app.materialLibraryNames = ['Stainless Steel', '6601 Aluminum', 'Titanium',
                                'PLA']
    app.materialLibrary = {'Stainless Steel': (192, 0.29),
                           '6601 Aluminum' : (69, 0.33),
                           'Titanium' : (120, 0.36),
                           'PLA' : (2.645, 0.33)
                          }
    #program 3: boundary conditions
    app.fixedSegments = [] #list of fixed segments
    #program 4: loads
    app.loadedSegment = None
    app.forceMagnitude = 0
    app.forceDirection = (0, 0)
    #extra one time processes
    app.buttons = createMenuButtons(app)
    createOtherButtons(app)
    createMaterialButtons(app)
    assembleEdges(app)
    app.currentMeshElements = rounded(getCurrentMeshElements(app))
    #program progress
    def allRequirementsReady():
        return (app.isMeshed and app.selectedMaterial != None and
                app.fixedBoundaries != [] and app.forceMagnitude != 0)
    app.programRequirements = [False for i in range(6)]
    
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
    if app.isMeshed and app.program == 1:
        drawMesh(app)

#drawing functions
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
    app.meshButton = Button(app.left + app.width - 300, 700, 300, 50, 'MESH!',
                            'limeGreen', -1)
    app.sliderButton = Button(app.left + app.width - 510, 50, 20, 20, None,
                              rgb(75, 75, 75), -1)
    app.solveButton = Button(app.left + app.width - 300, 700, 300, 50, 'SOLVE!',
                            'limeGreen', -1)
    app.singleMaterialButton = Button(app.left + app.width - 300, 500, 300, 35,
                                      'Select a Material', rgb(50, 50, 50), -1)
    app.resetButton = Button(app.left + app.width - 300, 700, 300, 50, 'Reset',
                             rgb(50, 50, 50), -1)

def createMaterialButtons(app):
    materialNames = [key for key in app.materialLibrary]
    for i in range(len(app.materialLibrary)):
        button = Button(app.left + app.width - 300, 530 + i*35, 300, 35, 
                        materialNames[i], rgb(30, 30, 30), -1)
        app.materialButtons.append(button)

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
    drawLabel("Press 'R' to restart", app.left + app.width - 150, 860, 
              fill=textColor, font='Burger Crunchy', size=14)
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
        drawLabel(f'Mesh Elements: {app.currentMeshElements}', app.left + 
                  app.width - 500, 30, size=14, font='Burger Crunchy', 
                  fill=textColor)
    elif app.program == 2:
        drawLabel('Select type of Material', app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)
    elif app.program == 3:
        drawLabel('Click or drag to select', app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)
        drawLabel('fixed edges', app.left + app.width - 150, 490, 
                  fill=textColor, font='Burger Crunchy', size=22)
    elif app.program == 4:
        drawLabel("Press which edge to load", app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)
        drawLabel("and type in magnitude (N)", app.left + app.width - 150, 490, 
                  fill=textColor, font='Burger Crunchy', size=22)
    elif app.program == 5:
        drawLabel("Press 'solve' to solve!", app.left + app.width - 150, 450, 
                  fill=textColor, font='Burger Crunchy', size=22)

def drawUniqueFeatures(app):
    if app.program == 1:
        app.meshButton.draw()
        drawRect(app.left + app.width - 600, 50, 200, 20, fill=rgb(150, 150, 
                 150))
        app.sliderButton.draw()
    elif app.program == 2:
        if app.materialMenuOpen:
            for button in app.materialButtons:
                if button.isHovering: 
                    button.color = rgb(50, 50, 50)
                else:
                    button.color = rgb(30, 30, 30)
                button.draw()
        app.singleMaterialButton.draw()
    elif app.program == 3:
        app.resetButton.draw()
        for segment in app.fixedSegments:
            points = flattenDraw(app, segment.points)
            drawLine(*points, fill=segment.color, 
                     lineWidth=segment.width)
    elif app.program == 4:
        app.resetButton.draw()
        if app.loadedSegment != None:
            points = flattenDraw(app, app.loadedSegment.points)
            drawLine(*points, fill=app.loadedSegment.color, 
                     lineWidth=app.loadedSegment.width)

def drawOutlines(app):
    drawRect(0, 0, app.width, app.height, fill=None, border=rgb(50, 50, 50), 
             borderWidth=1)
    drawRect(app.left + app.width - 300, 0, 300, app.height, fill=None, 
             border=rgb(50, 50, 50), borderWidth=1)

def flattenDraw(app, points):
    result = []
    for x, y in points:
        result.extend([x * app.scale + app.offsetX + app.cx, y * app.scale + 
                       app.offsetY + app.cy])
    return result

def drawMesh(app):
    for element in app.elements:
        element.draw(app)

def drawDXF(app):
    for edge in app.edges:
        points = flattenDraw(app, app.edges[edge])
        drawPolygon(*points, fill=None, border='white', borderWidth=2)  

#Assembling DXF
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
    for edge in app.edges:
        edgePoints = app.edges[edge]
        simplifiedPolygon = Polygon(edgePoints).simplify(tolerance=0.5)
        simplifiedPoints = list(simplifiedPolygon.exterior.coords)
        app.edges[edge] = simplifiedPoints
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
        angle1 = 2 * math.pi * (i/points)
        angle2 = 2 * math.pi * ((i+1)/points) # 1 step over
        p1 = getRadiusEndpoint(cx, cy, r, angle1)
        p2 = getRadiusEndpoint(cx, cy, r, angle2)
        segments.append(Segment(p1, p2))
    return segments
#Source: CS academy
def getRadiusEndpoint(cx, cy, r, theta):
    return (cx + r*math.cos(theta),
            cy - r*math.sin(theta))


#Meshing
#Source: partially claude.ai, general info: https://www.cs.cmu.edu/~quake/triangle.html
def createMesh(app):
    meshDict = dict()
    vertices = []
    segments = []
    holes = []
    for edge in app.edges:
        edgePoints = app.edges[edge]
        segments += (getVertexIndices(edgePoints, len(vertices)))
        vertices += edgePoints
        if isHoleEdge(app, edgePoints):
            centroid = Polygon(edgePoints).centroid
            holes.append([centroid.x, centroid.y])
    meshDict['vertices'] = vertices
    meshDict['segments'] = segments
    if holes != []:
        meshDict['holes'] = holes # points to treat as holes
    meshSize = getMeshSize(app)
    meshResult = tr.triangulate(meshDict, f'pq30a{meshSize}')
    trianglesList, nodesList = meshResult['triangles'], meshResult['vertices']
    for points in nodesList:
        node = Node(points[0], points[1])
        app.nodes.append(node)
    for triangle in trianglesList:
        node1 = app.nodes[triangle[0]]
        node2 = app.nodes[triangle[1]]
        node3 = app.nodes[triangle[2]]
        element = Element(node1, node2, node3)
        app.elements.append(element)

def getVertexIndices(pointsList, startIndex):
    result = []
    for i in range(len(pointsList)):
        if i < len(pointsList) - 1: #not the last entry
            result.append([i + startIndex, i + startIndex + 1])
        else: # last entry
            result.append([i + startIndex, startIndex])
    return result

def isHoleEdge(app, edgePoints):
    polygon1 = Polygon(edgePoints)
    for edge in app.edges:
        polygon2 = Polygon(app.edges[edge])
        if polygon1 != polygon2 and polygon2.contains(polygon1):
            return True
    return False

def getMeshSize(app):
    area = 0
    for edge in app.edges:
        edgePoints = app.edges[edge]
        if isHoleEdge(app, edgePoints):
            area -= Polygon(edgePoints).area
        else:
            area += Polygon(edgePoints).area
    #1500 max elements, minSize = area / 1500
    #50 min elements, maxSize = area / 50
    #scale value is 5.28 from 0-180 to 50-1000
    numElements = getCurrentMeshElements(app)
    meshSize = area/numElements
    return meshSize

def getCurrentMeshElements(app):
    currX = app.sliderButton.left - 999 #1 minimum
    return 50 + 5.28 * currX

#Other Functions
#Source: claude.ai
def isSegmentClicked(app, segment, mouseX, mouseY):
    points = flattenDraw(app, segment.points) #to adjust to drawn points
    p1, p2 = (points[0], points[1]), (points[2], points[3])
    line = LineString([p1, p2])
    point = Point(mouseX, mouseY)
    return point.distance(line) <= 5


#Controllers
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
    if key == 'R':
        setActiveScreen('titleScreen')
        restartApp(app)
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
        elif app.meshButton.isSelected(mouseX, mouseY) and not app.isMeshed:
            createMesh(app)
            app.isMeshed = True
            app.programRequirements[1] = True
            app.meshButton.color = rgb(50, 50, 50)
    elif app.program == 2:
        if app.singleMaterialButton.isSelected(mouseX, mouseY):
            app.materialMenuOpen = not app.materialMenuOpen
        for button in app.materialButtons:
            if button.isSelected(mouseX, mouseY):
                app.programRequirements[2] = True
                app.selectedMaterial = app.materialLibrary[button.label]
                app.singleMaterialButton.label = button.label
                app.materialMenuOpen = not app.materialMenuOpen
    elif app.program == 3:
        if app.resetButton.isSelected(mouseX, mouseY):
            app.fixedSegments = []
            app.programRequirements[3] = False
        else:
            for segment in app.allSegments:
                if isSegmentClicked(app, segment, mouseX, mouseY):
                    app.fixedSegments.append(segment)
                    app.programRequirements[3] = True
    elif app.program == 4:
        if app.resetButton.isSelected(mouseX, mouseY):
            app.loadedSegments = None
            app.programRequirements[4] = False
        else:
            for segment in app.allSegments:
                if isSegmentClicked(app, segment, mouseX, mouseY):
                    app.loadedSegment = segment
                    app.programRequirements[4] = True
            
        
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
            app.currentMeshElements = rounded(getCurrentMeshElements(app)) #change when it drags

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
    if app.program == 2:
        if app.materialMenuOpen:
            for button in app.materialButtons:
                if button.isSelected(mouseX, mouseY):
                    button.isHovering = True
                else:
                    button.isHovering = False
def main():
    runAppWithScreens(initialScreen='titleScreen')

main()

