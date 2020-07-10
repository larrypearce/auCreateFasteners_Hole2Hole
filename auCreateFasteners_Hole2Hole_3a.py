# coding: utf-8





import apex
from apex.construct import Point3D, Point2D

import math
import tempfile
import logging
import time

global apexRelease


logEnabled = False  # this defines logEnabled as global



def myEcho(msg, type):
	print(msg)
	if type == "Warning":
		if logEnabled: logging.warning(msg)
	else:
		if logEnabled: logging.info(msg)






def calcHoleCenter(edge):
	# This function does a very simple calculation to find the center of the hole feature
	# It is this function that may be incorrect if more than one edge is used to represent the hole
	edgeParam = edge.getParametricRange()
	startPoint = edge.evaluateEdgeParametricCoordinate(edgeParam["uStart"])
	uStart = edgeParam["uStart"]
	uEnd   = edgeParam["uEnd"]
	uHalf = uStart + 0.5*(uEnd-uStart)
	halfPoint = edge.evaluateEdgeParametricCoordinate(uHalf)
	x = 0.5*(startPoint.getX()+halfPoint.getX())
	y = 0.5*(startPoint.getY()+halfPoint.getY())
	z = 0.5*(startPoint.getZ()+halfPoint.getZ())
	point = apex.geometry.createPointXYZ(x, y, z)
	# I originally wanted to use POINT3D but could not get this to work further down in the code.  I am not sure
	# if the problem was me or the API or other.  Thus, instead I am creating points.  These will be deleted later.
	#point = Point3D(x, y, z)
	return point






def createPointAtCylinderCenter(ptA, ptB):
	dx = ptB.getX() - ptA.getX()
	dy = ptB.getY() - ptA.getY()
	dz = ptB.getZ() - ptA.getZ()
	
	x = ptA.getX() + 0.5*dx
	y = ptA.getY() + 0.5*dy
	z = ptA.getZ() + 0.5*dz
	
	point = apex.geometry.createPointXYZ(x, y, z)
	
	return point






def calcSurfaceNormalAtHole(surf, edge):
	edgeParam = edge.getParametricRange()
	startPoint = edge.evaluateEdgeParametricCoordinate(edgeParam["uStart"])
	normalVec = surf.evaluateSurfaceNormal(startPoint)
	
	iVec = normalizeVector(normalVec)
	
	return iVec






def calcVectorBetweenPoints(ptA, ptB):
	locA = ptA.asIPhysical()
	locB = ptB.asIPhysical()
	
	vec = apex.construct.Vector3D()
	vec.setX(locA.getX() - locB.getX())
	vec.setY(locA.getY() - locB.getY())
	vec.setZ(locA.getZ() - locB.getZ())
	
	iVec = normalizeVector(vec)
	
	return iVec






def calcDistanceBetweenPoints(ptA, ptB):
	
	dx = ptA.getX() - ptB.getX()
	dy = ptA.getY() - ptB.getY()
	dz = ptA.getZ() - ptB.getZ()
	
	dist = dx*dx + dy*dy + dz*dz
	if dist > 0.0: dist = math.sqrt(dist)
	
	return (dist)
	



def normalizeVector(vec):
	
	if vec.getLength() > 0.0:
		dx = vec.getX()/vec.getLength()
		dy = vec.getY()/vec.getLength()
		dz = vec.getZ()/vec.getLength()
	else:
		dx = dy = dz = 0.0
	
	return apex.construct.Vector3D(dx, dy, dz)



#def normalizeVector(vec):
#	mag = math.sqrt(vec.getX()**2 + vec.getY()**2 + vec.getZ()**2)
#	
#	iVec = apex.construct.Vector3D()
#	
	# I need to do more work on the case where the magnitude of iVec is 0.0
#	if mag == 0.0:
#		iVec.setX(0.0)
#		iVec.setY(0.0)
#		iVec.setZ(0.0)
#	else:
#		iVec.setX(vec.getX()/mag)
#		iVec.setY(vec.getY()/mag)
#		iVec.setZ(vec.getZ()/mag)
#	
#	return iVec




def isNotParallel(holeToHoleVec, surfNormal, tol):
	# vectors are already normalized
	dot  = holeToHoleVec.getX()*surfNormal.getX()
	dot += holeToHoleVec.getY()*surfNormal.getY()
	dot += holeToHoleVec.getZ()*surfNormal.getZ()
	dot = abs(dot)
	
	upperRange = 1.0 + .01
	lowerRange = 1.0 - .01
	if dot <= upperRange and dot >= lowerRange:
		notParallel = False
	else:
		notParallel = True
	
	return (notParallel)




def connectorProps(connectorType, dia, length, matl):

	_diameter = 0.0
	_material = None
	stiff = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
	
	if connectorType == apex.attribute.ConnectorType.FlexibleLink:
		_diameter = dia
		_material = matl
	elif connectorType == apex.attribute.ConnectorType.Bushing:
		stiff = calcBushingProps(dia, length, matl)
		
	
	connProp = apex.attribute.createConnectorProperties(
          stiffness               = 0.0,
          damping                 = 0.0,
          translationalStiffnessX = stiff[0],
          translationalStiffnessY = stiff[1],
          translationalStiffnessZ = stiff[2],
          rotationalStiffnessX    = stiff[3],
          rotationalStiffnessY    = stiff[4],
          rotationalStiffnessZ    = stiff[5],
          translationalDampingX   = 0.0,
          translationalDampingY   = 0.0,
          translationalDampingZ   = 0.0,
          rotationalDampingX      = 0.0,
          rotationalDampingY      = 0.0,
          rotationalDampingZ      = 0.0,
          diameter                = _diameter,
          linkMaterial            = _material)
	return connProp






