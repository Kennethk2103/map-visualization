from numbers import Number
import os as os
import sys as sys
from queue import PriorityQueue
from PIL import Image, ImageDraw
import imageio
import math as Math 
import json


isLinux=True
def getDistanceMeters(lat1, lon1, lat2, lon2):
    dLat = lat2-lat1
    dLon = lon2-lon1   
    return (dLat**2 + dLon**2)**0.5 * 111000
class node:
    def __init__(self, id, lat, lon, connectedNodes):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.connectedNodes = connectedNodes

    def __eq__(self, other):
        if isinstance(other, node):
            return self.id == other.id
        return False
    
    def __lt__(self, other):
        if isinstance(other, node):
            return self.id < other.id
        return False
    
    def __gt__(self, other):
        if isinstance(other, node):
            return self.id > other.id
        return False
    
    def __le__(self, other):
        if isinstance(other, node):
            return self.id <= other.id
        return False
    
    def __ge__(self, other):
        if isinstance(other, node):
            return self.id >= other.id
        return False
    
    def __ne__(self, other):
        if isinstance(other, node):
            return self.id != other.id
        return False
    
    

    def toJson(self):
        return {"id": self.id, "lat": self.lat, "lon": self.lon, "connectedNodes": self.connectedNodes
        }
    def toString(self):
        return "id: " + self.id + " lat: " + self.lat + " lon: " + self.lon + " connectedNodes: " + self.connectedNodes.__str__()

class way:
    def __init__(self, id, nodes):
        self.id = id
        self.nodes = nodes

    def toJson(self):
        return {"id": self.id, "nodes": self.nodes
        }

    def toString(self):
        return "id: " + self.id + " nodes: " + self.nodes.__str__()

nodes = {}

if os.path.isfile("pureData.json"):
    file = open("pureData.json", "r")
    data = file.read()
    file.close()
    data = json.loads(data)
    nodes = data["nodes"]
    ##convert inner back to node
    for key in nodes:
        nodes[key] = node(nodes[key]["id"], nodes[key]["lat"], nodes[key]["lon"], nodes[key]["connectedNodes"])

    ways = data["ways"]
    ##convert inner back to way
    for i in range(len(ways)):
        ways[i] = way(ways[i]["id"], ways[i]["nodes"])
else:
    ##get files in data directory with osm
    files = []

    for file in os.listdir("data"):
        if file.endswith(".osm"):
            files.append(file)
    if len(files) == 0:
        print("No osm files found")
        sys.exit()

    for file in files:
        file = open("data/" + file, "r")
        lines = file.readlines()
        file.close()

        ways = []


        for i in range(len(lines)):
            line = lines[i]
            line = line.strip()
            if line.startswith("<node"):
                nodeIndex = line.find("<node")
                nodeEndIndex = line.find("/>")
                nodeString = line[nodeIndex:nodeEndIndex]

                id= ""
                lat =""
                long =""
                nodeSplitString = nodeString.split(" ")
                for value in nodeSplitString:
                    if value.startswith("id"):
                        id = value.split("=")[1].replace('"', "")
                    elif value.startswith("lat"):
                        lat = value.split("=")[1].replace('"', "")
                    elif value.startswith("lon"):
                        long = value.split("=")[1].replace('"', "")
                if not nodes.get(id):
                    nodes[id] = (node(id, lat, long, []))
                

            elif line.startswith("<way"):
                wayIndex = line.find("<way")
                wayEndIndex = line.find(">")
                wayString = line[wayIndex:wayEndIndex].split(" ")
                id = ""
                for value in wayString:
                    if value.startswith("id"):
                        id = value.split("=")[1].replace('"', "")
                wayNodes = []

                while True:
                    currentLine = lines[i].strip()
                    if currentLine.startswith("</way"):
                        break
                    i+=1
                    if currentLine.startswith("<nd"):
                        ndIndex = currentLine.find("<nd")
                        ndEndIndex = currentLine.find("/>")
                        ndString = currentLine[ndIndex:ndEndIndex]
                        ndSplitString = ndString.split(" ")
                        ndId = ""
                        for value in ndSplitString:
                            if value.startswith("ref"):
                                ndId = value.split("=")[1].replace('"', "")
                                break
                        wayNodes.append(ndId)
                ways.append(way(id, wayNodes))
                
        for wayCur in ways:
            for i in range(len(wayCur.nodes)):
                alreadyInList = False
                for connectedNode in nodes[wayCur.nodes[i]].connectedNodes:
                    if connectedNode[0] == wayCur.nodes[i-1]:
                        alreadyInList = True
                        break
                if i != 0 and not alreadyInList:
                    nodes[wayCur.nodes[i]].connectedNodes.append((wayCur.nodes[i-1], getDistanceMeters(float(nodes[wayCur.nodes[i]].lat), float(nodes[wayCur.nodes[i]].lon), float(nodes[wayCur.nodes[i-1]].lat), float(nodes[wayCur.nodes[i-1]].lon))))
                if i != len(wayCur.nodes)-1 and not alreadyInList:
                    nodes[wayCur.nodes[i]].connectedNodes.append((wayCur.nodes[i+1], getDistanceMeters(float(nodes[wayCur.nodes[i]].lat), float(nodes[wayCur.nodes[i]].lon), float(nodes[wayCur.nodes[i+1]].lat), float(nodes[wayCur.nodes[i+1]].lon))))

    data = {"nodes": {}, "ways": []}
    for key in nodes:
        data["nodes"][key] = nodes[key].toJson()
    file = open("pureData.json", "w")
    file.write(json.dumps(data))
    file.close()

