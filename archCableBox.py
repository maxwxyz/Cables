"""ArchCableBox
"""

import FreeCAD
import ArchComponent
import os
import Part
from math import pi
import DraftVecUtils


_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "Resources/icons")
CLASS_CABLEBOX_ICON = os.path.join(iconPath, "classArchCableBox.svg")


class ArchCableBox(ArchComponent.Component):
    """The ArchCableBox object
    """
    def __init__(self, obj):
        ArchComponent.Component.__init__(self, obj)
        self.setProperties(obj)
        from ArchIFC import IfcTypes
        if "Cable Fitting" in IfcTypes:
            obj.IfcType = "Cable Fitting"
        else:
            # IFC2x3 does not know a Cable Fitting
            obj.IfcType = "Building Element Proxy"
        obj.addExtension('Part::AttachExtensionPython')

    def setProperties(self, obj):
        pl = obj.PropertiesList
        if "Diameter" not in pl:
            obj.addProperty("App::PropertyLength", "Diameter", "CableBox",
                            "The diameter of this box")
        if "Thickness" not in pl:
            obj.addProperty("App::PropertyLength", "Thickness", "CableBox",
                            "The wall thickness of this box")
        if "Height" not in pl:
            obj.addProperty("App::PropertyLength", "Height", "CableBox",
                            "The height of this box")
        if "BoxBodyHidden" not in pl:
            obj.addProperty("App::PropertyBool", "BoxBodyHidden", "CableBox",
                            "Hide the box body to have better access " +
                            "to helpers")
        if "HelperRingsHidden" not in pl:
            obj.addProperty("App::PropertyBool", "HelperRingsHidden",
                            "CableBoxHelpers", "Hide the helper rings " +
                            "if they are not needed")
        if "Ring1Diameter" not in pl:
            obj.addProperty("App::PropertyLength", "Ring1Diameter",
                            "CableBoxHelpers", "The diameter of helper ring 1")
        if "Ring1Height" not in pl:
            obj.addProperty("App::PropertyLength", "Ring1Height",
                            "CableBoxHelpers", "The height below lid of " +
                            "helper ring 1")
        if "Ring2Diameter" not in pl:
            obj.addProperty("App::PropertyLength", "Ring2Diameter",
                            "CableBoxHelpers", "The diameter of helper ring 2")
        if "Ring2Height" not in pl:
            obj.addProperty("App::PropertyLength", "Ring2Height",
                            "CableBoxHelpers", "The height below lid of " +
                            "helper ring 2")
        self.Type = "CableBox"

    def onChanged(self, obj, prop):
        pass

    def execute(self, obj):
        # FreeCAD.Console.PrintMessage("ArchBox.execute: start\n")
        pl = obj.Placement
        shapes = []
        shapes.append(self.makeHelperLines(obj))
        if not obj.HelperRingsHidden:
            shapes.append(self.makeHelperRings(obj))
        if not obj.BoxBodyHidden:
            shapes.append(self.makeBox(obj))
        sh = Part.makeCompound(shapes)
        obj.Shape = self.processSubShapes(obj, sh, pl)
        obj.Placement = pl
        # FreeCAD.Console.PrintMessage("ArchBox.execute: end\n")

    def makeHelperLines(self, obj):
        # helper crosses
        x0 = obj.Diameter.Value/2
        x = 6
        y0 = obj.Diameter.Value/2
        y = 6
        z0 = -2*obj.Height.Value/3
        z = 6
        cross1 = [(x0, 0, z0),
                  (x0, -y, z0),
                  (x0, y, z0),
                  (x0, 0, z0+z),
                  (x0, 0, z0-z)]
        cross2 = [(-x0, 0, z0),
                  (-x0, y, z0),
                  (-x0, -y, z0),
                  (-x0, 0, z0+z),
                  (-x0, 0, z0-z)]
        cross3 = [(0, y0, z0),
                  (x, y0, z0),
                  (-x, y0, z0),
                  (0, y0, z0+z),
                  (0, y0, z0-z)]
        cross4 = [(0, -y0, z0),
                  (-x, -y0, z0),
                  (x, -y0, z0),
                  (0, -y0, z0+z),
                  (0, -y0, z0-z)]
        crosses = [cross1, cross2, cross3, cross4]
        lines = []
        for cross in crosses:
            v = []
            for c in cross:
                v.append(FreeCAD.Vector(*c))
            lines.append(Part.LineSegment(v[1], v[0]))
            lines.append(Part.LineSegment(v[0], v[2]))
            lines.append(Part.LineSegment(v[3], v[0]))
            lines.append(Part.LineSegment(v[0], v[4]))
        s = Part.Shape(lines)
        return s

    def makeHelperRings(self, obj):
        # helper rings
        lines = []
        v1 = FreeCAD.Vector(0, obj.Ring1Diameter.Value/2,
                            -obj.Ring1Height.Value)
        v2 = FreeCAD.Vector(0, obj.Ring2Diameter.Value/2,
                            -obj.Ring2Height.Value)
        vh = [v1, v2]
        for nr in range(len(vh)):
            v = [vh[nr]]
            for i in range(12):
                angle = i*2*pi/12
                vn = DraftVecUtils.rotate2D(vh[nr], angle)
                v.append(vn)
            v.append(vh[nr])
            poly = Part.makePolygon(v)
            lines.append(poly)
        s = Part.Shape(lines)
        return s

    def makeBox(self, obj):
        vc = FreeCAD.Vector(0, 0, 0)
        vn = FreeCAD.Vector(0, 0, -1)
        box = Part.makeCylinder(obj.Diameter/2, obj.Height, vc, vn)
        inner_box = Part.makeCylinder(obj.Diameter/2-obj.Thickness,
                                      obj.Height-obj.Thickness, vc, vn)
        box = box.cut(inner_box)
        vn_list = [FreeCAD.Vector(1, 0, 0), FreeCAD.Vector(-1, 0, 0),
                   FreeCAD.Vector(0, 1, 0), FreeCAD.Vector(0, -1, 0)]
        vc = FreeCAD.Vector(0, 0, -2*obj.Height/3)
        hole_radius = 10
        hole_hight = obj.Diameter/2
        for vn in vn_list:
            hole = Part.makeCylinder(hole_radius, hole_hight, vc, vn)
            box = box.cut(hole)
        return box


class ViewProviderCableBox(ArchComponent.ViewProviderComponent):
    """A View Provider for the ArchCableBox object
    """

    def __init__(self, vobj):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLEBOX_ICON


def makeCableBox(baseobj=None, diameter=0, height=0, placement=None,
                 name=None):
    """Creates a cable box object from the given base object
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "CableBox")
    obj.Label = name if name else "CableBox"
    ArchCableBox(obj)
    if FreeCAD.GuiUp:
        ViewProviderCableBox(obj.ViewObject)
        if baseobj:
            baseobj.ViewObject.hide()
    if baseobj:
        obj.Base = baseobj
    else:
        obj.Diameter = diameter if diameter else 63
        obj.Height = height if height else 63
        obj.Thickness = 3
        # obj.Width = obj.Diameter
    obj.Ring1Diameter = 45
    obj.Ring1Height = 40
    obj.Ring2Diameter = 30
    obj.Ring2Height = 20
    obj.BoxBodyHidden = False
    obj.HelperRingsHidden = False
    if placement:
        obj.Placement = placement
    return obj