def calcBushingProps(dia, length, matl):

	E  = matl.getElasticModulus()
	NU = matl.getPoissonRatio()
	G  = E/2.0/(1.0+NU)
	
	Area    = math.pi*dia**2/4.0
	Inertia = math.pi*dia**4/64.0
	J       = 2.0*Inertia
	
	shearArea = 0.75*Area

	stiff = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
	
	stiff[0] = E*Area/length
	stiff[1] = G*shearArea/length
	stiff[2] = stiff[1]
	stiff[3] = G*J/length
	stiff[4] = E*Inertia/length + G*shearArea*length/3.0
	stiff[5] = stiff[4]
	
	return stiff






def isStraightLine(edge):
	verts = edge.getVertices()
	# if the edge has only 1 vertex or no vertices, i am going to assume it is a loop
	if verts.len() < 2: return False
	# for now I am going to cheat and any edge with at least 2 vertices is not a loop
	return True






def isStraightLine2(edge):
	verts = edge.getVertices()
	if verts.len() < 2: return False
	
	if verts.len() > 2: return False # this is an assumption for now
	
	if apexRelease == "Iberian Lynx":
		mp = edge.getMidPointLocation()
	else:
		mp = edge.getMidPoint()
	
	v1x = verts[1].getX() - verts[0].getX()
	v1y = verts[1].getY() - verts[0].getY()
	v1z = verts[1].getZ() - verts[0].getZ()
	
	v2x = mp.getX() - verts[0].getX()
	v2y = mp.getY() - verts[0].getY()
	v2z = mp.getZ() - verts[0].getZ()
	
	dot = v1x*v2x + v1y*v2y + v1z*v2z
	
	v1Norm = math.sqrt(v1x**2 + v1y**2 + v1z**2)
	v2Norm = math.sqrt(v2x**2 + v2y**2 + v2z**2)
	
	cosTheta = dot/v1Norm/v2Norm
	
	if abs(1-cosTheta) > .0001: return False
	
	return True
	





def isArc(edge):
	verts = edge.getVertices()
	
	if verts.len() != 2: return False
	
	dx = verts[1].getX() - verts[0].getX()
	dy = verts[1].getY() - verts[0].getY()
	dz = verts[1].getZ() - verts[0].getZ()
	
	dia = math.sqrt(dx**2 + dy**2 + dz**2)
	
	arcLength = math.pi*dia/2.0
	
	edgeLength = edge.getLength()
	
	if abs(edgeLength - arcLength) > .01: return False
	
	return True






def calcMidLoc(verts):
	dx = verts[1].getX() - verts[0].getX()
	dy = verts[1].getY() - verts[0].getY()
	dz = verts[1].getZ() - verts[0].getZ()

	midLoc = [0.0, 0.0, 0.0]
	midLoc[0] = verts[0].getX() + dx/2.0
	midLoc[1] = verts[0].getY() + dy/2.0
	midLoc[2] = verts[0].getZ() + dz/2.0

	return midLoc






def getCandidateWasherNodes(washerRadius, attachNode, edge):
	faces = edge.getConnectedFaces()
	# I should have only a single face
	face = faces[0]
	
	faceNodes = face.getInteriorNodes()
	
	mySearch = apex.utility.ProximitySearch()
	mySearch.insertCollection(faceNodes)
	zNearbyObjects = mySearch.findObjectsWithinDistance(attachNode.getLocation(), washerRadius)
	nearbyObjects = zNearbyObjects.foundObjects()
	
	return nearbyObjects






def findNodesInCircle(washerDiameter, connectionPoint, nodesToCheck):
	radius = washerDiameter/2.0
	rad2 = 1.1*radius
	
	px = connectionPoint.getX()
	py = connectionPoint.getY()
	pz = connectionPoint.getZ()
	
	nodesToKeep = apex.entityCollection()
	for node in nodesToCheck:
		dx = node.getX() - px
		dy = node.getY() - py
		dz = node.getZ() - pz
		
		dist = dx*dx + dy*dy + dz*dz
		if dist > 0.0:
			dist = math.sqrt(dist)
		if dist <= rad2:
			nodesToKeep.append(node)

	return nodesToKeep





def createRBE(fastenerName, parentPart, _distributionType, midNode, attach, isSlot, connectWasher, washerFactor):
	
	dt = apex.attribute.getDiscreteTies(target=[{"path":parentPart.getPath()+"/"+parentPart.getName()}])
	if dt.len() == 0:
		createDiscreteTie = True
	else:
		createDiscreteTie = False
	
	
	# for the moment, I am assuming that the only discrete ties are the ones that I have created
	if createDiscreteTie:
		discreteTie = apex.attribute.createDiscreteTie(
                  name              = "", 
                  distributionType  = _distributionType,
                  distributionMode  = apex.attribute.DistributionMode.Auto,
                  parentInstance    = parentPart)
	_referenceRegion  = midNode
	_attachmentRegion = apex.EntityCollection()
	if isSlot:
		_attachmentRegion = apex.EntityCollection()
		_attachmentRegion.extend(attach)
	else:
		if attach.getEntityType() == apex.EntityType.Edge and connectWasher == True:
			holeDiameter = attach.getLength()/math.pi
			washerDiameter = washerFactor*holeDiameter
			searchDist = 2*washerDiameter
			nearbyObjects = getCandidateWasherNodes(searchDist, midNode, attach)
			if len(nearbyObjects) > 0:
				washerNodes = findNodesInCircle(washerDiameter, midNode, nearbyObjects)
			_attachmentRegion.append(attach)
			if len(washerNodes) > 0: _attachmentRegion.extend(washerNodes)
		else:
			_attachmentRegion.append(attach)

	nodeTie = apex.attribute.createNodeTie(
              name                 = fastenerName,
              distributionType     = _distributionType,
              distributionMode     = apex.attribute.DistributionMode.Auto,
              dofDefinitionMode    = apex.attribute.DOFDefinitionMode.All,
              referencePoint       = _referenceRegion,
              attachmentRegions    = _attachmentRegion,
              description          = "")