pictureLeft = -73.13899
pictureRight = -73.10715
pictureTop = 40.92483
pictureBottom = 40.90644

pixelWidth = 1506
pixelHeight = 1149

def latToPixel(lat):
    return int((lat-pictureTop)/(pictureBottom-pictureTop)*pixelHeight)
    
def lonToPixel(lon):
    return int((lon-pictureLeft)/(pictureRight-pictureLeft)*pixelWidth)

colorList = ["black"]

def makeGif(actionList, path, outputFileName):
    images = []
    savedI = Math.ceil(len(actionList)/20)
    for i in range(Math.ceil(len(actionList)/20)):
        ##make file directory for images
        if(i==0):
            img = Image.new("RGB", (pixelWidth, pixelHeight), "white")
        else:
            img = Image.open("images/map" + (i-1).__str__() + ".png")
        draw = ImageDraw.Draw(img)
        for j in range(i*20, min((i+1)*20, len(actionList))):
            fromNode = actionList[j][0]
            toNode = nodes[actionList[j][1]]
            draw.line([(lonToPixel(float(fromNode.lon)), latToPixel(float(fromNode.lat))), (lonToPixel(float(toNode.lon)), latToPixel(float(toNode.lat)))], fill=colorList[i%len(colorList)], width=2)
        img.save("images/map" + i.__str__() + ".png")
        images.append("images/map" + i.__str__() + ".png")

    print(len(path))
    for k in range(0, len(path)):
        ##make file directory for images
        img = Image.open("images/map" + (savedI+k-1).__str__() + ".png")
        draw = ImageDraw.Draw(img)
        if k != 0:
            fromNode = path[k-1]
            toNode = path[k]
            draw.line([(lonToPixel(float(fromNode.lon)), latToPixel(float(fromNode.lat))), (lonToPixel(float(toNode.lon)), latToPixel(float(toNode.lat)))], fill="red", width=4)

        img.save("images/map" + (savedI+k).__str__() + ".png")
        images.append("images/map" + (savedI+k).__str__() + ".png")

  
    imageio.mimsave(outputFileName, [imageio.imread(img) for img in images], fps=30)
    if isLinux:
        os.system("rm -r images")
        os.system("mkdir images")
        os.system("gifsicle -O3 --lossy=80 --colors 256 " + outputFileName + " -o " + outputFileName)
    return outputFileName

def getClosestNode(lat, lon): 
    closestNode = None
    closestDistance = 1000000000000000
    for key in nodes:
        nodeWorking = nodes[key]
        distance = getDistanceMeters(lat, lon, float(nodeWorking.lat), float(nodeWorking.lon))
        if distance < closestDistance:
            closestDistance = distance
            closestNode = nodeWorking
    return closestNode


