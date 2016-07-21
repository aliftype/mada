#!/usr/bin/env python
# encoding: utf-8

import argparse
import math
import os
import unicodedata

from booleanOperations import BooleanOperationManager
from datetime import datetime
from defcon import Font, Component
from fontTools import subset
from fontTools.misc.transform import Transform
from fontTools.ttLib import TTFont
from goadb import GOADBParser
from tempfile import NamedTemporaryFile
from ufo2ft import compileOTF, compileTTF

from buildencoded import build as buildEncoded

MADA_UNICODES = "org.mada.subsetUnicodes"
POSTSCRIPT_NAME = "public.postscriptName"

def generateStyleSets(ufo):
    """Generates ss01 feature which is used to move the final Yeh down so that
    it does not raise above the connecting part of other glyphs, as it does by
    default. We calculate the height difference between Yeh and Tatweel and set
    the feature accordingly."""

    tatweel = ufo["uni0640"]
    yeh = ufo["arYeh.fina"]
    delta = tatweel.bounds[-1] - yeh.bounds[-1]

    fea = """
feature ss01 {
    pos arYeh.fina <0 %s 0 0>;
} ss01;
""" % int(delta)

    return fea

def parseSubset(filename):
    """Parses a file with Unicode code points one per line, in the form of
    U+XXXX. Returns a list of the parsed code points."""

    unicodes = []
    with open(filename) as f:
        lines = f.read()
        lines = lines.split()
        unicodes = [int(c.lstrip('U+'), 16) for c in lines if c]
    return unicodes

def merge(args):
    """Merges Arabic and Latin fonts together, and messages the combined font a
    bit. Returns the combined font."""

    ufo = Font(args.arabicfile)

    latin = Font(args.latinfile)
    # Parse the GlyphOrderAndAliasDB file for Unicode values and production
    # glyph names of the Latin glyphs.
    goadb = GOADBParser(os.path.dirname(args.latinfile) + "/../GlyphOrderAndAliasDB")

    # Populate the list of Unicode characters we want to keep in the font, this
    # will eventually be passed to fontTools.subset.
    unicodes = parseSubset(args.latin_subset)
    for glyph in ufo:
        unicodes.extend(glyph.unicodes)
    unicodes.append(0x25CC) # dotted circle

    # Generate production glyph names for Arabic glyphs, in case it differs
    # from working names. This will be used by ufo2ft to set the final glyph
    # names in the font file.
    for glyph in ufo:
        if glyph.unicode is not None:
            if glyph.unicode < 0xffff:
                postName = "uni%04X" % glyph.unicode
            else:
                postName = "u%06X" % glyph.unicode
            if postName != glyph.name:
                glyph.lib[POSTSCRIPT_NAME] = postName

    # Populate the font’s feature text, we keep our main feature file out of
    # the UFO to share it between the fonts.
    features = ufo.features
    with open(args.feature_file) as feafile:
        fea = feafile.read()
        # Set Latin language system, ufo2ft will use it when generating kern
        # feature.
        features.text += fea.replace("#{languagesystems}", "languagesystem latn dflt;")
    features.text += generateStyleSets(ufo)

    # Copy Latin glyphs.
    for glyph in latin:
        if glyph.name in goadb.encodings:
            glyph.unicode = goadb.encodings[glyph.name]
            # Source Sans Pro has different advance widths for space and NBSP
            # glyphs, so we drop the later, and map both Unicode characters to
            # the space glyph.
            if glyph.unicode == 0x00A0: # NBSP
                continue
            if glyph.unicode == 0x0020: # space
                glyph.unicodes = glyph.unicodes + [0x00A0]
        # Set Latin production names
        if glyph.name in goadb.names:
            glyph.lib[POSTSCRIPT_NAME] = goadb.names[glyph.name]
        # Remove anchors from spacing marks, otherwise ufo2ft will give them
        # mark glyph class which will cause HarfBuzz to zero their width.
        if glyph.unicode and unicodedata.category(chr(glyph.unicode)) in ("Sk", "Lm"):
            for anchor in glyph.anchors:
                glyph.removeAnchor(anchor)
        # Add Arabic anchors to the dotted circle, we use an offset of 100
        # units because the Latin anchors are too close to the glyph.
        if glyph.unicode == 0x25CC:
            offset = 100
            for anchor in glyph.anchors:
                if anchor.name == "aboveLC":
                    glyph.appendAnchor(dict(name="markAbove", x=anchor.x, y=anchor.y + offset))
                    glyph.appendAnchor(dict(name="hamzaAbove", x=anchor.x, y=anchor.y + offset))
                if anchor.name == "belowLC":
                    glyph.appendAnchor(dict(name="markBelow", x=anchor.x, y=anchor.y - offset))
                    glyph.appendAnchor(dict(name="hamzaBelow", x=anchor.x, y=anchor.y - offset))
        # Break loudly if we have duplicated glyph in Latin and Arabic.
        # TODO should check duplicated Unicode values as well
        assert glyph.name not in ufo, glyph.name
        ufo.insertGlyph(glyph)

    # Copy kerning and groups.
    for group in latin.groups:
        ufo.groups[group] = latin.groups[group]
    for kern in latin.kerning:
        ufo.kerning[kern] = latin.kerning[kern]

    # We don’t set these in the Arabic font, so we just copy the Latin’s.
    for attr in ("xHeight", "capHeight"):
        value = getattr(latin.info, attr)
        if value is not None:
            setattr(ufo.info, attr, getattr(latin.info, attr))

    # Build Arabic comma and semicolon glyphs, by rotating the Latin 180°, so
    # that they are similar in design.
    for code, name in [(ord(u'،'), "comma"), (ord(u'؛'), "semicolon")]:
        glyph = ufo.newGlyph("uni%04X" % code)
        glyph.unicode = code
        enGlyph = ufo[name]
        colon = ufo["colon"]
        component = Component()
        component.transformation = tuple(Transform().rotate(math.radians(180)))
        component.baseGlyph = enGlyph.name
        glyph.appendComponent(component)
        glyph.move((0, colon.bounds[1] - glyph.bounds[1]))
        glyph.leftMargin = enGlyph.rightMargin
        glyph.rightMargin = enGlyph.leftMargin
        unicodes.append(glyph.unicode)

    # Ditto for question mark, but here we flip.
    for code, name in [(ord(u'؟'), "question")]:
        glyph = ufo.newGlyph("uni%04X" % code)
        glyph.unicode = code
        enGlyph = ufo[name]
        component = Component()
        component.transformation = tuple(Transform().scale(-1, 1))
        component.baseGlyph = enGlyph.name
        glyph.appendComponent(component)
        glyph.leftMargin = enGlyph.rightMargin
        glyph.rightMargin = enGlyph.leftMargin
        unicodes.append(glyph.unicode)

    # We will pass this later to fontTools.subsets
    ufo.lib[MADA_UNICODES] = unicodes

    return ufo