#	if _distributionType == apex.attribute.DistributionType.Compliant:
#		nodeTie = apex.attribute.createNodeTie(
#              name                 = fastenerName,
#              distributionType     = _distributionType,
#              distributionMode     = apex.attribute.DistributionMode.Auto,
#              dofDefinitionMode    = apex.attribute.DOFDefinitionMode.All,
#              referencePoint       = _referenceRegion,
#              attachmentRegions    = _attachmentRegion,
#              description          = "")
#	else:
#		nodeTie = apex.attribute.createNodeTie(
#              name                 = fastenerName,
#              distributionType     = apex.attribute.DistributionType.Rigid,
#              distributionMode     = apex.attribute.DistributionMode.Auto,
#              dofDefinitionMode    = apex.attribute.DOFDefinitionMode.All,
#              referencePoint       = _referenceRegion,
#              attachmentRegions    = _attachmentRegion,
#              description          = "")
	
	return nodeTie






def createMaterial(matlName):

	myModel = apex.currentModel()

	allMatls = apex.catalog.getMaterials([{"path":myModel.getPath()}])
	if allMatls.len() > 0:
		for matl in allMatls:
			if matl.getName().lower() == matlName.lower():
				return matl
	
	# If I am here, the material does not yet exist in the db
	
	if matlName == "Aluminum":
		E    = 10.0E6
		NU   = 0.3
		DENS = .101/386.09
	elif matlName == "Titanium":
		E    = 16.0E6
		NU   = 0.27
		DENS = .16/386.09
	elif matlName == "Steel":
		E    = 30.0E6
		NU   = 0.3
		DENS = .284/386.09
	else:
		matlName = "Aluminum"
		E    = 10.0E6
		NU   = 0.3
		DENS = .101/386.09
		
	matl = apex.catalog.createMaterial( name = matlName, description = "created by auTools", color = [ 64, 254, 250 ] )
	matl.update(elasticModulus = E)
	matl.update(poissonRatio = NU)
	matl.update(density = DENS)

	return matl





def getNearestNodeInPart(point):
	#import apex
	part = point.getParent()
	
	meshes = part.getMeshes()
	nodes = apex.entityCollection()
	for mesh in meshes:
		nodes += mesh.getNodes()
	
	iNodes = apex.IPhysicalCollection()
	for node in nodes:
		iNodes.append(node.asEntity())
		
	mySearch = apex.utility.ProximitySearch()
	mySearch.insertCollection(iNodes)
	
	loc = point.getLocation()
	nearestObject = mySearch.findNearestObject(loc)
	nearNode = nearestObject.getNearestObject()
	
	return nearNode











def main(dict={}):
#def main():
	startTime = time.process_time()

	global logEnabled

	tol              = float(dict["tolerance"])
	fastenerName     = dict["name"]
	fastenerMatl     = dict["material"]
	fastenerType     = dict["fastenerType"]
	distributionType = dict["distributionType"]
	maxDia           = float(dict["maxDiameter"])
	
	attachWasher = False
	if dict["attachWasher"].upper() == "TRUE": attachWasher = True
	
	washerFactor = float(dict["washerFactor"])
	washerFactor = abs(washerFactor)
	if washerFactor <= 1.0: attachWasher = False

	#tol              = .1
	#fastenerName     = ""
	#fastenerMatl     = "Titanium"
	#fastenerType     = "Flexible"
	#distributionType = "Compliant"
	#maxDia           = .75

	scriptName = "auCreateFasteners_Hole2Hole.py"
	
	myModel = apex.currentModel()
	#tmpPart = myModel.createPart("tmpPart")
	
	logFileName = myModel.getName()+"_autoCreateFasteners.log"
	
	try:
		tmp = tempfile.gettempdir()
		logfile=tmp+"\\"+logFileName
	except:
		logfile="C:\\"+logFileName
	
	try:
		logging.basicConfig(filename=logfile,filemode='w',level=logging.DEBUG)
		print("Output data being written to: "+logfile)
		logEnabled = True
	except:
		logEnabled = False
	
	print("Send questions/comments to larry.pearce@mscsoftware.com")
	if logEnabled:
		logging.info("Script: "+scriptName)
		logging.info("Send questions/comments to larry.pearce@mscsoftware.com")
		logging.info("#####################################################")
	
	logging.info("Apex model: "+myModel.getName())
	logging.info(time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))
	
	unitSystem = r'''in-slinch-s-lbf'''
	if logEnabled: logging.info("Using unit system: "+unitSystem)
	print("Using unit system: "+unitSystem)
	
	apex.setScriptUnitSystem(unitSystemName = unitSystem)

	main2(fastenerName, fastenerType, distributionType, fastenerMatl, tol, maxDia, False, attachWasher, washerFactor)
	
	endTime = time.process_time()
	
	seconds = endTime-startTime
	min, sec = divmod(seconds, 60)
	
	msg = "Approximate elapsed time: "+"%02d : %02d" % (min, sec)
	
	logging.info(msg)
	print("### Normal exit")
	print(msg)
	
	if logEnabled: logging.shutdown()





