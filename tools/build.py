#!/usr/bin/env python
# encoding: utf-8

import argparse
import math
import os

from booleanOperations import BooleanOperationManager
from cu2qu.ufo import font_to_quadratic
from datetime import datetime
from defcon import Font, Component
from fontTools import subset
from fontTools.feaLib import builder as feabuilder
from fontTools.misc.transform import Transform
from fontTools.ttLib import TTFont
from goadb import GOADBParser
from tempfile import NamedTemporaryFile
from ufo2ft.markFeatureWriter import MarkFeatureWriter
from ufo2ft.outlineOTF import OutlineOTFCompiler as OTFCompiler
from ufo2ft.outlineOTF import OutlineTTFCompiler as TTFCompiler
from ufo2ft.otfPostProcessor import OTFPostProcessor

from buildencoded import build as buildEncoded

MADA_UNICODES = "org.mada.subsetUnicodes"
FONTFORGE_GLYPHCLASS = "org.fontforge.glyphclass"
POSTSCRIPT_NAME = "public.postscriptName"

def findClones(ufo, name):
    clones = []
    for glyph in ufo:
        if glyph.markColor and tuple(glyph.markColor) == (1, 0, 1, 1):
            assert len(glyph.components) > 0, glyph
            base = glyph.components[0]
            if base.baseGlyph == name:
                clones.append(glyph.name)
    return clones

def isMark(glyph):
    glyphClass = glyph.lib.get(FONTFORGE_GLYPHCLASS)
    return glyphClass == "mark"

def addAnchors(ufo):
    layer = ufo.layers["Marks"]
    for glyph in ufo:
        if isMark(glyph):
            glyph.appendAnchor(dict(name="_" + glyph.name, x=0, y=0))
        if glyph.name not in layer:
            continue
        components = layer[glyph.name].components
        if not components:
            continue

        bases = [glyph.name]
        clones = findClones(ufo, glyph.name)
        for clone in clones:
            bases.append(clone)
            bases.extend(findClones(ufo, clone))

        anchors = []
        for component in components:
            name = component.baseGlyph
            x = component.transformation[-2]
            y = component.transformation[-1]
            assert isMark(ufo[name]), name
            anchors.append((x, y, name))

        for base in bases:
            glyph = ufo[base]
            for x, y, name in anchors:
                glyph.appendAnchor(dict(name=name, x=x, y=y))

def generateAnchors(ufo):
    anchorPairs = []
    anchorNames = set()
    for glyph in ufo:
        for anchor in glyph.anchors:
            anchorNames.add(anchor.name)

    for baseName in sorted(anchorNames):
        accentName = "_" + baseName
        if accentName in anchorNames:
            anchorPairs.append((baseName, accentName))

    writer = MarkFeatureWriter(ufo, anchorPairs, anchorPairs)
    return writer.write()

def generateGlyphclasses(ufo):
    marks = []
    bases = []
    for glyph in ufo:
        glyphClass = glyph.lib.get(FONTFORGE_GLYPHCLASS)
        if glyphClass == "mark":
            marks.append(glyph.name)
        elif glyphClass == "baseglyph":
            bases.append(glyph.name)

    fea = ""
    fea += "table GDEF {"
    fea += "GlyphClassDef "
    fea += "[%s]," % " ".join(bases)
    fea += ","
    fea += "[%s]," % " ".join(marks)
    fea += ";"
    fea += "} GDEF;"

    return fea

def generateArabicFeatures(ufo, feafilename):
    fea = ""
    with open(feafilename) as feafile:
        fea += feafile.read()
        fea += generateAnchors(ufo)
        fea += generateGlyphclasses(ufo)

    return fea

def parseSubset(filename):
    unicodes = []
    with open(filename) as f:
        lines = f.read()
        lines = lines.split()
        unicodes = [int(c.lstrip('U+'), 16) for c in lines if c]
    return unicodes

