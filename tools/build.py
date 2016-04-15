#!/usr/bin/env python2
# encoding: utf-8

import argparse
import math
import os

from datetime import datetime
from defcon import Font, Component
from fontTools.feaLib import builder as feabuilder
from fontTools.misc.transform import Transform
from fontTools.ttLib import TTFont
from goadb import GOADBParser
from tempfile import NamedTemporaryFile
from ufo2ft.outlineOTF import OutlineOTFCompiler as OTFCompiler

def find_clones(font, name):
    clones = []
    for glyph in font:
        if glyph.markColor and tuple(glyph.markColor) == (1, 0, 1, 1):
            assert len(glyph.components) > 0, glyph
            base = glyph.components[0].baseGlyph
            if base == name:
                clones.append(glyph.name)
    return clones

def is_mark(glyph):
    glyphClass = glyph.lib.get("org.fontforge.glyphclass")
    return glyphClass == "mark"

def generate_anchor(font, glyph, marks):
    fea = ""
    layer = font.layers["Marks"]
    if glyph.name not in layer or not layer[glyph.name].components:
        return fea

    bases = [glyph.name]
    for clone in find_clones(font, glyph.name):
        bases.append(clone)
        bases.extend(find_clones(font, clone))
    bases = " ".join(bases)
    kind = "base"
    if is_mark(glyph):
        kind = "mark"
    fea += "position %s [%s]" % (kind, bases)
    for component in layer[glyph.name].components:
        name = component.baseGlyph
        x = component.transformation[-2]
        y = component.transformation[-1]
        assert name in marks, name
        fea += " <anchor %d %d> mark @%s" % (x, y, name.upper())
    fea += ";"

    return fea

def generate_anchors(font):
    marks = [g.name for g in font if is_mark(g)]

    fea = ""
    for mark in marks:
        fea += "markClass [%s] <anchor 0 0> @%s;" % (mark, mark.upper())

    fea += "feature mark {"
    for glyph in font:
        if not is_mark(glyph):
            fea += generate_anchor(font, glyph, marks)
    fea += "} mark;"

    fea += "feature mkmk {"
    for glyph in font:
        if is_mark(glyph):
            fea += generate_anchor(font, glyph, marks)
    fea += "} mkmk;"

    return fea

def generate_glyphclasses(font):
    marks = []
    bases = []
    for glyph in font:
        glyphClass = glyph.lib.get("org.fontforge.glyphclass")
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

def generate_arabic_features(font, feafilename):
    fea = ""
    with open(feafilename) as feafile:
        fea += feafile.read()
        fea += generate_anchors(font)
        fea += generate_glyphclasses(font)

    return fea

def merge(args):
    arabic = Font(args.arabicfile)

    latin = Font(args.latinfile)
    goadb = GOADBParser(os.path.dirname(args.latinfile) + "/../GlyphOrderAndAliasDB")

    latin_locl = ""
    for glyph in latin:
        if glyph.name in goadb.encodings:
            glyph.unicode = goadb.encodings[glyph.name]
        if glyph.name in arabic:
            name = glyph.name
            glyph.unicode = None
            glyph.name = name + ".latin"
            if not latin_locl:
                latin_locl = "feature locl {lookupflag IgnoreMarks; script latn;"
            latin_locl += "sub %s by %s;" % (name, glyph.name)
        arGlyph = arabic.newGlyph(glyph.name)
        glyph.draw(arGlyph.getPen())
        arGlyph.width = glyph.width
        arGlyph.unicode = glyph.unicode

    arabic.info.openTypeOS2WeightClass = latin.info.openTypeOS2WeightClass
    arabic.info.xHeight = latin.info.xHeight
    arabic.info.capHeight = latin.info.capHeight

    fea = "include(../%s)\n" % (os.path.dirname(args.latinfile) + "/features")
    fea += generate_arabic_features(arabic, args.feature_file)
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

    # Set metadata
    arabic.versionMajor, arabic.versionMinor = map(int, args.version.split("."))

    copyright = 'Copyright © 2015-%s The Mada Project Authors, with Reserved Font Name "Source". Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.' % datetime.now().year

    arabic.info.copyright = copyright

    arabic.info.openTypeNameDesigner = "Khaled Hosny"
    arabic.info.openTypeNameLicenseURL = "http://scripts.sil.org/OFL"
    arabic.info.openTypeNameLicense = "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"
    arabic.info.openTypeNameDescription = "Mada is a geometric, unmodulted Arabic display typeface inspired by Cairo road signage."
    arabic.info.openTypeNameSampleText = "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار."

    return arabic, fea

def applyFeatures(font, args, fea):
    try:
        feabuilder.addOpenTypeFeaturesFromString(font, fea, args.feature_file)
    except:
        with NamedTemporaryFile(delete=False) as feafile:
            feafile.write(fea.encode("utf-8"))
            print("Failed to apply features, saved to %s" % feafile.name)
        raise

def main():
    parser = argparse.ArgumentParser(description="Create a version of Amiri with colored marks using COLR/CPAL tables.")
    parser.add_argument("arabicfile", metavar="FILE", help="input font to process")
    parser.add_argument("latinfile", metavar="FILE", help="input font to process")
    parser.add_argument("--out-file", metavar="FILE", help="output font to write", required=True)
    parser.add_argument("--feature-file", metavar="FILE", help="output font to write", required=True)
    parser.add_argument("--version", metavar="version", help="version number", required=True)

    args = parser.parse_args()

    font, fea = merge(args)
    otfCompiler = OTFCompiler(font)
    otf = otfCompiler.compile()

    applyFeatures(otf, args, fea)
    otf.save(args.out_file)

if __name__ == "__main__":
    main()