def setMetdata(info, version):
    """Sets various font metadata fields."""

    info.versionMajor, info.versionMinor = map(int, version.split("."))

    copyright = 'Copyright © 2015-%s The Mada Project Authors, with Reserved Font Name "Source". Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.' % datetime.now().year

    info.copyright = copyright

    info.openTypeNameDesigner = "Khaled Hosny"
    info.openTypeNameLicenseURL = "http://scripts.sil.org/OFL"
    info.openTypeNameLicense = "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"
    info.openTypeNameDescription = "Mada is a geometric, unmodulted Arabic display typeface inspired by Cairo road signage."
    info.openTypeNameSampleText = "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار."
    info.openTypeOS2VendorID = "BLQ "

    familyName, styleName = info.postscriptFontName.split("-")
    try:
        info.styleMapStyleName = styleName.lower()
        info.styleMapFamilyName = familyName
    except:
        pass

    if info.openTypeOS2Selection is None:
        info.openTypeOS2Selection = []
    # Set use typo metrics bit
    info.openTypeOS2Selection += [7]

    # Make sure fsType is set to 0, i.e. Installable Embedding
    info.openTypeOS2Type = []

def subsetGlyphs(otf, ufo):
    """Subsets the final font to the set of characters that we only need since
    the Latin font can have too many characters than what wee need."""
    options = subset.Options()
    options.set(layout_features='*', name_IDs='*', notdef_outline=True,
                glyph_names=True, recalc_average_width=True)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=ufo.lib.get(MADA_UNICODES))
    subsetter.subset(otf)
    return otf

def removeOverlap(ufo):
    """Removes overlap by combining overlapping contours. Not really necessary,
    but some font rendering systems need this."""
    manager = BooleanOperationManager()
    for glyph in ufo:
        contours = list(glyph)
        glyph.clearContours()
        manager.union(contours, glyph.getPointPen())

def build(args):
    ufo = merge(args)

    setMetdata(ufo.info, args.version)
    # Build fallback glyphs, these are the base glyph that cmap maps to. We
    # decompose them immediately in the layout code, so they shouldn’t be used
    # for anything and we could just keep them blank, but then FontConfig will
    # think the font does not support these characters.
    buildEncoded(ufo)
    removeOverlap(ufo)

    if args.out_file.endswith(".ttf"):
        otf = compileTTF(ufo)
    else:
        otf = compileOTF(ufo)

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