def main2(fastenerName, fastenerType, distributionType, fastenerMatl, tol, maxDia, allowMisalignedHoles, attachWasher, washerFactor):

	global apexRelease

	appData = apex.getApplicationInfo()
	apexRelease = appData["release"]
	
	print(apexRelease)

	myModel = apex.currentModel()
	myPI = math.pi
	
	if fastenerName == "": fastenerName = "Connector"
	
	connectorDistributionType = {"Compliant":apex.attribute.DistributionType.Compliant, "Rigid":apex.attribute.DistributionType.Rigid}
	connectorType             = {"Flexible": apex.attribute.ConnectorType.FlexibleLink,
	                             "Bushing":  apex.attribute.ConnectorType.Bushing,
	                             "Rigid":    apex.attribute.ConnectorType.RigidLink}
	
	#myMatl = createMaterial(fastenerMatl)
	
	
	myMatl = None
	matls = apex.catalog.getMaterials([{"path":myModel.getName()+"/Materials"}])
	for matl in matls:
		if matl.getName() == fastenerMatl:
			myMatl = matl
			break
	if myMatl == None and fastenerType != "Rigid":
		print("Unknown material?")
		return
	
	
	
	
	
	myEcho("Fastener Name: "+fastenerName, "Info")
	myEcho("Fastener Type: "+fastenerType, "Info")
	myEcho("Distribution Type: "+distributionType, "Info")
	myEcho("Fastener Material: "+fastenerMatl, "Info")
	myEcho("Tolerance "+str(tol), "Info")
	myEcho("Allow misaligned holes: "+str(allowMisalignedHoles), "Info")
	myEcho("Max hole diameter: "+str(maxDia), "Info")
	
	slotAreaTol       = tol/10.0
	slotEdgeLengthTol = tol/1000.0
	myEcho("Slot Area Tolerance: "+str(slotAreaTol), "Info")
	myEcho("Slot Edge Length Tolerance: "+str(slotEdgeLengthTol), "Info")
	
	myEcho("Attach Washer: "+str(attachWasher), "Info")
	if attachWasher == True: myEcho("Washer Factor: "+str(washerFactor), "Info")
	
	_selected = apex.selection.getCurrentSelection()
	
	allParts = apex.EntityCollection()
	for sel in _selected:
		if sel.getEntityType() == apex.EntityType.Part: allParts.append(sel)
	
	if allParts.len() == 0: allParts = myModel.getParts(True)
	myEcho("Number of Parts: "+str(allParts.len()-1), "Info") # minus 1 is for the tmpPart that has been created

	featureDims  = {}
	featureSeeds = {}
	numHole2D = numHole3D = numSeedPoints = 0
	for part in allParts:
		featureDims[part.getFullName()]  = []
		featureSeeds[part.getFullName()] = []
		
		numSurfHoles = numSeeds = 0
		surfs = part.getSurfaces()
		if surfs.len() > 0:
			myEcho("Processing Surfaces in Part: "+part.getName(), "Info")
			aa = apex.geometry.identifyFeature(target=surfs)
			features = aa.getFeaturesIdentified()
			if features.len() > 0:
				minDim = 999999.; maxDim = -1.0
				for feature in features:
					if feature.getEntityType() != apex.EntityType.Hole2D: continue
					numHole2D     += 1; numSurfHoles  += 1
					dim = feature.getFeatureDimension()
					featureDims[part.getFullName()].append([apex.EntityType.Hole2D, dim])
					if dim <= minDim: minDim = dim
					if dim >= maxDim: maxDim = dim
				if logEnabled and numHole2D > 0:
					msg = "Hole dimensional range for surfaces in Part: "+part.getPath()+" -- Min/Max= %7.4f / %7.4f" % (minDim, maxDim)
					logging.info(msg)
			
		points = part.getPoints()
		for point in points:
			associatedSeed = point.getAssociatedSeedPoint()
			if associatedSeed == None: continue
			numSeeds      += 1
			numSeedPoints += 1
			featureSeeds[part.getFullName()].append([point, associatedSeed])
		#featureSeeds[part.getFullName()] = numSeeds
		if logEnabled and numSeeds > 0:
			msg = str(numSeeds)+" seed points found for surfaces in Part: "+part.getPath()
			print(msg)
			logging.info(msg)
		if numSurfHoles > 0: continue # I am only going to process surfaces or solids in a part but not both
		if numSeeds > 0:     continue
		
		# process solids for holes
		solids = part.getSolids()
		if solids.len() > 0:
			myEcho("Processing Solids in Part: "+part.getName(), "Info")
			aa = apex.geometry.identifyFeature(target=solids)
			features = aa.getFeaturesIdentified()
			if features.len() > 0:
				minDim = 999999.0; maxDim = -1.0
				for feature in features:
					if feature.getEntityType() != apex.EntityType.Hole3D: continue
					numHole3D += 1
					dim = feature.getFeatureDimension()
					featureDims[part.getFullName()].append([apex.EntityType.Hole3D, dim])
					if dim <= minDim: minDim = dim
					if dim >= maxDim: maxDim = dim
				if logEnabled and numHole3D > 0:
					msg = "Hole dimensional range for solids in Part: "+part.getPath()+" -- Min/Max= %7.4f / %7.4f" % (minDim, maxDim)
					logging.info(msg)
	if numHole2D + numHole3D + numSeedPoints == 0:
		myEcho("No Hole Features are present in any surface or solid in any Part!", "Warning")
		return
	## END OF PART LOOP #########
	
	
	# validate the holes that have been found & look for slots
	holes     = []
	holeData  = {}
	hole3Data = {}
	numSlotsFound = numSlotsUsed = 0
	for part in allParts:
		myPath = part.getPath()[part.getPath().find("/")+1:]
		assy = part.getParent()
		if assy == None:
			myModel.setCurrentPart("/"+part.getName())
		else:
			partPath = part.getPath()[part.getPath().find("/")+1:]+"/"+part.getName()
			myModel.setCurrentPart(partPath)
		
		#myModel.setCurrentPart(myPath+"/"+part.getName())
		if len(featureDims[part.getFullName()]) == 0 and len(featureSeeds[part.getFullName()]) == 0: continue
		
		surfs = part.getSurfaces()
		numSurfHoles = numSolidHoles = numSeeds = 0
		for surf in surfs:
			points = apex.entityCollection() 
			edges = surf.getEdges()
			numPotentialHoles = 0
			for edge in edges:
				if isStraightLine(edge): continue  # check to see if the edge is a straight line
				length = edge.getLength()
				dia = length/myPI
				if dia >= maxDia: continue
				# see if the edge length matches a feature dimension, circumference.  this will filter out edges that are not potentially holes
				for dimData in featureDims[part.getFullName()]:
					if dimData[0] != apex.EntityType.Hole2D: continue 
					dim = dimData[1]
					if abs(dia - dim) <= tol:
						center = calcHoleCenter(edge) # center is a Point
						normalVec = calcSurfaceNormalAtHole(surf, edge)
						holes.append(center)
						points.append(center)
						
						holeData[center.getFullName()] = {"centerPoint":center, "is2D":True, "surf":surf, "holeAttach":edge, "edgeLength":length, "isUsed":0, "part":part, "normal":normalVec,
						                                  "solid":None, "endPoints":None, "attachNode":None, "isSlot":False, "slotFaces":None, "p2p":False}
						numPotentialHoles += 1
						numSurfHoles      += 1
						#should also get an orientation to later verify proper fastener orientation and not build skew fasteners
						break
			myEcho("  Potential Holes: "+str(numPotentialHoles)+"  ("+part.getName()+"/"+surf.getName()+")", "Info")
		
		for data in featureSeeds[part.getFullName()]:
			point = data[0]
			associatedSeed = data[1]
			holes.append(point)
			surf = associatedSeed.getTarget().getBody().asSurface()
			normVec = surf.evaluateSurfaceNormal(point)
			normVec = normalizeVector(normVec)
			n1 = getNearestNodeInPart(point)
			holeData[point.getFullName()] = {"centerPoint":point, "is2D":True, "surf":surf, "holeAttach":n1, "edgeLength":0., "isUsed":0, "part":part, "normal":normVec, "solid":None, "endPoints":None, "attachNode":n1.asNode(), "isSlot":False, "slotFaces":None, "p2p":True}
		
		if numSurfHoles > 0:                          continue # I am only processing the surfaces or the solids in a Part and not both
		if len(featureSeeds[part.getFullName()]) > 0: continue
		
		solids = part.getSolids()
		for solid in solids:
			faces = solid.getFaces()
			numPotentialHoles = 0
			for face in faces:
				edges = face.getEdges()
				if edges.len() != 2: continue # a hole cylinder face will only have 2 edges.  i will need to extend this in the future
				isPotentialHole = False       # assume the face does not belong to a hole cylinder
				edgeLengths = []
				for edge in edges:
					if isStraightLine(edge): break # get out of edge loop, goto next face
					length = edge.getLength()
					dia = length/myPI
					if dia >= maxDia: break # get out of edge loop, goto next face
					for dimData in featureDims[part.getFullName()]:
						if dimData[0] != apex.EntityType.Hole3D: continue
						if abs(dia - dimData[1]) <= tol:
							isPotentialHole = True
							break
					edgeLengths.append(length)
				if isPotentialHole == False: continue                   # go to next face
				if len(edgeLengths) != 2:    continue                   # go to next face
				if abs(edgeLengths[0] - edgeLengths[1]) > tol: continue # go to next face
				points = apex.entityCollection()
				for edge in edges:
					points.append(calcHoleCenter(edge))
				holeHeight = calcDistanceBetweenPoints(points[0], points[1])
				calcArea = edgeLengths[0]*holeHeight
				area = face.getArea()
				if abs(area - calcArea) > tol:
					apex.deleteEntities(target = points)
					continue # go to next face
				
				numPotentialHoles += 1
				numSolidHoles     += 1
				center = createPointAtCylinderCenter(points[0], points[1])
				holes.append(center)
				
				holeData[center.getFullName()] = {"centerPoint":center, "is2D": False, "surf":None, "holeAttach":face, "edgeLength":edgeLengths[0], "isUsed":0, "part":part, "normal":None,
				                                  "solid":solid, "endPoints":points, "attachNode":None, "isSlot":False, "slotFaces":None, "p2p":False}
				hole3Data[points[0].getFullName()] = center
				hole3Data[points[1].getFullName()] = center
			myEcho("  Potential Holes: "+str(numPotentialHoles)+"  ("+part.getName()+"/"+solid.getName()+")", "Info")
		
		# check for slots in solids
		for solid in solids:
			faces = solid.getFaces()
			usedFaces = []
			for face in faces:
				if face.getId() in usedFaces: continue
				edges = face.getEdges()
				if edges.len() != 4: continue
				numStraightLines = 0
				numArcLines      = 0
				straightEdges    = []
				arcEdges         = []
				rectFaces        = []
				for edge in edges:
					if isStraightLine2(edge):
						numStraightLines += 1
						straightEdges.append(edge)
					elif isArc(edge):
						numArcLines += 1
						arcEdges.append(edge)
				if numArcLines == 2 and numStraightLines == 2: # I have potentially found one side of the slot
					arcFaceId   = face.getId()
					arcFace     = face
					arcFaceArea = face.getArea()
					arcLength   = arcEdges[0].getLength()
					
					if 2*arcLength/myPI > maxDia: continue
					
					midLocs = []
					for edge in arcEdges:
						verts = edge.getVertices()
						midLocs.append(calcMidLoc(verts))
					dx = midLocs[1][0] - midLocs[0][0]
					dy = midLocs[1][1] - midLocs[0][1]
					dz = midLocs[1][2] - midLocs[0][2]
					midLocs.append([midLocs[0][0]+dx/2.0, midLocs[0][1]+dy/2.0, midLocs[0][2]+dz/2.0])
					dist = dx**2 + dy**2 + dz**2
					dist = math.sqrt(dist)
					midLocs.append([dx/dist, dy/dist, dz/dist])
					midLocs.append([dist])
					
					ff = straightEdges[0].getConnectedFaces()
					# this should return 2 faces.  one is the arc face of the slot and one is the straight face of the slot
					if ff.len() == 2:
						for f in ff:
							if f.getId() == arcFaceId: continue
							if f.getEdges().len() == 4: rectFaces.append(f)
					ff = straightEdges[1].getConnectedFaces()
					if ff.len() == 2:
						for f in ff:
							if f.getId() == arcFaceId: continue
							if f.getEdges().len() == 4: rectFaces.append(f)
					if len(rectFaces) != 2: continue
					
					if abs(rectFaces[0].getArea() - rectFaces[1].getArea()) > slotAreaTol: continue
					
					length = straightEdges[0].getLength()
					edgeId = straightEdges[0].getId()
					edges = rectFaces[0].getEdges()
					newEdges = []
					for edge in edges:
						if edge.getId() == edgeId: continue
						if abs(edge.getLength() - length) <= slotEdgeLengthTol:
							newEdges.append(edge)
							break
					length = straightEdges[1].getLength()
					edgeId = straightEdges[1].getId()
					edges = rectFaces[1].getEdges()
					for edge in edges:
						if edge.getId() == edgeId: continue
						if abs(edge.getLength() - length) <= slotEdgeLengthTol:
							newEdges.append(edge)
							break
					if len(newEdges) != 2: continue
					
					ff1=newEdges[0].getConnectedFaces()
					ff2=newEdges[1].getConnectedFaces()
					
					nextFace = False
					for f1 in ff1:
						if f1.getId() == arcFaceId: continue
						straightEdges2 = []
						arcEdges2      = []
						for f2 in ff2:
							if f2.getId() == arcFaceId: continue
							if f1.getId() == f2.getId():
								arcFace2 = solid.getFace(int(f1.getId()))
								if abs(arcFace2.getArea() - arcFaceArea) > slotAreaTol: continue
								edges = arcFace2.getEdges()
								numArcLines = numStraightLines = 0
								for edge in edges:
									if isStraightLine2(edge):
										numStraightLines += 1
										straightEdges2.append(edge)
									elif isArc(edge):
										numArcLines += 1
										arcEdges2.append(edge)
									if numArcLines == 2 and numStraightLines == 2: # I have found the other side of the slot
										midLocs2 = []
										for edge in arcEdges2:
											verts = edge.getVertices()
											midLocs2.append(calcMidLoc(verts))
										dx = midLocs2[1][0] - midLocs2[0][0]
										dy = midLocs2[1][1] - midLocs2[0][1]
										dz = midLocs2[1][2] - midLocs2[0][2]
										midLocs2.append([midLocs2[0][0]+dx/2.0, midLocs2[0][1]+dy/2.0, midLocs2[0][2]+dz/2.0])
										
										dx = midLocs2[2][0] - midLocs[2][0]
										dy = midLocs2[2][1] - midLocs[2][1]
										dz = midLocs2[2][2] - midLocs[2][2]
										
										x = midLocs[2][0]+dx/2.0
										y = midLocs[2][1]+dy/2.0
										z = midLocs[2][2]+dz/2.0
										center = apex.geometry.createPointXYZ(x, y, z)
										
										dx = midLocs[3][0]*dist/2.0
										dy = midLocs[3][1]*dist/2.0
										dz = midLocs[3][2]*dist/2.0
										
										points = apex.entityCollection()
										points.append(apex.geometry.createPointXYZ(x+dx, y+dy, z+dz))
										points.append(apex.geometry.createPointXYZ(x-dx, y-dy, z-dz))
										holeAttach = apex.entityCollection()
										holeAttach.append(rectFaces[0])
										holeAttach.append(rectFaces[1])
										
										holes.append(center)
										
										holeData[center.getFullName()] = {"centerPoint":center, "is2D": False, "surf":None, "holeAttach":holeAttach, "edgeLength":2*arcLength, "isUsed":0, "part":part, "normal":None,
				                                                          "solid":solid, "endPoints":points, "attachNode":None, "isSlot":True, "slotFaces":holeAttach, "p2p":False}
										hole3Data[points[0].getFullName()] = center
										hole3Data[points[1].getFullName()] = center
										
										usedFaces.append(arcFaceId)
										usedFaces.append(arcFace2.getId())
										
										numSlotsFound += 1
										
										nextFace = True
										break # get out of edge loop
								if nextFace: break # get out of ff2 loop
						if nextFace: break # get out of ff1 loop and back into face loop
		print("Potential slots found: "+str(numSlotsFound))
		
		
		#points = part.getPoints()
		#for point in points:
		#	associatedSeed = point.getAssociatedSeedPoint()
		#	if associatedSeed is None: continue
		#	holes.append(point)
		#	surf = associatedSeed.getTarget().getBody().asSurface()
		#	normVec = surf.evaluateSurfaceNormal(point)
		#	normVec = normalizeVector(normVec)
		#	n1 = getNearestNodeInPart(point)
		#	holeData[point.getFullName()] = {"centerPoint":point, "is2D":True, "surf":surf, "holeAttach":n1, "edgeLength":0., "isUsed":0, "part":part, "normal":normVec, "solid":None, "endPoints":None, "attachNode":n1.asNode(), "isSlot":False, "slotFaces":None, "p2p":True}
	
	allLocs = apex.IPhysicalCollection()
	for hole in holes:
		if holeData[hole.getFullName()]["is2D"]:
			allLocs.append(holeData[hole.getFullName()]["centerPoint"])
		else:
			allLocs.append(holeData[hole.getFullName()]["endPoints"][0])
			allLocs.append(holeData[hole.getFullName()]["endPoints"][1])

	mySearch = apex.utility.ProximitySearch()
	mySearch.insertCollection(allLocs)

	connectors = []
	for hole in holes:
		locs = apex.entityCollection()
		if holeData[hole.getFullName()]["is2D"]:
			locs.append(hole)
		else:
			locs = holeData[hole.getFullName()]["endPoints"]
		
		# I am looking for x nearest objects.  One will be the point that I searched for, ie, itself and the other will be the nearest point which is what I want
		for loc in locs:
			nearbyObjects = mySearch.findNearestObjects(loc, 3)
			foundObjects = nearbyObjects.foundObjects()
		
			otherObj = []
			for obj in foundObjects:
				if obj.getFullName() not in holeData.keys(): # this means the found hole is for a solid
					center = hole3Data[obj.getFullName()]
				else: # this means the found hole is for a surface
					center = obj
				
				if center.getFullName() == hole.getFullName():
					startObj = obj
				else:
					otherObj.append(obj)
			
			if len(otherObj) == 0: continue  # effectively, no close points found
			
			foundObjects = []
			if len(otherObj) == 1:
				foundObjects.append(otherObj[0])
			else:
				# if 2 close objects are in the same direction from the startObj, then only take the closest
				objData = []
				for obj in otherObj:
					dist = calcDistanceBetweenPoints(startObj, obj)
					vec  = calcVectorBetweenPoints(startObj, obj)
					objData.append([obj, dist, vec])
				cosTheta  = objData[0][2].getX()*objData[1][2].getX()
				cosTheta += objData[0][2].getY()*objData[1][2].getY()
				cosTheta += objData[0][2].getZ()*objData[1][2].getZ()
				
				if (1.0-cosTheta <= .001):  # same direction, take closest
					if objData[0][1] < objData[1][1]:
						foundObjects.append(objData[0][0])
					else:
						foundObjects.append(objData[1][0])
				else: # opposite direction, keep both
					foundObjects.append(objData[0][0])
					foundObjects.append(objData[1][0])

			for obj in foundObjects:
				if obj.getFullName() not in holeData.keys(): # this means the found hole is for a solid
					center = hole3Data[obj.getFullName()]
				else: # this means the found hole is for a surface
					center = obj
				
				if center.getFullName() == hole.getFullName(): continue  # compare hole point names.  a point cannot find itself
				# skip if both edges or holes have already been used in a connector to avoid creating duplicate connectors
				##if holeData[center.getFullName()]["isUsed"]+holeData[hole.getFullName()]["isUsed"] == 2: continue
				# make sure the edge length between the 2 holes are the same within a tolerance
				# divide by PI to use hole diameter in check vs just the raw length.  i found this makes the script a little less dependent on units but it is still not perfect
				#if abs(holeData[center.getFullName()]["edgeLength"]-holeData[hole.getFullName()]["edgeLength"])/myPI > tol: continue
				
				if holeData[hole.getFullName()]["is2D"]      and holeData[center.getFullName()]["is2D"]:     connection = "2D2D"
				if holeData[hole.getFullName()]["is2D"]      and not holeData[center.getFullName()]["is2D"]: connection = "2D3D"
				if not holeData[hole.getFullName()]["is2D"]  and holeData[center.getFullName()]["is2D"]:     connection = "2D3D"
				if not holeData[hole.getFullName()]["is2D"]  and not holeData[center.getFullName()]["is2D"]: connection = "3D3D"
				
				if connection == "2D2D":
					# compare surface names where the holes are located.  I cannot find a hole that is in the same surface
					if holeData[hole.getFullName()]["surf"] == holeData[center.getFullName()]["surf"]: continue
					
					# check to see if hole axis is aligned with surfaces to be connected
					if not allowMisalignedHoles:
						holeToHoleVec = calcVectorBetweenPoints(hole, holeData[center.getFullName()]["centerPoint"])
						if isNotParallel(holeToHoleVec, holeData[center.getFullName()]["normal"], tol): continue
				elif connection == "3D3D":
					# compare solid names where the holes are located.  I cannot find a hole that is in the same solid
					if holeData[hole.getFullName()]["solid"] == holeData[center.getFullName()]["solid"]: continue
					
					# at this point, I am not checking for misaligned solids.  this would be a bit more effort to extract the correct solid faces
					# to compute the face normals
				else:
					if holeData[hole.getFullName()]["is2D"]:
						endLocs = holeData[center.getFullName()]["endPoints"]
					else:
						endLocs = holeData[hole.getFullName()]["endPoints"]
					vecA = calcVectorBetweenPoints(holeData[hole.getFullName()]["centerPoint"], holeData[center.getFullName()]["centerPoint"])
					vecB = calcVectorBetweenPoints(endLocs[0], endLocs[1])
					if isNotParallel(vecB, vecA, tol): continue
				
				
				if holeData[hole.getFullName()]["isUsed"] == 0 and holeData[hole.getFullName()]["p2p"] == False:
					attachNode = apex.mesh.createNodeByPickLocation(target = holeData[hole.getFullName()]["centerPoint"].getVertices()[0],
																	location = holeData[hole.getFullName()]["centerPoint"].getLocation())
					holeData[hole.getFullName()]["attachNode"] = attachNode
				if holeData[center.getFullName()]["isUsed"] == 0 and holeData[center.getFullName()]["p2p"] == False:
					attachNode = apex.mesh.createNodeByPickLocation(target = holeData[center.getFullName()]["centerPoint"].getVertices()[0],
																	location = holeData[center.getFullName()]["centerPoint"].getLocation())
					holeData[center.getFullName()]["attachNode"] = attachNode
						
						
				# NOTE THAT I COULD ALSO CHECK GRIP LENGTH BUT AM NOT DOING SO AT THIS TIME
				if holeData[center.getFullName()]["is2D"] and holeData[hole.getFullName()]["is2D"]:
					length = calcDistanceBetweenPoints(holeData[center.getFullName()]["centerPoint"], holeData[hole.getFullName()]["centerPoint"])
				elif holeData[hole.getFullName()]["is2D"] and not holeData[center.getFullName()]["is2D"]:
					d1 = calcDistanceBetweenPoints(holeData[center.getFullName()]["endPoints"][0], holeData[center.getFullName()]["endPoints"][1])
					d2 = calcDistanceBetweenPoints(holeData[hole.getFullName()]["centerPoint"], holeData[center.getFullName()]["centerPoint"])
					length = d2 + 0.5*d1
				elif not holeData[hole.getFullName()]["is2D"]  and holeData[center.getFullName()]["is2D"]:
					d1 = calcDistanceBetweenPoints(holeData[hole.getFullName()]["endPoints"][0], holeData[hole.getFullName()]["endPoints"][1])
					d2 = calcDistanceBetweenPoints(holeData[hole.getFullName()]["centerPoint"], holeData[center.getFullName()]["centerPoint"])
					length = d2 + 0.5*d1
				else:
					d1 = calcDistanceBetweenPoints(holeData[hole.getFullName()]["endPoints"][0], holeData[hole.getFullName()]["endPoints"][1])
					d2 = calcDistanceBetweenPoints(holeData[center.getFullName()]["endPoints"][0], holeData[center.getFullName()]["endPoints"][1])
					d3 = calcDistanceBetweenPoints(holeData[hole.getFullName()]["centerPoint"], holeData[center.getFullName()]["centerPoint"])
					length = d3 + 0.5*d1 + 0.5*d2
		
				connData = {"p1_is2D":       holeData[center.getFullName()]["is2D"], 
							"p1_isSlot":     holeData[center.getFullName()]["isSlot"], 
							"p1_attachNode": holeData[center.getFullName()]["attachNode"], 
							"p1_holeAttach": holeData[center.getFullName()]["holeAttach"],
							"p1_dia":        holeData[center.getFullName()]["edgeLength"]/myPI,
							"p1_part":       holeData[center.getFullName()]["part"],
							"p1_isP2P":      holeData[center.getFullName()]["p2p"],
							"p2_is2D":       holeData[hole.getFullName()]["is2D"], 
							"p2_isSlot":     holeData[hole.getFullName()]["isSlot"], 
							"p2_attachNode": holeData[hole.getFullName()]["attachNode"], 
							"p2_holeAttach": holeData[hole.getFullName()]["holeAttach"], 
							"p2_dia":        holeData[hole.getFullName()]["edgeLength"]/myPI,
							"p2_part":       holeData[hole.getFullName()]["part"],
							"p2_isP2P":      holeData[hole.getFullName()]["p2p"],
							"length":        length}
				connectors.append(connData)
				
				# set flag so that i know that both points or edges have been used in a connector
				holeData[center.getFullName()]["isUsed"]  = 1
				holeData[hole.getFullName()]["isUsed"]    = 1
		

	#if not keepPoints:
	#	_target = apex.entityCollection()
	#	for data in edgeData:
	#		_target.append(data)
	#	apex.deleteEntities(_target)

	myEcho("Potential connectors to be created: "+str(len(connectors)), "Info")
	
	fastenerMatl = myMatl
	
	connectorsCreated = []
	rbeNodes          = []
	numConnectorsCreated = 0
	for conn in connectors:
		p1NodeId = conn["p1_attachNode"].getId()
		p2NodeId = conn["p2_attachNode"].getId()
		connExist = False
		for cc in connectorsCreated:
			if p1NodeId == cc[0] and p2NodeId == cc[1]: connExist = True
			if p1NodeId == cc[1] and p2NodeId == cc[0]: connExist = True
			if connExist: break
		if connExist: continue
	
		distType = connectorDistributionType[distributionType]
		if conn["p1_isP2P"] == False and p1NodeId not in rbeNodes:
			createRBE(fastenerName, conn["p1_part"], distType, conn["p1_attachNode"], conn["p1_holeAttach"], conn["p1_isSlot"], attachWasher, washerFactor)
			rbeNodes.append(p1NodeId)
		if conn["p2_isP2P"] == False and p2NodeId not in rbeNodes:
			createRBE(fastenerName, conn["p2_part"], distType, conn["p2_attachNode"], conn["p2_holeAttach"], conn["p2_isSlot"], attachWasher, washerFactor)
			rbeNodes.append(p2NodeId)
		
		_endPoint1 = apex.construct.createLocationByEntity(entity = conn["p1_attachNode"])
		_endPoint2 = apex.construct.createLocationByEntity(entity = conn["p2_attachNode"])
		
		fastenerDia = conn["p1_dia"]
		if conn["p1_isP2P"]: fastenerDia = conn["p2_dia"]
		if conn["p2_isP2P"]: fastenerDia = conn["p1_dia"]
		fastenerLength = conn["length"]
		if fastenerLength <= 0.0: fastenerLength = 0.0
		
		
		if conn["p1_isP2P"] == True and conn["p2_isP2P"] == True: fastenerLength = 0.0
		
		if fastenerLength == 0.0:
			connProp = connectorProps(apex.attribute.ConnectorType.RigidLink, fastenerDia, fastenerLength, fastenerMatl)
			_connectorType = connectorType["Rigid"]
		else:
			connProp = connectorProps(connectorType[fastenerType], fastenerDia, fastenerLength, fastenerMatl)
			_connectorType = connectorType[fastenerType]
		
		myConnector = apex.attribute.createConnector(
                          name = fastenerName,
                          connectorType       = _connectorType,
                          connectorProperties = connProp,
                          applicationMethod1  = apex.attribute.ApplicationMethod.Direct,
                          applicationMethod2  = apex.attribute.ApplicationMethod.Direct,
                          end1InterfacePoint  = _endPoint1,
                          end2InterfacePoint  = _endPoint2,
                          description         = "")

		myConnector.addUserAttribute(userAttributeName = "au_P2P", stringValue = "auCreateFasteners_Hole2Hole")
		
		myConnector.addUserAttribute(userAttributeName = "end1_X", floatValue = _endPoint1.getAssociatedEntity().asNode().getX())
		myConnector.addUserAttribute(userAttributeName = "end1_Y", floatValue = _endPoint1.getAssociatedEntity().asNode().getY())
		myConnector.addUserAttribute(userAttributeName = "end1_Z", floatValue = _endPoint1.getAssociatedEntity().asNode().getZ())
		
		myConnector.addUserAttribute(userAttributeName = "end2_X", floatValue = _endPoint2.getAssociatedEntity().asNode().getX())
		myConnector.addUserAttribute(userAttributeName = "end2_Y", floatValue = _endPoint2.getAssociatedEntity().asNode().getY())
		myConnector.addUserAttribute(userAttributeName = "end2_Z", floatValue = _endPoint2.getAssociatedEntity().asNode().getZ())

		numConnectorsCreated += 1
		connectorsCreated.append([p1NodeId, p2NodeId])

	myEcho("Number of Connectors created: "+str(numConnectorsCreated), "Info")





#main()