def merge(args):
    arabic = Font(args.arabicfile)

    addAnchors(arabic)

    latin = Font(args.latinfile)
    goadb = GOADBParser(os.path.dirname(args.latinfile) + "/../GlyphOrderAndAliasDB")

    buildEncoded(arabic)

    unicodes = parseSubset(args.latin_subset)
    for glyph in arabic:
        unicodes.extend(glyph.unicodes)

    fea = "include(../%s)\n" % (os.path.dirname(args.latinfile) + "/features")
    fea += generateArabicFeatures(arabic, args.feature_file)

    latin_locl = ""
    for glyph in latin:
        if glyph.name in goadb.encodings:
            glyph.unicode = goadb.encodings[glyph.name]
        if glyph.name in goadb.names:
            glyph.lib[POSTSCRIPT_NAME] = goadb.names[glyph.name]
        if glyph.name in arabic:
            name = glyph.name
            glyph.unicode = None
            glyph.name = name + ".latn"
            if glyph.lib.get(POSTSCRIPT_NAME):
                glyph.lib[POSTSCRIPT_NAME] = glyph.lib.get(POSTSCRIPT_NAME) + ".latn"
            if not latin_locl:
                latin_locl = "feature locl {lookupflag IgnoreMarks; script latn;"
            latin_locl += "sub %s by %s;" % (name, glyph.name)
        arabic.insertGlyph(glyph)

    for attr in ("xHeight", "capHeight"):
        value = getattr(latin.info, attr)
        if value is not None:
            setattr(arabic.info, attr, getattr(latin.info, attr))

    if latin_locl:
        latin_locl += "} locl;"
        fea += latin_locl

    for ch in [(ord(u'،'), "comma"), (ord(u'؛'), "semicolon")]:
        arGlyph = arabic.newGlyph("uni%04X" %ch[0])
        arGlyph.unicode = ch[0]
        enGlyph = arabic[ch[1]]
        colon = arabic["colon"]
        component = Component()
        component.transformation = tuple(Transform().rotate(math.radians(180)))
        component.baseGlyph = enGlyph.name
        arGlyph.appendComponent(component)
        arGlyph.move((0, colon.bounds[1] - arGlyph.bounds[1]))
        arGlyph.leftMargin = enGlyph.rightMargin
        arGlyph.rightMargin = enGlyph.leftMargin
        unicodes.append(arGlyph.unicode)

    for ch in [(ord(u'؟'), "question")]:
        arGlyph = arabic.newGlyph("uni%04X" %ch[0])
        arGlyph.unicode = ch[0]
        enGlyph = arabic[ch[1]]
        component = Component()
        component.transformation = tuple(Transform().scale(-1, 1))
        component.baseGlyph = enGlyph.name
        arGlyph.appendComponent(component)
        arGlyph.leftMargin = enGlyph.rightMargin
        arGlyph.rightMargin = enGlyph.leftMargin
        unicodes.append(arGlyph.unicode)

    arabic.lib[MADA_UNICODES] = unicodes

    # Set metadata
    arabic.info.versionMajor, arabic.info.versionMinor = map(int, args.version.split("."))

    copyright = 'Copyright © 2015-%s The Mada Project Authors, with Reserved Font Name "Source". Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.' % datetime.now().year

    arabic.info.copyright = copyright

    arabic.info.openTypeNameDesigner = "Khaled Hosny"
    arabic.info.openTypeNameLicenseURL = "http://scripts.sil.org/OFL"
    arabic.info.openTypeNameLicense = "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"
    arabic.info.openTypeNameDescription = "Mada is a geometric, unmodulted Arabic display typeface inspired by Cairo road signage."
    arabic.info.openTypeNameSampleText = "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار."

    return arabic, fea

def applyFeatures(otf, fea, feafilename):
    try:
        feabuilder.addOpenTypeFeaturesFromString(otf, fea, feafilename)
    except:
        with NamedTemporaryFile(delete=False) as feafile:
            feafile.write(fea.encode("utf-8"))
            print("Failed to apply features, saved to %s" % feafile.name)
        raise
    return otf

def postProcess(otf, ufo):
    postProcessor = OTFPostProcessor(otf, ufo)
    otf = postProcessor.process(optimizeCff=True)
    return otf

def subsetGlyphs(otf, ufo):
    options = subset.Options()
    options.set(layout_features='*', name_IDs='*', notdef_outline=True)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=ufo.lib.get(MADA_UNICODES))
    subsetter.subset(otf)
    return otf

def removeOverlap(ufo):
    manager = BooleanOperationManager()
    for glyph in ufo:
        contours = list(glyph)
        glyph.clearContours()
        manager.union(contours, glyph.getPointPen())
    return ufo

def build(args):
    ufo, fea = merge(args)
    ufo = removeOverlap(ufo)

    if args.out_file.endswith(".ttf"):
        font_to_quadratic(ufo)
        otfCompiler = TTFCompiler(ufo)
    else:
        otfCompiler = OTFCompiler(ufo)
    otf = otfCompiler.compile()

    otf = applyFeatures(otf, fea, args.feature_file)
    otf = postProcess(otf, ufo)
    otf = subsetGlyphs(otf, ufo)

    return otf

def main():
    parser = argparse.ArgumentParser(description="Build Mada fonts.")
    parser.add_argument("arabicfile", metavar="FILE", help="input font to process")
    parser.add_argument("latinfile", metavar="FILE", help="input font to process")
    parser.add_argument("--out-file", metavar="FILE", help="output font to write", required=True)
    parser.add_argument("--feature-file", metavar="FILE", help="output font to write", required=True)
    parser.add_argument("--latin-subset", metavar="FILE", help="file containing Latin code points to keep", required=True)
    parser.add_argument("--version", metavar="version", help="version number", required=True)

    args = parser.parse_args()

    otf = build(args)
    otf.save(args.out_file)

if __name__ == "__main__":
    main()
