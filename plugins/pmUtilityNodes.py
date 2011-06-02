import sys

import maya.OpenMaya as om
import maya.OpenMayaMPx as mpx

SUPPLIER = "Paul Molodowitch"
VERSION = 0.1
API_VERSION = "Any"

# Node definition
class pmVertexColorComponents(mpx.MPxNode):
    nodeName = "pmVertexColorComponents"
    nodeId = om.MTypeId(0x83201)

    # attributes
    meshAttr = None
    
    COMPONENTS = ('red', 'green', 'blue', 'alpha',
                  'hue', 'saturation', 'value')
    
    multiAttrs = dict( (x, None) for x in COMPONENTS)
    # short names are rm, gm, bm, am, mm
    multiAttrLongNames = dict( (x, x + 'Multi') for x in COMPONENTS)
    multiAttrShortNames = dict( (x, x[0] + 'm') for x in COMPONENTS)

#    arrayAttrs = dict( (x, None) for x in COMPONENTS)
#    arrayAttrLongNames = dict( (x, x + 'Array') for x in COMPONENTS)
#    arrayAttrShortNames = dict( (x, x[0] + 'a') for x in COMPONENTS)
    
    def __init__(self):
        super(pmVertexColorComponents, self).__init__()

    @classmethod
    def creator(cls):
        return mpx.asMPxPtr( cls() )
    
    @classmethod
    def initialize(cls):
        # mesh
        typeAttr = om.MFnTypedAttribute()
        cls.meshAttr = typeAttr.create("mesh", "me", om.MFnData.kMesh)
        typeAttr.setReadable(False)
        cls.addAttribute(cls.meshAttr)
        
        for component in cls.COMPONENTS:
            numAttr = om.MFnNumericAttribute()
            newAttrObj = numAttr.create(cls.multiAttrLongNames[component],
                                        cls.multiAttrShortNames[component],
                                        om.MFnNumericData.kFloat, 0)
            cls.multiAttrs[component] = newAttrObj
            numAttr.setArray(True)
            numAttr.setWritable(False)
            numAttr.setUsesArrayDataBuilder(True)
            cls.addAttribute(newAttrObj)
            cls.attributeAffects(cls.meshAttr, newAttrObj)
            
        for comp, attr in cls.multiAttrs.iteritems():
            #print "%s %s" % (comp, attr)
            if attr is None:
                raise RuntimeError("%s %s" % (comp, attr))

    def compute(self, plug, dataBlock):
        # Always update the whole array at once - we shouldn't be connecting to
        # only a single element in the output arrays anyway (ie, what happens
        # if the number of verts changes, and we're connected to an output
        # index whose vert no longer exists?)
        
        #print plug
        #print self.multiAttrs.values()
        
        if plug in self.multiAttrs.values():
            meshDataHandle = dataBlock.inputValue(self.meshAttr)
            meshObj = meshDataHandle.asMesh()

            handles = {}
            for comp, attr in self.multiAttrs.iteritems():
                handles[comp] = dataBlock.outputArrayValue(attr)
                
            builders = {}
            for comp, handle in handles.iteritems():
                builders[comp] = handle.builder()
                        
            vertIter = om.MItMeshVertex(meshObj)
            while not vertIter.isDone():
                index = vertIter.index()
                
                # Retrieve the component color info
                color = om.MColor()
                if vertIter.hasColor():
                    vertIter.getColor(color)
                r = color.r
                g = color.g
                b = color.b
                a = color.a
                
                hUtil = om.MScriptUtil()
                hUtil.createFromDouble(0.0)
                hPtr = hUtil.asFloatPtr()

                sUtil = om.MScriptUtil()
                sUtil.createFromDouble(0.0)
                sPtr = hUtil.asFloatPtr()
                
                vUtil = om.MScriptUtil()
                vUtil.createFromDouble(0.0)
                vPtr = hUtil.asFloatPtr()
                
                color.get(color.kHSV, hPtr, sPtr, vPtr)
                
                h = hUtil.getFloat(hPtr)
                s = sUtil.getFloat(sPtr)
                v = vUtil.getFloat(vPtr)
                
                #print "rgba %3d: %s, %s, %s, %s" % (index, r, g, b, a)
                #print "hsv  %3d:  %s, %s, %s" % (index, h, s, v)
                
                # Add the elements to the array, and set them
                indexHandles = {}
                for comp, builder in builders.iteritems():
                    indexHandles[comp] = builder.addElement(index)
                    
                indexHandles['red'].setFloat(r)
                indexHandles['green'].setFloat(g)
                indexHandles['blue'].setFloat(b)
                indexHandles['alpha'].setFloat(a)
                indexHandles['hue'].setFloat(h)
                indexHandles['saturation'].setFloat(s)
                indexHandles['value'].setFloat(v)

                # done!
                vertIter.next()
                
            # Set the array plugs to the builders
            for comp, handle in handles.iteritems():
                handle.set(builders[comp])

            # mark all array plugs clean
            for handle in handles.itervalues():
                handle.setAllClean()
                
            dataBlock.setClean(plug)
        return om.kUnknownParameter


# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = mpx.MFnPlugin(mobject)
    try:
        mplugin.registerNode(pmVertexColorComponents.nodeName,
                             pmVertexColorComponents.nodeId,
                             pmVertexColorComponents.creator,
                             pmVertexColorComponents.initialize)
    except:
        sys.stderr.write( "Failed to register node: %s" % pmVertexColorComponents.nodeName )
        raise

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = mpx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( pmVertexColorComponents.nodeId )
    except:
        sys.stderr.write( "Failed to deregister node: %s" % pmVertexColorComponents.nodeName )
        raise
    