def getShortestPathAStar(startLat, startLon, endLat, endLon):
    startNode = getClosestNode(startLat, startLon)
    endNode = getClosestNode(endLat, endLon)

    openSet = PriorityQueue()
    openSet.put((0, startNode))
    cameFrom = {}
    gScore = {v: float('inf') for v in nodes}
    gScore[startNode.id] = 0
    fScore = {v: float('inf') for v in nodes}
    fScore[startNode.id] = getDistanceMeters(float(startNode.lat), float(startNode.lon), float(endNode.lat), float(endNode.lon))

    actionList = []

    while not openSet.empty():
        (currentF, currentVertex) = openSet.get()
        if currentVertex == endNode:
            break
        for neighbors in currentVertex.connectedNodes:
            distance = neighbors[1]
            tentativeGScore = gScore[currentVertex.id] + distance
            if tentativeGScore < gScore[nodes[neighbors[0]].id]:
                actionList.append((currentVertex, neighbors[0]))
                cameFrom[nodes[neighbors[0]].id] = currentVertex
                gScore[nodes[neighbors[0]].id] = tentativeGScore
                fScore[nodes[neighbors[0]].id] = gScore[nodes[neighbors[0]].id] + getDistanceMeters(float(nodes[neighbors[0]].lat), float(nodes[neighbors[0]].lon), float(endNode.lat), float(endNode.lon))
                openSet.put((fScore[nodes[neighbors[0]].id], nodes[neighbors[0]]))

    path = []
    currentNodeBeingHandled = endNode
    while currentNodeBeingHandled:
        path.insert(0, currentNodeBeingHandled)
        currentNodeBeingHandled = cameFrom[currentNodeBeingHandled.id]
        if(currentNodeBeingHandled == startNode):
            break
    
    path.insert(0, startNode)



    print("Making gif now")
    makeGif(actionList, path, "aStar.gif")
    return path

##need to fix this
def getShortestPathBreadthFirst(startLat, startLon, endLat, endLon):
    startNode = getClosestNode(startLat, startLon)
    endNode = getClosestNode(endLat, endLon)
    print(startNode.toString())
    print(endNode.toString())
    actionList = []

    visited = {}
    queue = []
    queue.append(startNode)
    visited[startNode.id] = None
    path = []
    while queue:
        currentVertex = queue.pop(0)
        if currentVertex == endNode:
            break
        for neighbors in currentVertex.connectedNodes:
            if neighbors[0] not in visited:
                visited[neighbors[0]] = currentVertex
                queue.append(nodes[neighbors[0]])
                actionList.append((currentVertex, neighbors[0]))
    
    print("done with algorithm")
    currentNodeBeingHandled = endNode

    while currentNodeBeingHandled:
        path.insert(0, currentNodeBeingHandled)
        currentNodeBeingHandled = visited[currentNodeBeingHandled.id]
        if(currentNodeBeingHandled == startNode):
            break

    path.insert(0, startNode)
    
    print("Making gif now")
    makeGif(actionList, path, "breadth.gif")

    return path

def getShortestPathDikstras(startLat, startLon, endLat, endLon):
    startNode = getClosestNode(startLat, startLon)
    endNode = getClosestNode(endLat, endLon)

    D = {v:(float('inf'), None) for v in nodes}
    D[startNode.id] = (0, None)

    pq = PriorityQueue()
    pq.put((0, startNode))

    actionList = []
    visited = set()

    while not pq.empty():

        (dist, current_vertex) = pq.get()
        visited.add(current_vertex.id)
        
        for neighbors in current_vertex.connectedNodes:
            distance = neighbors[1]

            if neighbors[0] not in visited:
                (old_cost, vertex) = D[neighbors[0]]
                new_cost = D[current_vertex.id][0] + distance

                if new_cost < old_cost:
                    D[neighbors[0]] = (new_cost, current_vertex.id)
                    pq.put((new_cost, nodes[neighbors[0]]))
                    actionList.append((current_vertex, neighbors[0]))

    path = []
    currentNodeBeingHandled = endNode
    while currentNodeBeingHandled:
        path.insert(0, currentNodeBeingHandled)
        currentNodeBeingHandled = nodes[D[currentNodeBeingHandled.id][1]] if D[currentNodeBeingHandled.id][1] != None else None
    path.insert(0, startNode)
    
    print("Making gif now")
    makeGif(actionList, path, "dikjstra.gif")
    return path
#path = getShortestPathBreadthFirst(40.914413, -73.12637, 40.914413, -73.119571)
path = getShortestPathDikstras(40.914413, -73.12637, 40.914413, -73.119571)

#path = getShortestPathAStar(40.914413, -73.12637, 40.914413, -73.119571)

print("Complete")




    