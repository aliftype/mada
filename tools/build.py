#!/usr/bin/env python2
# encoding: utf-8

import argparse

from datetime import datetime
from defcon import Font
from fontTools.feaLib import builder as feabuilder
from fontTools.ttLib import TTFont
from tempfile import NamedTemporaryFile
from ufo2ft.outlineOTF import OutlineOTFCompiler as OTFCompiler

#from sortsmill import ffcompat as fontforge
#import psMat
import math

def find_clones(font, name):
    clones = []
    for glyph in font.glyphs():
        if glyph.color == 0xff00ff:
            assert len(glyph.references) > 0, glyph
            base = glyph.references[0][0]
            if base == name:
                clones.append(glyph.name)
    return clones

def is_mark(glyph):
    return glyph.glyphclass == "mark"

def generate_anchor(font, glyph, marks):
    fea = ""
    for ref in glyph.layerrefs["Marks"]:
        name = ref[0]
        x = ref[1][-2]
        y = ref[1][-1]
        assert name in marks, name
        bases = [glyph.name]
        for clone in find_clones(font, glyph.name):
            bases.append(clone)
            bases.extend(find_clones(font, clone))
        bases = "[" + " ".join(bases) + "]"
        if is_mark(glyph):
            fea += "position mark %s <anchor %d %d> mark @%s;" % (bases, x, y, name.upper())
        else:
            fea += "position base %s <anchor %d %d> mark @%s;" % (bases, x, y, name.upper())

    return fea

def generate_anchors(font):
    marks = [g.name for g in font.glyphs() if is_mark(g)]

    fea = ""
    for mark in marks:
        fea += "markClass [%s] <anchor 0 0> @%s;" % (mark, mark.upper())

    fea += "feature mark {"
    for glyph in font.glyphs():
        if not is_mark(glyph):
            fea += generate_anchor(font, glyph, marks)
    fea += "} mark;"

    fea += "feature mkmk {"
    for glyph in font.glyphs():
        if is_mark(glyph):
            fea += generate_anchor(font, glyph, marks)
    fea += "} mkmk;"

    return fea

def generate_arabic_features(font, feafilename):
    fea = ""
    with open(feafilename) as feafile:
        fea += feafile.read()
        fea += generate_anchors(font)

    return fea

def merge(args):
    arabic = Font(args.arabicfile)

    fea = ""

#   latin = fontforge.open(args.latinfile)
#   latin.em = arabic.em
#
#   latin_locl = ""
#   for glyph in latin.glyphs():
#       if glyph.color == 0xff0000:
#           #latin.removeGlyph(glyph)
#           pass
#       else:
#           if glyph.glyphname in arabic:
#               name = glyph.glyphname
#               glyph.unicode = -1
#               glyph.glyphname = name + ".latin"
#               if not latin_locl:
#                   latin_locl = "feature locl {lookupflag IgnoreMarks; script latn;"
#               latin_locl += "sub %s by %s;" % (name, glyph.glyphname)

#   fea = generate_arabic_features(arabic, args.feature_file)
#   fea += latin.generateFeatureString()
#   if latin_locl:
#       latin_locl += "} locl;"
#       fea += latin_locl
#
#   arabic.mergeFonts(latin)
#
#   for ch in [(ord(u'،'), "comma"), (ord(u'؛'), "semicolon")]:
#       ar = arabic.createChar(ch[0], fontforge.nameFromUnicode(ch[0]))
#       en = arabic[ch[1]]
#       colon = arabic["colon"]
#       ar.addReference(en.glyphname, psMat.rotate(math.radians(180)))
#       delta = colon.boundingBox()[1] - ar.boundingBox()[1]
#       ar.transform(psMat.translate(0, delta))
#       ar.left_side_bearing = en.right_side_bearing
#       ar.right_side_bearing = en.left_side_bearing
#
#   question_ar = arabic.createChar(ord(u'؟'), "uni061F")
#   question_ar.addReference("question", psMat.scale(-1, 1))
#   question_ar.left_side_bearing = arabic["question"].right_side_bearing
#   question_ar.right_side_bearing = arabic["question"].left_side_bearing

    # Set metadata
    arabic.versionMajor, arabic.versionMinor = map(int, args.version.split("."))

    copyright = 'Copyright © 2015-%s The Mada Project Authors, with Reserved Font Name "Source". Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.' % datetime.now().year

    arabic.info.copyright = copyright

    arabic.info.openTypeNameDesigner = "Khaled Hosny"
    arabic.info.openTypeNameLicenseURL = "http://scripts.sil.org/OFL"
    arabic.info.openTypeNameLicense = "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"
    arabic.info.openTypeNameDescription = "Mada is a geometric, unmodulted Arabic display typeface inspired by Cairo road signage."
    arabic.info.openTypeNameSampleText = "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار."

    # FIXME
    arabic.info.xHeight = 0
    arabic.info.capHeight = 0
    
    return arabic, fea

def post_process(font, args, fea):
    # for GDI
    if font["OS/2"].usWeightClass == 100:
        font["OS/2"].usWeightClass = 250

    try:
        feabuilder.addOpenTypeFeaturesFromString(font, fea, args.feature_file)
    except:
        with NamedTemporaryFile(delete=False) as feafile:
            feafile.write(fea)
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

#   flags = ["round", "no-mac-names"]
#   font.generate(args.out_file, flags=flags)
    post_process(otf, args, fea)
    otf.save(args.out_file)

if __name__ == "__main__":
    main()
