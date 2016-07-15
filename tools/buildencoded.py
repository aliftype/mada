import sys
import os

from defcon import Font, Component
from feaTools.parser import parseFeatures, FeaToolsParserSyntaxError
from feaTools.writers.baseWriter import AbstractFeatureWriter

class FeatureWriter(AbstractFeatureWriter):
    def __init__(self):
        super(FeatureWriter).__init__()
        self.subs = {}
        self.name = ""

    def feature(self, name):
        self.name = name
        return self

    def lookup(self, name):
        self.name = ""
        return self

    def gsubType1(self, target, replacement):
        if self.name == "isol":
            self.subs[target] = [replacement]

    def gsubType2(self, target, replacement):
        if self.name == "isol":
            self.subs[target] = replacement

def addComponent(glyph, name, xoff=0, yoff=0):
    component = glyph.instantiateComponent()
    component.baseGlyph = name
    component.move((xoff, yoff))
    glyph.appendComponent(component)

def build(font):
    path = os.path.splitext(font.path)
    path = path[0].split("-")
    path = path[0] + ".fea"
    with open(path) as f:
        fea = f.read()
    writer = FeatureWriter()
    try:
        parseFeatures(writer, fea)
    except FeaToolsParserSyntaxError:
        pass
    subs = writer.subs

    for name, names in subs.items():
        baseGlyph = font[names[0]]
        glyph = font.newGlyph(name)
        glyph.unicode = int(name.lstrip('uni'), 16)
        glyph.width = baseGlyph.width
        glyph.leftMargin = baseGlyph.leftMargin
        glyph.rightMargin = baseGlyph.rightMargin
        addComponent(glyph, baseGlyph.name)
        for partName in names[1:]:
            partGlyph = font[partName]
            partAnchors = [a.name.replace("_", "", 1) for a in partGlyph.anchors if a.name.startswith("_")]
            baseAnchors = [a.name for a in baseGlyph.anchors if not a.name.startswith("_")]
            anchorName = set(baseAnchors).intersection(partAnchors)
            assert len(anchorName) == 1
            anchorName = list(anchorName)[0]
            partAnchor = [a for a in partGlyph.anchors if a.name == "_" + anchorName][0]
            baseAnchor = [a for a in baseGlyph.anchors if a.name == anchorName][0]
            xoff = baseAnchor.x - partAnchor.x
            yoff = baseAnchor.y - partAnchor.y
            addComponent(glyph, partName, xoff, yoff)
