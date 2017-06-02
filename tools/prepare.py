#!/usr/bin/env python
# encoding: utf-8

import argparse
import math
import os
import unicodedata

from collections import Counter
from datetime import datetime
from defcon import Font, Component
from fontTools.misc.py23 import *
from fontTools.misc.transform import Transform
from goadb import GOADBParser

from buildencoded import build as buildEncoded

POSTSCRIPT_NAMES = "public.postscriptNames"

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

def collectGlyphs(ufo, subset):
    """Collects the list of glyphs we want to keep in the font, based on
    subset."""

    unicodes = parseSubset(subset)
    unicodes.append(0x25CC) # dotted circle

    glyphs = set()
    components = []

    for glyph in ufo:
        if glyph.unicode in unicodes:
            glyphs.add(glyph.name)
            components.extend([c.baseGlyph for c in glyph.components])

    return glyphs, components

def merge(args):
    """Merges Arabic and Latin fonts together, and messages the combined font a
    bit. Returns the combined font."""

    ufo = Font(args.arabicfile)

    latin = Font(args.latinfile)
    # Parse the GlyphOrderAndAliasDB file for Unicode values and production
    # glyph names of the Latin glyphs.
    goadb = GOADBParser(os.path.dirname(args.latinfile) + "/../GlyphOrderAndAliasDB")

    ufo.lib[POSTSCRIPT_NAMES] = {}

    # Save original glyph order, used below.
    glyphOrder = ufo.glyphOrder + latin.glyphOrder

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
                ufo.lib[POSTSCRIPT_NAMES][glyph.name] = postName

    # Populate the font’s feature text, we keep our main feature file out of
    # the UFO to share it between the fonts.
    features = ufo.features
    with open(args.feature_file) as feafile:
        fea = feafile.read()
        # Set Latin language system, ufo2ft will use it when generating kern
        # feature.
        features.text += fea.replace("#{languagesystems}", "languagesystem latn dflt;")
    features.text += generateStyleSets(ufo)

    for glyph in latin:
        if glyph.name in goadb.encodings:
            glyph.unicode = goadb.encodings[glyph.name]

    # Source Sans Pro has different advance widths for space and NBSP
    # glyphs, fix it.
    latin["nbspace"].width = latin["space"].width

    glyphs, components = collectGlyphs(latin, args.latin_subset)

    counter = Counter(components)
    uniqueComponents = set()
    for name in counter:
        if name not in glyphs:
            latin[name].unicode = None
        if counter[name] == 1:
            uniqueComponents.add(name)
        else:
            glyphs.add(name)

    # Set Latin production names
    ufo.lib[POSTSCRIPT_NAMES].update(goadb.names)

    # Copy Latin glyphs.
    for name in glyphs:
        glyph = latin[name]
        for component in glyph.components:
            if component.baseGlyph in uniqueComponents:
                glyph.decomposeComponent(component)
        # Remove anchors from spacing marks, otherwise ufo2ft will give them
        # mark glyph class which will cause HarfBuzz to zero their width.
        if glyph.unicode and unicodedata.category(unichr(glyph.unicode)) in ("Sk", "Lm"):
            for anchor in glyph.anchors:
                glyph.removeAnchor(anchor)
        # Add Arabic anchors to the dotted circle, we use an offset of 100
        # units because the Latin anchors are too close to the glyph.
        offset = 100
        if glyph.unicode == 0x25CC:
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

    # MutatorMath does not like multiple unicodes and will drop it entirely,
    # turning the glyph unencoded:
    # https://github.com/LettError/MutatorMath/issues/85
    for glyph in ufo:
        assert not " " in glyph.unicodes

    # Make sure we don’t have glyphs with the same unicode value
    unicodes = []
    for glyph in ufo:
        unicodes.extend(glyph.unicodes)
    duplicates = set([u for u in unicodes if unicodes.count(u) > 1])
    assert len(duplicates) == 0, "Duplicate unicodes: %s " % (["%04X" % d for d in duplicates])

    # Make sure we have a fixed glyph order by using the original Arabic and
    # Latin glyph order, not whatever we end up with after adding glyphs.
    ufo.glyphOrder = sorted(ufo.glyphOrder, key=glyphOrder.index)

    return ufo

def buildExtraGlyphs(ufo):
    """Builds some necessary glyphs at runtime that are derived from other
    glyphs, instead of having to update them manually."""

    # Build fallback glyphs, these are the base glyph that cmap maps to. We
    # decompose them immediately in the layout code, so they shouldn’t be used
    # for anything and we could just keep them blank, but then FontConfig will
    # think the font does not support these characters.
    buildEncoded(ufo)

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

def setInfo(info, version):
    """Sets various font metadata fields."""

    info.versionMajor, info.versionMinor = map(int, version.split("."))

    copyright = u'Copyright © 2015-%s The Mada Project Authors, with Reserved Font Name "Source". Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.' % datetime.now().year

    info.copyright = copyright

    info.openTypeNameDesigner = u"Khaled Hosny"
    info.openTypeNameLicenseURL = u"http://scripts.sil.org/OFL"
    info.openTypeNameLicense = u"This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"
    info.openTypeNameDescription = u"Mada is a geometric, unmodulted Arabic display typeface inspired by Cairo road signage."
    info.openTypeNameSampleText = u"صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار."
    info.openTypeOS2VendorID = "ALIF"

    if info.openTypeOS2Selection is None:
        info.openTypeOS2Selection = []
    # Set use typo metrics bit
    info.openTypeOS2Selection += [7]

    # Make sure fsType is set to 0, i.e. Installable Embedding
    info.openTypeOS2Type = []

def build(args):
    ufo = merge(args)
    setInfo(ufo.info, args.version)
    buildExtraGlyphs(ufo)

    return ufo

def main():
    parser = argparse.ArgumentParser(description="Build Mada fonts.")
    parser.add_argument("arabicfile", metavar="FILE", help="input font to process")
    parser.add_argument("latinfile", metavar="FILE", help="input font to process")
    parser.add_argument("--out-file", metavar="FILE", help="output font to write", required=True)
    parser.add_argument("--feature-file", metavar="FILE", help="output font to write", required=True)
    parser.add_argument("--latin-subset", metavar="FILE", help="file containing Latin code points to keep", required=True)
    parser.add_argument("--version", metavar="version", help="version number", required=True)

    args = parser.parse_args()

    ufo = build(args)
    ufo.save(args.out_file)

if __name__ == "__main__":
    main()
